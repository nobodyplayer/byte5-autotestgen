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
        prd_images: List[str] = None,
        context: str = "",
        human_reference_cases: str = ""
    ) -> AsyncGenerator[str, None]:
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
        
    def generate_mindmap_from_test_cases(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        从测试用例生成思维导图数据
        
        参数:
            test_cases: 测试用例列表
        
        返回:
            思维导图的JSON数据结构
        """
        if not test_cases:
            return {"name": "测试用例", "children": []}
        
        # 创建根节点
        mindmap = {
            "name": "测试用例总览",
            "children": []
        }
        
        # 按优先级分组
        priority_groups = {}
        for tc in test_cases:
            priority = tc.get('priority', 'Medium')
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(tc)
        
        # 为每个优先级创建分支
        for priority, cases in priority_groups.items():
            priority_node = {
                "name": f"{priority} 优先级 ({len(cases)}个)",
                "children": []
            }
            
            for tc in cases:
                test_case_node = {
                    "name": tc.get('title', tc.get('id', '未知测试用例')),
                    "children": []
                }
                
                # 添加描述节点
                if tc.get('description'):
                    test_case_node["children"].append({
                        "name": f"描述: {tc['description'][:50]}{'...' if len(tc['description']) > 50 else ''}",
                        "children": []
                    })
                
                # 添加前置条件节点
                if tc.get('preconditions'):
                    test_case_node["children"].append({
                        "name": f"前置条件: {tc['preconditions'][:50]}{'...' if len(tc['preconditions']) > 50 else ''}",
                        "children": []
                    })
                
                # 添加测试步骤节点
                if tc.get('steps'):
                    steps_node = {
                        "name": f"测试步骤 ({len(tc['steps'])}步)",
                        "children": []
                    }
                    
                    for step in tc['steps'][:5]:  # 限制显示的步骤数量
                        step_node = {
                            "name": f"步骤{step.get('step_number', '?')}: {step.get('description', '')[:30]}{'...' if len(step.get('description', '')) > 30 else ''}",
                            "children": [{
                                "name": f"预期: {step.get('expected_result', '')[:40]}{'...' if len(step.get('expected_result', '')) > 40 else ''}",
                                "children": []
                            }]
                        }
                        steps_node["children"].append(step_node)
                    
                    test_case_node["children"].append(steps_node)
                
                priority_node["children"].append(test_case_node)
            
            mindmap["children"].append(priority_node)
        
        # 添加统计信息节点
        stats_node = {
            "name": "统计信息",
            "children": [
                {"name": f"总测试用例: {len(test_cases)}", "children": []},
                {"name": f"优先级分布: {len(priority_groups)}种", "children": []},
                {"name": f"平均步骤数: {self._calculate_average_steps(test_cases):.1f}", "children": []}
            ]
        }
        mindmap["children"].append(stats_node)
        
        return mindmap
    
    def _calculate_average_steps(self, test_cases: List[Dict[str, Any]]) -> float:
        """
        计算测试用例的平均步骤数
        """
        if not test_cases:
            return 0.0
        
        total_steps = 0
        valid_cases = 0
        
        for tc in test_cases:
            steps = tc.get('steps', [])
            if steps:
                total_steps += len(steps)
                valid_cases += 1
        
        return total_steps / valid_cases if valid_cases > 0 else 0.0
    
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
        # 第三步：解析评估结果并输出结构化数据
        try:
            parsed_results = self.parse_evaluation_results(evaluation_buffer)
            overall_summary = self.get_overall_metrics_summary(parsed_results["overall_metrics"])
            
            yield f"\n\n<!-- EVALUATION_RESULTS_START -->\n"
            yield f"```json\n{json.dumps(parsed_results, ensure_ascii=False, indent=2)}\n```\n"
            yield f"<!-- EVALUATION_RESULTS_END -->\n\n"
            
            yield f"<!-- OVERALL_SUMMARY_START -->\n"
            yield f"```json\n{json.dumps(overall_summary, ensure_ascii=False, indent=2)}\n```\n"
            yield f"<!-- OVERALL_SUMMARY_END -->\n\n"
            
            print(f"评估完成，解析到 {len(parsed_results['individual_evaluations'])} 个用例评估")
        except Exception as e:
            print(f"解析评估结果时出错: {e}")
            yield f"\n\n⚠️ 评估结果解析失败: {str(e)}\n\n"


    def _extract_test_cases_from_buffer(self, buffer: str) -> str:
        """
        从生成的测试点缓冲区中提取测试用例文本
        """
        try:
            # 尝试从JSON代码块中提取数据
            json_block_regex = r'```json\s*({[\s\S]*?})\s*```'
            json_block_match = re.search(json_block_regex, buffer)
            
            if json_block_match:
                test_points_json = json.loads(json_block_match.group(1))
                # 将JSON数据转换为文本格式
                extracted_text = ""
                for module_name, points in test_points_json.items():
                    extracted_text += f"## {module_name}\n\n"
                    for i, point in enumerate(points, 1):
                        if isinstance(point, dict):
                            title = point.get('title', point.get('name', f'测试点{i}'))
                            desc = point.get('description', point.get('desc', ''))
                            extracted_text += f"{i}. {title}\n{desc}\n\n"
                        else:
                            extracted_text += f"{i}. {point}\n\n"
                return extracted_text
            
            # 如果没有找到JSON，返回原始缓冲区的清理版本
            # 移除注释和特殊标记
            cleaned_buffer = re.sub(r'<!-- .*? -->', '', buffer)
            cleaned_buffer = re.sub(r'\*\*.*?完成\*\*', '', cleaned_buffer)
            return cleaned_buffer.strip()
            
        except Exception as e:
            print(f"提取测试用例时出错: {e}")
            return buffer
    
    def parse_evaluation_results(self, evaluation_markdown: str) -> Dict[str, Any]:
        result = {
            "overall_metrics": {},
            "individual_evaluations": []
        }
        
        try:
            # 查找所有JSON代码块
            json_blocks = re.findall(r'```json\s*([\s\S]*?)```', evaluation_markdown)
            
            for block in json_blocks:
                try:
                    # 简单清理：移除尾随逗号
                    cleaned_block = re.sub(r',\s*([}\]])', r'\1', block.strip())
                    parsed_json = json.loads(cleaned_block)
                    
                    # 判断是整体指标还是单个评估
                    if isinstance(parsed_json, dict) and any(key in parsed_json for key in ['completeness', 'accuracy', 'executability', 'quality']):
                        result["overall_metrics"] = parsed_json
                        print(f"解析到整体指标")
                    elif isinstance(parsed_json, list):
                        result["individual_evaluations"] = parsed_json
                        print(f"解析到 {len(parsed_json)} 个用例评估")
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"解析评估结果时出错: {e}")
        
        return result
    
    def get_overall_metrics_summary(self, overall_metrics: Dict[str, Any]) -> Dict[str, Any]:

        summary = {
            "completeness": {
                "name": "完整性指标",
                "score": overall_metrics.get("completeness", {}).get("score", 0),
                "description": overall_metrics.get("completeness", {}).get("description", ""),
                "details": overall_metrics.get("completeness", {}).get("details", "")
            },
            "accuracy": {
                "name": "准确性指标", 
                "score": overall_metrics.get("accuracy", {}).get("score", 0),
                "description": overall_metrics.get("accuracy", {}).get("description", ""),
                "details": overall_metrics.get("accuracy", {}).get("details", "")
            },
            "executability": {
                "name": "可执行性指标",
                "score": overall_metrics.get("executability", {}).get("score", 0),
                "description": overall_metrics.get("executability", {}).get("description", ""),
                "details": overall_metrics.get("executability", {}).get("details", "")
            },
            "quality": {
                "name": "质量指标",
                "score": overall_metrics.get("quality", {}).get("score", 0),
                "description": overall_metrics.get("quality", {}).get("description", ""),
                "details": overall_metrics.get("quality", {}).get("details", "")
            }
        }
        
        return summary