import json
import os
from typing import List, Dict, Any, AsyncGenerator

from PIL import Image as PILImage
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, MultiModalMessage as AGMultiModalMessage
from autogen_core import Image as AGImage

from models.test_case import TestCase
from models.state import TestCaseGenerationState
from utils.llms import model_client
from utils.llm_initial_util import initialize_llm
from .feishu_service import FeishuService
from .prompts import TestCasePrompts, SystemMessages, ErrorMessages
from agent import generator, evaluator, reconstructor


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

    async def generate_test_cases_full_pipeline(self, prd_text):

        # 初始化大模型、嵌入模型、状态对象
        llm, embeddings = initialize_llm("Volcengine", "doubao-Seed-1.6-thinking", "doubao-embedding")
        sta = TestCaseGenerationState(prd_content=prd_text, detected_testPoint=[], generated_cases=[],
                                            total_evaluation_report={}, single_evaluation_report=[])

        # 文档分析迭代
        eval_count = 0
        max_score = 0.0
        best_record = []
        # 评估得分大于4.5时跳出迭代
        while not sta["total_evaluation_report"] or float(sta["total_evaluation_report"].get("score")) < 4.5:
            # 评估次数抵达最大上限
            if eval_count > 5:
                print("需求文档提取需求点，迭代次数已经超过上限")
                break
            # 分析出的测试点，如果出现异常则结束本轮迭代
            detected = generator.analyser_agent_node(sta, llm)
            if not detected or detected == []:
                print("分析器：执行文档分析时大模型输出异常", "WARNING")
                continue
            sta["detected_testPoint"] = detected
            # 评估报告，如果出现异常则结束本轮迭代
            evaluation_report = evaluator.total_evaluator_agent_node(sta, llm)
            if not evaluation_report or evaluation_report == []:
                print("评估器：执行测试点评估时大模型输出异常", "WARNING")
                continue
            # 检查评估结果是否大于当前的最高分
            sta["total_evaluation_report"] = evaluation_report
            if float(evaluation_report["score"]) > max_score:
                best_record = sta["detected_testPoint"]
                max_score = evaluation_report["score"]
            eval_count += 1
        # 取得分最高的测试点
        sta["detected_testPoint"] = best_record

        # 测试用例生成
        while True:
            test_case = generator.generator_agent_node(sta, llm, embeddings)
            if not test_case or test_case == []:
                print("生成器：执行测试用例生成时大模型输出异常", "WARNING")
            else:
                sta["generated_cases"] = test_case
                break

        # 测试用例迭代
        reconstruct_count = 0
        final_generated_cases = []
        history_case = {}
        history_evaluation_report = {}
        while sta["generated_cases"]:
            if reconstruct_count > 5:
                print("测试案例重构次数抵达上限", "WARNING")
                break
            # 生成报告
            single_eval_report = evaluator.single_evaluator_agent_node(sta, llm, embeddings)
            if not single_eval_report or single_eval_report == []:
                print("单例评估器：执行测试用例评估时大模型输出异常", "WARNING")
            sta["single_evaluation_report"] = single_eval_report

            # 集合按case_ID做检索，分高质量用例、低质量用例、高质量评估、低质量评估集合
            score_map = {item['case_ID']: item for item in sta["single_evaluation_report"]}
            high_quality_cases = []
            low_quality_cases = []
            low_quality_scores = []

            # 遍历主测试用例列表
            for case in sta["generated_cases"]:
                # 按ID索引
                case_id = case.get("case_ID")
                score_obj = score_map.get(case_id)
                if score_obj and isinstance(score_obj, dict):
                    # 具有相应的评分
                    score_str = score_obj.get('score')
                    try:
                        score_value = float(score_str)
                        if score_value >= 4.5:
                            # 添加到高质量组
                            high_quality_cases.append(case)
                        else:
                            # 得分比上次高则进入待优化组
                            if history_case == {} or float(history_case.get(case_id).get('score')) < score_value:
                                low_quality_cases.append(case)
                                low_quality_scores.append(score_obj)
                            # 得分比上次低则丢弃，取历史版本
                            else:
                                low_quality_cases.append(history_case.get(case_id))
                                low_quality_scores.append(history_evaluation_report.get(case_id))
                    except (ValueError, TypeError):
                        # 如果分数无效，同步添加到待优化组
                        print(f"警告: Case ID '{case_id}' 的分数 '{score_str}' 无效，已同步归入待优化组。")
                        low_quality_cases.append(case)
                        low_quality_scores.append(score_obj)
                else:
                    # 如果找不到评分，只将测试用例归入待优化组
                    print(f"警告: 未找到 Case ID '{case_id}' 的评分，用例已归入待优化组。")
                    low_quality_cases.append(case)

            # 记录待优化信息
            final_generated_cases.extend(high_quality_cases)
            sta["generated_cases"] = low_quality_cases
            sta["single_evaluation_report"] = low_quality_scores
            # 更新历史记录
            history_case = {item['case_ID']: item for item in sta["generated_cases"]}
            history_evaluation_report = {item['case_ID']: item for item in sta["single_evaluation_report"]}
            # 开始重构测试用例
            sta["generated_cases"] = reconstructor.reconstructor_agent_node(sta, llm, embeddings)
            reconstruct_count += 1

        return final_generated_cases
