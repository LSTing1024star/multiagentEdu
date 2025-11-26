import os
import sys
from typing import Optional, List, Dict, Any

# 确保项目路径正确
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
current_file_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(os.path.dirname(current_file_path))
sys.path.append(parent_dir)

from agents_wrapper import AgentsManager
from utils.utils import validate_input, format_result


def clear_screen() -> None:
    """跨平台清屏函数"""
    os.system('cls' if os.name == 'nt' else 'clear')


def handle_assessment(agent_manager: AgentsManager) -> None:
    """处理学业评估功能"""
    student_id = validate_input("🎒 学生ID：")
    subject = validate_input("📚 科目（如math/语文/英语）：", 
                           validator=lambda x: x in ["math", "语文", "英语"],
                           error_msg="❌ 支持的科目：math/语文/英语")
    
    print("\n⏳ 正在生成学业评估...")
    result = agent_manager.run_assessment(student_id, subject)
    print(format_result(result, "学业评估结果"))


def handle_planning(agent_manager: AgentsManager) -> None:
    """处理学习规划功能"""
    student_id = validate_input("🎒 学生ID：")
    subject = validate_input("📚 科目（如math/语文/英语）：",
                           validator=lambda x: x in ["math", "语文", "英语"],
                           error_msg="❌ 支持的科目：math/语文/英语")
    long_term_goal = validate_input("🎯 长期目标（如：期末数学提分20分）：")
    
    # 可选反馈输入
    execution_feedback: Optional[Dict[str, Any]] = None
    if validate_input("是否有执行反馈？(y/n)：", 
                     validator=lambda x: x in ["y", "n"],
                     error_msg="❌ 请输入y或n") == "y":
        task_id = validate_input("📝 未完成任务ID：")
        completion_rate = validate_input("📊 任务完成率（%）：", int, 
                                        error_msg="❌ 请输入整数")
        feedback_note = validate_input("💡 反馈备注：")
        execution_feedback = {
            "task_id": task_id,
            "completion_rate": completion_rate,
            "feedback_note": feedback_note
        }
    
    print("\n⏳ 正在生成学习规划...")
    result = agent_manager.run_planning(student_id, subject, long_term_goal, execution_feedback)
    print(format_result(result, "个性化学习规划"))


def handle_guidance(agent_manager: AgentsManager) -> None:
    """处理问题引导功能"""
    student_id = validate_input("🎒 学生ID：")
    subject = validate_input("📚 科目（如math/语文/英语）：",
                           validator=lambda x: x in ["math", "语文", "英语"],
                           error_msg="❌ 支持的科目：math/语文/英语")
    question_desc = validate_input("❓ 你的问题（如：为什么函数f(x)=x²在x>0时递增？）：")
    
    # 可选回答输入
    inquiry_answers: Optional[List[str]] = None
    if validate_input("是否已回答追问？(y/n)：",
                     validator=lambda x: x in ["y", "n"],
                     error_msg="❌ 请输入y或n") == "y":
        inquiry_answers = []
        print("💡 请输入你的回答（输入q结束）：")
        while True:
            ans = input("👉 ").strip()
            if ans.lower() == "q":
                break
            if ans:
                inquiry_answers.append(ans)
    
    print("\n⏳ 正在生成引导方案...")
    result = agent_manager.run_guidance(student_id, subject, question_desc, inquiry_answers)
    print(format_result(result, "问题引导结果"))


def handle_coordination(agent_manager: AgentsManager) -> None:
    """处理智能协调功能"""
    student_id = validate_input("🎒 学生ID：")
    subject = validate_input("📚 科目（如math/语文/英语）：",
                           validator=lambda x: x in ["math", "语文", "英语"],
                           error_msg="❌ 支持的科目：math/语文/英语")
    long_term_goal = validate_input("🎯 长期目标：")
    
    # 可选反馈输入
    execution_feedback: Optional[Dict[str, Any]] = None
    if validate_input("是否有执行反馈？(y/n)：",
                     validator=lambda x: x in ["y", "n"],
                     error_msg="❌ 请输入y或n") == "y":
        task_id = validate_input("📝 任务ID：")
        completion_rate = validate_input("📊 完成率（%）：", int,
                                        error_msg="❌ 请输入整数")
        execution_feedback = {
            "task_id": task_id,
            "completion_rate": completion_rate
        }
    
    print("\n⏳ 正在协调冲突并优化方案...")
    result = agent_manager.run_coordination(student_id, subject, long_term_goal, execution_feedback)
    print(format_result(result, "智能协调结果"))


def main() -> None:
    """教育智能助手交互入口"""
    clear_screen()
    print("="*50)
    print("🎓 教育智能助手 - 交互中心")
    print("="*50)

    # 初始化Agent管理器
    try:
        agent_manager = AgentsManager()  # 支持传入自定义data_path，如AgentsManager("自定义路径")
    except RuntimeError as e:
        print(f"\n❌ 系统初始化失败：{e}")
        input("\n按Enter退出...")
        return

    while True:
        print("\n" + "-"*50)
        print("请选择功能（输入编号）：")
        print("1. 学业评估 📊 - 分析薄弱点与能力等级")
        print("2. 学习规划 📅 - 生成个性化学习计划")
        print("3. 问题引导 ❓ - 交互式解题与场景拆解")
        print("4. 智能协调 🔧 - 冲突检测与方案优化")
        print("0. 退出系统 👋")
        print("-"*50)

        # 功能选择
        choice = validate_input("👉 功能编号：", int,
                               validator=lambda x: x in [0,1,2,3,4],
                               error_msg="❌ 无效选项，请输入0-4！")
        
        if choice == 0:
            print("\n👋 感谢使用，再见！")
            break

        # 分发到对应处理函数
        try:
            if choice == 1:
                handle_assessment(agent_manager)
            elif choice == 2:
                handle_planning(agent_manager)
            elif choice == 3:
                handle_guidance(agent_manager)
            elif choice == 4:
                handle_coordination(agent_manager)
        except Exception as e:
            print(f"\n❌ 功能执行失败：{str(e)}")

        input("\n按Enter继续...")
        clear_screen()


if __name__ == "__main__":
    main()