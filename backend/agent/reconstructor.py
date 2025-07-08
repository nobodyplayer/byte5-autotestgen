import asyncio

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from operator import itemgetter

from models.state import TestCaseGenerationState
from config.config import (
    CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_SEARCH_K, CASE_RECONSTRUCTION_BATCH_SIZE,
    RECONSTRUCTION_AGENT_PROMPT
)
from utils.json_parse_util import parse_json_output


async def reconstructor_agent_node(state:TestCaseGenerationState, llm: BaseChatModel, embeddings: Embeddings) -> list:
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
    print("--- Node: 重构器")
    if not llm:
        print("没有可用的大语言模型")
    if not embeddings:
        print("没有可用的嵌入")
    if not state or state["prd_content"] is None:
        print("需求文档为空")
    if not state or state["detected_testPoint"] == []:
        print("未检测到测试点")
    if not state or state["single_evaluation_report"] == []:
        print("没有评估文档")

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
        case_generation_prompt = ChatPromptTemplate.from_template(RECONSTRUCTION_AGENT_PROMPT)
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
    reconstruct_case = []
    try:
        batch_num = int(len(state["generated_cases"]) / CASE_RECONSTRUCTION_BATCH_SIZE)
        # 异步处理
        tasks = []
        for i in range(batch_num + 1):
            if i == batch_num:
                case_batch = str(state["generated_cases"][i * CASE_RECONSTRUCTION_BATCH_SIZE:])
                eval_batch = str(state["single_evaluation_report"][i * CASE_RECONSTRUCTION_BATCH_SIZE:])
            else:
                case_batch = str(state["generated_cases"][i * CASE_RECONSTRUCTION_BATCH_SIZE : (i + 1) * CASE_RECONSTRUCTION_BATCH_SIZE])
                eval_batch = str(state["single_evaluation_report"][i * CASE_RECONSTRUCTION_BATCH_SIZE : (i + 1) * CASE_RECONSTRUCTION_BATCH_SIZE])
            input = f"""
                # 待重构的原始测试用例列表:
                {case_batch}
                # 评估信息与修改建议列表
                {eval_batch}
            """
            task = retriever_chain.ainvoke({"input": input})
            tasks.append(task)
        batch_result_list = await asyncio.gather(*tasks)
        for result_str in batch_result_list:
            print(result_str)
            # 转JSON
            batch_case = parse_json_output(result_str, expected_type=list)
            # 加入批次
            if batch_case is not None:
                reconstruct_case.extend(batch_case)
        print(reconstruct_case)
        return reconstruct_case
    except Exception as e:
        print(f"!!!!!!!!!! 在generator_agent_node中发生严重错误 !!!!!!!!!!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        return []