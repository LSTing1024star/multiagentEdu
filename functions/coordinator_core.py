from typing import Dict, List, Any
from datetime import datetime, timedelta

# -------------------------- 评估结果整合函数 --------------------------
def integrate_assessment_result(assessment: Dict[str, Any]) -> Dict[str, Any]:
    """整合评估结果为冲突检测所需的结构化数据"""
    return {
        "student_id": assessment.get("student_id"),
        "subject": assessment.get("subject"),
        "knowledge_mastery": assessment.get("knowledge_mastery", {}),
        "ability_level": assessment.get("ability_level", {}),
        "learning_habits": assessment.get("learning_habits", {}),
        "role_goals": assessment.get("role_goals", {}),
        "multi_source_data": assessment.get("multi_source_data", {}),
        "error_points": assessment.get("error_points", []),
        "diagnosis": assessment.get("diagnosis", "")
    }

# -------------------------- 冲突检测工具函数 --------------------------
def get_progress_lag(plan: Dict[str, Any]) -> int:
    """计算进度滞后周数"""
    total_unfinished = sum(
        t["duration_hour"] for week in plan.get("weekly_tasks", [])
        for t in week.get("tasks", []) if t.get("completion_rate", 0) < 100
    )
    weekly_avg = sum(
        t["duration_hour"] for week in plan.get("weekly_tasks", [])[:1]
        for t in week.get("tasks", [])
    ) or 1  # 避免除以0
    return int(total_unfinished // weekly_avg)

def check_resource_ability_mismatch(assessment: Dict[str, Any], plan: Dict[str, Any]) -> bool:
    """检测资源与能力/偏好不匹配"""
    student_ability = assessment["ability_level"].get("comprehensive", 3)
    learning_preference = assessment["learning_habits"].get("preference", "text")
    
    for resource_id in plan.get("resource_mapping", {}).values():
        resource = query_resource_detail(resource_id)
        if (resource["difficulty_level"] > student_ability + 1) or \
           (learning_preference == "visual" and resource["format"] == "text") or \
           (learning_preference == "auditory" and resource["format"] == "video"):
            return True
    return False

def check_role_goal_mismatch(assessment: Dict[str, Any], plan: Dict[str, Any]) -> bool:
    """检测多角色目标冲突"""
    role_goals = assessment.get("role_goals", {})
    if not role_goals:
        return False
    
    student_goal = role_goals.get("student", "").lower()
    parent_goal = role_goals.get("parent", "").lower()
    teacher_goal = role_goals.get("teacher", "").lower()
    
    conflict_scene1 = ("补弱" in student_goal or "基础" in student_goal) and \
                      ("提分" in parent_goal or "拔高" in parent_goal)
    conflict_scene2 = ("短期" in student_goal or "期末" in student_goal) and \
                      ("高考" in teacher_goal or "长期" in teacher_goal)
    return conflict_scene1 or conflict_scene2

def check_data_inconsistency(assessment: Dict[str, Any], plan: Dict[str, Any]) -> bool:  # 新增plan参数
    """检测多源数据矛盾"""
    knowledge_points = assessment["knowledge_mastery"].keys()
    for kp in knowledge_points:
        exam = assessment["multi_source_data"].get("exam", {}).get(kp, 0)
        homework = assessment["multi_source_data"].get("homework", {}).get(kp, 0)
        class_interaction = assessment["multi_source_data"].get("class_interaction", {}).get(kp, 0)
        
        if max(exam, homework, class_interaction) - min(exam, homework, class_interaction) > 30:
            return True
    return False

# -------------------------- 冲突解决策略函数 --------------------------
def resolve_weak_hard_conflict(assessment: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    """解决基础薄弱vs高难度规划冲突"""
    weak_points = assessment["error_points"]
    if not weak_points:
        return plan
    
    for weekly_task in plan.get("weekly_tasks", []):
        new_tasks = []
        for task in weekly_task.get("tasks", []):
            if "难题" in task["content"] or "压轴题" in task["content"]:
                base_resource = query_base_resource(weak_points[0])
                new_task = {
                    "task_id": task["task_id"].replace("hard", "base"),
                    "content": f"学习{weak_points[0]}基础知识点（资源ID：{base_resource}）",
                    "duration_hour": task["duration_hour"],
                    "completion_standard": "5道基础题正确率≥90%"
                }
                new_tasks.append(new_task)
            else:
                new_tasks.append(task)
        weekly_task["tasks"] = new_tasks
    
    if plan.get("monthly_plans"):
        plan["monthly_plans"][0]["goal"] = f"延期1周：{plan['monthly_plans'][0]['goal']}"
    return plan

def resolve_progress_plan_conflict(plan: Dict[str, Any]) -> Dict[str, Any]:
    """解决进度滞后vs规划周期冲突"""
    lag_weeks = get_progress_lag(plan)
    if lag_weeks <= 0:
        return plan
    
    # 提取未完成任务
    unfinished_tasks = [
        t for week in plan.get("weekly_tasks", [])
        for t in week.get("tasks", []) if t.get("completion_rate", 0) < 100
    ]
    
    # 插入补漏周
    for i in range(lag_weeks):
        supplement_week = {
            "week": f"补漏周{i+1}",
            "tasks": [
                {**task, "task_id": f"supplement_{task['task_id']}"}
                for task in unfinished_tasks[i::lag_weeks]
            ]
        }
        plan["weekly_tasks"].insert(i, supplement_week)
    
    # 顺延月度截止日期
    for idx, monthly_plan in enumerate(plan.get("monthly_plans", [])):
        plan["monthly_plans"][idx]["deadline"] = postpone_date(monthly_plan["deadline"], lag_weeks)
    return plan

def resolve_resource_ability_conflict(assessment: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    """解决资源与能力/偏好不匹配冲突"""
    student_ability = assessment["ability_level"].get("comprehensive", 3)
    learning_preference = assessment["learning_habits"].get("preference", "text")
    
    new_resource_mapping = {}
    for task_id, resource_id in plan.get("resource_mapping", {}).items():
        old_resource = query_resource_detail(resource_id)
        new_resource = query_matched_resource(
            old_resource["knowledge_point"],
            student_ability,
            learning_preference
        )
        new_resource_mapping[task_id] = new_resource["resource_id"]
        
        # 更新任务内容
        for week in plan.get("weekly_tasks", []):
            for task in week.get("tasks", []):
                if task["task_id"] == task_id:
                    task["content"] = task["content"].replace(resource_id, new_resource["resource_id"])
                    task["completion_standard"] = new_resource["completion_standard"]
    
    plan["resource_mapping"] = new_resource_mapping
    return plan

def resolve_role_goal_conflict(assessment: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    """解决多角色目标冲突"""
    role_goals = assessment.get("role_goals", {})
    if not role_goals:
        return plan
    
    # 提取目标关键词
    student_keywords = extract_goal_keywords(role_goals.get("student", ""))
    teacher_keywords = extract_goal_keywords(role_goals.get("teacher", ""))
    parent_keywords = extract_goal_keywords(role_goals.get("parent", ""))
    
    # 融合关键词
    common_keywords = set(student_keywords) & set(teacher_keywords) & set(parent_keywords)
    weighted_keywords = (
        [kw for kw in student_keywords if kw not in common_keywords] * 4 +
        [kw for kw in teacher_keywords if kw not in common_keywords] * 3 +
        [kw for kw in parent_keywords if kw not in common_keywords] * 3
    )
    final_keywords = list(common_keywords) + sorted(
        weighted_keywords, key=lambda x: weighted_keywords.count(x), reverse=True
    )
    
    # 更新规划目标
    plan["long_term_goal"] = reconstruct_goal(final_keywords, plan.get("long_term_goal", ""))
    
    # 插入融合任务
    for week in plan.get("weekly_tasks", []):
        week["tasks"].insert(0, {
            "task_id": f"fusion_goal_task_{week['week']}",
            "content": f"融合多角色目标：{', '.join(final_keywords[:3])}（优先完成）",
            "duration_hour": 2,
            "completion_standard": "完成对应资源学习+1道综合题"
        })
    return plan

def resolve_data_conflict(assessment: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    """解决多源数据矛盾冲突"""
    knowledge_points = assessment["knowledge_mastery"].keys()
    conflicting_kps = []
    
    # 识别矛盾知识点（以考试数据为基准）
    for kp in knowledge_points:
        exam = assessment["multi_source_data"].get("exam", {}).get(kp, 0)
        homework = assessment["multi_source_data"].get("homework", {}).get(kp, 0)
        if abs(exam - homework) > 30:
            conflicting_kps.append((kp, exam))
    
    if not conflicting_kps:
        return plan
    
    # 插入补充评估周
    supplement_tasks = [
        {
            "task_id": f"verify_{kp}",
            "content": f"补充评估：{kp}知识点（数据矛盾验证）",
            "duration_hour": 1.5,
            "completion_standard": "8道验证题正确率≥70%（确认真实掌握度）",
            "resource_id": query_verification_resource(kp)
        }
        for kp, _ in conflicting_kps
    ]
    plan["weekly_tasks"].insert(0, {
        "week": "补充评估周",
        "tasks": supplement_tasks
    })
    
    # 临时调整任务难度（修正切片语法错误）
    for week in plan.get("weekly_tasks", [])[1:]:  # 跳过补充评估周
        for task in week.get("tasks", []):
            for kp, true_mastery in conflicting_kps:
                if kp in task["content"]:
                    if true_mastery < 60:
                        task["content"] = task["content"].replace("进阶", "基础").replace("难题", "基础题")
                    else:
                        task["content"] = task["content"].replace("基础", "进阶")
    return plan

# -------------------------- 通用辅助函数 --------------------------
def query_base_resource(knowledge_point: str) -> str:
    """查询基础资源"""
    return f"base_{knowledge_point}_r{hash(knowledge_point)%1000}"

def query_resource_detail(resource_id: str) -> Dict[str, Any]:
    """查询资源详情"""
    return {
        "resource_id": resource_id,
        "knowledge_point": resource_id.split("_")[1] if "_" in resource_id else "default",
        "difficulty_level": int(resource_id[-1]) if resource_id[-1].isdigit() else 3,
        "format": "video" if "video" in resource_id else "text",
        "completion_standard": "完成学习+3道练习题"
    }

def query_matched_resource(knowledge_point: str, target_ability: int, preferred_format: str) -> Dict[str, Any]:
    """查询匹配资源"""
    resource_id = f"matched_{knowledge_point}_{target_ability}_{preferred_format[:3]}"
    return {
        "resource_id": resource_id,
        "knowledge_point": knowledge_point,
        "difficulty_level": target_ability,
        "format": preferred_format,
        "completion_standard": f"完成学习+{target_ability+2}道适配题"
    }

def extract_goal_keywords(goal: str) -> List[str]:
    """提取目标关键词"""
    keywords = []
    if any(word in goal for word in ["补弱", "基础"]):
        keywords.append("补弱")
    if any(word in goal for word in ["提分", "拔高"]):
        keywords.append("提分")
    if any(word in goal for word in ["巩固", "复习"]):
        keywords.append("巩固")
    if "数学" in goal:
        keywords.append("数学")
    if "函数" in goal:
        keywords.append("函数")
    return keywords

def reconstruct_goal(keywords: List[str], original_goal: str) -> str:
    """重构融合目标"""
    unique_keywords = list(dict.fromkeys(keywords))[:5]
    return f"{original_goal}（融合多角色目标：{', '.join(unique_keywords)}）"

def query_verification_resource(knowledge_point: str) -> str:
    """查询验证资源"""
    return f"verify_{knowledge_point}_r{hash(knowledge_point)%500}"

def postpone_date(date_str: str, weeks: int) -> str:
    """日期顺延"""
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return (date + timedelta(weeks=weeks)).strftime("%Y-%m-%d")

# -------------------------- 冲突检测与解决主函数 --------------------------
def detect_and_resolve_conflicts(assessment: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    """自动化冲突检测与解决"""
    # 定义冲突规则映射（修正lambda换行语法）
    conflict_rules = {
        "weak_vs_hard": {
            "detect": lambda a, p: (any(v < 60 for v in a["knowledge_mastery"].values()) and
                                   any("难题" in t["content"] or "压轴题" in t["content"] 
                                       for week in p.get("weekly_tasks", []) 
                                       for t in week.get("tasks", []))),
            "resolve": resolve_weak_hard_conflict
        },
        "progress_vs_plan": {
            "detect": lambda a, p: get_progress_lag(p) > 2,
            "resolve": resolve_progress_plan_conflict
        },
        "resource_vs_ability": {
            "detect": check_resource_ability_mismatch,
            "resolve": resolve_resource_ability_conflict
        },
        "role_goal_conflict": {
            "detect": check_role_goal_mismatch,
            "resolve": resolve_role_goal_conflict
        },
        "data_conflict": {
            "detect": check_data_inconsistency,
            "resolve": resolve_data_conflict
        }
    }
    
    # 检测并解决冲突
    conflict_records = []
    resolved_plan = plan.copy()
    
    for conflict_type, rule in conflict_rules.items():
        if rule["detect"](assessment, resolved_plan):
            conflict_records.append({
                "conflict_type": conflict_type,
                "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "resolved"
            })
            # 执行解决策略
            if conflict_type in ["weak_vs_hard", "resource_vs_ability", "role_goal_conflict", "data_conflict"]:
                resolved_plan = rule["resolve"](assessment, resolved_plan)
            else:
                resolved_plan = rule["resolve"](resolved_plan)
    
    return {
        "resolved_plan": resolved_plan,
        "conflict_records": conflict_records,
        "conflict_count": len(conflict_records)
    }

# -------------------------- 服务输出整合函数 --------------------------
def integrate_service_output(assessment: Dict[str, Any], conflict_result: Dict[str, Any]) -> Dict[str, Any]:
    """整合最终服务输出"""
    return {
        "service_summary": {
            "student_id": assessment["student_id"],
            "subject": assessment["subject"],
            "processing_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "conflict_count": conflict_result["conflict_count"],
            "status": "success" if conflict_result["conflict_count"] >= 0 else "failed"
        },
        "assessment_summary": {
            "key_weak_points": assessment["error_points"],
            "comprehensive_ability": assessment["ability_level"].get("comprehensive", 3),
            "diagnosis": assessment["diagnosis"]
        },
        "resolved_plan": conflict_result["resolved_plan"],
        "conflict_records": conflict_result["conflict_records"],
        "next_steps": [
            "按调整后的规划执行任务",
            "完成补充评估任务（如有）",
            "定期反馈任务完成情况以优化规划"
        ]
    }