from typing import Tuple, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

from utils.dynamic_import_util import import_class
from config.config import LLM_PROVIDER_CONFIG


def initialize_llm(provider, llm_model_name, embedding_model_name) -> Tuple[
    Optional[BaseChatModel], Optional[Embeddings]]:
    """
    初始化LLM模型和嵌入模型。

    参数:
        provider: LLM提供商
        llm_model_name: LLM模型名称
        embedding_model_name: 嵌入模型名称

    Returns:
        LLM模型和嵌入模型（都可能为空）
    """
    # LLM及嵌入对应类加载
    LLM_class = import_class(LLM_PROVIDER_CONFIG[provider]["llm_module"], LLM_PROVIDER_CONFIG[provider]["llm_class"])
    embeddings_class = import_class(LLM_PROVIDER_CONFIG[provider]["embeddings_module"],
                                    LLM_PROVIDER_CONFIG[provider]["embeddings_class"])
    if not LLM_class:
        print("未找到对应的LLM模型类")
        return None, None
    try:
        # LLM模型对象
        llm = LLM_class(openai_api_key=LLM_PROVIDER_CONFIG[provider]["api_secret"],
                        openai_api_base=LLM_PROVIDER_CONFIG[provider]["api_base_url"],
                        model_name=LLM_PROVIDER_CONFIG[provider]["model_endpoint"][llm_model_name])
        if not embeddings_class:
            # 没有embedding
            print("未找到对应的嵌入模型类")
            return llm, None
        # 嵌入模型对象
        embeddings = embeddings_class(api_url=LLM_PROVIDER_CONFIG[provider]["embedding_api_base_url"],
                                      api_key=LLM_PROVIDER_CONFIG[provider]["api_secret"],
                                      model_name=LLM_PROVIDER_CONFIG[provider]["model_endpoint"][embedding_model_name])
        return llm, embeddings
    except Exception as e:
        print(e)
        return None, None
