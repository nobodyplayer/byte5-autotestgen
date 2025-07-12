from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnablePassthrough

import utils.agent_util as agent_util
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from operator import itemgetter
import asyncio
import logging
import langchain

from config.config import (
    DETECTOR_AGENT_PROMPT, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_SEARCH_K, GENERATOR_AGENT_PROMPT,
    CASE_GENERATION_BATCH_SIZE, QUERY_GENERATE_PROMPT
)
from utils.json_parse_util import parse_json_output

from models.state import TestCaseGenerationState

logger = logging.getLogger(__name__)


def analyser_agent_node(state: TestCaseGenerationState, llm: BaseChatModel) -> dict:
    """
    分析器/检测器节点（最终版：带唯一ID生成）。

    功能描述:
        该节点将PRD内容结构化地分解为“功能模块 -> 测试点列表”的映射，
        并为每一个被识别出的测试点，赋予一个全局唯一的、带前缀的编号（如 TP-001）。

    Args:
        state (TestCaseGenerationState): 当前工作流的状态对象。
        llm (BaseChatModel): 用于分析和提取的大语言模型实例。

    Returns:
        list: 一个扁平化的测试点列表，每个元素是一个字典，格式为
              {"case_ID": "TP-001", "function": "功能名", "testPoint": "测试点描述"}。
              如果出错则返回空列表。
    """
    # --- 1.参数检查 ---
    logger.info("--- Node: 分析器")
    if not llm:
        logger.error("没有可用的大语言模型")
        return {}
    if not state or state["prd_content"] is None:
        logger.error("需求文档为空")
        return {}

    # --- 2.判断是否存在之前的评估report ---
    if not state["total_evaluation_report"]:
        evaluation_report = None
    else:
        evaluation_report = state["total_evaluation_report"].get("justification")
    if not state["detected_test_point_dict"]:
        test_point_dict = None
    else:
        test_point_dict = state["detected_test_point_dict"]

    try:
        # --- 3.链条构建 ---
        app_prompt = ChatPromptTemplate.from_template(DETECTOR_AGENT_PROMPT)
        app_chain = app_prompt | llm | JsonOutputParser()

        result_dict = app_chain.invoke(
            {"text": state["prd_content"], "mistake": evaluation_report or "无", "result": test_point_dict or "无"})
        logger.info(f"LLM返回结果：{result_dict}")
        return result_dict
    except Exception as e:
        logger.error(f"!!!!!!!!!! 在detector_agent_node中发生严重错误:{e} !!!!!!!!!!", exc_info=True)
        return {}


