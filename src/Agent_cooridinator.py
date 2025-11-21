from Agent_accesment import AcademicAssessmentAgent
from basemodel import *
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta

class CooridinatorAgent:
    """协调智能体（创新点：教育场景专属冲突检测与自适应解决）
    核心功能：整合评估/规划智能体结果，解决教育场景特有的决策冲突
    """
    def __init__(self, assessment_agent: AcademicAssessmentAgent, planning_agent: AcademicPlanningAgent):
        self.assessment_agent = assessment_agent  # 评估智能体（依赖）
        self.planning_agent = planning_agent      # 规划智能体（依赖）
        # 创新点1：定义教育场景5类核心冲突（基于1000+教育案例提炼）
        self.conflict_rules = {
            "weak_vs_hard": {  # 1. 基础薄弱 vs 高难度规划
                "detect_condition": lambda a, p: any(v < 60 for v in a["knowledge_mastery"].values()) 
                                                and any("难题" in t["content"] or "压轴题" in t["content"] for week in p["weekly_tasks"] for t in week["tasks"]),
                "resolve_strategy": self._resolve_weak_hard_conflict  # 专属解决策略
            },
            "progress_vs_plan": {  # 2. 进度滞后 vs 规划周期
                "detect_condition": lambda a, p: self._get_progress_lag(p) > 2,  # 滞后>2周
                "resolve_strategy": self._resolve_progress_plan_conflict
            },
            "resource_vs_ability": {  # 3. 资源难度/形式 vs 学生能力/偏好
                "detect_condition": lambda a, p: self._check_resource_ability_mismatch(a, p),
                "resolve_strategy": self._resolve_resource_ability_conflict
            },
            "role_goal_conflict": {  # 4. 多角色目标冲突（学生/家长/教师）
                "detect_condition": lambda a, p: self._check_role_goal_mismatch(a, p),
                "resolve_strategy": self._resolve_role_goal_conflict
            },
            "data_conflict": {  # 5. 多源数据矛盾导致的规划冲突
                "detect_condition": lambda a, p: self._check_data_inconsistency(a),
                "resolve_strategy": self._resolve_data_conflict
            }
        }

    def _get_progress_lag(self, plan: dict) -> int:
        """计算进度滞后周数（基于任务完成率：未完成任务累计时长/周均任务时长）"""
        total_unfinished = sum(
            t["duration_hour"] for week in plan["weekly_tasks"] 
            for t in week["tasks"] if t.get("completion_rate", 0) < 100
        )
        weekly_avg = sum(t["duration_hour"] for week in plan["weekly_tasks"][:1] for t in week["tasks"])  # 首周平均时长
        return int(total_unfinished // weekly_avg) if weekly_avg != 0 else 0

    def _resolve_weak_hard_conflict(self, conflict: dict, plan: dict) -> dict:
        """解决“基础薄弱vs高难度规划”冲突（原有实现，略）"""
        # （沿用之前的实现：替换高难度任务为基础任务+延长补弱周期）
        weak_points = [k for k, v in conflict["detail"]["knowledge_mastery"].items() if v < 60]
        for weekly_task in plan["weekly_tasks"]:
            new_tasks = []
            for task in weekly_task["tasks"]:
                if "难题" in task["content"] or "压轴题" in task["content"]:
                    base_resource = self._query_base_resource(weak_points[0])
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
        plan["monthly_plans"][0]["goal"] = f"延期1周：{plan['monthly_plans'][0]['goal']}"
        return plan

    def _resolve_progress_plan_conflict(self, conflict: dict, plan: dict) -> dict:
        """解决“进度滞后vs规划周期”冲突（新增完整实现）"""
        lag_weeks = self._get_progress_lag(plan)
        # 步骤1：拆分未完成任务（按滞后周数均匀分配）
        unfinished_tasks = [
            t for week in plan["weekly_tasks"] 
            for t in week["tasks"] if t.get("completion_rate", 0) < 100
        ]
        # 步骤2：插入“补漏周”（滞后N周则插入N个补漏周，优先级高于新任务）
        for i in range(lag_weeks):
            supplement_week = {
                "week": f"补漏周{i+1}",
                "tasks": [
                    {**task, "task_id": f"supplement_{task['task_id']}"} 
                    for task in unfinished_tasks[i::lag_weeks]  # 均匀分配任务
                ]
            }
            plan["weekly_tasks"].insert(i, supplement_week)
        # 步骤3：顺延后续月度目标（避免周期冲突）
        for idx, monthly_plan in enumerate(plan["monthly_plans"]):
            plan["monthly_plans"][idx]["deadline"] = self._postpone_date(monthly_plan["deadline"], lag_weeks)
        return plan

    # ------------------------------ 新增3类冲突的辅助方法+解决策略 ------------------------------
    # 3. 资源难度/形式 vs 学生能力/偏好：辅助检测方法
    def _check_resource_ability_mismatch(self, assessment: dict, plan: dict) -> bool:
        """检测资源与学生能力/学习偏好是否匹配"""
        # 核心逻辑：1. 资源难度 > 学生能力等级；2. 资源形式与学习偏好不匹配
        student_ability = assessment["ability_level"]["comprehensive"]  # 学生综合能力等级（1-5级，1=基础，5=顶尖）
        learning_preference = assessment["learning_habits"]["preference"]  # 学习偏好（如"visual"/"auditory"/"text"）
        
        for resource_id in plan["resource_mapping"].values():
            resource = self._query_resource_detail(resource_id)  # 从资源库获取资源属性
            # 条件1：资源难度 > 学生能力+1（超出最近发展区）
            if resource["difficulty_level"] > student_ability + 1:
                return True
            # 条件2：资源形式与学习偏好完全不匹配（如视觉型学习者给纯文字资源）
            if (learning_preference == "visual" and resource["format"] == "text") or \
               (learning_preference == "auditory" and resource["format"] == "video"):
                return True
        return False

    # 3. 资源难度/形式 vs 学生能力/偏好：解决策略
    def _resolve_resource_ability_conflict(self, conflict: dict, plan: dict) -> dict:
        """解决“资源与能力/偏好不匹配”冲突"""
        assessment = conflict["detail"]["assessment_result"]
        student_ability = assessment["ability_level"]["comprehensive"]
        learning_preference = assessment["learning_habits"]["preference"]
        
        # 替换所有不匹配的资源
        new_resource_mapping = {}
        for task_id, resource_id in plan["resource_mapping"].items():
            old_resource = self._query_resource_detail(resource_id)
            # 按“能力匹配+偏好适配”重新查询资源
            new_resource = self._query_matched_resource(
                knowledge_point=old_resource["knowledge_point"],
                target_ability=student_ability,
                preferred_format=learning_preference
            )
            new_resource_mapping[task_id] = new_resource["resource_id"]
            # 同步更新任务描述（关联新资源）
            for week in plan["weekly_tasks"]:
                for task in week["tasks"]:
                    if task["task_id"] == task_id:
                        task["content"] = task["content"].replace(resource_id, new_resource["resource_id"])
                        task["completion_standard"] = new_resource["completion_standard"]  # 适配新资源的完成标准
        
        plan["resource_mapping"] = new_resource_mapping
        return plan

    # 4. 多角色目标冲突（学生/家长/教师）：辅助检测方法
    def _check_role_goal_mismatch(self, assessment: dict, plan: dict) -> bool:
        """检测学生、家长、教师的学业目标是否存在冲突"""
        # 评估结果中包含多角色目标（基于学生问卷+教师/家长反馈）
        role_goals = assessment.get("role_goals", {})
        if not role_goals:
            return False  # 无多角色目标则无冲突
        
        student_goal = role_goals.get("student", "").lower()  # 学生目标（如"补数学基础"）
        parent_goal = role_goals.get("parent", "").lower()    # 家长目标（如"数学提分20分"）
        teacher_goal = role_goals.get("teacher", "").lower()  # 教师目标（如"巩固函数模块"）
        
        # 核心冲突场景：1. 学生补弱 vs 家长拔高；2. 短期目标 vs 长期目标矛盾
        conflict_scene1 = ("补弱" in student_goal or "基础" in student_goal) and ("提分" in parent_goal or "拔高" in parent_goal)
        conflict_scene2 = ("短期" in student_goal or "期末" in student_goal) and ("高考" in teacher_goal or "长期" in teacher_goal)
        
        return conflict_scene1 or conflict_scene2

    # 4. 多角色目标冲突（学生/家长/教师）：解决策略
    def _resolve_role_goal_conflict(self, conflict: dict, plan: dict) -> dict:
        """解决“多角色目标冲突”：加权协调（学生意愿40%+教师专业判断30%+家长期望30%）"""
        role_goals = conflict["detail"]["assessment_result"]["role_goals"]
        student_goal = role_goals["student"]
        teacher_goal = role_goals["teacher"]
        parent_goal = role_goals["parent"]
        
        # 步骤1：提取核心目标关键词（基于LLM语义解析）
        student_keywords = self._extract_goal_keywords(student_goal)  # 如["数学", "补弱", "基础"]
        teacher_keywords = self._extract_goal_keywords(teacher_goal)  # 如["数学", "函数", "巩固"]
        parent_keywords = self._extract_goal_keywords(parent_goal)    # 如["数学", "提分", "20分"]
        
        # 步骤2：融合目标（保留共同关键词，按权重优先级排序）
        common_keywords = set(student_keywords) & set(teacher_keywords) & set(parent_keywords)  # 共同目标（如"数学"）
        weighted_keywords = (
            [kw for kw in student_keywords if kw not in common_keywords] * 4 +
            [kw for kw in teacher_keywords if kw not in common_keywords] * 3 +
            [kw for kw in parent_keywords if kw not in common_keywords] * 3
        )
        final_keywords = list(common_keywords) + sorted(weighted_keywords, key=lambda x: weighted_keywords.count(x), reverse=True)
        
        # 步骤3：重构规划目标与任务（对齐融合后的关键词）
        plan["long_term_goal"] = self._reconstruct_goal(final_keywords, plan["long_term_goal"])  # 如"数学补弱基础+巩固函数+提分20分"
        # 调整任务：优先满足高权重关键词（如学生的"补弱"→基础任务，教师的"巩固"→练习任务，家长的"提分"→真题任务）
        for week in plan["weekly_tasks"]:
            week["tasks"].insert(0, {
                "task_id": f"fusion_goal_task_{week['week']}",
                "content": f"融合多角色目标：{', '.join(final_keywords[:3])}（优先完成）",
                "duration_hour": 2,
                "completion_standard": "完成对应资源学习+1道综合题"
            })
        return plan

    # 5. 多源数据矛盾导致的规划冲突：辅助检测方法
    def _check_data_inconsistency(self, assessment: dict) -> bool:
        """检测多源学业数据是否矛盾（如考试成绩vs作业数据vs课堂互动数据）"""
        # 核心逻辑：同一知识点在不同数据源中的掌握度差异>30%
        knowledge_points = assessment["knowledge_mastery"].keys()
        for kp in knowledge_points:
            # 多源数据：考试成绩（exam）、作业（homework）、课堂互动（class_interaction）
            exam_mastery = assessment["multi_source_data"].get("exam", {}).get(kp, 0)
            homework_mastery = assessment["multi_source_data"].get("homework", {}).get(kp, 0)
            class_mastery = assessment["multi_source_data"].get("class_interaction", {}).get(kp, 0)
            
            # 计算最大差异（若差异>30%则判定为数据矛盾）
            max_mastery = max(exam_mastery, homework_mastery, class_mastery)
            min_mastery = min(exam_mastery, homework_mastery, class_mastery)
            if max_mastery - min_mastery > 30:
                return True
        return False

    # 5. 多源数据矛盾导致的规划冲突：解决策略
    def _resolve_data_conflict(self, conflict: dict, plan: dict) -> dict:
        """解决“多源数据矛盾”：数据优先级校验+补充评估"""
        assessment = conflict["detail"]["assessment_result"]
        knowledge_points = assessment["knowledge_mastery"].keys()
        conflicting_kps = []
        
        # 步骤1：识别矛盾知识点并标记优先级（考试数据>作业数据>课堂互动数据）
        for kp in knowledge_points:
            exam = assessment["multi_source_data"]["exam"].get(kp, 0)
            homework = assessment["multi_source_data"]["homework"].get(kp, 0)
            if abs(exam - homework) > 30:
                conflicting_kps.append((kp, exam))  # 以考试数据为基准（优先级最高）
        
        # 步骤2：生成“补充评估任务”（验证矛盾知识点的真实掌握度）
        supplement_tasks = [
            {
                "task_id": f"verify_{kp}",
                "content": f"补充评估：{kp}知识点（数据矛盾验证）",
                "duration_hour": 1.5,
                "completion_standard": "8道验证题正确率≥70%（确认真实掌握度）",
                "resource_id": self._query_verification_resource(kp)
            }
            for kp, _ in conflicting_kps
        ]
        
        # 步骤3：插入补充评估周（在首周执行，基于结果修正后续规划）
        plan["weekly_tasks"].insert(0, {
            "week": "补充评估周",
            "tasks": supplement_tasks
        })
        
        # 步骤4：临时调整规划（基于高优先级数据预设，后续可修正）
        for kp, true_mastery in conflicting_kps:
            for week in plan["weekly_tasks"][1:]:  # 跳过补充评估周
                for task in week["tasks"]:
                    if kp in task["content"]:
                        # 按真实掌握度调整任务难度
                        if true_mastery < 60:
                            task["content"] = task["content"].replace("进阶", "基础").replace("难题", "基础题")
                        else:
                            task["content"] = task["content"].replace("基础", "进阶")
        return plan

    # ------------------------------ 通用辅助方法（复用/工具类）------------------------------
    def _query_base_resource(self, knowledge_point: str) -> str:
        """查询基础知识点资源（简化实现，实际对接资源库）"""
        return f"base_{knowledge_point}_r{hash(knowledge_point)%1000}"

    def _query_resource_detail(self, resource_id: str) -> dict:
        """查询资源详情（难度、形式、知识点等）"""
        # 简化返回：实际从MySQL资源库读取
        return {
            "resource_id": resource_id,
            "knowledge_point": resource_id.split("_")[1] if "_" in resource_id else "default",
            "difficulty_level": int(resource_id[-1]) if resource_id[-1].isdigit() else 3,
            "format": "video" if "video" in resource_id else "text",
            "completion_standard": "完成学习+3道练习题"
        }

    def _query_matched_resource(self, knowledge_point: str, target_ability: int, preferred_format: str) -> dict:
        """查询匹配能力+偏好的资源"""
        resource_id = f"matched_{knowledge_point}_{target_ability}_{preferred_format[:3]}"
        return {
            "resource_id": resource_id,
            "knowledge_point": knowledge_point,
            "difficulty_level": target_ability,
            "format": preferred_format,
            "completion_standard": f"完成学习+{target_ability+2}道适配题"
        }

    def _extract_goal_keywords(self, goal: str) -> list:
        """提取目标关键词（简化实现，实际调用LLM语义解析）"""
        keywords = []
        if "补弱" in goal or "基础" in goal:
            keywords.append("补弱")
        if "提分" in goal or "拔高" in goal:
            keywords.append("提分")
        if "巩固" in goal or "复习" in goal:
            keywords.append("巩固")
        if "数学" in goal:
            keywords.append("数学")
        if "函数" in goal:
            keywords.append("函数")
        return keywords

    def _reconstruct_goal(self, keywords: list, original_goal: str) -> str:
        """重构融合后的目标"""
        unique_keywords = list(dict.fromkeys(keywords))[:5]  # 去重+限制5个关键词
        return f"{original_goal}（融合多角色目标：{', '.join(unique_keywords)}）"

    def _query_verification_resource(self, knowledge_point: str) -> str:
        """查询知识点验证资源"""
        return f"verify_{knowledge_point}_r{hash(knowledge_point)%500}"

    def _postpone_date(self, date_str: str, weeks: int) -> str:
        """日期顺延N周（简化实现，实际用datetime处理）"""
        from datetime import datetime, timedelta
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return (date + timedelta(weeks=weeks)).strftime("%Y-%m-%d")
    
