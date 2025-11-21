import uvicorn
import sys
import os
import json
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict

# ============================== 路径配置 ==============================
current_file_path = os.path.abspath(__file__)
project_root = os.path.dirname(current_file_path)
sys.path.append(project_root)

# ============================== API 应用导入 ==============================
# 从 utils.api 模块中导入 FastAPI 的 app 实例
from utils.api import app

# ============================== 实验数据处理代码 (从 api.py 移动到这里) ==============================

def analyze_assessment_accuracy(teacher_data_path: str, model_data_path: str) -> Dict[str, float]:
    """分析评估智能体准确率（对比教师人工评估）"""
    print(f"[*] 开始分析评估准确率...")
    print(f"[*] 教师数据路径: {teacher_data_path}")
    print(f"[*] 模型数据路径: {model_data_path}")

    # 检查文件是否存在
    if not os.path.exists(teacher_data_path):
        raise FileNotFoundError(f"教师数据文件未找到: {teacher_data_path}")
    if not os.path.exists(model_data_path):
        raise FileNotFoundError(f"模型数据文件未找到: {model_data_path}")

    # 加载数据
    teacher_df = pd.read_csv(teacher_data_path)
    model_df = pd.read_csv(model_data_path)
    
    # 数据预处理
    teacher_df["weak_knowledge"] = teacher_df["weak_knowledge"].apply(eval)
    model_df["knowledge_mastery"] = model_df["knowledge_mastery"].apply(json.loads)
    
    # 合并数据
    merged_df = pd.merge(teacher_df, model_df, on="student_id", how="inner")
    
    # 计算匹配准确率
    def is_match(teacher_weak: list, model_mastery: dict) -> bool:
        model_weak = [k for k, v in model_mastery.items() if v < 60]
        if not teacher_weak:
            return not model_weak
        match_rate = len(set(teacher_weak) & set(model_weak)) / len(teacher_weak)
        return match_rate >= 0.7
    
    merged_df["is_accurate"] = merged_df.apply(
        lambda x: is_match(x["weak_knowledge"], x["knowledge_mastery"]), axis=1
    )
    
    # 统计指标
    accuracy = merged_df["is_accurate"].mean() * 100
    t_stat, p_value = stats.ttest_1samp(merged_df["is_accurate"], 0.5, alternative='greater')
    
    result = {
        "assessment_accuracy": round(accuracy, 2),
        "t_statistic": round(t_stat, 4),
        "p_value": round(p_value, 4)
    }
    
    print("\n[✓] 评估准确率分析完成:")
    print(f"    - 准确率: {result['assessment_accuracy']}%")
    print(f"    - T统计量: {result['t_statistic']}")
    print(f"    - P值: {result['p_value']}")
    
    return result

def analyze_plan_effectiveness(pre_test_path: str, post_test_path: str, group_col: str = "group") -> Dict[str, float]:
    """分析规划效果（成绩提升幅度）"""
    print(f"[*] 开始分析规划效果...")
    print(f"[*] 前测数据路径: {pre_test_path}")
    print(f"[*] 后测数据路径: {post_test_path}")

    if not os.path.exists(pre_test_path):
        raise FileNotFoundError(f"前测数据文件未找到: {pre_test_path}")
    if not os.path.exists(post_test_path):
        raise FileNotFoundError(f"后测数据文件未找到: {post_test_path}")

    # 加载数据
    pre_df = pd.read_csv(pre_test_path)
    post_df = pd.read_csv(post_test_path)
    
    # 合并数据
    effect_df = pd.merge(pre_df, post_df, on=["student_id", group_col], suffixes=("_pre", "_post"))
    
    # 计算提升幅度
    effect_df["score_increase"] = (effect_df["score_post"] - effect_df["score_pre"]) / effect_df["score_pre"] * 100
    
    # 分组统计
    result = {}
    for group in effect_df[group_col].unique():
        group_df = effect_df[effect_df[group_col] == group]
        avg_inc = round(group_df["score_increase"].mean(), 2)
        t_stat, p_value = stats.ttest_rel(group_df["score_pre"], group_df["score_post"])
        
        result[f"{group}_avg_increase"] = avg_inc
        result[f"{group}_p_value"] = round(p_value, 4)

    print("\n[✓] 规划效果分析完成:")
    for group in effect_df[group_col].unique():
        print(f"    - {group} 组平均提升: {result[f'{group}_avg_increase']}%")
        print(f"    - {group} 组 P值: {result[f'{group}_p_value']}")

    return result

# ============================== 服务启动和数据分析入口 ==============================
HOST = "0.0.0.0"
PORT = 8000

if __name__ == "__main__":
    """
    应用程序主入口。
    - 无参数: 启动 API 服务。
    - 带 '--analyze' 参数: 运行数据分析。
    """
    if len(sys.argv) > 1 and sys.argv[1] == '--analyze':
        print("="*50)
        print("          运行实验数据分析")
        print("="*50)
        
        try:
            # 示例：请确保你的数据文件路径正确
            accuracy_result = analyze_assessment_accuracy(
                teacher_data_path=os.path.join(project_root, "data", "teacher_evaluation.csv"),
                model_data_path=os.path.join(project_root, "data", "model_evaluation.csv")
            )
            
            print("\n" + "-"*30)

            effectiveness_result = analyze_plan_effectiveness(
                pre_test_path=os.path.join(project_root, "data", "pre_test_scores.csv"),
                post_test_path=os.path.join(project_root, "data", "post_test_scores.csv")
            )
        except Exception as e:
            print(f"\n[!] 分析过程中发生错误: {e}")
            
        print("\n" + "="*50)

    else:
        print(f"[*] 正在启动 API 服务...")
        print(f"[*] 访问 http://{HOST}:{PORT}/docs 查看 API 文档")
        print(f"[*] 要运行数据分析，请使用命令: python main.py --analyze")
        
        # 启动 FastAPI 服务
        uvicorn.run("main:app", host=HOST, port=PORT, reload=True)