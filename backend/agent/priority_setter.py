from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from models.state import TestCaseGenerationState
import logging

logger = logging.getLogger(__name__)


def priority_setter_agent_node(state: TestCaseGenerationState, llm: BaseChatModel, embeddings: Embeddings):
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

