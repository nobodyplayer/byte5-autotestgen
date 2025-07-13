import json
import os
import requests
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import List
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings

load_dotenv()

def _setup_vllm_model_client():
    """设置模型客户端"""
    api_key = os.getenv("DASHSCOPE_API_KEY", "sk-a95e9d6b446a409b8c9e8282a56361c2")
    if not api_key:
        raise ValueError("请在环境变量DASHSCOPE_API_KEY中配置有效的API Key")
    
    model_config = {
        "model": "qwen-vl-max-latest",
        "api_key": api_key,
        "model_info": {
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "family": "unknown",
            "multiple_system_messages": True,
            "structured_output": True
        },
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    }
    
    return OpenAIChatCompletionClient(**model_config)

class EmbeddingClient(Embeddings):
    """向量模型客户端"""
    def __init__(self):
        self.api_url = os.getenv("EMBEDDINGS_API_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3/embeddings")
        self.api_key = os.getenv("VOLCENGINE_API_SECRET")
        self.model_name = "doubao-embedding-large-text-250515"
        if not self.api_key:
            raise ValueError("请在环境变量VOLCENGINE_API_SECRET中配置有效的API Key")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model_name,
            "input": texts,
            "encoding_format": "float"
        }
        response = requests.post(self.api_url, json=data, headers=headers)
        if response.status_code != 200:
            raise Exception(f"向量化API请求失败: {response.text}")
        
        response_json = response.json()
        if "data" not in response_json:
            raise ValueError(f"向量化响应格式错误: {response_json}")
        
        embeddings = []
        for result in response_json["data"]:
            if "embedding" not in result:
                raise ValueError(f"向量化结果缺少embedding字段: {result}")
            embeddings.append(result["embedding"])
        
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        return self.embed_documents([text])[0]

class ModelClientWrapper:
    """模型客户端包装器，支持图片对话"""
    def __init__(self, client):
        self.client = client
    
    def chat_with_image(self, messages, image_path=None):
        """支持图片的对话方法"""
        if image_path:
            # 这里需要根据实际的模型API来实现图片处理
            # 暂时返回一个模拟的响应
            return {"content": "图片分析结果"}
        else:
            # 普通文本对话
            return self.client.create(messages=messages)

# 初始化模型客户端
model_client = _setup_vllm_model_client()
embedding_client = EmbeddingClient()
