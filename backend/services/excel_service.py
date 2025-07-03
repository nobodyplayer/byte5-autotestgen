import os
import pandas as pd
from typing import List, Dict, Any, Union
from datetime import datetime
from models.test_case import TestCase

class ExcelService:
    def __init__(self):
        self.results_dir = "results"
        os.makedirs(self.results_dir, exist_ok=True)

    def generate_excel(self, test_cases: List[Union[TestCase, Dict[str, Any]]], filename_prefix: str = "test_cases") -> str:
        """
        从测试用例生成Excel文件

        参数:
            test_cases: 要包含在Excel文件中的测试用例列表
            filename_prefix: 生成的Excel文件的前缀

        返回:
            生成的Excel文件的路径
        """
        # 为文件名创建时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.xlsx"
        filepath = os.path.join(self.results_dir, filename)

        # 为测试用例创建数据帧
        test_case_data = []
        for tc in test_cases:
            # 检查是否为字典类型（从 Markdown 提取的数据）
            if isinstance(tc, dict):
                # 添加主要测试用例信息
                test_case_info = {
                    "ID": tc.get('id', ''),
                    "Title": tc.get('title', ''),
                    "Description": tc.get('description', ''),
                    "Preconditions": tc.get('preconditions', '') or "",
                    "Priority": tc.get('priority', '') or "Medium"
                }

                # 将每个步骤作为单独的行添加
                steps = tc.get('steps', [])
                for i, step in enumerate(steps):
                    if i == 0:
                        # 第一个步骤使用测试用例信息
                        row = {
                            **test_case_info,
                            "Step Number": step.get('step_number', i+1),
                            "Step Description": step.get('description', ''),
                            "Expected Result": step.get('expected_result', '')
                        }
                    else:
                        # 后续步骤只包含步骤信息
                        row = {
                            "ID": "",
                            "Title": "",
                            "Description": "",
                            "Preconditions": "",
                            "Priority": "",
                            "Step Number": step.get('step_number', i+1),
                            "Step Description": step.get('description', ''),
                            "Expected Result": step.get('expected_result', '')
                        }
                    test_case_data.append(row)
            else:
                # 处理 TestCase 对象
                # 添加主要测试用例信息
                test_case_info = {
                    "ID": tc.id,
                    "Title": tc.title,
                    "Description": tc.description,
                    "Preconditions": tc.preconditions or "",
                    "Priority": tc.priority or "Medium"
                }

                # 将每个步骤作为单独的行添加
                for i, step in enumerate(tc.steps):
                    if i == 0:
                        # 第一个步骤使用测试用例信息
                        row = {
                            **test_case_info,
                            "Step Number": step.step_number,
                            "Step Description": step.description,
                            "Expected Result": step.expected_result
                        }
                    else:
                        # 后续步骤只包含步骤信息
                        row = {
                            "ID": "",
                            "Title": "",
                            "Description": "",
                            "Preconditions": "",
                            "Priority": "",
                            "Step Number": step.step_number,
                            "Step Description": step.description,
                            "Expected Result": step.expected_result
                        }
                    test_case_data.append(row)

        # 创建数据帧并写入Excel
        df = pd.DataFrame(test_case_data)

        # 使用xlsxwriter引擎创建写入器
        writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Test Cases', index=False)

        # 获取xlsxwriter工作簿和工作表对象
        workbook = writer.book
        worksheet = writer.sheets['Test Cases']

        # 添加一些格式化
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })

        # 使用标题格式写入列标题
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # 设置列宽
        worksheet.set_column('A:A', 10)  # ID
        worksheet.set_column('B:B', 30)  # Title
        worksheet.set_column('C:C', 40)  # Description
        worksheet.set_column('D:D', 30)  # Preconditions
        worksheet.set_column('E:E', 10)  # Priority
        worksheet.set_column('F:F', 10)  # Step Number
        worksheet.set_column('G:G', 40)  # Step Description
        worksheet.set_column('H:H', 40)  # Expected Result

        # 关闭写入器
        writer.close()

        return filepath

excel_service = ExcelService()
