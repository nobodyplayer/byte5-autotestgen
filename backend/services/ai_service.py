import json
import os
import re
from typing import List, Dict, Any, AsyncGenerator
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import UserMessage, ModelClientStreamingChunkEvent
from utils.llms import model_client
from .feishu_service import FeishuService
from .prompts import TestCasePrompts, ErrorMessages
from .text_processor import TextProcessor
from .image_processor import ImageProcessor
from utils.utils import generate_mindmap_from_test_cases, _calculate_average_steps
def generate_mindmap_from_test_cases(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    return generate_mindmap_from_test_cases(test_cases)
def _calculate_average_steps(self, test_cases: List[Dict[str, Any]]) -> float:
    return _calculate_average_steps(test_cases)
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

        # 存储最后生成的测试点JSON数据
        self.last_test_points_json = None

    async def generate_test_points_stream(
        self,
        feishu_url: str = None,
        prd_text: str = None,
        prd_images: list = None,
        context: str = "",
        human_reference_cases: str = ""
    ):
        if feishu_url:
            print("获取飞书文档内容...\n")
            if not self.feishu_service:
                raise ValueError("飞书服务未初始化，请提供飞书应用凭证")
            document_text, document_images = await self.feishu_service.get_document_multimodal_content(feishu_url)
            prd_text = document_text
            prd_images = document_images or []
            print(f"获取到文档内容，图片数量: {len(prd_images)}\n")
        # 第一步：数据预处理
        print("第一步：数据预处理\n")
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
            human_reference_cases=human_reference_cases
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

        # 流式输出结束后固定markdown格式到前端
        yield f"\n\n**输出结束**\n\n<!-- MARKDOWN_CONTENT_START -->\n{markdown_buffer}\n<!-- MARKDOWN_CONTENT_END -->"

        # 后台处理JSON解析（不输出到前端）
        print(markdown_buffer)

    def generate_mindmap_from_test_cases(self, test_cases: list) -> dict:
        return generate_mindmap_from_test_cases(test_cases)

    def _calculate_average_steps(self, test_cases: list) -> float:
        return _calculate_average_steps(test_cases)
    
    async def evaluate_test_cases_stream(
        self,
        ai_generated_cases: str,
        human_reference_cases: str
    ) -> AsyncGenerator[str, None]:
        evaluation_prompt = TestCasePrompts.get_evaluation_prompt(human_reference_cases, ai_generated_cases)
        agent = AssistantAgent(
            name="test_case_evaluator",
            model_client=model_client,
            system_message="你是专业的测试用例评估专家，请严格按照指定的JSON格式输出评估结果。",
            model_client_stream=True,
        )
        yield "# 正在进行自动化评测...\n\n"
        markdown_buffer = ""
        async for event in agent.run_stream(task=evaluation_prompt):
            if isinstance(event, ModelClientStreamingChunkEvent):
                markdown_buffer += event.content
                yield event.content
        # 流式输出结束后统一输出完整markdown内容
        yield f"\n\n**评测完成**\n\n<!-- MARKDOWN_CONTENT_START -->\n{markdown_buffer}\n<!-- MARKDOWN_CONTENT_END -->"
    
    async def generate_test_points_with_evaluation_stream(
        self,
        feishu_url: str = None,
        prd_text: str = None,
        prd_images: List[str] = None,
        context: str = "",
        human_reference_cases: str = ""
    ) -> AsyncGenerator[str, None]:
        """
        生成测试点并自动进行评估的流式方法
        """
        # 第一步：生成测试点
        yield "# 🚀 开始生成功能测试点...\n\n"
        
        test_points_buffer = ""
        async for chunk in self.generate_test_points_stream(
            feishu_url=feishu_url,
            prd_text=prd_text,
            prd_images=prd_images,
            context=context,
            human_reference_cases=human_reference_cases
        ):
            test_points_buffer += chunk
            yield chunk
        
        # 第二步：进行自动评估    
        yield "# 📊 开始自动化评估...\n\n"
        ai_generated_cases = self._extract_test_cases_from_buffer(test_points_buffer)
        evaluation_buffer = ""
        yield f"✅ 成功提取AI生成的测试用例（{len(ai_generated_cases)}字符）\n\n"
        async for chunk in self.evaluate_test_cases_stream(
            ai_generated_cases=ai_generated_cases,
            human_reference_cases=human_reference_cases or ""
        ):
            evaluation_buffer += chunk
            yield chunk
        print(evaluation_buffer)