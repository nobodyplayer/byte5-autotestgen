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
from services.agents import GeneratorAgent, EvaluatorAgent, CoordinatorAgent
from .session import MultiAgentSession
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
        print("🔍 第一阶段：数据解析与存储...")
        yield "# 🔍 第一阶段：数据解析与存储...\n\n"
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
        yield "✅ 数据解析完成，已保存到会话中\n\n"
        yield "# 🤖 第二步，初始化智能体...\n\n"
        # 第二步：流式生成测试点
        prompt = TestCasePrompts.get_final_test_points_prompt(
            prd_text=prd_text or "",
            flowchart_info=image_analysis_results["flowchart_info"],
            structure_info=image_analysis_results["structure_info"],
            ui_info=image_analysis_results["ui_info"],
            evaluation=context,
            human_reference_cases=human_reference_cases
        )
        agent = AssistantAgent(
            name="final_test_points_agent",
            model_client=model_client,
            system_message="你是专业的测试工程师，请严格按照用户指定的JSON格式输出功能模块化的测试点。",
            model_client_stream=True,
        )
        yield "✅ 智能体初始化完成\n\n"
        yield "# 正在生成功能测试点...\n\n"
        markdown_buffer = ""
        async for event in agent.run_stream(task=prompt):
            if isinstance(event, ModelClientStreamingChunkEvent):
                markdown_buffer += event.content
                yield event.content  # 实时将所有内容输出到前端

        # 流式输出结束后固定markdown格式到前端
        yield "✅ 初始用例生成完成\n\n"
        yield "# 📊 自动评估测试用例...\n\n"
        yield f"\n\n**输出结束**\n\n<!-- MARKDOWN_CONTENT_START -->\n{markdown_buffer}\n<!-- MARKDOWN_CONTENT_END -->"

        # 后台处理JSON解析（不输出到前端）
        print(markdown_buffer)

    
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
    
    async def generate_initial_with_evaluation(
        self,
        session: MultiAgentSession,
        feishu_url: str = None,
        prd_text: str = None,
        prd_images: list = None,
        context: str = "",
        human_reference_cases: str = ""
    ):  
        print("🔍 第一阶段：数据解析与存储...")
        yield "# 🔍 第一阶段：数据解析与存储...\n\n"
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

        session.parsed_data.update({
            "prd_text": prd_text or "",
            "prd_images": prd_images or [],
            "context": context,
            "human_reference_cases": human_reference_cases,
            "flowchart_info": image_analysis_results["flowchart_info"],
            "structure_info": image_analysis_results["structure_info"],
            "ui_info": image_analysis_results["ui_info"]
        })


        yield "✅ 数据解析完成，已保存到会话中\n\n"
        yield "# 🤖 第二步，初始化智能体...\n\n"
        session.generator = GeneratorAgent(name="GeneratorAgent", model_client=model_client)
        session.evaluator = EvaluatorAgent(name="EvaluatorAgent", model_client=model_client)
        session.coordinator = CoordinatorAgent(name="CoordinatorAgent", model_client=model_client)
        session.generator.memory.update(session.parsed_data)
        session.evaluator.memory["human_reference_cases"] = human_reference_cases


        yield "✅ 智能体初始化完成\n\n"
        yield "# 📝 生成初始测试用例...\n\n"
        result = ""
        async for chunk in session.generator.generate_reply([{"content": "生成初始测试用例"}]):
            result+=chunk
            yield chunk
        yield f"\n\n**输出结束**\n\n<!-- MARKDOWN_CONTENT_START -->\n{result}\n<!-- MARKDOWN_CONTENT_END -->"
        
        session.results["initial_cases"] = session.generator.memory["latest_cases"]
        yield "✅ 初始用例生成完成\n\n"
        yield "# 📊 自动评估测试用例...\n\n"
        session.evaluator.memory["latest_cases"] = session.results["initial_cases"]
        result = ""
        async for chunk in session.evaluator.generate_reply([{"content": "评估初始测试用例"}]):
            result+=chunk
            yield chunk
        yield f"\n\n**输出结束**\n\n<!-- MARKDOWN_CONTENT_START -->\n{result}\n<!-- MARKDOWN_CONTENT_END -->"

        session.results["initial_evaluation"] = session.evaluator.memory["last_evaluation"]
        yield "✅ 初始评估完成\n\n"
        yield "# 🎯 第一阶段完成\n\n"
        yield f"**会话ID**: {session.session_id}\n\n"


    
    async def optimize_with_multi_rounds(
        self,
        session: MultiAgentSession,
        user_feedback: str = ""
    ):
        """多轮自动优化测试用例"""
        for round_idx in range(session.max_rounds):
            session.round_count += 1
            yield f"# 🔄 第{session.round_count}轮优化...\n\n"
            session.coordinator.round = session.round_count
            session.generator.memory["last_evaluation"] = session.results["initial_evaluation"] if round_idx == 0 else session.results["optimization_history"][-1]["evaluation"]
            session.generator.memory["user_feedback"] = user_feedback
            await session.generator.generate_reply([{"content": "优化测试用例"}])
            optimized_cases = session.generator.memory["latest_cases"]
            session.evaluator.memory["latest_cases"] = optimized_cases
            await session.evaluator.generate_reply([{"content": "评估优化后测试用例"}])
            evaluation = session.evaluator.memory["last_evaluation"]
            session.results["optimization_history"].append({
                "cases": optimized_cases,
                "evaluation": evaluation
            })
            yield f"✅ 第{session.round_count}轮优化与评估完成\n\n"
        session.results["optimized_cases"] = session.results["optimization_history"][-1]["cases"] if session.results["optimization_history"] else ""
        yield "# 🏁 多轮优化完成，输出最终用例\n\n"
        yield session.results["optimized_cases"]