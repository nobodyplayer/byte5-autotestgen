import json
import os
import re
from typing import List, Dict, Any, AsyncGenerator

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import UserMessage, ModelClientStreamingChunkEvent
from autogen_core import CancellationToken
from utils.llms import model_client
from .feishu_service import FeishuService
from .prompts import TestCasePrompts, ErrorMessages
from .text_processor import TextProcessor
from .image_processor import ImageProcessor


class AIService:
    def __init__(self, feishu_app_id: str = None, feishu_app_secret: str = None):
        # 初始化飞书服务（如果提供了凭证）
        if feishu_app_id and feishu_app_secret:
            self.feishu_service = FeishuService(feishu_app_id, feishu_app_secret)
        else:
            self.feishu_service = None
        
        # 初始化文本和图片处理器
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()

    
    async def generate_test_points_stream(
        self,
        feishu_url: str = None,
        prd_text: str = None,
        prd_images: List[str] = None,
        context: str = "",
        requirements: str = ""
    ) -> AsyncGenerator[str, None]:
        """生成功能测试点：预处理 → 功能模块分解 → 按模块生成测试点"""
        
        if feishu_url:
            print("### 获取飞书文档内容...\n")
            if not self.feishu_service:
                raise ValueError("飞书服务未初始化，请提供飞书应用凭证")
            document_text, document_images = await self.feishu_service.get_document_multimodal_content(feishu_url)
            prd_text = document_text
            prd_images = document_images or []
            print(f"获取到文档内容，图片数量: {len(prd_images)}\n")
        # 第一步：数据预处理
        print("## 第一步：数据预处理\n")
        # 1.1 文本处理（仅向量化）
        if prd_text:
            print("开始处理文本...\n")
            self.text_processor.process(prd_text)
            print("文本向量化完成\n")

        # 1.2 图片处理（分类分析）
        if prd_images:
            print("开始处理图片...\n")
            image_analysis_results = await self.image_processor.process_images(prd_images, prd_text or "")
            print(f"图片处理完成，共处理{len(prd_images)}张图片\n")
        else:
            print("未提供图片，跳过图片处理\n")
            image_analysis_results = {"flowchart_info": "", "structure_info": "", "ui_info": ""}

        # 第二步：流式生成测试点
        prompt = TestCasePrompts.get_final_test_points_prompt(
            prd_text=prd_text or "",
            flowchart_info=image_analysis_results["flowchart_info"],
            structure_info=image_analysis_results["structure_info"],
            ui_info=image_analysis_results["ui_info"],
            context=context,
            requirements=requirements
        )
        agent = AssistantAgent(
            name="final_test_points_agent",
            model_client=model_client,
            system_message="你是专业的测试工程师，请严格按照用户指定的JSON格式输出功能模块化的测试点。",
            model_client_stream=True,
        )

        yield "# 正在生成功能测试点...\n\n"
        markdown_buffer = ""

        async for event in agent.run_stream(task=prompt):
            if isinstance(event, ModelClientStreamingChunkEvent):
                markdown_buffer += event.content
                yield event.content  # 实时将所有内容输出到前端
        # 结束后输出隐藏 JSON 注释，供前端结构化解析
        print("检查markdown_buffer是否为空：", markdown_buffer)

