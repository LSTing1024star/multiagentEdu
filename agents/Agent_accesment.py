# academic_assessment_agent.py
import sys
import os
import json

# 添加项目路径
current_path = os.path.abspath(__file__)
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.append(parent_path)

# 导入核心函数和组件
from Agent_dbmanager import DatabaseManagerAgent
from src.Clinet_LLM import LLMClient
from functions.academic_assessment_core import run_academic_assessment

def main():
    """调用学业评估核心函数"""
    # 初始化依赖组件
    db_agent = DatabaseManagerAgent(data_path="/home/lst/data/assistment2009/skill_builder_data.csv")
    llm_client = LLMClient()  # 初始化你的LLM客户端
    
    # 执行评估
    student_id = "S92523"
    subject = "math"
    
    try:
        assessment_result = run_academic_assessment(db_agent, llm_client, student_id, subject)
        
        # 输出结果
        print("===== 学生学业评估报告 =====")
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
        
    except Exception as e:
        print(f"评估执行失败：{str(e)}")

if __name__ == "__main__":
    main()