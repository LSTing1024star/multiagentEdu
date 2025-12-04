import pandas as pd
import numpy as np
from typing import Dict, List, Any

class AssistmentDataProcessor:
    """Assistment2009数据集处理工具类（加载/清洗/转换/结构化）"""
    
    def __init__(self, data_path: str = "skill_builder_data.csv"):
        """初始化数据集处理器
        Args:
            data_path: Assistment2009数据集文件路径（CSV格式）
        """
        self.data_path = data_path
        self.raw_df = self._load_data()
        self.processed_df = self._preprocess_data()

    def _load_data(self) -> pd.DataFrame:
        """加载原始数据集（解决DtypeWarning）"""
        try:
            # 添加low_memory=False解决混合类型警告
            df = pd.read_csv(self.data_path, low_memory=False)
            print(f"成功加载数据集，共{len(df)}条记录")
            return df
        except FileNotFoundError:
            print(f"警告：未找到数据集文件{self.data_path}，使用模拟数据")
            return self._generate_mock_data()

    def _map_error_rate_to_difficulty(self, error_rate: float) -> int:
        """将错误率映射为1-5级难度（错误率越高难度越大）"""
        if error_rate <= 0.2:
            return 1  # 简单
        elif error_rate <= 0.4:
            return 2  # 较简单
        elif error_rate <= 0.6:
            return 3  # 中等
        elif error_rate <= 0.8:
            return 4  # 较难
        else:
            return 5  # 困难

    def _preprocess_data(self) -> pd.DataFrame:
        """数据预处理（修复skill_name类型问题）"""
        df = self.raw_df.copy()

        if "unique_record" in df.columns:
            # 保留第一条出现的记录，删除后续重复项
            df = df.drop_duplicates(subset=["unique_record"], keep="first")
            print(f"已去除{len(self.raw_df) - len(df)}条unique_record重复记录")
        
        # 定义核心字段并筛选存在的列
        core_fields = ["user_id", "skill_name", "problem_id", "correct", "difficulty", "grade"]
        existing_fields = [f for f in core_fields if f in df.columns]
        df = df[existing_fields].drop_duplicates()
        
        # 处理skill_name缺失值和类型（关键修复）
        if "skill_name" in df.columns:
            df["skill_name"] = df["skill_name"].fillna("Unknown").astype(str)
        
        # 补全其他缺失值
        if "difficulty" in df.columns:
            df["difficulty"] = df.groupby("skill_name")["difficulty"].transform(
                lambda x: x.fillna(x.median()) if not x.isna().all() else 3
            )
        if "grade" in df.columns:
            df["grade"] = df["grade"].fillna("Unknown").astype(str)
        else:
            df["grade"]="Unknown"
        
        # 计算错误率和难度等级
        if {"problem_id", "correct"}.issubset(df.columns):
            problem_error = df.groupby("problem_id")["correct"].apply(
                lambda x: 1 - x.mean()
            ).reset_index(name="error_rate")
            df = df.merge(problem_error, on="problem_id", how="left")
            df["difficulty_level"] = df["error_rate"].apply(self._map_error_rate_to_difficulty)
        
        # 标准化字段格式
        if "user_id" in df.columns:
            df["user_id"] = df["user_id"].astype(str)
        if "problem_id" in df.columns:
            df["problem_id"] = df["problem_id"].astype(str)
        
        return df

    def _generate_mock_data(self) -> pd.DataFrame:
        """生成模拟数据"""
        mock_data = {
            "user_id": ["1", "1", "2", "2", "3"],
            "skill_name": ["Addition", "Subtraction", "Multiplication", "Addition", "Geometry"],
            "problem_id": ["P001", "P002", "P003", "P004", "P005"],
            "correct": [1, 0, 1, 1, 0],
            "difficulty": [2, 3, 4, 2, 5],
            "grade": ["Grade 7", "Grade 7", "Grade 8", "Grade 8", "Grade 9"]
        }
        return pd.DataFrame(mock_data)

    def build_student_data(self) -> Dict[str, Dict[str, Any]]:
        """构建学生基础数据"""
        student_data = {}
        student_groups = self.processed_df.groupby("user_id")
        
        for user_id, group in student_groups:
            student_id = f"S{user_id}"
            grade = group["grade"].iloc[0].replace("Grade ", "初") if "Grade" in group["grade"].iloc[0] else group["grade"].iloc[0]
            subject = "math"
            accuracy = group["correct"].mean()
            # 处理skill_name可能为Unknown的情况
            prefer_format = "video" if any(geo in s for s in group["skill_name"].unique() for geo in ["Geometry", "Graph"]) else "text"
            
            student_data[student_id] = {
                "grade": grade,
                "subject": subject,
                "learning_preference": prefer_format,
                "behavior_portrait": {
                    "accuracy": round(accuracy, 2),
                    "total_problems": len(group),
                    "mastered_skills": list(group[group["correct"]==1]["skill_name"].unique())
                }
            }
        return student_data

    def build_resource_data(self) -> List[Dict[str, Any]]:
        """构建学习资源数据（修复skill类型判断）"""
        resource_data = []
        problem_groups = self.processed_df.groupby("problem_id")
        
        for problem_id, group in problem_groups:
            # 安全获取skill_name并确保为字符串
            skill = group["skill_name"].iloc[0]
            skill = str(skill) if pd.notna(skill) else "Unknown"
            
            # 选择难度等级（优先用错误率生成的）
            if "difficulty_level" in group.columns:
                difficulty = group["difficulty_level"].iloc[0]
            else:
                difficulty = int(group["difficulty"].iloc[0]) if "difficulty" in group.columns else 3
            
            avg_correct = group["correct"].mean()
            error_rate = group["error_rate"].iloc[0] if "error_rate" in group.columns else (1 - avg_correct)
            
            # 安全判断资源格式（修复核心错误）
            format_type = "video" if any(geo in skill for geo in ["Geometry", "Graph"]) else "text"
            completion_std = f"{len(group)}道同类题≥{max(50, int(avg_correct*100)-10)}%正确率"
            
            # 获取关联题目（兼容skill_name为Unknown的情况）
            related_problems = list(group["problem_id"].unique()) if "problem_id" in group.columns else []
            
            resource_data.append({
                "resource_id": f"r_{problem_id}",
                "knowledge_point": skill,
                "error_rate": round(error_rate, 2),
                "difficulty_level": difficulty,
                "format": format_type,
                "completion_standard": completion_std,
                "related_problems": related_problems,
                "avg_correct_rate": round(avg_correct, 2)
            })
        return resource_data

    def build_knowledge_graph(self) -> Dict[str, List[str]]:
        """构建知识点关联图谱"""
        kg = {
            "代数基础": ["Addition", "Subtraction", "Multiplication", "Division"],
            "几何基础": ["Geometry", "Graph", "Measurement"],
            "进阶运算": ["Algebra", "Equation", "Fraction"],
            "未知知识点": ["Unknown"]
        }
        all_skills = self.processed_df["skill_name"].unique()
        for skill in all_skills:
            skill_str = str(skill)
            if skill_str not in sum(kg.values(), []):
                kg["其他知识点"].append(skill_str) if "其他知识点" in kg else kg.update({"其他知识点": [skill_str]})
        return kg


