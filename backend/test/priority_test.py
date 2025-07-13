import asyncio

from agent import priority_setter
from config.test_config import prd_context, generated_cases, detected_test_point_dict
import models.state as state
import logging

from utils.llm_initial_util import initialize_llm

logging.basicConfig(
    level=logging.INFO,  # 设置根logger的级别为DEBUG，能捕获所有级别的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建一个我们自己应用的顶层logger（可选，但推荐）
main_logger = logging.getLogger(__name__)
main_logger.info("应用程序启动...")


async def main():
    sta = state.create_default_state()
    sta["prd_content"] = prd_context
    sta["detected_test_point_dict"] = detected_test_point_dict
    sta["generated_cases"] = generated_cases
    llm, embeddings = initialize_llm("Volcengine", "doubao-1.5-pro-32k", "doubao-embedding")
    priority = await priority_setter.priority_setter_agent_node(sta, llm, embeddings)
    print(priority)
    # evaluator.total_evaluator_agent_node(sta, llm)


if __name__ == "__main__":
    asyncio.run(main())
