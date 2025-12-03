# src/main.py（修改后）
import os
import sys
from typing import Optional, List, Dict, Any

# 确保项目路径正确
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
current_file_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(os.path.dirname(current_file_path))
sys.path.append(parent_dir)

# 替换原有功能处理逻辑，引入NLU智能体
from agents.Agent_nlu import AgentNLU  # 假设Agent_nlu放在agents目录下
from utils.utils import clear_screen


def main() -> None:
    """教育智能助手交互入口（自然语言版）"""
    clear_screen()
    print("="*50)
    print("🎓 教育智能助手 - 自然语言交互模式")
    print("="*50)

    # 初始化NLU智能体（复用原有数据路径配置）
    try:
        # data_path = os.path.join(parent_dir, "data", "assistment2009", "skill_builder_data.csv")
        data_path="/home/lst/data/assistment2009/skill_builder_data.csv"
        nlu_agent = AgentNLU(data_path=data_path)
    except RuntimeError as e:
        print(f"\n❌ 系统初始化失败：{e}")
        input("\n按Enter退出...")
        return

    # 启动自然语言交互循环
    nlu_agent.run_interactive_loop()


if __name__ == "__main__":
    main()