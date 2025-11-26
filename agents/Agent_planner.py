from Clinet_LLM import LLMClient
from Agent_accesment import AcademicAssessmentAgent
from Agent_dbmanager import DatabaseManagerAgent
from basemodel import *
from typing import List, Optional
from datetime import datetime, timedelta

class AcademicPlanningAgent:
    """学业规划智能体（创新点：反馈驱动动态路径优化）"""
    def __init__(self, llm_client: LLMClient, assessment_agent: AcademicAssessmentAgent, db_agent: DatabaseManagerAgent):
        self.llm_client = llm_client
        self.assessment_agent = assessment_agent
        self.db_agent = db_agent
    
    def run(self, student_id: str, subject: str, long_term_goal: str, execution_feedback: Optional[ExecutionFeedback] = None) -> PersonalizedPlan:
        """生成/优化个性化规划（初始规划+反馈调整）"""
        # 步骤1：获取评估结果
        assessment_result = self.assessment_agent.run(student_id, subject)
        
        # 步骤2：生成初始规划路径
        initial_plan = self._generate_initial_plan(assessment_result, long_term_goal, subject)
        
        # 步骤3：基于反馈动态调整（核心创新）
        if execution_feedback:
            optimized_plan = self._adjust_plan_by_feedback(initial_plan, execution_feedback, assessment_result)
        else:
            optimized_plan = initial_plan
        
        return optimized_plan
    
    def _generate_initial_plan(self, assessment: StudentAssessment, long_term_goal: str, subject: str) -> PersonalizedPlan:
        """生成初始规划（目标分层拆解+资源匹配）"""
        # 步骤1：目标拆解（长期→学期→月度）
        semester_goal = f"本学期{subject} {assessment['error_points'][0]}模块掌握度提升至85%"
        monthly_plans = [
            MonthlyPlan(month=1, goal=f"掌握{assessment['error_points'][0]}基础知识点", deadline=self._get_deadline(1)),
            MonthlyPlan(month=2, goal=f"进阶训练{assessment['error_points'][0]}综合题", deadline=self._get_deadline(2))
        ]
        
        # 步骤2：生成周度任务（关联资源）
        weekly_tasks = self._generate_weekly_tasks(monthly_plans, assessment, subject)
        
        # 步骤3：构建资源映射
        resource_mapping = {task["task_id"]: task["resource_id"] for week in weekly_tasks for task in week["tasks"]}
        
        return PersonalizedPlan(
            long_term_goal=long_term_goal,
            semester_goal=semester_goal,
            monthly_plans=monthly_plans,
            weekly_tasks=weekly_tasks,
            resource_mapping=resource_mapping
        )
    
    def _generate_weekly_tasks(self, monthly_plans: List[MonthlyPlan], assessment: StudentAssessment, subject: str) -> List[WeeklyTask]:
        """生成周度任务（创新点：知识点-资源-能力匹配）"""
        weekly_tasks = []
        for idx, month_plan in enumerate(monthly_plans):
            knowledge_point = assessment["error_points"][0]
            preference = assessment["learning_habits"]["preference"]
            
            # 前2周：基础任务（难度=能力等级）
            for week in range(1, 3):
                resource = self.db_agent.query_resource(
                    knowledge_point=knowledge_point,
                    difficulty_level=assessment["ability_level"]["comprehensive"],
                    format=preference
                )
                weekly_tasks.append(WeeklyTask(
                    week=f"第{idx*4 + week}周",
                    tasks=[{
                        "task_id": f"t_base_{knowledge_point}_{week}",
                        "content": f"学习{knowledge_point}基础知识点（资源ID：{resource['resource_id']}）",
                        "duration_hour": 3,
                        "completion_standard": resource["completion_standard"],
                        "completion_rate": 100  # 初始默认完成率
                    }]
                ))
            
            # 后2周：进阶任务（难度=能力等级+1）
            for week in range(3, 5):
                resource = self.db_agent.query_resource(
                    knowledge_point=knowledge_point,
                    difficulty_level=assessment["ability_level"]["comprehensive"] + 1,
                    format=preference
                )
                weekly_tasks.append(WeeklyTask(
                    week=f"第{idx*4 + week}周",
                    tasks=[{
                        "task_id": f"t_adv_{knowledge_point}_{week}",
                        "content": f"学习{knowledge_point}进阶知识点（资源ID：{resource['resource_id']}）",
                        "duration_hour": 4,
                        "completion_standard": resource["completion_standard"],
                        "completion_rate": 100
                    }]
                ))
        return weekly_tasks
    
    def _adjust_plan_by_feedback(self, plan: PersonalizedPlan, feedback: ExecutionFeedback, assessment: StudentAssessment) -> PersonalizedPlan:
        """反馈驱动调整（核心创新：完成率阈值触发调整）"""
        # 低完成率（<70%）：延长任务周期
        if feedback.completion_rate < 70:
            plan = self._extend_task_cycle(plan, feedback.task_id)
        # 高完成率（>90%）：提前进阶
        elif feedback.completion_rate > 90:
            plan = self._advance_task_level(plan, feedback.task_id, assessment)
        return plan
    
    def _extend_task_cycle(self, plan: PersonalizedPlan, task_id: str) -> PersonalizedPlan:
        """延长任务周期（复制任务到下一周）"""
        for idx, week_task in enumerate(plan.weekly_tasks):
            for task in week_task.tasks:
                if task["task_id"] == task_id:
                    # 在下一周插入相同任务（修改ID）
                    new_task = {**task, "task_id": f"{task_id}_extend", "completion_rate": 0}
                    if idx + 1 < len(plan.weekly_tasks):
                        plan.weekly_tasks[idx + 1].tasks.insert(0, new_task)
                    else:
                        plan.weekly_tasks.append(WeeklyTask(week="延长周", tasks=[new_task]))
                    # 顺延月度截止日期
                    for month_plan in plan.monthly_plans:
                        month_plan.deadline = self._postpone_date(month_plan.deadline, 1)
                    return plan
        return plan
    
    def _advance_task_level(self, plan: PersonalizedPlan, task_id: str, assessment: StudentAssessment) -> PersonalizedPlan:
        """提前进阶（提升任务难度）"""
        knowledge_point = assessment["error_points"][0]
        for week_task in plan.weekly_tasks:
            for task in week_task.tasks:
                if task["task_id"] == task_id or task["task_id"].startswith(f"t_adv_{knowledge_point}"):
                    # 提升难度（能力等级+2）
                    advanced_resource = self.db_agent.query_resource(
                        knowledge_point=knowledge_point,
                        difficulty_level=assessment["ability_level"]["comprehensive"] + 2,
                        format=assessment["learning_habits"]["preference"]
                    )
                    task["content"] = task["content"].replace(task["resource_id"], advanced_resource["resource_id"])
                    task["resource_id"] = advanced_resource["resource_id"]
                    task["completion_standard"] = advanced_resource["completion_standard"]
                    task["content"] = task["content"].replace("基础", "进阶").replace("进阶", "高阶")
        return plan
    
    def _get_deadline(self, month: int) -> str:
        """获取月度截止日期（当前日期+month个月）"""
        return (datetime.now() + timedelta(days=30*month)).strftime("%Y-%m-%d")
    
    def _postpone_date(self, date_str: str, weeks: int) -> str:
        """日期顺延N周"""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return (date + timedelta(weeks=weeks)).strftime("%Y-%m-%d")
