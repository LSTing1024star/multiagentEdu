# Agent_accesment.py
import sys
import os
import json

# 添加项目路径
current_path = os.path.abspath(__file__)
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.append(parent_path)

# 导入核心函数和组件
from agents.Agent_dbmanager import DatabaseManagerAgent
from src.Clinet_LLM import LLMClient
from functions.academic_assessment_core import run_academic_assessment

class AcademicAssessmentAgent:
    """学业评估Agent类（封装评估逻辑）"""
    
    def __init__(self, llm_client: LLMClient, db_agent: DatabaseManagerAgent = None):
        """
        初始化评估Agent
        :param llm_client: LLM客户端实例
        :param db_agent: 数据库Agent实例（可选，默认自动初始化）
        """
        self.llm_client = llm_client
        self.db_agent = db_agent or DatabaseManagerAgent(data_path="/home/lst/data/assistment2009/skill_builder_data.csv")

    def run(self, student_id: str, subject: str) -> dict:
        """
        执行学业评估
        :param student_id: 学生ID
        :param subject: 评估学科（如math/语文）
        :return: 整合后的评估结果字典
        """
        try:
            # 调用核心评估函数
            assessment_result = run_academic_assessment(
                db_agent=self.db_agent,
                llm_client=self.llm_client,
                student_id=student_id,
                subject=subject
            )
            return assessment_result
        
        except Exception as e:
            raise RuntimeError(f"学业评估执行失败：{str(e)}")

    def print_report(self, assessment_result: dict) -> None:
        """格式化打印评估报告（辅助方法）"""
        print("\n===== 学生学业评估报告 =====")
        print(f"学生ID：{assessment_result['student_id']}")
        print(f"评估学科：{assessment_result['subject']}")
        print("\n1. 知识点掌握度：")
        print(json.dumps(assessment_result['knowledge_mastery'], ensure_ascii=False, indent=2))
        print("\n2. 能力等级：")
        print(json.dumps(assessment_result['ability_level'], ensure_ascii=False, indent=2))
        print("\n3. 学习习惯：")
        print(json.dumps(assessment_result['learning_habits'], ensure_ascii=False, indent=2))
        print("\n4. 诊断结论：")
        print(assessment_result['diagnosis'])
        print("\n5. 薄弱知识点：")
        print(assessment_result['error_points'])
        print("\n6. 改进建议：")
        print(json.dumps(assessment_result['improvement_suggestions'], ensure_ascii=False, indent=2))


# 测试代码（保持原有功能）
if __name__ == "__main__":
    # 初始化依赖
    db_agent = DatabaseManagerAgent(data_path="/home/lst/data/assistment2009/skill_builder_data.csv")
    llm_client = LLMClient()  # 初始化LLM客户端
    
    # 创建Agent实例
    assessment_agent = AcademicAssessmentAgent(llm_client=llm_client, db_agent=db_agent)
    
    # 执行评估
    try:
        result = assessment_agent.run(student_id="S92523", subject="math")
        assessment_agent.print_report(result)
    except RuntimeError as e:
        print(e)