import uuid

class MultiAgentSession:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.stage = "initial"  # initial, optimization
        self.round_count = 0
        self.max_rounds = 3
        # 持久化数据
        self.parsed_data = {
            "prd_text": "",
            "prd_images": [],
            "context": "",
            "human_reference_cases": ""
        }
        # 结果存储
        self.results = {
            "initial_cases": "",
            "initial_evaluation": "",
            "optimized_cases": "",
            "optimization_history": [],
            "user_feedback": []
        }
        # 智能体实例
        self.generator = None
        self.evaluator = None
        self.coordinator = None