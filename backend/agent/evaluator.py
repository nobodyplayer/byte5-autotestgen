from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from operator import itemgetter
import asyncio
from config.config import (
    CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_SEARCH_K, SINGLE_EVALUATOR_AGENT_PROMPT,
    TOTAL_EVALUATOR_AGENT_PROMPT, CASE_EVALUATION_BATCH_SIZE
)


from models.state import TestCaseGenerationState
from utils.json_parse_util import parse_json_output


async def single_evaluator_agent_node(state:TestCaseGenerationState, llm: BaseChatModel, embeddings: Embeddings):
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
    # 检查参数
    print("--- Node: 单例评估器")
    if not llm or not embeddings:
        print("没有大模型或嵌入")
    if not state or state["prd_content"] is None:
        print("需求文档为空")
    if not state or state["generated_cases"] == []:
        print("没有生成的测试用例")

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

    # RAG链条构建
    try:
        retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_SEARCH_K})
        case_generation_prompt = ChatPromptTemplate.from_template(SINGLE_EVALUATOR_AGENT_PROMPT)
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

    # 大模型评估
    try:
        eval_report = []
        batch_num = int(len(state["generated_cases"]) / CASE_EVALUATION_BATCH_SIZE)
        # 异步处理不同批次
        tasks = []
        for i in range(batch_num + 1):
            if i == batch_num:
                input_batch = str(state["generated_cases"][i * CASE_EVALUATION_BATCH_SIZE:])
            else:
                input_batch = str(state["generated_cases"][i * CASE_EVALUATION_BATCH_SIZE : (i + 1) * CASE_EVALUATION_BATCH_SIZE])
            task = retriever_chain.ainvoke({"input": input_batch})
            tasks.append(task)
        batch_result_list = await asyncio.gather(*tasks)
        for result_str in batch_result_list:
            print(result_str)
            # 转json
            batch_eval = parse_json_output(result_str, expected_type=list)
            # 加入批次
            if batch_eval is not None:
                eval_report.extend(batch_eval)
        print(eval_report)
        return eval_report
    except Exception as e:
        print(f"!!!!!!!!!! 在generator_agent_node中发生严重错误 !!!!!!!!!!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        return []





def total_evaluator_agent_node(state:TestCaseGenerationState, llm: BaseChatModel):
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
    print("--- Node: 全体评估器")
    # 检查参数
    if not llm:
        print("没有可用的大语言模型")
    if not state or state["prd_content"] is None:
        print("需求文档为空")
    if not state or state["detected_testPoint"] == []:
        print("解析的测试点列表为空")
    try:
        # 构建整体链条
        app_prompt = ChatPromptTemplate.from_template(TOTAL_EVALUATOR_AGENT_PROMPT)
        app_chain = app_prompt | llm | StrOutputParser()

        result_str = app_chain.invoke({"document": state["prd_content"], "testPoint": state["detected_testPoint"]})
        print(result_str)

        # 转JSON
        evalResult = parse_json_output(result_str, expected_type=dict)

        # 文档解析失败
        if evalResult is None:
            # 启发式解析，判断是否返回了一个逗号分割的简单字符串
            if result_str and not result_str.startswith("I cannot") and len(
                    result_str) < 200 and '[' not in result_str and '{' not in result_str:
                possible_apps = [app.strip().strip("'\"") for app in result_str.split(',') if app.strip()]
                if possible_apps:
                    return sorted(list(set(possible_apps)))
            return []
        return evalResult
    except Exception as e:
        print(f"!!!!!!!!!! 在total_evaluator_node中发生严重错误 !!!!!!!!!!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        return []