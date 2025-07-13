import os
import re
from typing import List, Dict, Any
from PIL import Image as PILImage
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import MultiModalMessage
from autogen_core import Image as AGImage
from utils.llms import model_client
from .prompts import TestCasePrompts

class ImageProcessor:
    def __init__(self):
        self.model_client = model_client

    async def process_images(self, image_paths: List[str], prd_text: str = "") -> Dict[str, Any]:
        """处理图片列表，分类并调用大模型分析，返回结构化信息"""
        image_analysis_results = {
            "flowchart_info": "",
            "structure_info": "",
            "ui_info": ""
        }
        if not image_paths:
            return image_analysis_results
        # 1. 图片分类
        categorization_prompt = TestCasePrompts.get_image_categorization_prompt(len(image_paths))
        
        ag_images = []
        if image_paths:  # 只有当有图片时才处理
            for i, image_path in enumerate(image_paths):
                try:
                    if not os.path.exists(image_path):
                        print(f"跳过第{i+1}张图片：文件不存在 {image_path}")
                        continue
                    with PILImage.open(image_path) as pil_image:
                        # 验证图片尺寸
                        if pil_image.size[0] > 0 and pil_image.size[1] > 0:
                            # 创建AGImage对象时需要复制图片，避免文件关闭后无法访问
                            pil_image_copy = pil_image.copy()
                            ag_image = AGImage(pil_image_copy)
                            ag_images.append(ag_image)
                            print(f"成功转换第{i+1}张图片")
                        else:
                            print(f"跳过第{i+1}张图片")
                        
                except Exception as e:
                    import traceback
                    print(f"处理第{i+1}张图片时出错: {e}")
                    print(f"错误堆栈: {traceback.format_exc()}")
                    continue 
        
        categorization_agent = AssistantAgent(
            name="image_categorizer",
            model_client=self.model_client,
            system_message="你是专业的图像分析师，负责对图片进行分类。"
        )
        
        try:
            response = await categorization_agent.run(
                task=MultiModalMessage(content=[categorization_prompt] + ag_images, source="user")
            )
            # 按官方文档获取最终内容
            if hasattr(response, "messages") and response.messages:
                last_message = response.messages[-1]
                categorization_result = getattr(last_message, "content", None)
            else:
                categorization_result = None
        except Exception as e:
            import traceback
            print(f"[ImageProcessor] Traceback: {traceback.format_exc()}")
            return image_analysis_results
        
        # 解析分类结果
        flowchart_indices = self._parse_indices(categorization_result, "流程图")
        structure_indices = self._parse_indices(categorization_result, "功能结构图")
        ui_indices = self._parse_indices(categorization_result, "UI界面图")

        # 2. 按类别分析图片

        if flowchart_indices:
    
            image_analysis_results["flowchart_info"] = await self._analyze_image_category(
                [image_paths[i] for i in flowchart_indices], 
                "flowchart", 
                prd_text
            )
        if structure_indices:
            image_analysis_results["structure_info"] = await self._analyze_image_category(
                [image_paths[i] for i in structure_indices], 
                "structure", 
                prd_text
            )
        if ui_indices:
            image_analysis_results["ui_info"] = await self._analyze_image_category(
                [image_paths[i] for i in ui_indices], 
                "ui", 
                prd_text
            )
        return image_analysis_results

    def _parse_indices(self, result_text: str, category_name: str) -> List[int]:
        try:
            match = re.search(f'{category_name}.*?:.*?(\d[\d,\s]*)', result_text, re.IGNORECASE)
            if match:
                indices_str = match.group(1).strip()
        
                return [int(i.strip()) for i in indices_str.split(',') if i.strip().isdigit()]
            else:
                print(f"    No match found for '{category_name}'.")
        except Exception as e:
            print(f"    Error parsing indices for {category_name}: {e}")
        return []

    async def _analyze_image_category(self, image_paths: List[str], category: str, prd_text: str) -> str:
        if not image_paths:
            return ""

        prompt = TestCasePrompts.get_image_analysis_prompt(category, prd_text)
        ag_images = []
        if image_paths:  # 只有当有图片时才处理
            for i, image_path in enumerate(image_paths):
                try:
                    if not os.path.exists(image_path):
                        print(f"分析阶段跳过第{i+1}张图片：文件不存在 {image_path}")
                        continue
                    
                    with PILImage.open(image_path) as pil_image:
                        if pil_image.size[0] > 0 and pil_image.size[1] > 0:
                            pil_image_copy = pil_image.copy()
                            ag_image = AGImage(pil_image_copy)
                            ag_images.append(ag_image)
                            print(f"分析阶段成功处理第{i+1}张图片")
                        else:
                            print(f"分析阶段跳过第{i+1}张图片")
                except Exception as e:
                    import traceback
                    print(f"分析阶段处理第{i+1}张图片时出错: {e}")
                    print(f"错误堆栈: {traceback.format_exc()}")
                    continue

        analysis_agent = AssistantAgent(
            name=f"{category}_analysis_agent",
            model_client=self.model_client,
            system_message="你是一个多模态AI助手，负责分析图片并提取关键信息。"
        )
        
        response = await analysis_agent.run(
            task=MultiModalMessage(content=[prompt] + ag_images, source="user")
        )
        # 按官方文档获取最终内容
        if hasattr(response, "messages") and response.messages:
            last_message = response.messages[-1]
            analysis_result = getattr(last_message, "content", None)
        else:
            analysis_result = None

        return analysis_result
