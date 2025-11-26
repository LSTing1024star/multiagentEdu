from typing import Dict, Any, Optional, List  # 补全缺失的List导入
from termcolor import colored

import sys
import os
current_file_path = os.path.abspath(__file__)  
a_dir = os.path.dirname(current_file_path)    
parent_dir = os.path.dirname(a_dir)           
sys.path.append(parent_dir)
from functions.dataprocessor import AssistmentDataProcessor  # 导入数据处理器类

class DatabaseManagerAgent:
    """数据库管理智能体（集成Assistment2009数据处理）"""
    
    def __init__(self, data_path: str = "skill_builder_data.csv"):
        """初始化智能体并加载数据
        Args:
            data_path: Assistment2009数据集路径
        """
        # 初始化数据处理器
        self.data_processor = AssistmentDataProcessor(data_path)
        # 加载结构化数据
        self.student_basic_data = self.data_processor.build_student_data()
        self.resource_lib = self.data_processor.build_resource_data()
        self.knowledge_graph = self.data_processor.build_knowledge_graph()

    def query_student_basic(self, student_id: str) -> Dict[str, Any]:
        """查询学生基础信息（含画像）"""
        return self.student_basic_data.get(student_id, {"error": "学生ID不存在"})

    def query_resource(self, **kwargs) -> Optional[Dict[str, Any]]:
        """多条件查询资源（适配新字段：error_rate/difficulty_level）
        Args:
            kwargs: 支持knowledge_point/difficulty_level/format/error_rate等条件
        """
        matched_resources = []
        for resource in self.resource_lib:
            match = True
            # 基础条件匹配
            if "knowledge_point" in kwargs and resource["knowledge_point"] != kwargs["knowledge_point"]:
                match = False
            if "difficulty_level" in kwargs and resource["difficulty_level"] != kwargs["difficulty_level"]:
                match = False
            if "format" in kwargs and resource["format"] != kwargs["format"]:
                match = False
            # 新增错误率范围匹配（可选）
            if "min_error_rate" in kwargs and resource["error_rate"] < kwargs["min_error_rate"]:
                match = False
            if "max_error_rate" in kwargs and resource["error_rate"] > kwargs["max_error_rate"]:
                match = False
            
            if match:
                matched_resources.append(resource)
        
        # 返回第一个匹配项，或None（若需返回所有可改为return matched_resources）
        return matched_resources[0] if matched_resources else None

    def query_knowledge_relation(self, skill: str) -> List[str]:
        """查询知识点关联关系（适配新的知识图谱结构：含skill_names）"""
        for parent_category, category_info in self.knowledge_graph.items():
            # 兼容新旧知识图谱结构（若processor返回旧结构则降级处理）
            if isinstance(category_info, list):
                skill_list = category_info
            else:
                skill_list = category_info.get("skill_names", [])
            
            if skill in skill_list:
                # 返回父分类 + 同分类下其他知识点
                siblings = [s for s in skill_list if s != skill]
                return [f"父分类：{parent_category}"] + siblings
        return ["无关联知识点"]

    def query_resource_by_error_rate(self, min_rate: float, max_rate: float) -> List[Dict[str, Any]]:
        """新增：按错误率范围查询资源"""
        return [
            res for res in self.resource_lib
            if min_rate <= res["error_rate"] <= max_rate
        ]

    def desensitize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """学生数据脱敏处理（适配新增的行为画像字段）"""
        if "phone" in raw_data:
            raw_data["phone"] = raw_data["phone"][:3] + "****" + raw_data["phone"][7:] if len(raw_data["phone"]) >= 11 else raw_data["phone"]
        if "name" in raw_data:
            raw_data["name"] = raw_data["name"][0] + "同学" if raw_data["name"] else "匿名同学"
        # 隐藏行为画像中的敏感细节（适配新增的hint_dependency/avg_attempts）
        if "behavior_portrait" in raw_data:
            for sensitive_key in ["mastered_skills", "hint_dependency"]:
                raw_data["behavior_portrait"].pop(sensitive_key, None)
        return raw_data

    def update_student_progress(self, student_id: str, progress_data: Dict[str, Any]):
        """更新学生学习进度（增强容错）"""
        if student_id in self.student_basic_data:
            # 若已存在进度则合并，否则新增
            current_progress = self.student_basic_data[student_id].get("learning_progress", {})
            current_progress.update(progress_data)
            self.student_basic_data[student_id]["learning_progress"] = current_progress
            print(f"✅ 学生{student_id}进度已更新：{current_progress}")
        else:
            print(f"❌ 学生{student_id}不存在")

    def get_resource_statistics(self) -> Dict[str, Any]:
        """新增：获取资源统计信息（适配新字段）"""
        if not self.resource_lib:
            return {"error": "无资源数据"}
        
        total_resources = len(self.resource_lib)
        difficulty_dist = {}
        format_dist = {}
        avg_error_rate = sum(res["error_rate"] for res in self.resource_lib) / total_resources

        for res in self.resource_lib:
            # 统计难度分布
            diff = res["difficulty_level"]
            difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1
            # 统计格式分布
            fmt = res["format"]
            format_dist[fmt] = format_dist.get(fmt, 0) + 1

        return {
            "总资源数": total_resources,
            "平均错误率": round(avg_error_rate, 2),
            "难度分布": difficulty_dist,
            "格式分布": format_dist
        }



