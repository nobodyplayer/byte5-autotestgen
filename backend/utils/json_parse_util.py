import json
import re

def parse_json_output(llm_output: str, expected_type: type = list):
    """
    从LLM输出中提取JSON, 处理markdown块。

    参数:
        llm_output: LLM输出的原始字符串
        expected_type: 希望的python类型 (e.g., list, dict).

    Returns:
        转换出的JSON数据或为空
    """
    # 将LLM输出转化为JSON
    if not llm_output:
        print("LLM输出为空")
        return None

    # 尝试找寻markdown中的JSON
    patterns = [
        r'```json\s*(.*)\s*```', # 标准markdown块
        r'```\s*(.*)\s*```'      # 通用代码块
    ]
    # 放宽模板条件
    if expected_type == list:
        patterns.append(r'(\[.*\])') # 输出为一个列表
    elif expected_type == dict:
        patterns.append(r'(\{.*\})') # 输出为一个字典

    json_str = None
    match_found = False
    for pattern in patterns:
        # 模板匹配
        match = re.search(pattern, llm_output, re.DOTALL | re.IGNORECASE)
        if match:
            # 提取可能json
            potential_json = match.group(1).strip()
            # 基本检查，确认是否符合期望的要求
            looks_like_list = expected_type == list and potential_json.startswith('[') and potential_json.endswith(']')
            looks_like_dict = expected_type == dict and potential_json.startswith('{') and potential_json.endswith('}')

            if looks_like_list or looks_like_dict:
                 json_str = potential_json
                 match_found = True
                 break # 使用第一个有效的匹配

    if not match_found:
        # 未匹配，解析源输出是否符合期望的规则
        trimmed_output = llm_output.strip()
        if expected_type == list and trimmed_output.startswith('[') and trimmed_output.endswith(']'):
            json_str = trimmed_output
        elif expected_type == dict and trimmed_output.startswith('{') and trimmed_output.endswith('}'):
            json_str = trimmed_output

    if not json_str:
        # 无法找到JSON字符串
        print(f"无法从LLM中提取有效的{expected_type.__name__}结构", "WARNING")
        return None
    try:
        # json加载
        parsed_data = json.loads(json_str)
        if isinstance(parsed_data, expected_type):
            return parsed_data
        else:
            # 与所期望的数据类型不匹配
            print(f"转换出的数据类型是{type(parsed_data).__name__}, 期望的数据类型是{expected_type.__name__}.", "WARNING")
            return None
    except json.JSONDecodeError as e:
        # JSON转换失败
        print(f"JSON转换失败: {e}. 无效的JSON字符: '{json_str[:200]}...'", "ERROR")
        return None
    except Exception as e:
        # 其他错误
        print(f"JSON转换时出现未知错误: {e}", "ERROR")
        return None