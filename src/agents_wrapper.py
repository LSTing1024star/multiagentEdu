# src/agents_wrapper.py
import sys
import os
from typing import Dict, Any, Optional, List

# 将项目根目录加入Python路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

# 导入项目模块
from src.Clinet_LLM import LLMClient
from agents.Agent_dbmanager import DatabaseManagerAgent
from agents.Agent_accesment import AcademicAssessmentAgent
from agents.Agent_planner import AcademicPlanningAgent
from agents.Agent_guidence import AcademicGuidanceAgent
from agents.Agent_cooridinator import CoordinatorAgent


class AgentsManager:
    """Agent管理器（统一初始化+调用接口）"""
    
    def __init__(self, data_path: str = "/home/lst/data/assistment2009/skill_builder_data.csv"):
        """
        初始化所有Agent依赖
        :param data_path: 数据集路径（支持外部传入，增强灵活性）
        """
        try:
            # 1. 初始化基础组件
            self.llm_client = LLMClient(model_type="cloud", model_name="llama3-edu")
            self.db_agent = DatabaseManagerAgent(data_path=data_path)
            print("✅ 基础组件（LLM客户端/数据库）初始化成功！")

            # 2. 初始化业务Agent（严格匹配各Agent构造函数参数）
            self.assessment_agent = AcademicAssessmentAgent(
                llm_client=self.llm_client,
                db_agent=self.db_agent
            )
            
            self.planning_agent = AcademicPlanningAgent(
                llm_client=self.llm_client,
                db_agent=self.db_agent
            )
            
            self.guidance_agent = AcademicGuidanceAgent(
                llm_client=self.llm_client,
                db_agent=self.db_agent  # 修复：移除多余的assessment_agent参数
            )
            
            self.coordinator_agent = CoordinatorAgent(
                llm_client=self.llm_client,  # 修复：匹配CoordinatorAgent所需参数
                db_agent=self.db_agent
            )
            
            print("✅ 所有业务Agent初始化成功！")

        except Exception as e:
            raise RuntimeError(f"Agent初始化失败：{str(e)}") from e

    def run_assessment(self, student_id: str, subject: str) -> Dict[str, Any]:
        """调用学业评估Agent"""
        if not all([student_id, subject]):
            raise ValueError("学生ID和科目不能为空")
        return self.assessment_agent.run(student_id, subject)

    def run_planning(self, 
                    student_id: str, 
                    subject: str, 
                    long_term_goal: str, 
                    execution_feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """调用学习规划Agent（统一参数名：execution_feedback）"""
        if not all([student_id, subject, long_term_goal]):
            raise ValueError("学生ID、科目和长期目标不能为空")
        return self.planning_agent.run(student_id, subject, long_term_goal, execution_feedback)

    def run_guidance(self, 
                    student_id: str, 
                    subject: str, 
                    question_desc: str, 
                    inquiry_answers: Optional[List[str]] = None) -> Dict[str, Any]:
        """调用问题引导Agent（统一参数名：question_desc）"""
        if not all([student_id, subject, question_desc]):
            raise ValueError("学生ID、科目和问题描述不能为空")
        return self.guidance_agent.run(student_id, subject, question_desc, inquiry_answers)

    def run_coordination(self, 
                        student_id: str, 
                        subject: str, 
                        long_term_goal: str, 
                        execution_feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """调用协调Agent（统一参数名：execution_feedback）"""
        if not all([student_id, subject, long_term_goal]):
            raise ValueError("学生ID、科目和长期目标不能为空")
        return self.coordinator_agent.run(student_id, subject, long_term_goal, execution_feedback)