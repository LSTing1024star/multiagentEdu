# academic_guidance_core.py
from typing import Dict, List, Any, Optional

import sys
import os
import json

# 添加项目路径
current_path = os.path.abspath(__file__)
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.append(parent_path)

from agents.Agent_dbmanager import DatabaseManagerAgent

# -------------------------- 学生水平适配函数 --------------------------
def get_student_adapted_context(assessment: Dict[str, Any], question_desc: str) -> str:
    """生成适配学生水平的上下文（结合薄弱点+能力等级）"""
    weak_points = assessment.get("error_points", ["基础知识点"])
    ability_level = assessment.get("ability_level", {}).get("comprehensive", 3)
    grade = assessment.get("grade", "初中")
    
    return f"""
    Student Context:
    - Grade: {grade}
    - Ability Level: {ability_level}/5 (1=基础, 5=优秀)
    - Weak Points: {weak_points}
    - Current Question: {question_desc}
    """

# -------------------------- 交互式追问函数 --------------------------
def generate_inquiry_questions(llm_client: Any, question_desc: str, assessment: Dict[str, Any]) -> List[str]:
    """生成场景化追问（聚焦根源+场景关联）"""
    adapted_context = get_student_adapted_context(assessment, question_desc)
    
    prompt = f"""
    {adapted_context}
    Task: Generate 3 interactive inquiry questions to clarify the root cause of the student's confusion.
    Requirements:
    1. Questions must be scenario-based (link to real-life scenarios if possible)
    2. Cover 3 dimensions: knowledge gap / method misunderstanding / scenario application
    3. Simple and clear, suitable for the student's grade
    
    Output format: List of 3 questions (only the questions, no extra text).
    """
    
    try:
        llm_result = llm_client.generate_edu_response(prompt, temperature=0.4)
        # 解析LLM返回的列表（兼容JSON或纯文本）
        if isinstance(llm_result, str):
            # 处理纯文本列表（如"- 问题1\n- 问题2"）
            lines = [line.strip("- ").strip() for line in llm_result.split("\n") if line.strip()]
            return [line for line in lines if line and "?" in line][:3]
        return llm_result[:3]
    except Exception as e:
        # 默认追问（场景化）
        weak_point = assessment.get("error_points", ["函数单调性"])[0]
        return [
            f"你能举一个生活中用到{weak_point}的例子吗？",
            f"你觉得这个问题和你之前做过的{weak_point}题目有什么不同？",
            f"你在哪个具体步骤卡住了（比如审题/公式应用/计算）？"
        ]

# -------------------------- 场景化问题拆解函数 --------------------------
def scenario_based_problem_decomposition(question_desc: str, subject: str) -> List[str]:
    """问题拆解场景化（抽象问题→具体场景）"""
    # 数学场景化映射
    math_scenario_map = {
        "函数单调性": ["气温变化趋势", "商品销量增长", "跑步速度变化"],
        "导数应用": ["汽车加速度计算", "利润最大化", "水位上升速率"],
        "几何证明": ["建筑结构稳定性", "地图比例尺换算", "包装盒设计"]
    }
    
    # 提取知识点关键词
    key_kp = next((kp for kp in math_scenario_map.keys() if kp in question_desc), "基础知识点")
    scenarios = math_scenario_map.get(key_kp, ["日常学习场景"])
    
    # 生成场景化拆解步骤
    return [
        f"Step1：将问题转化为{scenarios[0]}场景理解（比如：{question_desc.replace(key_kp, scenarios[0])}）",
        f"Step2：从场景中提取核心数学关系（如变量/规律/约束条件）",
        f"Step3：回归知识点{key_kp}的解题方法",
        f"Step4：验证场景结论与数学结论的一致性"
    ]

