from typing import TypedDict, List, Dict, Optional

from langchain_community.vectorstores import FAISS


class TestCaseGenerationState(TypedDict):
    """
    在不同Agent之间传递的状态上下文
    """
    prd_content: str  # 原始PRD内容
    prd_vector: Optional[FAISS]  # 需求文本向量缓存
    flow_chart_vector: Optional[FAISS]  # 流程图向量缓存
    ui_chart_vector: Optional[FAISS]    # UI图向量缓存
    detected_test_point_dict: Dict  # 测试点字典
    detected_test_point_list: List[Dict]  # 测试点列表
    generated_cases: List[Dict]  # 生成的测试用例
    total_evaluation_report: Dict  # 总体评估报告
    single_evaluation_report: List[Dict]  # 单体评估报告


def create_default_state() -> TestCaseGenerationState:
    """
    创建一个空的、默认的 TestCaseGenerationState 状态
    """
    return {
        "prd_content": "",
        "prd_vector": None,
        "flow_chart_vector": None,
        "ui_chart_vector": None,
        "detected_test_point_list": [],
        "detected_test_point_dict": {},
        "generated_cases": [],
        "total_evaluation_report": {},
        "single_evaluation_report": [],
    }
