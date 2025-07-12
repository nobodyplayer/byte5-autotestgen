import asyncio
import logging
from operator import itemgetter

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

import utils.agent_util as agent_util
from config.config import (
    RETRIEVER_SEARCH_K, SINGLE_EVALUATOR_AGENT_PROMPT,
    TOTAL_EVALUATOR_AGENT_PROMPT, CASE_EVALUATION_BATCH_SIZE, QUERY_GENERATE_PROMPT
)
from models.state import TestCaseGenerationState

logger = logging.getLogger(__name__)


async def single_evaluator_agent_node(state: TestCaseGenerationState, llm: BaseChatModel, embeddings: Embeddings) -> list:
    """
    单例评估器节点（微观评估）。

    功能描述:
        该节点负责对已生成的测试用例进行详细评估。它采用RAG（检索增强生成）技术，
        首先将需求文档（PRD）向量化并存入FAISS向量库。然后，对于每一批测试用例，
        它会从向量库中检索最相关的需求片段作为上下文，再调用大语言模型（LLM）
        判断测试用例的准确性、相关性和有效性。

    Args:
        state (TestCaseGenerationState): 当前工作流的状态对象，需包含：
            - prd_content (str): 原始的产品需求文档内容。
            - generated_cases (list): 已生成的测试用例列表。
        llm (BaseChatModel): 用于评估的大语言模型实例。
        embeddings (Embeddings): 用于文本向量化的嵌入模型实例。

    Returns:
        list: 一个包含所有测试用例评估结果的列表。每个评估结果通常是一个字典。
                如果过程中发生严重错误，则返回空列表。
    """
    # --- 1.检查参数 ---
    logger.info("--- Node: 单例评估器")
    if not llm or not embeddings:
        logger.error("没有大模型或嵌入")
        return []
    if not state or state["prd_content"] is None:
        logger.error("需求文档为空")
        return []
    if not state or state["generated_cases"] == []:
        logger.error("没有生成的测试用例")
        return []

    # --- 2.文本向量化 ---
    if state.get("prd_vector") is None:
        vectorstore = agent_util.text_split(state["prd_content"], embeddings)
        state["prd_vector"] = vectorstore  # 存入状态
    else:
        vectorstore = state["prd_vector"]

    # --- 3.超级查询 + RAG链条构建 ---
    try:
        # 超级查询生成链条
        query_generator_prompt = ChatPromptTemplate.from_template(QUERY_GENERATE_PROMPT)
        query_generator_chain = query_generator_prompt | llm | StrOutputParser()
        # 检索器
        retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_SEARCH_K})
        case_generation_prompt = ChatPromptTemplate.from_template(SINGLE_EVALUATOR_AGENT_PROMPT)
        # 整体的端到端链条
        end_to_end_chain = (
            # ↓ 原始输入input存储在'original_input'键中并透传
            RunnablePassthrough.assign(
                original_input=itemgetter("input")
            )
            # ↑ e.g. {"input": "测试点列表...", "original_input": "测试点列表..."}
            # ↓ 使用原始输入生成“超级查询”，并将其结果存储在'super_query'键中
            | RunnablePassthrough.assign(
                super_query=itemgetter("original_input") | query_generator_chain
            )
            # ↑ e.g. {"input": ..., "original_input": ..., "super_query": "超级查询..."}
            # ↓ 使用“超级查询”进行RAG检索，并将结果存储在"context"键中
            | RunnablePassthrough.assign(
                context=itemgetter("super_query") | retriever
            )
            # ↑ {"input": ..., "original_input": ..., "super_query": ..., "context": [Docs...]}
            # ↓ Prompt模板填充
            | {
                "context": itemgetter("context"),
                "input": itemgetter("original_input")
            }
            | case_generation_prompt
            | llm
            | JsonOutputParser()
        )
    except Exception as e:
        logger.error(f"!!!!!!!!!! 构建过程链过程中发生错误 !!!!!!!!!! {e}", exc_info=True)
        return []
    if not end_to_end_chain:
        logger.error("单例评估过程，链条创建失败")
        return []

    # --- 4.数据分组处理 ---
    grouped_data = {}
    for item in state["generated_cases"]:
        key_value = item["function"]
        if key_value not in grouped_data:
            grouped_data[key_value] = []
        grouped_data[key_value].append(item)

    # --- 5.大模型评估 ---
    try:
        eval_report = []
        # 异步任务列表
        tasks = []
        for function_name, cases in grouped_data.items():
            batch_num = int(len(cases) / CASE_EVALUATION_BATCH_SIZE)
            for i in range(batch_num + 1):
                if i == batch_num:
                    input_batch = str(f"# 测试功能：{function_name} "
                                      f"# 测试用例：{cases[i * CASE_EVALUATION_BATCH_SIZE:]}")
                else:
                    input_batch = str(f"# 测试功能：{function_name} "
                                      f"# 测试用例：{cases[i * CASE_EVALUATION_BATCH_SIZE: (i + 1) * CASE_EVALUATION_BATCH_SIZE]}")
                task = end_to_end_chain.ainvoke({"input": input_batch})
                tasks.append(task)
        batch_result_list = await asyncio.gather(*tasks)
        for result_dict in batch_result_list:
            logger.info(f"单例评估单次大模型输出结果：{result_dict}")
            # 加入批次
            if result_dict is not None:
                eval_report.extend(result_dict)
        logger.info(f"单例评估最终输出结果：{eval_report}")
        return eval_report
    except Exception as e:
        logger.info(f"!!!!!!!!!! 在generator_agent_node中发生严重错误 {e} !!!!!!!!!!", exc_info=True)
        return []


