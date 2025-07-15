import asyncio
from autogen_agentchat.agents import AssistantAgent
from .prompts import TestCasePrompts
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from .ai_service import model_client

class EvaluatorAgent(AssistantAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = {}
        self.previous_chunks = []
    async def generate_reply(self, messages):
        ai_cases = self.memory.get("latest_cases", "")
        human_cases = self.memory.get("human_reference_cases", "")
        evaluation_prompt = TestCasePrompts.get_evaluation_prompt(human_cases, ai_cases)
        agent = AssistantAgent(
            name="test_case_evaluator",
            model_client=model_client,
            system_message="你是专业的测试用例评估专家，请严格按照指定的JSON格式输出评估结果。",
            model_client_stream=True,
        )
        result = ""
        async for event in agent.run_stream(task=evaluation_prompt):
            if isinstance(event, ModelClientStreamingChunkEvent):
                result += event.content
                yield event.content
                self.previous_chunks.append(event.content)
        self.memory["last_evaluation"] = result

class GeneratorAgent(AssistantAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = {}
        self.previous_chunks = []
    async def generate_reply(self, messages):
        prd_text = self.memory.get("prd_text", "")
        prd_images = self.memory.get("prd_images", [])
        context = self.memory.get("context", "")
        evaluation = self.memory.get("last_evaluation", "")
        human_cases = self.memory.get("human_reference_cases", "")
        flowchart_info = self.memory.get("flowchart_info", "")
        structure_info = self.memory.get("structure_info", "")
        ui_info = self.memory.get("ui_info", "")
        prompt = TestCasePrompts.get_final_test_points_prompt(
            prd_text=prd_text,
            flowchart_info=flowchart_info,
            structure_info=structure_info,
            ui_info=ui_info,
            evaluation=evaluation,
            human_reference_cases=human_cases
        )
        agent = AssistantAgent(
            name="final_test_points_agent",
            model_client=model_client,
            system_message="你是专业的测试工程师，请严格按照用户指定的JSON格式输出功能模块化的测试点。",
            model_client_stream=True,
        )
        result = ""
        async for event in agent.run_stream(task=prompt):
            if isinstance(event, ModelClientStreamingChunkEvent):
                result += event.content
                self.previous_chunks.append(event.content)
                yield event.content
        self.memory["latest_cases"] = result

class CoordinatorAgent(AssistantAgent):
    def __init__(self, max_round=3, **kwargs):
        super().__init__(**kwargs)
        self.memory = {}
        self.previous_chunks = []
        self.round = 0
        self.max_round = max_round

    async def generate_reply(self, messages):
        self.round += 1
        if self.round == 1:
            return "第一轮，请 GeneratorAgent 生成测试用例"
        elif self.round == 2:
            return "第二轮，请 EvaluatorAgent 进行自动评估"
        elif 3 <= self.round <= self.max_round+1:
            return f"第{self.round-1}轮，请 GeneratorAgent 根据评估优化用例"
        else:
            return "优化完成，输出最终生成的测试用例"