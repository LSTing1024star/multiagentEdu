import json
from typing import Dict, Any, Callable, Optional

def validate_input(
    prompt: str, 
    input_type: type = str, 
    non_empty: bool = True,
    validator: Optional[Callable[[Any], bool]] = None,  # 新增：验证函数
    error_msg: str = "❌ 输入不符合要求，请重新输入！"  # 新增：验证失败提示
) -> Any:
    """验证用户输入（类型+非空+自定义验证）"""
    while True:
        user_input = input(prompt).strip()
        # 非空校验
        if non_empty and not user_input:
            print("❌ 输入不能为空，请重新输入！")
            continue
        # 类型转换
        try:
            converted_input = input_type(user_input)
        except ValueError:
            print(f"❌ 输入类型错误，请输入{input_type.__name__}类型！")
            continue
        # 自定义验证（如果提供了验证函数）
        if validator is not None and not validator(converted_input):
            print(error_msg)
            continue
        # 所有验证通过
        return converted_input

def format_result(result: Dict[str, Any], title: str = "结果") -> str:
    # （保持原函数不变）
    formatted = f"\n===== {title} =====\n"
    if "service_summary" in result:  # 协调Agent结果
        summary = result["service_summary"]
        formatted += f"学生ID：{summary['student_id']}\n"
        formatted += f"科目：{summary['subject']}\n"
        formatted += f"冲突数量：{summary['conflict_count']}\n"
        formatted += f"处理状态：{summary['status']}\n\n"
        
        assessment = result["assessment_summary"]
        formatted += "📊 评估摘要：\n"
        formatted += f"- 薄弱点：{', '.join(assessment['key_weak_points'])}\n"
        formatted += f"- 综合能力等级：{assessment['comprehensive_ability']}/5\n"
        formatted += f"- 诊断：{assessment['diagnosis']}\n\n"
        
        if result["conflict_records"]:
            formatted += "🔧 冲突处理记录：\n"
            for conflict in result["conflict_records"]:
                formatted += f"- {conflict['conflict_type']}（{conflict['detected_at']}）：已解决\n"
    elif "inquiry_questions" in result:  # 问题引导Agent结果
        formatted += "❓ 交互式追问：\n"
        for idx, q in enumerate(result["inquiry_questions"], 1):
            formatted += f"{idx}. {q}\n"
        if result["step_by_step_guide"]:
            formatted += "\n📝 场景化引导：\n"
            for idx, step in enumerate(result["step_by_step_guide"], 1):
                formatted += f"{idx}. {step}\n"
        if result["practice_resources"]:
            formatted += "\n📚 推荐资源：\n"
            for res in result["practice_resources"]:
                formatted += f"- [{res['type']}] {res['title']}（ID：{res['resource_id']}）\n"
    elif "weekly_tasks" in result:  # 规划Agent结果
        formatted += "📅 个性化学习规划：\n"
        formatted += f"长期目标：{result['long_term_goal']}\n"
        formatted += "周任务安排：\n"
        for week in result["weekly_tasks"][:3]:  # 只显示前3周
            formatted += f"- {week['week']}：\n"
            for task in week["tasks"]:
                formatted += f"  ✅ {task['content']}（时长：{task['duration_hour']}h）\n"
    else:  # 评估Agent结果
        formatted += "📊 学业评估结果：\n"
        formatted += f"薄弱知识点：{', '.join(result.get('error_points', []))}\n"
        formatted += f"综合能力等级：{result.get('ability_level', {}).get('comprehensive', 0)}/5\n"
        formatted += f"诊断结论：{result.get('diagnosis', '无')}\n"
    return formatted