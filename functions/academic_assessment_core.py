# academic_assessment_core.py
from typing import Dict, Any, List
import json
import sys
import os

# 添加项目路径
current_path = os.path.abspath(__file__)
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.append(parent_path)

from agents.Agent_dbmanager import DatabaseManagerAgent
from src.Clinet_LLM import LLMClient

# -------------------------- 数据获取函数 --------------------------
def get_student_basic_data(db_agent: DatabaseManagerAgent, student_id: str) -> Dict[str, Any]:
    """从DatabaseManagerAgent获取学生基础信息"""
    basic_data = db_agent.query_student_basic(student_id)
    if "error" in basic_data:
        raise ValueError(f"学生{student_id}不存在（DatabaseManagerAgent返回错误）")
    # 标准化字段格式
    return {
        "student_id": student_id,
        "grade": basic_data.get("grade", "未知年级"),
        "learning_preference": basic_data.get("learning_preference", "text"),
        "behavior_portrait": basic_data.get("behavior_portrait", {}),
        "mastered_skills": basic_data.get("behavior_portrait", {}).get("mastered_skills", [])
    }


def get_resource_interaction_data(db_agent: DatabaseManagerAgent, min_error_rate: float = 0.4) -> Dict[str, Any]:
    """从DatabaseManagerAgent获取学生资源交互数据"""
    high_error_resources = db_agent.query_resource_by_error_rate(min_rate=min_error_rate, max_rate=1.0)
    return {
        "high_error_knowledge": [res["knowledge_point"] for res in high_error_resources[:5]],
        "avg_error_rate": round(sum(res["error_rate"] for res in high_error_resources[:5]) / len(high_error_resources[:5]), 2) if high_error_resources else 0.0,
        "total_high_error_resources": len(high_error_resources)
    }


def get_student_dynamic_data(db_agent: DatabaseManagerAgent, student_id: str, subject: str) -> Dict[str, Any]:
    """整合多源动态数据（学业数据+资源交互数据）"""
    # 模拟学业数据（可替换为真实数据库查询）
    exam_data = _mock_exam_data(subject)
    homework_data = _mock_homework_data(subject)
    class_data = _mock_class_data(subject)
    # 从DatabaseManagerAgent获取资源交互数据
    resource_data = get_resource_interaction_data(db_agent)
    
    return {
        "exam": exam_data,
        "homework": homework_data,
        "class_interaction": class_data,
        "resource_interaction": resource_data
    }


def _mock_exam_data(subject: str) -> Dict[str, int]:
    """模拟考试数据（私有辅助函数）"""
    exam_map = {
        "math": {"函数单调性": 58, "导数应用": 65, "几何证明": 72},
        "english": {"语法填空": 62, "阅读理解": 78, "作文": 68},
        "chinese": {"文言文": 70, "现代文阅读": 65, "作文": 75}
    }
    return exam_map.get(subject.lower(), {})


def _mock_homework_data(subject: str) -> Dict[str, int]:
    """模拟作业数据（私有辅助函数）"""
    homework_map = {
        "math": {"函数单调性": 45, "导数应用": 70, "几何证明": 68},
        "english": {"语法填空": 75, "阅读理解": 82, "作文": 70},
        "chinese": {"文言文": 65, "现代文阅读": 70, "作文": 80}
    }
    return homework_map.get(subject.lower(), {})


def _mock_class_data(subject: str) -> Dict[str, int]:
    """模拟课堂互动数据（私有辅助函数）"""
    class_map = {
        "math": {"函数单调性": 80, "导数应用": 60, "几何证明": 75},
        "english": {"语法填空": 70, "阅读理解": 85, "作文": 65},
        "chinese": {"文言文": 75, "现代文阅读": 80, "作文": 70}
    }
    return class_map.get(subject.lower(), {})