def test_real_assistment_data_processor():
    """针对真实Assistment2009数据集的核心功能测试（含输出示例）"""
    print("===== 真实Assistment2009数据集测试开始 =====")
    
    try:
        processor = AssistmentDataProcessor(data_path="/home/lst/data/assistment2009/skill_builder_data.csv")
        print(f"\n1. 真实数据集加载成功：共{len(processor.raw_df)}条原始记录")
    except Exception as e:
        print(f"数据集加载失败：{str(e)}")
        return

    # 验证预处理功能（含输出示例）
    print("\n" + "-"*50)
    print("2. 预处理后数据验证：")
    processed_df = processor.processed_df
    required_fields = ["user_id", "skill_name", "problem_id", "correct", "grade"]
    assert all(field in processed_df.columns for field in required_fields), "预处理后缺失核心字段"
    assert processed_df["skill_name"].dtype == "object", "skill_name应为字符串类型"
    print("✅ 预处理功能验证通过")
    # 输出预处理后数据示例（前3行）
    print("\n预处理后数据示例（前3行）：")
    print(processed_df[["user_id", "skill_name", "problem_id", "error_rate", "difficulty_level"]].head(3).to_string(index=False))

    # 验证学生数据（含输出示例）
    print("\n" + "-"*50)
    print("3. 学生数据功能验证：")
    student_data = processor.build_student_data()
    assert isinstance(student_data, dict) and len(student_data) >= 100, "学生数据异常"
    print(f"✅ 学生数据验证通过（共{len(student_data)}名学生）")
    # 输出某学生的详细信息示例（选第一个学生）
    sample_student_id = next(iter(student_data.keys()))
    print(f"\n学生【{sample_student_id}】详细信息示例：")
    for key, value in student_data[sample_student_id].items():
        if isinstance(value, dict):
            print(f"  - {key}:")
            for sub_k, sub_v in value.items():
                print(f"    · {sub_k}: {sub_v}")
        else:
            print(f"  - {key}: {value}")

    # 验证资源数据（含输出示例）
    print("\n" + "-"*50)
    print("4. 资源数据功能验证：")
    resource_data = processor.build_resource_data()
    assert isinstance(resource_data, list) and len(resource_data) >= 1000, "资源数据异常"
    sample_resource = resource_data[0]
    assert "knowledge_point" in sample_resource and isinstance(sample_resource["knowledge_point"], str), "知识点格式错误"
    assert 1 <= sample_resource["difficulty_level"] <= 5, "难度等级异常"
    print(f"✅ 资源数据验证通过（共{len(resource_data)}个资源）")
    # 输出第一个资源的详细信息示例
    print("\n资源【r_P001】详细信息示例：")
    for key, value in sample_resource.items():
        print(f"  - {key}: {value}")

    # 验证知识图谱（含输出示例）
    print("\n" + "-"*50)
    print("5. 知识图谱功能验证：")
    kg_data = processor.build_knowledge_graph()
    assert isinstance(kg_data, dict) and len(kg_data) >= 3, "知识图谱异常"
    print(f"✅ 知识图谱验证通过（共{len(kg_data)}个分类）")
    # 输出知识图谱部分分类示例
    print("\n知识图谱分类示例：")
    for category, skills in list(kg_data.items())[:3]:  # 展示前3个分类
        print(f"  - {category}:")
        if isinstance(skills, list):
            print(f"    · 知识点：{skills[:5]}...")  # 展示前5个知识点
        else:  # 兼容新结构
            print(f"    · 知识点：{skills['skill_names'][:5]}...")

    # 额外验证：错误率与难度的对应关系示例
    print("\n" + "-"*50)
    print("6. 错误率与难度对应关系验证：")
    # 随机选5个资源展示错误率和难度
    print("部分资源错误率与难度对应示例：")
    for res in resource_data[:5]:
        print(f"  - 资源{res['resource_id']}: 错误率{res['error_rate']} → 难度等级{res['difficulty_level']}")

    print("\n===== 真实Assistment2009数据集所有核心功能测试通过 =====")


if __name__ == "__main__":
    test_real_assistment_data_processor()