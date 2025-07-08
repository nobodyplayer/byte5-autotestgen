from typing import TypedDict, List, Dict, Optional

from langchain_community.vectorstores import FAISS


class TestCaseGenerationState(TypedDict):
    """
    在不同Agent之间传递的状态上下文
    """
    prd_content: str                 # 原始PRD内容
    vectorstore: Optional[FAISS]    # 向量缓存
    detected_testPoint: List[Dict]   # 检测到的测试点
    generated_cases: List[Dict]      # 生成的测试用例
    total_evaluation_report: Dict          # 总体评估报告
    single_evaluation_report: List[Dict]    # 单体评估报告