# academic_planning_core.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import sys
import os
import json

# 添加项目路径
current_path = os.path.abspath(__file__)
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.append(parent_path)

from agents.Agent_dbmanager import DatabaseManagerAgent

# -------------------------- 日期工具函数 --------------------------
def get_deadline(month: int) -> str:
    """获取月度截止日期（当前日期+month个月）"""
    return (datetime.now() + timedelta(days=30*month)).strftime("%Y-%m-%d")

def postpone_date(date_str: str, weeks: int) -> str:
    """日期顺延N周"""
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return (date + timedelta(weeks=weeks)).strftime("%Y-%m-%d")

# -------------------------- 任务生成函数 --------------------------
def generate_weekly_tasks(monthly_plans: List[Dict[str, Any]], assessment: Dict[str, Any], subject: str, db_agent: DatabaseManagerAgent) -> List[Dict[str, Any]]:
    """生成周度任务（适配字典格式评估结果）"""
    weekly_tasks = []
    knowledge_point = assessment["error_points"][0] if assessment["error_points"] else "基础知识点"
    preference = assessment["learning_habits"].get("preference", "text")
    ability_level = assessment["ability_level"].get("comprehensive", 2)

    for idx, month_plan in enumerate(monthly_plans):
        # 前2周：基础任务（难度=能力等级）
        for week in range(1, 3):
            resource = db_agent.query_resource(
                knowledge_point=knowledge_point,
                difficulty_level=ability_level,
                format=preference
            ) or {"resource_id": "default_r1", "completion_standard": "完成所有练习题"}
            
            weekly_tasks.append({
                "week": f"第{idx*4 + week}周",
                "tasks": [{
                    "task_id": f"t_base_{knowledge_point}_{week}",
                    "content": f"学习{knowledge_point}基础知识点（资源ID：{resource['resource_id']}）",
                    "duration_hour": 3,
                    "completion_standard": resource["completion_standard"],
                    "completion_rate": 100
                }]
            })
        
        # 后2周：进阶任务（难度=能力等级+1）
        for week in range(3, 5):
            resource = db_agent.query_resource(
                knowledge_point=knowledge_point,
                difficulty_level=ability_level + 1,
                format=preference
            ) or {"resource_id": "default_r2", "completion_standard": "完成综合应用题"}
            
            weekly_tasks.append({
                "week": f"第{idx*4 + week}周",
                "tasks": [{
                    "task_id": f"t_adv_{knowledge_point}_{week}",
                    "content": f"学习{knowledge_point}进阶知识点（资源ID：{resource['resource_id']}）",
                    "duration_hour": 4,
                    "completion_standard": resource["completion_standard"],
                    "completion_rate": 100
                }]
            })
    return weekly_tasks

# -------------------------- 初始规划生成函数 --------------------------
def generate_initial_plan(assessment: Dict[str, Any], long_term_goal: str, subject: str, db_agent: DatabaseManagerAgent) -> Dict[str, Any]:
    """生成初始规划（适配字典格式评估结果）"""
    error_point = assessment["error_points"][0] if assessment["error_points"] else "基础模块"
    semester_goal = f"本学期{subject} {error_point}模块掌握度提升至85%"
    
    # 生成月度计划
    monthly_plans = [
        {"month": 1, "goal": f"掌握{error_point}基础知识点", "deadline": get_deadline(1)},
        {"month": 2, "goal": f"进阶训练{error_point}综合题", "deadline": get_deadline(2)}
    ]
    
    # 生成周度任务
    weekly_tasks = generate_weekly_tasks(monthly_plans, assessment, subject, db_agent)
    
    # 构建资源映射
    resource_mapping = {}
    for week_task in weekly_tasks:
        for task in week_task["tasks"]:
            resource_id = task["content"].split("：")[-1].strip("）")
            resource_mapping[task["task_id"]] = resource_id
    
    return {
        "long_term_goal": long_term_goal,
        "semester_goal": semester_goal,
        "monthly_plans": monthly_plans,
        "weekly_tasks": weekly_tasks,
        "resource_mapping": resource_mapping
    }

# -------------------------- 反馈调整函数 --------------------------
def extend_task_cycle(plan: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    """延长任务周期（适配字典格式规划）"""
    for idx, week_task in enumerate(plan["weekly_tasks"]):
        for task in week_task["tasks"]:
            if task["task_id"] == task_id:
                # 在下一周插入延长任务
                new_task = {**task, "task_id": f"{task_id}_extend", "completion_rate": 0}
                if idx + 1 < len(plan["weekly_tasks"]):
                    plan["weekly_tasks"][idx + 1]["tasks"].insert(0, new_task)
                else:
                    plan["weekly_tasks"].append({"week": "延长周", "tasks": [new_task]})
                # 顺延月度截止日期
                for month_plan in plan["monthly_plans"]:
                    month_plan["deadline"] = postpone_date(month_plan["deadline"], 1)
                return plan
    return plan

def advance_task_level(plan: Dict[str, Any], task_id: str, assessment: Dict[str, Any], db_agent: DatabaseManagerAgent) -> Dict[str, Any]:
    """提前进阶（适配字典格式）"""
    knowledge_point = assessment["error_points"][0] if assessment["error_points"] else "基础知识点"
    preference = assessment["learning_habits"].get("preference", "text")
    ability_level = assessment["ability_level"].get("comprehensive", 2) + 2  # 提升2级难度

    # 获取高阶资源
    advanced_resource = db_agent.query_resource(
        knowledge_point=knowledge_point,
        difficulty_level=ability_level,
        format=preference
    ) or {"resource_id": "default_r3", "completion_standard": "完成高阶拓展题"}

    # 更新任务
    for week_task in plan["weekly_tasks"]:
        for task in week_task["tasks"]:
            if task["task_id"] == task_id or task["task_id"].startswith(f"t_adv_{knowledge_point}"):
                task["content"] = task["content"].replace(task["content"].split("（")[0], f"学习{knowledge_point}高阶知识点")
                task["content"] = task["content"].replace(task["content"].split("：")[-1], f"资源ID：{advanced_resource['resource_id']}）")
                task["completion_standard"] = advanced_resource["completion_standard"]
                task["duration_hour"] = 5
    return plan

def adjust_plan_by_feedback(plan: Dict[str, Any], feedback: Dict[str, Any], assessment: Dict[str, Any], db_agent: DatabaseManagerAgent) -> Dict[str, Any]:
    """反馈驱动调整（核心逻辑）"""
    completion_rate = feedback.get("completion_rate", 100)
    task_id = feedback.get("task_id", "")
    
    if completion_rate < 70:
        plan = extend_task_cycle(plan, task_id)
    elif completion_rate > 90:
        plan = advance_task_level(plan, task_id, assessment, db_agent)
    return plan

# -------------------------- 主流程函数 --------------------------
def run_academic_planning(assessment_result: Dict[str, Any], long_term_goal: str, subject: str, db_agent: DatabaseManagerAgent, execution_feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """学业规划主流程"""
    # 生成初始规划
    initial_plan = generate_initial_plan(assessment_result, long_term_goal, subject, db_agent)
    
    # 基于反馈调整
    if execution_feedback:
        optimized_plan = adjust_plan_by_feedback(initial_plan, execution_feedback, assessment_result, db_agent)
    else:
        optimized_plan = initial_plan
    
    return optimized_plan