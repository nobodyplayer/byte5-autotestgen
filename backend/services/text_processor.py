import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from utils.llms import embedding_client, model_client
import logging
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import UserMessage
from autogen_core import CancellationToken

logger = logging.getLogger(__name__)

class TextProcessor:
    """处理PRD文本，实现功能模块提取和文本向量化检索"""
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " "],
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )
        self.vector_store = None
        self.chunks_with_metadata = []

    def process(self, text: str):
        """仅对文本进行切片和向量化"""
        sub_chunks = self.text_splitter.create_documents([text])
        self.chunks_with_metadata = sub_chunks
        if self.chunks_with_metadata:
            texts = [chunk.page_content for chunk in self.chunks_with_metadata]
            metadatas = [{'source': 'text'} for _ in texts]  # 简化metadata
            self.vector_store = FAISS.from_texts(texts, embedding_client, metadatas=metadatas)
            logger.info("向量数据库创建成功")
        return self.chunks_with_metadata

    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> list:
        if not self.vector_store:
            return []
        docs = self.vector_store.similarity_search(query, k=top_k)
        return [doc.page_content for doc in docs]