def total_evaluator_agent_node(state: TestCaseGenerationState, llm: BaseChatModel) -> dict:
    """
    总体评估器节点（宏观评估）。

    功能描述:
        该节点负责从整体上评估测试的覆盖度。它接收完整的需求文档和从文档中
        提取出的所有测试点（Test Points），然后调用大语言模型进行一次性的
        高层次分析，判断这些测试点是否全面、无遗漏地覆盖了需求文档中的
        所有关键功能。该节点包含一个智能的启发式回退机制，用于处理LLM未按
        预期返回JSON格式的情况。

    Args:
        state (TestCaseGenerationState): 当前工作流的状态对象，需包含：
            - prd_content (str): 原始的产品需求文档内容。
            - detected_testPoint (list): 从需求中提取出的所有测试点的列表。
        llm (BaseChatModel): 用于评估的大语言模型实例。

    Returns:
        dict | list: 理想情况下返回一个包含整体评估结论的字典。
                    如果JSON解析失败，但启发式解析成功，则可能返回一个字符串列表。
                    如果发生严重错误，则返回空列表。
    """
    logger.info("--- Node: 全体评估器")
    # --- 1.检查参数 ---
    if not llm:
        logger.error("没有可用的大语言模型")
        return {}
    if not state or state["prd_content"] is None:
        logger.error("需求文档为空")
        return {}
    if not state or state["detected_test_point_dict"] == {}:
        logger.error("解析的测试点列表为空")
        return {}

    try:
        # --- 2.构建整体链条 ---
        app_prompt = ChatPromptTemplate.from_template(TOTAL_EVALUATOR_AGENT_PROMPT)
        app_chain = app_prompt | llm | JsonOutputParser()
        # --- 3.执行评估 ---
        result_dict = app_chain.invoke({"document": state["prd_content"], "testPoint": state["detected_test_point_dict"]})
        logger.info(f"全体评估器输出的JSON对象：{result_dict}")
        return result_dict
    except Exception as e:
        logger.error(f"!!!!!!!!!! 在total_evaluator_node中发生严重错误:{e}!!!!!!!!!!", exc_info=True)
        return {}