# -------------------------- 迁移化解决方案函数 --------------------------
def generate_transferable_solution(llm_client: Any, question_desc: str, inquiry_answers: List[str], assessment: Dict[str, Any]) -> List[str]:
    """生成迁移化解决方案（当前问题→同类场景）"""
    adapted_context = get_student_adapted_context(assessment, question_desc)
    scenario_decomp = scenario_based_problem_decomposition(question_desc, assessment.get("subject", "math"))
    
    prompt = f"""
    {adapted_context}
    Student's answers to inquiries: {inquiry_answers}
    Scenario decomposition: {scenario_decomp}
    
    Task: Generate step-by-step guidance with transferable solutions.
    Requirements:
    1. First guide the student to solve the current problem (no direct answer)
    2. Then provide 2 transferable scenarios with similar solutions
    3. Highlight the common method across scenarios
    
    Output format: List of guidance steps + transfer tips.
    """
    
    try:
        llm_result = llm_client.generate_edu_response(prompt, temperature=0.3)
        return llm_result if isinstance(llm_result, list) else llm_result.split("\n")
    except Exception as e:
        weak_point = assessment.get("error_points", ["函数单调性"])[0]
        return [
            f"1. 先回忆{weak_point}的核心判定方法（如导数符号法）",
            f"2. 标记题目中的关键条件（如定义域/参数范围）",
            f"3. 尝试用{scenario_decomp[0].split('：')[1]}的场景类比解题",
            f"\n迁移应用：",
            f"- 场景1：分析{scenario_decomp[1].split('：')[1]}时，可用同样的判定方法",
            f"- 场景2：解决{weak_point}的实际问题时，重点关注变量变化规律"
        ]

# -------------------------- 学习资源匹配函数 --------------------------
def match_scenario_based_resources(db_agent: DatabaseManagerAgent, question_desc: str, subject: str) -> List[Dict[str, Any]]:
    """匹配场景化学习资源（知识点+场景双维度）"""
    # 提取知识点关键词
    key_kp = next(
        (kp for kp in ["函数单调性", "导数应用", "几何证明", "语法填空", "阅读理解"] if kp in question_desc),
        "通用知识点"
    )
    
    # 1. 匹配同类知识点资源
    kp_resources = [
        res for res in db_agent.resource_lib 
        if res.get("knowledge_point") == key_kp
    ]
    
    # 2. 匹配场景化资源（格式=video优先）
    scenario_resources = [
        res for res in kp_resources 
        if res.get("format") == "video"  # 场景化资源优先视频
    ]
    
    # 3. 构造资源详情（含场景说明）
    matched_resources = []
    for res in (scenario_resources[:2] or kp_resources[:3]):
        matched_resources.append({
            "resource_id": res.get("resource_id"),
            "title": f"{res.get('knowledge_point')}场景化讲解：{question_desc[:10]}...",
            "type": res.get("format"),
            "scenario": "生活案例分析" if "video" in res.get("format", "") else "基础练习题",
            "link": f"/resources/{res.get('resource_id')}"
        })
    
    return matched_resources

# -------------------------- 主流程函数 --------------------------
def run_academic_guidance(
    llm_client: Any,
    db_agent: DatabaseManagerAgent,
    assessment_result: Dict[str, Any],
    question_desc: str,
    inquiry_answers: Optional[List[str]] = None
) -> Dict[str, Any]:
    """学业引导主流程（交互式+场景化+迁移化）"""
    # 1. 多轮交互式追问（无答案时）
    if not inquiry_answers:
        inquiry_questions = generate_inquiry_questions(llm_client, question_desc, assessment_result)
        return {
            "interactive_step": "inquiry",
            "inquiry_questions": inquiry_questions,
            "scenario_decomposition": scenario_based_problem_decomposition(question_desc, assessment_result.get("subject", "math")),
            "guide_content": [],
            "practice_resources": []
        }
    
    # 2. 场景化引导+迁移化方案（有答案时）
    else:
        guide_content = generate_transferable_solution(llm_client, question_desc, inquiry_answers, assessment_result)
        practice_resources = match_scenario_based_resources(db_agent, question_desc, assessment_result.get("subject", "math"))
        
        return {
            "interactive_step": "solution",
            "inquiry_questions": [],
            "scenario_decomposition": scenario_based_problem_decomposition(question_desc, assessment_result.get("subject", "math")),
            "guide_content": guide_content,
            "practice_resources": practice_resources,
            "transfer_tips": "记住：同类场景的解题方法可迁移，重点关注核心规律！"
        }