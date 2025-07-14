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
    api_key = os.getenv("VOLCENGINE_API_SECRET")
    
    if not api_key:
        raise ValueError("请在环境变量VOLCENGINE_API_SECRET中配置有效的API Key")

    model_config = {
        "model": "doubao-1-5-vision-lite-250315",
        "api_key": api_key,
        "model_info": {
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "family": "unknown",
            "multiple_system_messages": True,
            "structured_output": True
        },
        "base_url": "https://ark.cn-beijing.volces.com/api/v3"
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

# 初始化模型客户端
model_client = _setup_vllm_model_client()
embedding_client = EmbeddingClient()