# -------------------------- Prompt生成函数 --------------------------
def generate_assessment_prompt(basic_data: Dict[str, Any], dynamic_data: Dict[str, Any], subject: str) -> str:
    """生成学业评估的LLM Prompt"""
    mastery_threshold = 60
    return f"""
    ### 学生学业评估指令 ###
    评估对象：{basic_data['grade']}学生（ID：{basic_data['student_id']}）
    评估学科：{subject}
    基础信息：{json.dumps(basic_data, ensure_ascii=False)}
    多源动态数据：{json.dumps(dynamic_data, ensure_ascii=False)}
    
    ### 输出要求（必须返回JSON格式）###
    {{
        "knowledge_mastery": {{知识点: 掌握度(0-{mastery_threshold}为未掌握)}},
        "ability_level": {{"comprehensive": 1-5, "understand": 1-5, "apply": 1-5}},
        "learning_habits": {{"preference": "visual/auditory/text", "delay_rate": 0-1}},
        "role_goals": {{"student": "目标", "parent": "目标", "teacher": "目标"}},
        "diagnosis": "核心问题结论",
        "error_points": ["未掌握知识点列表"],
        "improvement_suggestions": {{
            "knowledge": "知识点建议",
            "resource": "资源使用建议"
        }}
    }}
    """

# -------------------------- LLM调用函数 --------------------------
def call_llm_for_assessment(llm_client: LLMClient, prompt: str, subject: str) -> Dict[str, Any]:
    """调用LLM生成评估结果"""
    try:
        llm_result = llm_client.generate_edu_response(prompt, subject)
        return json.loads(llm_result) if isinstance(llm_result, str) else llm_result
    except Exception as e:
        print(f"LLM调用失败，使用默认结果：{str(e)}")
        return get_default_assessment_result(subject)


def get_default_assessment_result(subject: str) -> Dict[str, Any]:
    """生成默认评估结果（容错用）"""
    return {
        "knowledge_mastery": {"函数单调性": 51, "导数应用": 67, "几何证明": 70},
        "ability_level": {"comprehensive": 3, "understand": 3, "apply": 2},
        "learning_habits": {"preference": "visual", "delay_rate": 0.35},
        "role_goals": {
            "student": f"巩固{subject}薄弱知识点",
            "parent": f"{subject}成绩提升至80分",
            "teacher": f"重点辅导{subject}高频错误点"
        },
        "diagnosis": f"{subject}函数模块基础薄弱，资源利用率不足",
        "error_points": ["函数单调性"],
        "improvement_suggestions": {
            "knowledge": "优先练习函数单调性基础题型",
            "resource": "使用DatabaseManagerAgent推荐的低错误率资源"
        }
    }

# -------------------------- 结果整合函数 --------------------------
def integrate_assessment_result(llm_result: Dict[str, Any], student_id: str, subject: str, dynamic_data: Dict[str, Any]) -> Dict[str, Any]:
    """整合评估结果为统一字典格式"""
    return {
        "student_id": student_id,
        "subject": subject,
        "knowledge_mastery": llm_result.get("knowledge_mastery", {}),
        "ability_level": llm_result.get("ability_level", {}),
        "learning_habits": llm_result.get("learning_habits", {}),
        "role_goals": llm_result.get("role_goals", {}),
        "multi_source_data": dynamic_data,
        "diagnosis": llm_result.get("diagnosis", "暂无诊断"),
        "error_points": llm_result.get("error_points", []),
        "improvement_suggestions": llm_result.get("improvement_suggestions", {})
    }

# -------------------------- 主流程函数 --------------------------
def run_academic_assessment(db_agent: DatabaseManagerAgent, llm_client: LLMClient, student_id: str, subject: str) -> Dict[str, Any]:
    """学业评估主流程（串联所有函数）"""
    # 1. 获取基础数据
    basic_data = get_student_basic_data(db_agent, student_id)
    # 2. 获取动态数据
    dynamic_data = get_student_dynamic_data(db_agent, student_id, subject)
    # 3. 生成Prompt
    prompt = generate_assessment_prompt(basic_data, dynamic_data, subject)
    # 4. 调用LLM
    llm_result = call_llm_for_assessment(llm_client, prompt, subject)
    # 5. 整合结果
    assessment_result = integrate_assessment_result(llm_result, student_id, subject, dynamic_data)
    
    return assessment_result