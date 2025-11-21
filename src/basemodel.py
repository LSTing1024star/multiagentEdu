from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class StudentAssessment(BaseModel):
    """评估结果数据模型"""
    student_id: str
    subject: str
    knowledge_mastery: Dict[str, int]  # 知识点掌握度（{知识点: 分数}）
    ability_level: Dict[str, int]      # 能力水平（{理解: 2, 应用: 1}）
    learning_habits: Dict[str, Any]    # 学习习惯（{偏好: 视觉, 拖延率: 0.3}）
    role_goals: Dict[str, str]         # 多角色目标（学生/家长/教师）
    multi_source_data: Dict[str, Dict[str, int]]  # 多源数据（考试/作业/课堂）
    diagnosis: str                     # 诊断结论
    error_points: List[str]            # 薄弱知识点

class WeeklyTask(BaseModel):
    """周度任务模型"""
    week: str
    tasks: List[Dict[str, Any]]  # {task_id, content, duration_hour, completion_standard, completion_rate}

class MonthlyPlan(BaseModel):
    """月度计划模型"""
    month: int
    goal: str
    deadline: str

class PersonalizedPlan(BaseModel):
    """个性化规划模型"""
    long_term_goal: str
    semester_goal: str
    monthly_plans: List[MonthlyPlan]
    weekly_tasks: List[WeeklyTask]
    resource_mapping: Dict[str, str]  # 任务-资源映射（task_id: resource_id）

class ExecutionFeedback(BaseModel):
    """执行反馈模型"""
    task_id: str
    completion_rate: int
    score: Optional[int] = None

class PlanningRequest(BaseModel):
    """规划API请求模型"""
    student_id: str
    subject: str
    long_term_goal: str
    execution_feedback: Optional[ExecutionFeedback] = None

class PlanningResponse(BaseModel):
    """规划API响应模型"""
    student_id: str
    personalized_plan: PersonalizedPlan
    conflict_resolution_log: List[str]
    recommended_resources: List[str]