def test_database_manager_agent():
    """DatabaseManagerAgent核心功能测试（含输出样例）"""
    print("===== DatabaseManagerAgent功能测试开始 =====")
    
    # 1. 初始化Agent
    print("\n" + "-"*50)
    print("1. 初始化Agent：")
    try:
        agent = DatabaseManagerAgent(data_path="/home/lst/data/assistment2009/skill_builder_data.csv")
        print("✅ Agent初始化成功")
        print(f"   - 加载学生数：{len(agent.student_basic_data)}")
        print(f"   - 加载资源数：{len(agent.resource_lib)}")
        print(f"   - 知识图谱分类数：{len(agent.knowledge_graph)}")
    except Exception as e:
        print(f"❌ Agent初始化失败：{str(e)}")
        return

    # 2. 测试学生信息查询
    print("\n" + "-"*50)
    print("2. 学生信息查询功能：")
    # 查询存在的学生
    existing_student = agent.query_student_basic("S92523")
    print("   存在的学生（S92523）信息：")
    for key, value in existing_student.items():
        if isinstance(value, dict):
            print(f"   - {key}:")
            for sub_k, sub_v in value.items():
                print(f"     · {sub_k}: {sub_v}")
        else:
            print(f"   - {key}: {value}")
    # 查询不存在的学生
    non_exist_student = agent.query_student_basic("S9999")
    print(f"   不存在的学生（S9999）信息：{non_exist_student}")

    # 3. 测试资源查询
    print("\n" + "-"*50)
    print("3. 资源查询功能：")
    # 按知识点+难度查询
    geo_resource = agent.query_resource(knowledge_point="Geometry", difficulty_level=5)
    if geo_resource:
        print("   高难度几何资源（Geometry+难度5）：")
        for key in ["resource_id", "knowledge_point", "error_rate", "difficulty_level", "format"]:
            print(f"   - {key}: {geo_resource[key]}")
    else:
        print("目前无相关资源")
    # 按格式查询
    video_resource = agent.query_resource(format="video")
    if video_resource:
        print(f"   视频格式资源示例：{video_resource['resource_id']}（{video_resource['knowledge_point']}）")

    # 4. 测试知识点关联查询
    print("\n" + "-"*50)
    print("4. 知识点关联查询功能：")
    geometry_relation = agent.query_knowledge_relation("Geometry")
    print(f"   Geometry知识点关联：{geometry_relation}")
    addition_relation = agent.query_knowledge_relation("Addition")
    print(f"   Addition知识点关联：{addition_relation}")
    unknown_relation = agent.query_knowledge_relation("UnknownSkill")
    print(f"   未知知识点关联：{unknown_relation}")

    # 5. 测试按错误率查询资源
    print("\n" + "-"*50)
    print("5. 按错误率查询资源功能：")
    mid_error_resources = agent.query_resource_by_error_rate(0.3, 0.5)
    print(f"   错误率0.3~0.5的资源数：{len(mid_error_resources)}")
    print("   前3个资源示例：")
    for res in mid_error_resources[:3]:
        print(f"   - {res['resource_id']}: 错误率{res['error_rate']}（{res['knowledge_point']}）")

    # 6. 测试数据脱敏
    print("\n" + "-"*50)
    print("6. 数据脱敏功能：")
    raw_data = {
        "name": "张三",
        "phone": "13812345678",
        "grade": "初一",
        "behavior_portrait": {
            "accuracy": 0.85,
            "mastered_skills": ["Addition", "Subtraction"],
            "hint_dependency": 0.2
        }
    }
    print("   原始数据：")
    print(f"     {raw_data}")
    desensitized_data = agent.desensitize_data(raw_data)
    print("   脱敏后数据：")
    print(f"     {desensitized_data}")

    # 7. 测试学生进度更新
    print("\n" + "-"*50)
    print("7. 学生进度更新功能：")
    agent.update_student_progress("S92523", {"completed_resources": ["r_1", "r_5"], "current_skill": "Geometry"})
    agent.update_student_progress("S92523", {"score": 90})  # 增量更新
    agent.update_student_progress("S9999", {"completed_resources": ["r_10"]})  # 不存在的学生

    # 8. 测试资源统计
    print("\n" + "-"*50)
    print("8. 资源统计功能：")
    resource_stats = agent.get_resource_statistics()
    print("   资源统计信息：")
    for key, value in resource_stats.items():
        print(f"   - {key}: {value}")

    print("\n===== DatabaseManagerAgent所有核心功能测试完成 =====")


if __name__ == "__main__":
    test_database_manager_agent()