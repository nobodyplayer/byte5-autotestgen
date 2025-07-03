class TestCasePrompts:
    """测试用例生成相关的提示词模板"""
    

    

    
    @staticmethod
    def get_multimodal_prd_prompt(prd_text: str, context: str, requirements: str) -> str:
        """获取多模态PRD分析的提示词"""
        format_instructions = TestCasePrompts._get_format_instructions()
        return f"""请基于PRD文档内容（包括文本和图片）生成全面的测试用例。

PRD文档文本内容:
{prd_text}

上下文信息: {context}

特殊要求: {requirements}

{format_instructions}

请结合PRD文档的文本内容和提供的图片（如UI设计图、流程图等），生成覆盖所有功能点、用户场景和边界条件的测试用例。特别注意：
1. 分析图片中的UI元素、交互流程和业务逻辑
2. 结合文本描述理解完整的产品需求
3. 确保测试用例涵盖正常流程、异常流程和边界条件
4. 考虑不同用户角色和使用场景"""
    
    @staticmethod
    def _get_format_instructions() -> str:
        """获取测试用例格式说明"""
        return """请先以 Markdown 格式生成测试用例，包含以下内容：
1. 测试用例 ID 和标题（使用二级标题格式，如 ## TC-001: 测试标题）
2. 优先级（加粗显示，如 **优先级:** 高）
3. 描述（加粗显示，如 **描述:** 测试描述）
4. 前置条件（如果有，加粗显示，如 **前置条件:** 条件描述）
5. 测试步骤和预期结果（使用标准 Markdown 表格格式）

对于测试步骤表格，请使用以下格式：

```
### 测试步骤

| # | 步骤描述 | 预期结果 |
| --- | --- | --- |
| 1 | 第一步描述 | 第一步预期结果 |
| 2 | 第二步描述 | 第二步预期结果 |
```

请确保表格格式正确，包含表头和分隔行。

然后，在生成完 Markdown 格式的测试用例后，请生成结构化的测试用例数据，包含相同的内容，但使用 JSON 格式，以便于导出到 Excel。

请确保测试用例覆盖全面，包含正向和负向测试场景。"""

class SystemMessages:
    """系统消息模板"""    
    
    MULTIMODAL_ANALYSIS = (
        "你是一个专业的测试工程师，专门负责基于多模态PRD文档（包含文本和图片）生成高质量的测试用例。"
        "请综合分析PRD文档的文本内容和相关图片（如UI设计图、流程图、架构图等），"
        "深入理解产品需求、用户交互流程和业务逻辑，"
        "生成全面、准确且可执行的测试用例。"
        "特别注意图片中的UI元素、交互细节和业务流程，"
        "确保测试用例覆盖所有功能点、用户场景、正常流程、异常情况和边界条件。"
    )

class ErrorMessages:
    """错误消息模板"""
    
    FEISHU_SERVICE_NOT_INITIALIZED = "飞书服务未初始化，请提供飞书应用凭证"
    DOCUMENT_CONTENT_EMPTY = "无法获取文档内容或文档为空"
    
    @staticmethod
    def get_feishu_error(error_detail: str) -> str:
        """获取飞书相关错误消息"""
        return f"获取飞书文档内容失败: {error_detail}"
    
    @staticmethod
    def get_generation_error(error_detail: str) -> str:
        """获取测试用例生成错误消息"""
        return f"生成测试用例时出错: {error_detail}"