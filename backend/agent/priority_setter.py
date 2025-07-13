import asyncio
import logging
from operator import itemgetter

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

import utils.agent_util as agent_util
from config.config import QUERY_GENERATE_PROMPT, RETRIEVER_SEARCH_K, PRIORITY_EVALUATION_PROMPT, \
    CASE_PRIORITY_BATCH_SIZE
from models.state import TestCaseGenerationState

logger = logging.getLogger(__name__)


async def priority_setter_agent_node(state: TestCaseGenerationState, llm: BaseChatModel, embeddings: Embeddings):
    # --- 1.参数检查 ---
    logger.info("--- Node: 优先级设置器")
    if not llm:
        logger.error("优先级设置，没有可用的大语言模型")
        return []
    if not embeddings:
        logger.error("优先级设置，没有可用的嵌入模型")
        return []
    if not state or state["prd_content"] is None:
        logger.error("优先级设置，需求文档为空")
        return []
    if not state or state["detected_test_point_dict"] == {}:
        logger.error("优先级设置，未检测到测试点")
        return []
    if not state or state["generated_cases"] == []:
        logger.error("优先级设置，没有生成的测试案例")
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
        case_generation_prompt = ChatPromptTemplate.from_template(PRIORITY_EVALUATION_PROMPT)
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
        priority_report = []
        # 异步任务列表
        tasks = []
        for function_name, cases in grouped_data.items():
            batch_num = int(len(cases) / CASE_PRIORITY_BATCH_SIZE)
            for i in range(batch_num + 1):
                if i == batch_num:
                    input_batch = str(f"# 测试功能：{function_name} "
                                      f"# 测试用例：{cases[i * CASE_PRIORITY_BATCH_SIZE:]}")
                else:
                    input_batch = str(f"# 测试功能：{function_name} "
                                      f"# 测试用例：{cases[i * CASE_PRIORITY_BATCH_SIZE: (i + 1) * CASE_PRIORITY_BATCH_SIZE]}")
                task = end_to_end_chain.ainvoke({"input": input_batch})
                tasks.append(task)
        batch_result_list = await asyncio.gather(*tasks)
        for result_dict in batch_result_list:
            logger.info(f"单例优先级评估单次大模型输出结果：{result_dict}")
            # 加入批次
            if result_dict is not None:
                priority_report.extend(result_dict)
        logger.info(f"单例优先级评估最终输出结果：{priority_report}")
        return priority_report
    except Exception as e:
        logger.info(f"!!!!!!!!!! 在priority_setter_agent_node中发生严重错误 {e} !!!!!!!!!!", exc_info=True)
        return []

