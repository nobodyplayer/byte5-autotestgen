import asyncio
import logging
from operator import itemgetter

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

import utils.agent_util as agent_util
from config.config import (
    RETRIEVER_SEARCH_K, CASE_RECONSTRUCTION_BATCH_SIZE,
    RECONSTRUCTION_AGENT_PROMPT, QUERY_GENERATE_PROMPT
)
from models.state import TestCaseGenerationState
from utils.json_parse_util import parse_json_output

logger = logging.getLogger(__name__)


async def reconstructor_agent_node(state: TestCaseGenerationState, llm: BaseChatModel, embeddings: Embeddings) -> list:
    """
    测试用例重构器节点。

    功能描述:
       该节点是工作流中的“修正”与“优化”环节，体现了迭代改进的思想。
       它接收初始生成的测试用例（generated_cases）以及针对这些用例的
       “单例评估”报告（single_evaluation_report）。
       其核心任务是根据评估报告中提供的修改建议，对原始测试用例进行重构和修正。
       此过程同样利用RAG技术，确保重构后的用例在修正缺陷的同时，
       依然严格遵循原始需求文档（PRD）的上下文。

    Args:
        state (TestCaseGenerationState): 当前工作流的状态对象，需包含：
            - prd_content (str): 原始的产品需求文档内容。
            - generated_cases (list): 由生成器节点创建的初始测试用例列表。
            - single_evaluation_report (list): 由单例评估器生成的评估报告和修改建议。
        llm (BaseChatModel): 用于执行重构任务的大语言模型实例。
        embeddings (Embeddings): 用于文本向量化的嵌入模型实例。

    Returns:
        list: 一个包含所有经过重构和修正后的测试用例（通常是字典格式）的列表。
              如果发生严重错误，则返回空列表。
   """
    # --- 1.参数检查 ---
    logger.info("--- Node: 重构器")
    if not llm:
        logger.error("没有可用的大语言模型")
        return []
    if not embeddings:
        logger.error("没有可用的嵌入模型")
        return []
    if not state or state["prd_content"] is None:
        logger.error("需求文档为空")
        return []
    if not state or state["detected_test_point_dict"] == {}:
        logger.error("未检测到测试点")
        return []
    if not state or state["generated_cases"] == []:
        logger.error("没有生成的测试案例")
        return []
    if not state or state["single_evaluation_report"] == []:
        logger.error("没有评估文档")
        return []

    # --- 2.文本向量化 ---
    if state.get("prd_vector") is None:
        vectorstore = agent_util.text_split(state["prd_content"], embeddings)
        state["prd_vector"] = vectorstore  # 存入状态
    else:
        vectorstore = state["prd_vector"]

    # --- 3.超级查询 + RAG链条构建
    try:
        # 超级查询生成链条
        query_generator_prompt = ChatPromptTemplate.from_template(QUERY_GENERATE_PROMPT)
        query_generator_chain = query_generator_prompt | llm | StrOutputParser()
        # 检索器
        retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_SEARCH_K})
        case_generation_prompt = ChatPromptTemplate.from_template(RECONSTRUCTION_AGENT_PROMPT)
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
        logger.error(f"!!!!!!!!!! 构建过程链过程中发生错误 {e} !!!!!!!!!!", exc_info=True)
        return []
    if not end_to_end_chain:
        logger.error("重构器链条创建失败")
        return []

    # --- 4.数据分组处理 ---
    grouped_cases = {}
    grouped_eval_report = {}
    case_eval_map = {item['case_ID']: item for item in state["single_evaluation_report"]}
    for item in state["generated_cases"]:
        key_value = item["function"]
        if key_value not in grouped_cases:
            grouped_cases[key_value] = []
            grouped_eval_report[key_value] = []
        grouped_cases[key_value].append(item)
        grouped_eval_report[key_value].append(case_eval_map[item['case_ID']])

    # --- 5.大模型评估 ---
    try:
        # 异步处理
        tasks = []
        reconstruct_case = []
        for function_name, cases in grouped_cases.items():
            batch_num = int(len(cases) / CASE_RECONSTRUCTION_BATCH_SIZE)
            for i in range(batch_num + 1):
                if i == batch_num:
                    case_batch = str(cases[i * CASE_RECONSTRUCTION_BATCH_SIZE:])
                    eval_batch = str(grouped_eval_report[function_name][i * CASE_RECONSTRUCTION_BATCH_SIZE:])
                else:
                    case_batch = str(cases[i * CASE_RECONSTRUCTION_BATCH_SIZE: (i + 1) * CASE_RECONSTRUCTION_BATCH_SIZE])
                    eval_batch = str(grouped_eval_report[function_name][i * CASE_RECONSTRUCTION_BATCH_SIZE: (i + 1) * CASE_RECONSTRUCTION_BATCH_SIZE])
                input_str = f"""
                    # 进行重构的功能
                    {function_name}
                    # 待重构的原始测试用例列表:
                    {case_batch}
                    # 评估信息与修改建议列表
                    {eval_batch}
                """
                task = end_to_end_chain.ainvoke({"input": input_str})
                tasks.append(task)
        batch_result_list = await asyncio.gather(*tasks)
        for result_dict in batch_result_list:
            logger.info(f"单例评估单次大模型输出结果：{result_dict}")
            # 加入批次
            if result_dict is not None:
                reconstruct_case.extend(result_dict)
        logger.info(f"单例评估最终输出结果：{reconstruct_case}")
        return reconstruct_case
    except Exception as e:
        logger.error(f"!!!!!!!!!! 在generator_agent_node中发生严重错误 {e} !!!!!!!!!!", exc_info=True)
        return []
