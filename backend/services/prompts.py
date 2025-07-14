class TestCasePrompts:
    @staticmethod
    def get_evaluation_prompt(human_reference_cases: str, ai_generated_cases: str) -> str:
        # 如果没有人工参考用例，进行自我评估
        if not human_reference_cases or not human_reference_cases.strip():
            return f"""
请评估以下AI生成的测试用例质量，从完整性、准确性、可执行性、质量四个维度打分（1-5分）。

【AI生成用例】：
{ai_generated_cases}

请输出两个JSON格式的评估结果：

<!-- OVERALL_METRICS_START -->
```json
{{
  "completeness": {{
    "score": 0,
    "description": "完整性评估",
    "details": "具体评估说明"
  }},
  "accuracy": {{
    "score": 0,
    "description": "准确性评估", 
    "details": "具体评估说明"
  }},
  "executability": {{
    "score": 0,
    "description": "可执行性评估",
    "details": "具体评估说明"
  }},
  "quality": {{
    "score": 0,
    "description": "质量指标",
    "details": "具体评估说明"
  }}
}}
```

```json
[
  {{
    "testCaseId": "用例ID",
    "testCaseTitle": "用例标题",
    "scores": {{
      "logic": 0,
      "clarity": 0,
      "completeness": 0,
      "executability": 0
    }},
    "evaluation": {{
      "strengths": ["优点1", "优点2"],
      "weaknesses": ["不足1", "不足2"],
      "suggestions": ["建议1", "建议2"]
    }},
    "overallRating": "A",
    "summary": "总体评价"
  }}
]
```
"""
        else:
            return f"""
请对比AI生成用例与人工参考用例，评估质量并打分（1-5分）。

【人工参考用例】：
{human_reference_cases}

【AI生成用例】：
{ai_generated_cases}

请输出两个JSON格式的评估结果：

```json
{{
  "completeness": {{
    "score": 0,
    "description": "覆盖度评估",
    "details": "具体评估说明"
  }},
  "accuracy": {{
    "score": 0,
    "description": "深度广度评估",
    "details": "具体评估说明"
  }},
  "executability": {{
    "score": 0,
    "description": "创新性评估",
    "details": "具体评估说明"
  }},
  "quality": {{
    "score": 0,
    "description": "简洁性评估",
    "details": "具体评估说明"
  }}
}}
```

```json
[
  {{
    "testCaseId": "用例ID",
    "testCaseTitle": "用例标题",
    "humanReference": "对应人工用例",
    "scores": {{
      "semanticMatch": 0,
      "clarity": 0,
      "executability": 0,
      "automationFriendly": 0
    }},
    "evaluation": {{
      "matchDescription": "匹配说明",
      "strengths": ["优点1", "优点2"],
      "weaknesses": ["不足1", "不足2"],
      "suggestions": ["建议1", "建议2"]
    }},
    "overallRating": "A",
    "summary": "总体评价"
  }}
]
```
            """

    @staticmethod
    def get_image_categorization_prompt(image_count: int) -> str:
        """生成用于图片分类的Prompt"""
        return f"""
        请对以下{image_count}张图片进行分类，识别出哪些是【流程图】、哪些是【功能结构图】、哪些是【UI界面图】。
        请严格按照以下格式返回每种分类包含的图片索引（从0开始），如果某个分类下没有图片，则返回空列表。

        流程图: [索引1, 索引2, ...]
        功能结构图: [索引A, 索引B, ...]
        UI界面图: [索引X, 索引Y, ...]
        """

    @staticmethod
    def get_image_analysis_prompt(category: str, prd_text: str = "") -> str:

    # 通用开头，声明角色与要求
        system_header = """
# 角色：Visua-Logic，多模态AI分析师

你是“Visua-Logic”，一个专注于视觉图表和用户界面语义分析的高级AI系统。你的核心能力是将复杂的视觉信息转化为结构清晰、机器可读的JSON数据。你拥有资深业务分析师、技术架构师和用户体验专家的综合视角。

# 使命：解码、构建与丰富

你的使命是分析所提供的图片，并在任何附带文本的指引下，不仅要提取元素，还要理解其目的、关系和业务背景。你将把这份经过丰富处理的理解，输出为一个单一且无误的JSON对象。
"""

        # 一个共享的认知工具集，用于指导AI的分析过程。
        cognitive_toolkit = """
        # 认知工具集：你的分析框架

        1.  **确认类别**: 首先，在内部确认图片与指定的类别(`{category}`)相匹配。如果严重不符，请在输出的`description`或`error`字段中注明。
        2.  **识别主要目标**: 此图表或UI的核心目标是什么？是为了用户登录，展示数据，还是规划一个业务流程？在整个分析过程中牢记此目标。
        3.  **与文本融合**: 将提供的`[PRD文本上下文]`作为核心信息来源。它能帮助你正确定名元素、理解其业务目的，并推断出视觉上不明确的关系。
        4.  **丰富，而不仅是提取**: 你的价值在于增加语义。一个按钮不只是按钮，它是一个“提交登录表单”的按钮；一个菱形不只是节点，它是一个“决策判断点”。
        """

        # 针对不同图片类别量身定制的、具体的指令和输出格式。
    # 这个字典是整个Prompt的核心逻辑。
        category_specifics = {
        "flowchart": {
            "instructions": """
请深入分析这张业务流程图。识别出每一个处理步骤、决策判断点以及它们之间的流转关系。务必关注流转路径上的判断条件文本。
""",
            "json_schema": """
```json
{{
  "diagramType": "流程图",
  "description": "<对此图表所展示业务流程的一句话摘要>",
  "nodes": [
    {{
      "id": "<节点的唯一标识符，例如：'node_1'>",
      "label": "<节点内部的文本，例如：'用户输入账号密码'>",
      "type": "<节点类型，必须是 'start' (开始节点), 'end' (结束节点), 'process' (处理步骤), 或 'decision' (判断节点) 之一>"
    }}
  ],
  "edges": [
    {{
      "from": "<起始节点的id>",
      "to": "<目标节点的id>",
      "condition": "<路径上的条件文本，例如：'账号密码正确'。若无文本则为空字符串>"
    }}
  ]
}}
```"""
        },
        "structure": {
            "instructions": """
请解析这张功能结构图。识别所有模块与子模块之间的层级归属关系，构建出一棵完整的树状结构。
""",
            "json_schema": """
```json
{{
  "diagramType": "功能结构图",
  "description": "<关于此图表所构建的系统或功能的一句话摘要>",
  "modules": [
    {{
      "name": "<顶层模块名称，例如：'用户中心'>",
      "description": "<从PRD文本中推断出的此模块用途，例如：'管理所有与用户相关的功能'>",
      "submodules": [
        {{
          "name": "<子模块名称，例如：'登录注册'>",
          "description": "<子模块的用途>",
          "submodules": []
        }}
      ]
    }}
  ]
}}
```"""
        },
        "ui": {
            "instructions": """
请从此用户界面（UI）截图中，提取所有可交互的和关键的信息元素。对于每个元素，需判断其最可能的用途和技术类型。请利用PRD文本，将其归类到正确的功能模块下。
""",
            "json_schema": """
```json
{{
  "diagramType": "用户界面",
  "description": "<对此UI用途的一句话摘要，例如：'用户登录界面'>",
  "module": "<此UI所属的主要功能模块，从文本中推断，例如：'登录认证'>",
  "elements": [
    {{
      "name": "<一个描述性的名称，例如：'用户名输入框', '登录按钮', '忘记密码链接'>",
      "type": "<必须是 'button'(按钮), 'input'(输入框), 'textarea'(文本域), 'select'(下拉选择), 'checkbox'(复选框), 'radio_button'(单选按钮), 'toggle_switch'(开关), 'link'(链接), 'tab'(标签页), 'datepicker'(日期选择器), 'icon'(图标), 'label'(静态文本), 'modal_dialog'(模态对话框) 之一>",
      "placeholder": "<输入框的占位提示文本，若无则为null>",
      "purpose": "<推断出的此元素的功能或行为，例如：'用于用户输入注册的手机号', '点击后触发表单提交'>",
      "value": "<控件当前显示的值，若无则为null>"
    }}
  ]
}}
```"""
        },
        "default": {
            "instructions": "此图片类别非标准，请用结构化的方式描述其主要内容和用途。",
            "json_schema": """
```json
{{
  "diagramType": "其他",
  "description": "<对图片内容的详细描述>",
  "extracted_text": "<图片中识别出的所有文本的集合>"
}}
```"""
        }
    }

        # 根据传入的类别，选择对应的指令和规格。
        selected_spec = category_specifics.get(category, category_specifics["default"])

        # 组装最终的完整Prompt。
        prompt = f"""{system_header}
        {cognitive_toolkit.format(category=category)}
        # 输入数据与指令

        ## 1. 图像
        [此处将提供一张'{category}'类型的图片]

        ## 2. PRD文本上下文 (可选)
        {prd_text or '未提供PRD文本上下文。'}
        ## 3. 你的任务
        {selected_spec['instructions']}

        # 输出格式：严格的JSON

        你的回复必须是一个、且只能是一个严格遵循以下Schema规范的JSON对象。请勿在JSON结构之前或之后添加任何文本、注释或Markdown格式。

        {selected_spec['json_schema']}
        """
        return prompt



    @staticmethod
    def get_final_test_points_prompt(
        prd_text: str, 
        flowchart_info: str, 
        structure_info: str, 
        ui_info: str, 
        context: str, 
        human_reference_cases: str
    ) -> str:
        """生成最终的测试点生成Prompt"""
        return f"""
        # Persona: The QA Brain Trust

你不再是单一的测试专家，而是模拟一个由三人组成的顶级“质量保证智囊团(QA Brain Trust)”，每个角色都有明确分工：
- **业务分析师 (BA):** 专注于理解业务逻辑、用户故事和PRD文本，确保测试点完整覆盖所有业务规则和用户需求。
- **技术测试架构师 (TA):** 专注于分析流程图、功能结构和UI元素，从技术实现、系统交互和数据流动的角度发现潜在的测试场景，尤其擅长识别边界和异常情况。
- **用户体验设计师 (UXD):** 专注于从终端用户的视角审视产品，思考易用性、交互友好性和场景的流畅性，提出与用户体验相关的测试点。

你们将协同工作，确保最终输出的测试点既有业务深度，又有技术广度，同时不失用户视角。

# Master Plan: Your Systematic Approach

你们必须遵循以下“三步走”的行动纲领来完成任务：

1.  **第一步：信息全景融合 (Holistic Information Synthesis)**
    - 仔细阅读并融合下方提供的所有信息源（PRD、流程图、结构图、UI、上下文、特殊要求）。
    - 基于**功能结构图（structure_info）**作为核心骨架，将其他信息（PRD文本、UI元素等）精准地关联和填充到对应的功能模块下。这一步的目标是为每个功能模块建立一个360度的信息视图。

2.  **第二步：模块化深度打击 (Modular Deep-Dive Analysis)**
    - 以第一步整合好的功能模块为单位，逐一进行分析。
    - 对每个模块，你们三人需要共同调用下面的 **“Comprehensive Testing Methodology”** 思维框架，从所有维度进行头脑风暴，提出尽可能完整的测试点。

3.  **第三步：结构化精准输出 (Structured & Precise Output)**
    - 将所有讨论出的测试点汇总。
    - 严格遵循“输出格式与约束”的要求，生成最终的JSON对象。

# Comprehensive Testing Methodology (Your Core Thinking Framework)

在分析每个功能模块时，必须系统性地从以下十个维度进行思考和扩展，以确保测试的绝对全面性：

1.  **功能符合性测试 (Functional Conformance):**
    - **正向核心路径:** 是否实现了PRD中描述的所有主要成功路径？（例如：“验证使用有效账号密码能成功登录”）
    - **负向功能场景:** 如果不满足前提条件，功能是否能正确阻止？（例如：“验证未输入密码时，登录按钮为置灰状态或点击后提示错误”）

2.  **边界值分析 (Boundary Value Analysis):**
    - **输入框长度:** 考虑所有输入字段的最小-1、最小、常规、最大、最大+1个字符。（例如：“验证昵称输入框在输入最大长度+1个字符时被截断或提示超长”）
    - **数值范围:** 对于数字输入，测试最小值-1、最小值、有效值、最大值、最大值+1。（例如：“验证商品数量输入0时下单失败”）
    - **时间边界:** 测试日期/时间的临界点，如跨天、跨月、跨年、闰年等。

3.  **等价类划分 (Equivalence Class Partitioning):**
    - **有效等价类:** 从一组有效输入中取一个代表值。（例如：“验证输入合法的手机号可以收到验证码”）
    - **无效等价类:** 从各种典型的无效输入中各取一个代表值。（例如：“验证输入10位手机号、包含字母的手机号、或中文手机号时，系统均提示格式错误”）

4.  **状态迁移测试 (State Transition Testing):**
    - **状态变化:** 基于流程图（flowchart_info），验证对象或页面在不同操作下的状态是否正确切换。（例如：“验证订单在‘支付成功’后，状态从‘待支付’变为‘待发货’”）
    - **不可达迁移:** 验证是否存在非法的状态跳转。（例如：“验证无法将一个‘已取消’的订单直接标记为‘已完成’”）

5.  **异常与错误处理测试 (Exception & Error Handling):**
    - **接口/网络异常:** 模拟操作过程中网络中断、服务器超时、返回5xx/4xx错误码时，前端是否有友好的提示和重试机制。（例如：“验证在提交订单时断开网络，页面显示‘网络错误，请稍后重试’的提示”）
    - **权限控制:** 使用不同权限的账户，验证是否能访问/操作其不应触及的功能。（例如：“验证普通用户无法看到‘系统管理’入口”）
    - **数据异常:** 模拟关键数据（如用户信息）丢失或格式错误时，系统的表现。

6.  **UI与交互测试 (UI & Interaction Testing):**
    - **元素校验:** 检查UI界面（ui_info）中的所有可见元素是否与设计稿一致（文本、颜色、布局）。
    - **交互反馈:** 所有可交互控件（按钮、链接、输入框）在点击、悬停、输入等操作后，是否提供即时且正确的视觉反馈。（例如：“验证鼠标悬停在‘保存’按钮上时，按钮高亮显示”）
    - **响应式布局:** 如果适用，验证在不同分辨率或设备尺寸下，页面布局是否依然合理。

7.  **数据一致性与正确性测试 (Data Consistency & Correctness):**
    - **增删改查(CRUD):** 验证数据在创建、读取、更新、删除后，前端展示与后端存储是否完全一致。
    - **计算准确性:** 验证所有涉及计算的功能（如价格、折扣、统计）结果是否准确无误。

8.  **易用性与文案测试 (Usability & Copywriting Testing):**
    - **引导文案:** 页面上的提示文字、标签、说明是否清晰易懂，无歧义，无错别字。
    - **操作流程:** 用户完成一个任务的步骤是否足够简化和直观？

9.  **性能阈值测试 (Performance Threshold - Sanity Check):**
    - **大数据量:** 当列表或页面需要加载大量数据时，响应时间是否在可接受范围内？（例如：“验证当订单历史超过1000条时，打开页面是否会导致浏览器卡顿”）
    - **并发操作:** 快速重复点击同一个按钮，系统是否能正确处理，防止重复提交？

10. **安全性测试 (Security - Basic Checks):**
    - **输入注入:** 在输入框中尝试输入简单的SQL注入或XSS攻击脚本，验证系统是否能有效防止。（例如：“验证在搜索框输入`<script>alert(1)</script>`后，页面没有弹出警告框”）
    - **信息暴露:** 验证在URL、接口响应或页面源码中，没有暴露敏感信息（如用户ID、密钥）。

# 可用信息
1.  **PRD核心文本**：
    ```
    {prd_text or '无相关文本'}
    ```
2.  **流程图分析结果**：
    ```
    {flowchart_info or '无相关流程图'}
    ```
3.  **功能结构图分析结果 (核心)**：
    ```
    {structure_info or '无相关功能结构图'}
    ```
4.  **UI界面图分析结果**：
    ```
    {ui_info or '无相关UI图'}
    ```
5.  **额外上下文**：
    ```
    {context or '无额外上下文'}
    ```
6.  **人工参考用例**：
    ```
    {human_reference_cases or '无人工参考用例'}
    ```

# 输出格式与约束
- **严格JSON:** 你的最终输出必须是一个、且只能是一个严格遵循RFC8259标准的JSON对象。不要在JSON的`{{`之前或`}}`之后添加任何介绍、解释或注释。
- **模块化结构:** 以**功能结构图**或**PRD**中识别出的**功能模块名称**作为JSON的键（Key）。
- **测试点数组:** 每个键的值（Value）必须是一个字符串数组（Array of strings）。
- **原子化描述:** 每条测试点必须以“验证”开头，是一个具体、可执行的测试场景描述，保持为一行完整的句子，不得换行或拆分。
- **全面覆盖:** 确保应用了上述所有测试方法论，产出的测试点列表需要体现出深度和广度。
- **空处理:** 如果根据所有输入信息，确实无法识别出任何功能模块或测试点，必须返回一个空的JSON对象：`{{}}`。

# 输出示例 (这是一个格式参考，你的输出需要更全面)
```json
{{
    "用户登录与认证": [
        "验证输入正确的用户名和密码并点击登录，页面成功跳转到主页",
        "验证输入已注册但密码错误的账号，页面提示'用户名或密码错误'",
        "验证输入未注册的用户名，页面提示'用户不存在'",
        "验证用户名输入框输入最大长度+1个字符时，无法继续输入",
        "验证密码输入框为密文显示",
        "验证点击'显示密码'图标后，密码变为明文可见",
        "验证在登录页面断开网络后点击登录，页面出现网络异常的友好提示",
        "验证密码输入框输入简单的SQL注入语句，登录失败且服务器无异常"
    ],
    "个人资料修改": [
        "验证登录后进入个人资料页，能成功修改昵称并保存",
        "验证昵称输入框为空时，保存按钮置灰或点击后提示'昵称不能为空'",
        "验证修改头像功能，从本地上传一张小于2MB的JPG图片能成功显示",
        "验证修改头像功能，上传一张大于2MB的图片时提示'文件过大'",
        "验证修改头像功能，上传一个非图片格式文件（如.txt）时提示'格式不支持'"
    ]
}}
        """
        


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