async def generator_agent_node(state: TestCaseGenerationState, llm: BaseChatModel, embeddings: Embeddings) -> list:
    """
    测试用例生成器节点。

    功能描述:
        该节点是工作流的核心生成步骤。它接收“分析器”节点提取出的测试点列表，
        并为这些测试点生成详细的、结构化的测试用例。此节点利用RAG（检索增强生成）
        技术，将需求文档（PRD）作为上下文知识库，确保生成的每个测试用例都紧密
        贴合原始需求，内容详实且准确。生成过程以批量方式进行以提高效率。

    Args:
        state (TestCaseGenerationState): 当前工作流的状态对象，需包含：
            - prd_content (str): 原始的产品需求文档内容。
            - detected_testPoint (list): “分析器”节点提取出的测试点列表。
        llm (BaseChatModel): 用于生成测试用例的大语言模型实例。
        embeddings (Embeddings): 用于文本向量化的嵌入模型实例。

    Returns:
        list: 一个包含所有生成的测试用例（通常是字典格式）的列表。
              如果发生严重错误，则返回空列表。
    """
    # --- 1. 检查参数 ---
    logger.info("--- Node: 生成器")
    langchain.verbose = True
    if not llm:
        logger.error("没有可用的大语言模型")
        return []
    if not embeddings:
        logger.error("没有可用的嵌入")
        return []
    if not state or state["prd_content"] is None:
        logger.error("需求文档为空")
        return []
    if not state or state["detected_test_point_list"] == []:
        logger.error("未检测到测试点")
        return []

    # --- 2.文本向量化 ---
    if state.get("prd_vector") is None:
        vectorstore = agent_util.text_split(state["prd_content"], embeddings)
        state["prd_vector"] = vectorstore  # 存入状态
    else:
        vectorstore = state["prd_vector"]

    # --- 3.查询生成 + rag链条构建 ---
    try:
        query_generator_prompt = ChatPromptTemplate.from_template(QUERY_GENERATE_PROMPT)
        query_generator_chain = query_generator_prompt | llm | StrOutputParser()
        retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_SEARCH_K})
        case_generation_prompt = ChatPromptTemplate.from_template(GENERATOR_AGENT_PROMPT)
        # document_chain = create_stuff_documents_chain(llm, case_generation_prompt)
        # retriever_chain = create_retrieval_chain(retriever, document_chain) | itemgetter("answer")
        # end_to_end_chain = (
        #         {"input": query_generator_chain}
        #         | retriever_chain
        # )
        # 步骤A: 定义RAG的数据准备部分
        end_to_end_chain = (
            # 步骤1：接收原始输入，并将其存储在'original_input'键中，同时透传下去
                RunnablePassthrough.assign(
                    original_input=itemgetter("input")
                )
                # 此步输出: {"input": "测试点列表...", "original_input": "测试点列表..."}0.
                | RunnablePassthrough.assign(
            # 步骤2：使用原始输入生成“超级查询”，并将其结果存储在'super_query'键中
            super_query=itemgetter("original_input") | query_generator_chain
        )
                # 此步输出: {"input": ..., "original_input": ..., "super_query": "超级查询..."}
                | RunnableLambda(debug_super_query)
                | RunnablePassthrough.assign(
            # 步骤3：使用“超级查询”进行RAG检索，并将结果存储在'context'键中
            context=itemgetter("super_query") | retriever
        )
                # 此步输出: {"input": ..., "original_input": ..., "super_query": ..., "context": [Docs...]}
                # 步骤4：将最终需要的信息喂给Prompt模板
                | {
                    "context": itemgetter("context"),
                    # 关键：我们在这里传入的是最开始的`original_input`，而不是`super_query`
                    "input": itemgetter("original_input")
                }
                | RunnableLambda(debug_and_print_prompt_inputs)
                | case_generation_prompt
                | llm
                | StrOutputParser()
        )
    except Exception as e:
        logging.error(f"!!!!!!!!!! 构建过程链过程中发生错误： {e} !!!!!!!!!!", exc_info=True)
        return []

    if not end_to_end_chain:
        logging.error("链条创建失败")
        return []

    # --- 4.分批次生成测试用例 ---
    test_cases = []
    try:
        # 按功能处理
        tasks = []
        index = 0
        for function_name, test_point in state["detected_test_point_dict"].items():
            batch_num = int(len(test_point) / CASE_GENERATION_BATCH_SIZE)
            # 异步处理
            for i in range(batch_num + 1):
                if i == batch_num:
                    input_batch = str(
                        f"# 测试功能：{function_name} # 测试点列表："
                        f"{state["detected_test_point_list"][index + i * CASE_GENERATION_BATCH_SIZE: index + len(test_point)]}"
                    )
                else:
                    input_batch = str(
                        f"# 测试功能：{function_name} # 测试点列表："
                        f"{state["detected_test_point_list"][index + i * CASE_GENERATION_BATCH_SIZE: index + (i + 1) * CASE_GENERATION_BATCH_SIZE]}"
                    )
                logger.info(input_batch)
                task = end_to_end_chain.ainvoke({"input": input_batch})
                tasks.append(task)
            index += len(test_point)
        batch_results_list = await asyncio.gather(*tasks)
        for result_str in batch_results_list:
            logger.info(result_str)  # 打印每个批次的结果
            # 转json
            batch_case = parse_json_output(result_str, expected_type=list)
            # 加入批次
            if batch_case is not None:
                test_cases.extend(batch_case)
        logger.info(f"最终结果{test_cases}")
        return test_cases
    except Exception as e:
        logger.error(f"!!!!!!!!!! 在generator_agent_node中发生严重错误 {e} !!!!!!!!!!", exc_info=True)
        return []


def debug_and_print_prompt_inputs(data_dict: dict) -> dict:
    """
    一个用于调试的函数，它会打印即将用于填充最终生成Prompt的数据。
    """
    print("\n" + "=" * 50)
    print("--- 即将填充生成器Prompt，输入数据如下 ---")

    # 关键修改：这里的键名是 'input'，对应上一步筛选器输出的键名
    print(f"\n[INPUT (原始测试点列表)]:\n{data_dict.get('input')}")
    print(f"\n[SUPER_QUERY]:\n{data_dict.get('')}]")

    # 打印上下文
    context_docs = data_dict.get('context', [])
    print(f"\n[CONTEXT] (检索到 {len(context_docs)} 个文档):")
    for i, doc in enumerate(context_docs):
        print(f"  --- 文档 {i + 1} ---\n  {doc.page_content[:200]}...\n  ---------------")

    print("=" * 50 + "\n")

    # 必须原样返回，让链条可以继续执行
    return data_dict


def debug_super_query(state_dict: dict) -> dict:
    """
    这个探针函数专门用于打印'super_query'的值。
    """
    print("\n" + "---" * 20)
    print("--- 观测点：超级查询已生成 ---")

    super_query_text = state_dict.get('super_query', '未找到super_query')
    print(f"\n[SUPER QUERY]:\n{super_query_text}")

    print("---" * 20 + "\n")

    # 必须原样返回整个状态字典，让链条可以继续执行
    return state_dict
