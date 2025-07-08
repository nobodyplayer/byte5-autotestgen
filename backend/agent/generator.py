from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from operator import itemgetter
import asyncio


from config.config import (
    DETECTOR_AGENT_PROMPT, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_SEARCH_K, GENERATOR_AGENT_PROMPT,
    CASE_GENERATION_BATCH_SIZE
)
from utils.json_parse_util import parse_json_output

from models.state import TestCaseGenerationState


def analyser_agent_node(state:TestCaseGenerationState, llm: BaseChatModel) -> list:
    """
    分析器/检测器节点。

    功能描述:
        该节点作为工作流的前期步骤，负责从原始需求文档（PRD）中分析并提取出
        核心的测试点或功能模块。它可以选择性地接收上一次“总体评估”的反馈报告
        （mistake），从而在再次分析时能够规避之前的错误，实现迭代优化。
        该节点同样包含了对LLM输出的智能解析和启发式回退机制。

    Args:
        state (TestCaseGenerationState): 当前工作流的状态对象，需包含：
            - prd_content (str): 原始的产品需求文档内容。
            - total_evaluation_report (dict, optional): 上一轮的总体评估报告，可选。
        llm (BaseChatModel): 用于分析和提取的大语言模型实例。

    Returns:
        list: 一个包含所有从文档中提取出的测试点（字符串）的列表。
              如果发生严重错误，则返回空列表。
    """
    print("--- Node: 分析器")
    if not llm:
        print("没有可用的大语言模型")
    if not state or state["prd_content"] is None:
        print("需求文档为空")

    # 判断是否存在之前的评估report
    if not state["total_evaluation_report"]:
        evaluation_report = None
    else:
        evaluation_report = state["total_evaluation_report"].get("justification")

    try:
        # 链条构建
        app_prompt = ChatPromptTemplate.from_template(DETECTOR_AGENT_PROMPT)
        app_chain = app_prompt | llm | StrOutputParser()

        result_str = app_chain.invoke({"text": state["prd_content"], "mistake": evaluation_report})
        print(result_str)

        # 转JSON
        parsed_apps = parse_json_output(result_str, expected_type=list)

        # 文档解析失败
        if parsed_apps is None:
            # 启发式解析，判断是否返回了一个逗号分割的简单字符串
            if result_str and not result_str.startswith("I cannot") and len(
                    result_str) < 200 and '[' not in result_str and '{' not in result_str:
                possible_apps = [app.strip().strip("'\"") for app in result_str.split(',') if app.strip()]
                if possible_apps:
                    return sorted(list(set(possible_apps)))
            return []
        return parsed_apps
    except Exception as e:
        print(f"!!!!!!!!!! 在detector_agent_node中发生严重错误 !!!!!!!!!!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        return []

async def generator_agent_node(state:TestCaseGenerationState, llm: BaseChatModel, embeddings: Embeddings) -> list:
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
    print("--- Node: 生成器")
    if not llm:
        print("没有可用的大语言模型")
    if not embeddings:
        print("没有可用的嵌入")
    if not state or state["prd_content"] is None:
        print("需求文档为空")
    if not state or state["detected_testPoint"] == []:
        print("未检测到测试点")

    # 文本向量化
    if state.get("vectorstore") is None:
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
            )
            splits = text_splitter.split_text(state["prd_content"])
            if not splits:
                print("文本分割失败")
                return []
            vectorstore = FAISS.from_texts(splits, embedding=embeddings)
        except Exception as e:
            print(f"!!!!!!!!!! 文本向量化过程中发生错误 !!!!!!!!!!")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {e}")
            return []
        state["vectorstore"] = vectorstore  # 存入状态
    else:
        vectorstore = state["vectorstore"]


    # RAG
    try:
        retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_SEARCH_K})
        case_generation_prompt = ChatPromptTemplate.from_template(GENERATOR_AGENT_PROMPT)
        document_chain = create_stuff_documents_chain(llm, case_generation_prompt)
        retriever_chain = create_retrieval_chain(retriever, document_chain) | itemgetter("answer")
    except Exception as e:
        print(f"!!!!!!!!!! 构建过程链过程中发生错误 !!!!!!!!!!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        return []

    if not retriever_chain:
        print("链条创建失败")
        return []
    test_cases = []
    try:
        batch_num = int(len(state["detected_testPoint"]) / CASE_GENERATION_BATCH_SIZE)
        # 异步处理
        tasks = []
        for i in range(batch_num + 1):
            if i == batch_num:
                input_batch = str(state["detected_testPoint"][i * CASE_GENERATION_BATCH_SIZE:])
            else:
                input_batch = str(state["detected_testPoint"][i * CASE_GENERATION_BATCH_SIZE : (i + 1) * CASE_GENERATION_BATCH_SIZE])
            task = retriever_chain.ainvoke({"input": input_batch})
            tasks.append(task)
        batch_results_list = await asyncio.gather(*tasks)
        for result_str in batch_results_list:
            print(result_str)  # 打印每个批次的结果
            # 转json
            batch_case = parse_json_output(result_str, expected_type=list)
            # 加入批次
            if batch_case is not None:
                test_cases.extend(batch_case)
        print(test_cases)
        return test_cases
    except Exception as e:
        print(f"!!!!!!!!!! 在generator_agent_node中发生严重错误 !!!!!!!!!!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        return []




