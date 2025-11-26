from typing import Dict, Any, Optional

import sys
import os
import json

# 添加项目路径
current_path = os.path.abspath(__file__)
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.append(parent_path)

from functions.academic_assessment_core import run_academic_assessment
from functions.academic_planning_core import run_academic_planning
from functions.coordinator_core import (
    integrate_assessment_result,
    detect_and_resolve_conflicts,
    integrate_service_output
)
from agents.Agent_dbmanager import DatabaseManagerAgent
from src.Clinet_LLM import LLMClient

class CoordinatorAgent:
    """协调智能体（评估整合+冲突解决+服务输出）"""
    def __init__(self, llm_client: LLMClient, db_agent: DatabaseManagerAgent):
        self.llm_client = llm_client
        self.db_agent = db_agent
    
    def run(
        self,
        student_id: str,
        subject: str,
        long_term_goal: str,
        execution_feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行协调流程"""
        # 1. 获取评估结果并整合
        raw_assessment = run_academic_assessment(self.db_agent, self.llm_client, student_id, subject)
        integrated_assessment = integrate_assessment_result(raw_assessment)
        
        # 2. 获取初始规划结果
        raw_plan = run_academic_planning(
            integrated_assessment,
            long_term_goal,
            subject,
            self.db_agent,
            execution_feedback
        )
        
        # 3. 自动化冲突检测与解决
        conflict_result = detect_and_resolve_conflicts(integrated_assessment, raw_plan)
        
        # 4. 整合最终服务输出
        final_output = integrate_service_output(integrated_assessment, conflict_result)
        
        return final_output




def test_coordinator():
    """测试协调智能体功能"""
    # 初始化依赖组件
    db_agent = DatabaseManagerAgent(data_path="/home/lst/data/assistment2009/skill_builder_data.csv")
    llm_client = LLMClient(model_type="cloud", model_name="llama3-edu")
    
    # 初始化协调智能体
    coordinator = CoordinatorAgent(llm_client=llm_client, db_agent=db_agent)
    
    # 测试参数
    student_id = "S92523"
    subject = "math"
    long_term_goal = "期末数学成绩提升至90分以上"
    execution_feedback = {
        "task_id": "t_base_函数单调性_1",
        "completion_rate": 50,
        "feedback_note": "基础知识点理解不透彻"
    }
    
    try:
        # 执行协调流程
        result = coordinator.run(student_id, subject, long_term_goal, execution_feedback)
        
        # 打印结果（格式化输出）
        print("===== 协调智能体最终输出 =====")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"执行出错：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_coordinator()