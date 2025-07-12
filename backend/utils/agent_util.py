import logging
from typing import List, Any

from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.config import (
    CHUNK_SIZE, CHUNK_OVERLAP,
)
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)


def test_case_number(result_dict: dict):
    """
    将按功能分组的测试点字典，转换为带唯一ID的扁平列表。

    函数的核心功能是将一个按功能模块分组的、嵌套的测试点字典，
    换为一个扁平化的测试点对象列表。在转换过程中，它会为每一个
    立的测试点赋予一个全局唯一的、有序的、带前缀的ID
    格式为 'TP-XXX'，例如 'TP-001'）。

    个函数是数据结构转换和标准化的关键步骤，它为后续的批量生成、
    估和跟踪提供了便利的数据格式。

    args:
       result_dict (Dict[str, List[str]]):
           从大模型（LLM）的分析器节点解析出的、按功能模块分组的
           测试点字典。期望的格式为：
           {
               "功能模块A": ["测试点1描述", "测试点2描述"],
               "功能模块B": ["测试点3描述", ...]
           }

    returns:
       List[Dict[str, Any]]:
           一个扁平化的测试点对象列表。列表中的每个元素都是一个字典，
           包含 'case_ID', 'function', 和 'testPoint' 三个键。
           如果输入字典为空或无效，则返回一个空列表。
           示例输出：
           [
               {"case_ID": "TP-001", "function": "功能模块A", "testPoint": "测试点1描述"},
               {"case_ID": "TP-002", "function": "功能模块A", "testPoint": "测试点2描述"},
               ...
           ]
    """
    flat_test_points = []
    case_id_counter = 1
    if isinstance(result_dict, dict):
        # 遍历每个功能模块和其下的测试点列表
        for function_name, test_points in result_dict.items():
            if isinstance(test_points, list):
                for point_description in test_points:
                    # 创建一个包含所有信息的字典
                    point_object = {
                        # 使用f-string格式化ID，例如: "TP-001", "TP-002", ...
                        "case_ID": f"TP-{case_id_counter:03d}",
                        "function": function_name,
                        "testPoint": str(point_description)
                    }
                    flat_test_points.append(point_object)
                    case_id_counter += 1  # 计数器自增
    if not flat_test_points:
        logger.warning("未能从LLM的输出中解析出任何有效的测试点。")
    logger.info(flat_test_points)
    return flat_test_points


def text_split(prd_content: str, embeddings: Embeddings) -> None | FAISS:
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        splits = text_splitter.split_text(prd_content)
        if not splits:
            print("文本分割失败")
            return None
        vectorstore = FAISS.from_texts(splits, embedding=embeddings)
    except Exception as e:
        print(f"!!!!!!!!!! 文本向量化过程中发生错误 !!!!!!!!!!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        return None
    return vectorstore
