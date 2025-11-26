# academic_guidance_agent.py
from typing import Dict, List, Any, Optional

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
from functions.academic_guidance_core import run_academic_guidance

class AcademicGuidanceAgent:
    """学业问题引导智能体（交互式+场景化+迁移化）"""
    def __init__(self, llm_client: LLMClient, db_agent: DatabaseManagerAgent):
        self.llm_client = llm_client
        self.db_agent = db_agent
    
    def run(
        self, 
        student_id: str, 
        subject: str, 
        question_desc: str, 
        inquiry_answers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """交互式引导主入口"""
        # 1. 获取学生评估结果（适配字典格式）
        assessment_result = run_academic_assessment(self.db_agent, self.llm_client, student_id, subject)
        
        # 2. 执行引导流程
        guidance_result = run_academic_guidance(
            llm_client=self.llm_client,
            db_agent=self.db_agent,
            assessment_result=assessment_result,
            question_desc=question_desc,
            inquiry_answers=inquiry_answers
        )
        
        return guidance_result



def simulate_interactive_guidance():
    """模拟交互式学业引导流程"""
    # 初始化组件
    db_agent = DatabaseManagerAgent(data_path="/home/lst/data/assistment2009/skill_builder_data.csv")
    llm_client = LLMClient(model_type="cloud", model_name="llama3-edu")
    guidance_agent = AcademicGuidanceAgent(llm_client=llm_client, db_agent=db_agent)
    
    # 学生提问
    student_id = "S92523"
    subject = "math"
    question_desc = "为什么函数f(x)=x²-4x+3在x>2时是单调递增的？"
    
    print("===== 第一轮：交互式追问 =====")
    # 第一步：生成追问
    first_round = guidance_agent.run(student_id, subject, question_desc)
    print("场景化拆解：")
    for step in first_round["scenario_decomposition"]:
        print(f"  - {step}")
    print("\n追问问题：")
    for idx, q in enumerate(first_round["inquiry_questions"], 1):
        print(f"  {idx}. {q}")
    
    # 学生回答追问（模拟）
    inquiry_answers = [
        "生活中气温在中午后上升可以类比这个函数？",
        "我之前做过一次函数的单调性，这个二次函数不一样",
        "卡在导数计算后的符号判断步骤"
    ]
    print(f"\n===== 第二轮：场景化引导+迁移方案 =====")
    # 第二步：生成引导+资源
    second_round = guidance_agent.run(student_id, subject, question_desc, inquiry_answers)
    print("场景化引导：")
    for idx, guide in enumerate(second_round["guide_content"], 1):
        print(f"  {idx}. {guide}")
    print("\n推荐学习资源：")
    for res in second_round["practice_resources"]:
        print(f"  - [{res['type']}] {res['title']} (ID: {res['resource_id']})")
    print(f"\n迁移化提示：{second_round['transfer_tips']}")

if __name__ == "__main__":
    simulate_interactive_guidance()