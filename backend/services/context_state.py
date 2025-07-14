from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import json
import uuid

"""
# 创建状态管理实例
context = ContextState()

# 开始第一轮优化
round_id = context.start_new_round("初始测试用例生成")

# 添加文本和图片信息
context.update_text_info("用户注册功能需求", "manual")
context.add_image("/path/to/image.png", "界面截图")

# 更新测试用例
test_cases = [{"title": "用户注册", "description": "测试用户注册流程"}]
context.update_test_cases(test_cases)

# 添加评价信息
context.add_human_evaluation("测试专家", 85.0, "整体不错，需要补充边界用例")
context.update_auto_evaluation(90.0, 80.0, 85.0, 85.0)

# 开始下一轮优化
context.start_new_round("根据评价优化测试用例")

# 获取优化上下文
optimization_context = context.get_context_for_optimization()
"""
@dataclass
class TextInfo:
    """文本信息类"""
    content: str
    source: str  # 'manual', 'feishu', 'file'
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageInfo:
    """图片信息类"""
    path: str
    description: str = ""
    source: str = ""  # 'upload', 'feishu', 'generated'
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCasePoint:
    """测试用例点信息类"""
    id: str
    title: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    category: str
    steps: List[str] = field(default_factory=list)
    expected_result: str = ""
    actual_result: str = ""
    status: str = "pending"  # 'pending', 'passed', 'failed', 'blocked'
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HumanEvaluation:
    """人工评价信息类"""
    evaluator: str
    score: float  # 0-100
    comments: str
    suggestions: List[str] = field(default_factory=list)
    evaluation_criteria: Dict[str, float] = field(default_factory=dict)  # 各项评分标准
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutoEvaluation:
    """自动化评估信息类"""
    coverage_score: float  # 覆盖率得分
    quality_score: float   # 质量得分
    completeness_score: float  # 完整性得分
    overall_score: float   # 总体得分
    metrics: Dict[str, Any] = field(default_factory=dict)  # 详细指标
    timestamp: datetime = field(default_factory=datetime.now)
    evaluation_model: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationRound:
    """优化轮次信息类"""
    round_id: str
    round_number: int
    text_info: Optional[TextInfo] = None
    images: List[ImageInfo] = field(default_factory=list)
    test_cases: List[TestCasePoint] = field(default_factory=list)
    human_evaluations: List[HumanEvaluation] = field(default_factory=list)
    auto_evaluation: Optional[AutoEvaluation] = None
    optimization_notes: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextState:
    """上下文状态管理类，支持多轮优化和增量保留机制"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.rounds: List[OptimizationRound] = []
        self.current_round_number = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata: Dict[str, Any] = {}
    
    def start_new_round(self, optimization_notes: str = "") -> str:
        """开始新的优化轮次
        
        Args:
            optimization_notes: 本轮优化说明
            
        Returns:
            str: 新轮次的ID
        """
        self.current_round_number += 1
        round_id = f"{self.session_id}_round_{self.current_round_number}"
        
        new_round = OptimizationRound(
            round_id=round_id,
            round_number=self.current_round_number,
            optimization_notes=optimization_notes
        )
        
        # 如果有前一轮的数据，继承部分信息
        if self.rounds:
            previous_round = self.rounds[-1]
            # 继承文本信息（如果没有新的文本输入）
            new_round.text_info = previous_round.text_info
            # 继承图片信息
            new_round.images = previous_round.images.copy()
        
        self.rounds.append(new_round)
        self.updated_at = datetime.now()
        return round_id
    
    def get_current_round(self) -> Optional[OptimizationRound]:
        """获取当前轮次"""
        return self.rounds[-1] if self.rounds else None
    
    def get_round_by_id(self, round_id: str) -> Optional[OptimizationRound]:
        """根据ID获取指定轮次"""
        for round_data in self.rounds:
            if round_data.round_id == round_id:
                return round_data
        return None
    
    def update_text_info(self, content: str, source: str = "manual", 
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """更新当前轮次的文本信息"""
        current_round = self.get_current_round()
        if not current_round:
            self.start_new_round("Initial round")
            current_round = self.get_current_round()
        
        current_round.text_info = TextInfo(
            content=content,
            source=source,
            metadata=metadata or {}
        )
        self.updated_at = datetime.now()
    
    def add_image(self, path: str, description: str = "", source: str = "upload",
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加图片信息到当前轮次"""
        current_round = self.get_current_round()
        if not current_round:
            self.start_new_round("Initial round")
            current_round = self.get_current_round()
        
        image_info = ImageInfo(
            path=path,
            description=description,
            source=source,
            metadata=metadata or {}
        )
        current_round.images.append(image_info)
        self.updated_at = datetime.now()
    
    def update_test_cases(self, test_cases: List[Dict[str, Any]]) -> None:
        """更新当前轮次的测试用例"""
        current_round = self.get_current_round()
        if not current_round:
            self.start_new_round("Initial round")
            current_round = self.get_current_round()
        
        current_round.test_cases = []
        for case_data in test_cases:
            test_case = TestCasePoint(
                id=case_data.get('id', str(uuid.uuid4())),
                title=case_data.get('title', ''),
                description=case_data.get('description', ''),
                priority=case_data.get('priority', 'medium'),
                category=case_data.get('category', ''),
                steps=case_data.get('steps', []),
                expected_result=case_data.get('expected_result', ''),
                actual_result=case_data.get('actual_result', ''),
                status=case_data.get('status', 'pending'),
                metadata=case_data.get('metadata', {})
            )
            current_round.test_cases.append(test_case)
        
        self.updated_at = datetime.now()
    
    def add_human_evaluation(self, evaluator: str, score: float, comments: str,
                           suggestions: Optional[List[str]] = None,
                           evaluation_criteria: Optional[Dict[str, float]] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加人工评价"""
        current_round = self.get_current_round()
        if not current_round:
            self.start_new_round("Initial round")
            current_round = self.get_current_round()
        
        evaluation = HumanEvaluation(
            evaluator=evaluator,
            score=score,
            comments=comments,
            suggestions=suggestions or [],
            evaluation_criteria=evaluation_criteria or {},
            metadata=metadata or {}
        )
        current_round.human_evaluations.append(evaluation)
        self.updated_at = datetime.now()
    
    def update_auto_evaluation(self, coverage_score: float, quality_score: float,
                             completeness_score: float, overall_score: float,
                             metrics: Optional[Dict[str, Any]] = None,
                             evaluation_model: str = "default",
                             metadata: Optional[Dict[str, Any]] = None) -> None:
        """更新自动化评估结果"""
        current_round = self.get_current_round()
        if not current_round:
            self.start_new_round("Initial round")
            current_round = self.get_current_round()
        
        current_round.auto_evaluation = AutoEvaluation(
            coverage_score=coverage_score,
            quality_score=quality_score,
            completeness_score=completeness_score,
            overall_score=overall_score,
            metrics=metrics or {},
            evaluation_model=evaluation_model,
            metadata=metadata or {}
        )
        self.updated_at = datetime.now()
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """获取优化历史记录"""
        history = []
        for round_data in self.rounds:
            round_summary = {
                'round_id': round_data.round_id,
                'round_number': round_data.round_number,
                'timestamp': round_data.timestamp.isoformat(),
                'optimization_notes': round_data.optimization_notes,
                'test_cases_count': len(round_data.test_cases),
                'human_evaluations_count': len(round_data.human_evaluations),
                'has_auto_evaluation': round_data.auto_evaluation is not None,
                'images_count': len(round_data.images)
            }
            
            # 添加评分信息
            if round_data.auto_evaluation:
                round_summary['auto_scores'] = {
                    'coverage': round_data.auto_evaluation.coverage_score,
                    'quality': round_data.auto_evaluation.quality_score,
                    'completeness': round_data.auto_evaluation.completeness_score,
                    'overall': round_data.auto_evaluation.overall_score
                }
            
            if round_data.human_evaluations:
                avg_human_score = sum(eval.score for eval in round_data.human_evaluations) / len(round_data.human_evaluations)
                round_summary['avg_human_score'] = avg_human_score
            
            history.append(round_summary)
        
        return history
    
    def get_context_for_optimization(self) -> Dict[str, Any]:
        """获取用于优化的完整上下文信息"""
        current_round = self.get_current_round()
        if not current_round:
            return {}
        
        context = {
            'session_id': self.session_id,
            'current_round_number': self.current_round_number,
            'text_content': current_round.text_info.content if current_round.text_info else "",
            'images': [{
                'path': img.path,
                'description': img.description,
                'source': img.source
            } for img in current_round.images],
            'current_test_cases': [{
                'id': case.id,
                'title': case.title,
                'description': case.description,
                'priority': case.priority,
                'category': case.category,
                'steps': case.steps,
                'expected_result': case.expected_result,
                'status': case.status
            } for case in current_round.test_cases],
            'previous_evaluations': {
                'human': [{
                    'evaluator': eval.evaluator,
                    'score': eval.score,
                    'comments': eval.comments,
                    'suggestions': eval.suggestions
                } for eval in current_round.human_evaluations],
                'auto': {
                    'coverage_score': current_round.auto_evaluation.coverage_score,
                    'quality_score': current_round.auto_evaluation.quality_score,
                    'completeness_score': current_round.auto_evaluation.completeness_score,
                    'overall_score': current_round.auto_evaluation.overall_score,
                    'metrics': current_round.auto_evaluation.metrics
                } if current_round.auto_evaluation else None
            },
            'optimization_history': self.get_optimization_history()
        }
        
        return context
    
    def export_to_dict(self) -> Dict[str, Any]:
        """导出完整状态为字典"""
        return {
            'session_id': self.session_id,
            'current_round_number': self.current_round_number,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata,
            'rounds': [{
                'round_id': round_data.round_id,
                'round_number': round_data.round_number,
                'optimization_notes': round_data.optimization_notes,
                'timestamp': round_data.timestamp.isoformat(),
                'text_info': {
                    'content': round_data.text_info.content,
                    'source': round_data.text_info.source,
                    'timestamp': round_data.text_info.timestamp.isoformat(),
                    'metadata': round_data.text_info.metadata
                } if round_data.text_info else None,
                'images': [{
                    'path': img.path,
                    'description': img.description,
                    'source': img.source,
                    'timestamp': img.timestamp.isoformat(),
                    'metadata': img.metadata
                } for img in round_data.images],
                'test_cases': [{
                    'id': case.id,
                    'title': case.title,
                    'description': case.description,
                    'priority': case.priority,
                    'category': case.category,
                    'steps': case.steps,
                    'expected_result': case.expected_result,
                    'actual_result': case.actual_result,
                    'status': case.status,
                    'timestamp': case.timestamp.isoformat(),
                    'metadata': case.metadata
                } for case in round_data.test_cases],
                'human_evaluations': [{
                    'evaluator': eval.evaluator,
                    'score': eval.score,
                    'comments': eval.comments,
                    'suggestions': eval.suggestions,
                    'evaluation_criteria': eval.evaluation_criteria,
                    'timestamp': eval.timestamp.isoformat(),
                    'metadata': eval.metadata
                } for eval in round_data.human_evaluations],
                'auto_evaluation': {
                    'coverage_score': round_data.auto_evaluation.coverage_score,
                    'quality_score': round_data.auto_evaluation.quality_score,
                    'completeness_score': round_data.auto_evaluation.completeness_score,
                    'overall_score': round_data.auto_evaluation.overall_score,
                    'metrics': round_data.auto_evaluation.metrics,
                    'timestamp': round_data.auto_evaluation.timestamp.isoformat(),
                    'evaluation_model': round_data.auto_evaluation.evaluation_model,
                    'metadata': round_data.auto_evaluation.metadata
                } if round_data.auto_evaluation else None,
                'metadata': round_data.metadata
            } for round_data in self.rounds]
        }
    
    def save_to_file(self, filepath: str) -> None:
        """保存状态到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.export_to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'ContextState':
        """从文件加载状态"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 创建新实例
        instance = cls(session_id=data['session_id'])
        instance.current_round_number = data['current_round_number']
        instance.created_at = datetime.fromisoformat(data['created_at'])
        instance.updated_at = datetime.fromisoformat(data['updated_at'])
        instance.metadata = data['metadata']
        
        # 重建轮次数据
        for round_data in data['rounds']:
            round_obj = OptimizationRound(
                round_id=round_data['round_id'],
                round_number=round_data['round_number'],
                optimization_notes=round_data['optimization_notes'],
                timestamp=datetime.fromisoformat(round_data['timestamp']),
                metadata=round_data['metadata']
            )
            
            # 重建文本信息
            if round_data['text_info']:
                text_data = round_data['text_info']
                round_obj.text_info = TextInfo(
                    content=text_data['content'],
                    source=text_data['source'],
                    timestamp=datetime.fromisoformat(text_data['timestamp']),
                    metadata=text_data['metadata']
                )
            
            # 重建图片信息
            for img_data in round_data['images']:
                image_obj = ImageInfo(
                    path=img_data['path'],
                    description=img_data['description'],
                    source=img_data['source'],
                    timestamp=datetime.fromisoformat(img_data['timestamp']),
                    metadata=img_data['metadata']
                )
                round_obj.images.append(image_obj)
            
            # 重建测试用例
            for case_data in round_data['test_cases']:
                case_obj = TestCasePoint(
                    id=case_data['id'],
                    title=case_data['title'],
                    description=case_data['description'],
                    priority=case_data['priority'],
                    category=case_data['category'],
                    steps=case_data['steps'],
                    expected_result=case_data['expected_result'],
                    actual_result=case_data['actual_result'],
                    status=case_data['status'],
                    timestamp=datetime.fromisoformat(case_data['timestamp']),
                    metadata=case_data['metadata']
                )
                round_obj.test_cases.append(case_obj)
            
            # 重建人工评价
            for eval_data in round_data['human_evaluations']:
                eval_obj = HumanEvaluation(
                    evaluator=eval_data['evaluator'],
                    score=eval_data['score'],
                    comments=eval_data['comments'],
                    suggestions=eval_data['suggestions'],
                    evaluation_criteria=eval_data['evaluation_criteria'],
                    timestamp=datetime.fromisoformat(eval_data['timestamp']),
                    metadata=eval_data['metadata']
                )
                round_obj.human_evaluations.append(eval_obj)
            
            # 重建自动评估
            if round_data['auto_evaluation']:
                auto_data = round_data['auto_evaluation']
                round_obj.auto_evaluation = AutoEvaluation(
                    coverage_score=auto_data['coverage_score'],
                    quality_score=auto_data['quality_score'],
                    completeness_score=auto_data['completeness_score'],
                    overall_score=auto_data['overall_score'],
                    metrics=auto_data['metrics'],
                    timestamp=datetime.fromisoformat(auto_data['timestamp']),
                    evaluation_model=auto_data['evaluation_model'],
                    metadata=auto_data['metadata']
                )
            
            instance.rounds.append(round_obj)
        
        return instance