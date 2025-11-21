import os
import sys
from typing import List, Optional
from fastapi import FastAPI

# ============================== 路径配置 ==============================
current_file_path = os.path.abspath(__file__)
utils_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(utils_dir)
sys.path.append(project_root)

# ============================== 核心逻辑导入 ==============================
from src.Clinet_LLM import LLMClient
from src.Agent_accesment import AcademicAssessmentAgent
from src.Agent_cooridinator import CoordinatorAgent
from src.Agent_dbmanager import DatabaseManagerAgent
from src.Agent_guidence import AcademicGuidanceAgent
from src.Agent_planner import AcademicPlanningAgent
from schemas import PlanningRequest, PlanningResponse, ExecutionFeedback

# ============================== FastAPI 应用初始化 ==============================
app = FastAPI(title="LLM多智能体协同学业领航框架API")

# ============================== 全局组件初始化 ==============================
global_llm = LLMClient(model_type="local", model_name="llama3-edu")
db_agent = DatabaseManagerAgent()
assessment_agent = AcademicAssessmentAgent(global_llm, db_agent)
planning_agent = AcademicPlanningAgent(global_llm, assessment_agent, db_agent)
coordinator_agent = CoordinatorAgent(assessment_agent, planning_agent, db_agent)
guidance_agent = AcademicGuidanceAgent(global_llm, assessment_agent, db_agent)

# ============================== API 接口实现 ==============================
@app.post("/api/v1/planning", response_model=PlanningResponse, summary="获取个性化学习规划")
async def get_planning(request: PlanningRequest):
    initial_plan = planning_agent.run(
        student_id=request.student_id,
        subject=request.subject,
        long_term_goal=request.long_term_goal,
        execution_feedback=request.execution_feedback
    )
    assessment_result = assessment_agent.run(request.student_id, request.subject)
    conflicts = coordinator_agent.detect_conflict(assessment_result, initial_plan)
    conflict_log = [f"冲突类型：{c['conflict_type']}，详情：{c['detail']['diagnosis'] if 'diagnosis' in c['detail'] else '数据矛盾/目标冲突'}" for c in conflicts]
    
    optimized_plan = initial_plan
    for conflict in conflicts:
        optimized_plan = coordinator_agent.resolve_conflict(conflict, optimized_plan, assessment_result)
    
    recommended_resources = list(optimized_plan.resource_mapping.values())[:5]
    
    return PlanningResponse(
        student_id=request.student_id,
        personalized_plan=optimized_plan,
        conflict_resolution_log=conflict_log,
        recommended_resources=recommended_resources
    )

@app.post("/api/v1/guidance", summary="学业问题交互式引导")
async def get_guidance(student_id: str, subject: str, question_desc: str, inquiry_answers: Optional[List[str]] = None):
    return guidance_agent.run(student_id, subject, question_desc, inquiry_answers)

# ============================== 模块内测试代码 ==============================
if __name__ == "__main__":
    test_student_id = "S2023001"
    test_subject = "math"
    test_goal = "高考数学130+"
    
    print("--- 开始测试 API 核心功能 ---")
    
    try:
        print(f"\n1. 测试评估智能体 (学生ID: {test_student_id}, 科目: {test_subject})")
        assessment = assessment_agent.run(test_student_id, test_subject)
        print("评估结果：", assessment.dict())
    except Exception as e:
        print(f"评估智能体测试失败: {e}")
    
    try:
        print(f"\n2. 测试规划智能体 (目标: {test_goal})")
        feedback = ExecutionFeedback(task_id="t_adv_函数单调性_3", completion_rate=65, score=58)
        plan = planning_agent.run(test_student_id, test_subject, test_goal, feedback)
        print("规划结果：", plan.dict())
    except Exception as e:
        print(f"规划智能体测试失败: {e}")