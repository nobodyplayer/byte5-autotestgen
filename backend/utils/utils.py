from typing import List, Dict, Any

def generate_mindmap_from_test_cases(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        ]
    }
    mindmap["children"].append(stats_node)

    return mindmap

def _calculate_average_steps(test_cases: List[Dict[str, Any]]) -> float:
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