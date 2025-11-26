# academic_planning_agent.py
from typing import Dict, Any, Optional

import sys
import os
import json

# 添加项目路径
current_path = os.path.abspath(__file__)
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.append(parent_path)


from Agent_dbmanager import DatabaseManagerAgent
from src.Clinet_LLM import LLMClient
from functions.academic_assessment_core import run_academic_assessment
from functions.academic_planning_core import run_academic_planning

class AcademicPlanningAgent:
    """学业规划智能体（调用核心函数实现功能）"""
    def __init__(self, llm_client: LLMClient, db_agent: DatabaseManagerAgent):
        self.llm_client = llm_client
        self.db_agent = db_agent
    
    def run(self, student_id: str, subject: str, long_term_goal: str, execution_feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行学业规划（集成评估+规划）"""
        # 1. 先调用评估智能体获取评估结果
        assessment_result = run_academic_assessment(self.db_agent, self.llm_client, student_id, subject)
        
        # 2. 执行规划生成/优化
        plan_result = run_academic_planning(assessment_result, long_term_goal, subject, self.db_agent, execution_feedback)
        
        return plan_result



def main():
    """测试学业规划智能体"""
    # 初始化依赖
    db_agent = DatabaseManagerAgent(data_path="/home/lst/data/assistment2009/skill_builder_data.csv")
    llm_client = LLMClient(model_type="cloud", model_name=None)
    
    # 初始化规划Agent
    planning_agent = AcademicPlanningAgent(llm_client=llm_client, db_agent=db_agent)
    
    # 1. 生成初始规划
    student_id = "S92523"
    subject = "math"
    long_term_goal = "期末数学成绩提升至90分以上"
    
    print("===== 初始学业规划 =====")
    initial_plan = planning_agent.run(student_id, subject, long_term_goal)
    print(json.dumps(initial_plan, ensure_ascii=False, indent=2))
    
    # 2. 模拟反馈后优化规划
    print("\n===== 反馈后优化规划 =====")
    execution_feedback = {
        "task_id": "t_base_函数单调性_1",
        "completion_rate": 65,  # 低完成率触发延长周期
        "feedback_note": "基础知识点理解不透彻，需要更多练习"
    }
    optimized_plan = planning_agent.run(student_id, subject, long_term_goal, execution_feedback)
    print(json.dumps(optimized_plan, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()