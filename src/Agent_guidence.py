from Clinet_LLM import LLMClient
from Agent_accesment import AcademicAssessmentAgent
from Agent_dbmanager import DatabaseManagerAgent
from basemodel import *
from typing import List, Dict, Optional, Any

class AcademicGuidanceAgent:
    """学业问题引导智能体（创新点：追问式引导+同类题匹配）"""
    def __init__(self, llm_client: LLMClient, assessment_agent: AcademicAssessmentAgent, db_agent: DatabaseManagerAgent):
        self.llm_client = llm_client
        self.assessment_agent = assessment_agent
        self.db_agent = db_agent
    
    def run(self, student_id: str, subject: str, question_desc: str, inquiry_answers: Optional[List[str]] = None) -> Dict[str, Any]:
        """交互式问题引导（追问→拆解→引导→练习）"""
        # 步骤1：获取学生水平
        assessment = self.assessment_agent.run(student_id, subject)
        # 步骤2：无追问答案→生成追问
        if not inquiry_answers:
            inquiry_questions = self._generate_inquiry(question_desc, assessment)
            return {"inquiry_questions": inquiry_questions, "step_by_step_guide": [], "practice_resources": []}
        # 步骤3：有追问答案→生成引导内容+同类题
        else:
            guide_content = self._generate_guide(question_desc, inquiry_answers, assessment)
            practice_resources = self._match_practice_resources(question_desc, subject)
            return {
                "inquiry_questions": [],
                "step_by_step_guide": guide_content,
                "practice_resources": practice_resources
            }
    
    def _generate_inquiry(self, question_desc: str, assessment: StudentAssessment) -> List[str]:
        """生成追问问题（聚焦根源）"""
        prompt = f"""
        Student's question: {question_desc}
        Student's level: ability={assessment.ability_level['comprehensive']}, weak points={assessment.error_points}
        Generate 3 inquiry questions to clarify the root cause (knowledge gap/method lack/understanding issue):
        Output format: list of 3 questions.
        """
        llm_result = self.llm_client.generate_edu_response(prompt, assessment.subject)
        return llm_result.get("inquiry_questions", [
            f"你是否掌握了{assessment.error_points[0]}的基础定义？",
            "你在解题时是否卡壳在公式应用环节？",
            "你是否因为审题不清导致无法下手？"
        ])
    
    def _generate_guide(self, question_desc: str, inquiry_answers: List[str], assessment: StudentAssessment) -> List[str]:
        """生成分步引导内容（不直接给答案）"""
        prompt = f"""
        Student's question: {question_desc}
        Student's answers to inquiry: {inquiry_answers}
        Student's weak points: {assessment.error_points}
        Generate step-by-step guide (no direct answer, focus on thinking guidance):
        1. Review related basic knowledge
        2. Break down problem-solving ideas
        3. Hint key steps
        Output format: list of guide steps.
        """
        llm_result = self.llm_client.generate_edu_response(prompt, assessment.subject)
        return llm_result.get("step_by_step_guide", [
            f"回顾{assessment.error_points[0]}的核心定义：XXX",
            "解题思路拆解：第一步确定定义域→第二步判断单调性→第三步验证结果",
            "提示：注意题目中隐藏的约束条件（如自变量取值范围）"
        ])
    
    def _match_practice_resources(self, question_desc: str, subject: str) -> List[str]:
        """匹配同类题资源"""
        # 提取问题关键词（简化实现）
        if "函数" in question_desc and "单调性" in question_desc:
            kp = "函数单调性"
        else:
            kp = "通用"
        # 查询同类题资源
        resources = [r["resource_id"] for r in self.db_agent.resource_lib if r["knowledge_point"] == kp]
        return resources[:3]  # 返回Top3
