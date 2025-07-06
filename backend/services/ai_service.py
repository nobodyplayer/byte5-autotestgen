import json
import os
from typing import List, Dict, Any, AsyncGenerator
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, MultiModalMessage as AGMultiModalMessage, StructuredMessage
from autogen_core import Image as AGImage
from PIL import Image as PILImage

from utils.llms import model_client
from models.test_case import TestCase, TestCaseResponse
from .feishu_service import FeishuService
from .prompts import TestCasePrompts, SystemMessages, ErrorMessages


class AIService:
    def __init__(self, feishu_app_id: str = None, feishu_app_secret: str = None):
        # 初始化飞书服务（如果提供了凭证）
        if feishu_app_id and feishu_app_secret:
            self.feishu_service = FeishuService(feishu_app_id, feishu_app_secret)
        else:
            self.feishu_service = None

    async def generate_test_cases_from_multimodal_prd_stream(
        self,
        prd_text: str,
        prd_images: List[str],  # 改为接收文件路径列表
        context: str,
        requirements: str
    ) -> AsyncGenerator[str, None]:
        """基于PRD文本和图片组合生成测试用例（支持纯文本模式）"""
        try:
            ag_images = []
            if prd_images:  # 只有当有图片时才处理
                for i, image_path in enumerate(prd_images):
                    try:
                        print(f"处理第{i+1}张图片: {image_path}")
                        
                        # 检查文件是否存在
                        if not os.path.exists(image_path):
                            print(f"跳过第{i+1}张图片：文件不存在 {image_path}")
                            continue
                        
                        # 使用PIL直接打开文件路径，使用上下文管理器确保文件正确关闭
                        with PILImage.open(image_path) as pil_image:
                            # 验证图片尺寸
                            if pil_image.size[0] > 0 and pil_image.size[1] > 0:
                                # 创建AGImage对象时需要复制图片，避免文件关闭后无法访问
                                pil_image_copy = pil_image.copy()
                                ag_image = AGImage(pil_image_copy)
                                ag_images.append(ag_image)
                                print(f"成功处理第{i+1}张图片")
                            else:
                                print(f"跳过第{i+1}张图片")
                            
                    except Exception as e:
                        import traceback
                        print(f"处理第{i+1}张图片时出错: {e}")
                        print(f"错误堆栈: {traceback.format_exc()}")
                        continue
            
            # 创建组合提示词
            prompt = TestCasePrompts.get_multimodal_prd_prompt(prd_text, context, requirements)

            content = [prompt] + ag_images
            multi_modal_message = AGMultiModalMessage(content=content, source="user")
            
            agent = AssistantAgent(
                name="agent",
                model_client=model_client,
                system_message=SystemMessages.MULTIMODAL_ANALYSIS,
                model_client_stream=True,
            )
            
            # 首先输出标题
            yield "# 正在生成测试用例...\n\n"
            
            # 初始化markdown缓冲区
            markdown_buffer = ""
            
            # 流式输出生成的测试用例
            async for event in agent.run_stream(task=multi_modal_message):
                if isinstance(event, ModelClientStreamingChunkEvent):
                    content = event.content
                    markdown_buffer += content
                    yield content
                elif isinstance(event, TaskResult):
                    pass
            
            # 在流式输出结束后，尝试从Markdown中提取测试用例
            test_cases_json = self._extract_test_cases_from_markdown(markdown_buffer)
            if test_cases_json:
                # 只输出隐藏的JSON注释，供后端处理使用，前端会解析但不显示
                yield "\n\n<!-- TEST_CASES_JSON: " + json.dumps(test_cases_json) + " -->\n"
                
        except Exception as e:
            error_message = ErrorMessages.get_generation_error(str(e))
            yield f"\n\n**错误:** {error_message}\n\n"
            

            
    async def generate_test_cases_stream_from_feishu(
        self,
        feishu_url: str,
        context: str,
        requirements: str
    ) -> AsyncGenerator[str, None]:
        """基于飞书文档URL生成测试用例"""
        if not self.feishu_service:
            raise ValueError("飞书服务未初始化，请提供飞书应用凭证")
        
        try:
            # 获取飞书文档的多模态内容（文本+图片）
            document_text, document_images = await self.feishu_service.get_document_multimodal_content(feishu_url)
            if not document_text.strip():
                raise ValueError("无法获取文档内容或文档为空")
            
            # 复用多模态PRD处理方法
            async for chunk in self.generate_test_cases_from_multimodal_prd_stream(
                prd_text=document_text,
                prd_images=document_images,
                context=context,
                requirements=requirements
            ):
                yield chunk
                
        except Exception as e:
            error_msg = ErrorMessages.get_feishu_error(str(e))
            yield f"\n\n**错误:** {error_msg}\n\n"
            


    def _test_case_to_dict(self, test_case: TestCase) -> Dict[str, Any]:
        """
        将TestCase对象转换为字典格式
        """
        return {
            "id": test_case.id,
            "title": test_case.title,
            "priority": test_case.priority,
            "description": test_case.description,
            "preconditions": test_case.preconditions,
            "steps": [{
                "step_number": step.step_number,
                "description": step.description,
                "expected_result": step.expected_result
            } for step in test_case.steps],
            "status": test_case.status
        }

    def _generate_markdown_from_test_cases(self, test_cases: List[TestCase]) -> str:
        """
        从测试用例列表生成Markdown格式的输出
        """
        markdown_lines = []
        
        for test_case in test_cases:
            # 测试用例标题
            markdown_lines.append(f"## {test_case.id}: {test_case.title}")
            markdown_lines.append("")
            
            # 基本信息
            markdown_lines.append(f"**优先级:** {test_case.priority}")
            markdown_lines.append(f"**描述:** {test_case.description}")
            
            if test_case.preconditions:
                markdown_lines.append(f"**前置条件:** {test_case.preconditions}")
            
            markdown_lines.append("")
            
            # 测试步骤表格
            markdown_lines.append("### 测试步骤")
            markdown_lines.append("")
            markdown_lines.append("| # | 步骤描述 | 预期结果 |")
            markdown_lines.append("| --- | --- | --- |")
            
            for step in test_case.steps:
                markdown_lines.append(f"| {step.step_number} | {step.description} | {step.expected_result} |")
            
            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")
        
        return "\n".join(markdown_lines)

    def _extract_test_cases_from_markdown(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        从Markdown文本中提取测试用例信息

        参数:
            markdown_text: Markdown格式的测试用例文本

        返回:
            测试用例列表
        """
        test_cases = []
        lines = markdown_text.split('\n')

        current_test_case = None
        current_steps = []
        in_table = False
        table_headers = []

        for line in lines:
            # 检测新测试用例的开始
            if line.startswith('## '):
                # 如果有当前测试用例，将其添加到列表中
                if current_test_case is not None and current_steps:
                    current_test_case['steps'] = current_steps
                    test_cases.append(current_test_case)

                # 初始化新的测试用例
                title_parts = line[3:].strip().split(': ', 1)
                if len(title_parts) > 1:
                    test_id = title_parts[0].strip()
                    title = title_parts[1].strip()
                else:
                    test_id = f"TC-{len(test_cases) + 1}"
                    title = line[3:].strip()

                current_test_case = {
                    'id': test_id,
                    'title': title,
                    'description': '',
                    'preconditions': None,
                    'priority': None
                }
                current_steps = []
                in_table = False

            # 提取优先级
            elif line.startswith('**优先级:**') and current_test_case:
                current_test_case['priority'] = line.replace('**优先级:**', '').strip()

            # 提取描述
            elif line.startswith('**描述:**') and current_test_case:
                current_test_case['description'] = line.replace('**描述:**', '').strip()

            # 提取前置条件
            elif line.startswith('**前置条件:**') and current_test_case:
                current_test_case['preconditions'] = line.replace('**前置条件:**', '').strip()

            # 检测表格头
            elif '| --- | --- | --- |' in line:
                in_table = True
                # 获取前一行的表头
                for i, prev_line in enumerate(reversed(lines[:lines.index(line)])):
                    if '|' in prev_line:
                        table_headers = [h.strip() for h in prev_line.split('|')[1:-1]]
                        break

            # 提取测试步骤
            elif in_table and '|' in line and '---' not in line and len(line.split('|')) > 3:
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) >= 3:
                    try:
                        step_number = int(cells[0])
                        description = cells[1]
                        expected_result = cells[2]

                        current_steps.append({
                            'step_number': step_number,
                            'description': description,
                            'expected_result': expected_result
                        })
                    except (ValueError, IndexError):
                        pass  # 忽略无法解析的行

        # 添加最后一个测试用例
        if current_test_case is not None and current_steps:
            current_test_case['steps'] = current_steps
            test_cases.append(current_test_case)

        return test_cases
