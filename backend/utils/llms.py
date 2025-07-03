import json
import os
from autogen_ext.models.openai import OpenAIChatCompletionClient


def _setup_vllm_model_client():
    """设置模型客户端"""
    api_key = os.getenv("DASHSCOPE_API_KEY", "sk-a95e9d6b446a409b8c9e8282a56361c2")
    if not api_key:
        raise ValueError("请在环境变量DASHSCOPE_API_KEY中配置有效的API Key")
    model_config = {"model": "qwen-vl-max-latest", "api_key": api_key, "model_info": {
        "vision": True,
        "function_calling": True,
        "json_output": True,
        "family": "unknown",
        "multiple_system_messages": True,
        "structured_output": True
    }, "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"}

    return OpenAIChatCompletionClient(**model_config)

model_client = _setup_vllm_model_client()
