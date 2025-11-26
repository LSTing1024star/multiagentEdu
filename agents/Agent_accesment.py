from Agent_dbmanager import DatabaseManagerAgent
from basemodel import *
import json
from typing import List, Dict, Any

import sys
import os
current_file_path = os.path.abspath(__file__)  
a_dir = os.path.dirname(current_file_path)    
parent_dir = os.path.dirname(a_dir)           
sys.path.append(parent_dir)
from Clinet_LLM import LLMClient

class AcademicAssessmentAgent:
    """学业评估智能体（创新点：三维评估+多源数据融合）"""
    def __init__(self, llm_client: LLMClient, db_agent: DatabaseManagerAgent):
        self.llm_client = llm_client
        self.db_agent = db_agent
    
    def run(self, student_id: str, subject: str) -> StudentAssessment:
        """执行评估（全链路：数据获取→Prompt生成→LLM评估→结果解析）"""
        # 步骤1：获取多源数据（基础数据+动态数据）
        basic_data = self.db_agent.query_student_basic(student_id)
        dynamic_data = self._get_dynamic_data(student_id, subject)  # 考试/作业/课堂数据
        
        # 步骤2：生成评估Prompt
        assessment_prompt = self._generate_assessment_prompt(basic_data, dynamic_data, subject)
        
        # 步骤3：调用LLM生成评估结果
        llm_result = self.llm_client.generate_edu_response(assessment_prompt, subject)
        
        # 步骤4：结构化解析+补全
        structured_result = self._parse_assessment_result(llm_result, student_id, subject)
        
        return structured_result
    
    def _get_dynamic_data(self, student_id: str, subject: str) -> Dict[str, Any]:
        """获取动态数据（模拟多源数据融合）"""
        return {
            "exam": {"函数单调性": 58, "导数应用": 65},
            "homework": {"函数单调性": 25, "导数应用": 70},
            "class_interaction": {"函数单调性": 80, "导数应用": 60}
        }
    
    def _generate_assessment_prompt(self, basic_data: Dict[str, Any], dynamic_data: Dict[str, Any], subject: str) -> str:
        """生成评估Prompt（融合多源数据）"""
        return f"""
        Evaluate the {subject} academic level of the student (ID: {basic_data.get('grade')} student) based on the following data:
        1. Basic info: {basic_data}
        2. Dynamic data (exam/homework/class): {dynamic_data}
        Output requirements:
        - knowledge_mastery: key=knowledge point, value=mastery score (0-100)
        - ability_level: comprehensive=1-5, understand=1-5, apply=1-5
        - learning_habits: preference=visual/auditory/text, delay_rate=0-1
        - role_goals: student=goal, parent=goal, teacher=goal
        - multi_source_data: same as input dynamic data
        - diagnosis: 1 sentence conclusion
        - error_points: list of weak knowledge points (mastery < 60)
        """
    
    def _parse_assessment_result(self, llm_result: Dict[str, Any], student_id: str, subject: str) -> StudentAssessment:
        """解析LLM评估结果（补全缺失字段）"""
        # 模拟LLM结果补全（实际为真实解析逻辑）
        default_result = {
            "knowledge_mastery": llm_result.get("knowledge_mastery", {"函数单调性": 58, "导数应用": 65}),
            "ability_level": llm_result.get("ability_level", {"comprehensive": 2, "understand": 2, "apply": 1}),
            "learning_habits": llm_result.get("learning_habits", {"preference": "visual", "delay_rate": 0.3}),
            "role_goals": llm_result.get("role_goals", {
                "student": "补数学函数基础",
                "parent": "数学提分20分",
                "teacher": "巩固函数模块"
            }),
            "multi_source_data": llm_result.get("multi_source_data", self._get_dynamic_data(student_id, subject)),
            "diagnosis": llm_result.get("diagnosis", "函数单调性基础薄弱，多源数据存在矛盾"),
            "error_points": llm_result.get("error_points", ["函数单调性"])
        }
        return StudentAssessment(
            student_id=student_id,
            subject=subject,
            **default_result
        )


if __name__=="__main__":
    pass