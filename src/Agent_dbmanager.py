from basemodel import *
from typing import Dict, Any

class DatabaseManagerAgent:
    """数据库管理智能体（数据同步/查询/缓存/脱敏）"""
    def __init__(self):
        # 模拟资源库（实际为MySQL+Redis）
        self.resource_lib = [
            {"resource_id": "r_base_func", "knowledge_point": "函数单调性", "difficulty_level": 2, "format": "video", "completion_standard": "5道基础题≥90%"},
            {"resource_id": "r_adv_func", "knowledge_point": "函数单调性", "difficulty_level": 4, "format": "text", "completion_standard": "3道压轴题≥80%"},
            {"resource_id": "r_verify_func", "knowledge_point": "函数单调性", "difficulty_level": 3, "format": "video", "completion_standard": "8道验证题≥70%"}
        ]
        # 模拟学生基础数据（实际从教务系统同步）
        self.student_basic_data = {
            "S2023001": {"grade": "高一", "subject": "math", "learning_preference": "visual"},
            "S2023002": {"grade": "大二", "subject": "computer", "learning_preference": "text"}
        }
    
    def query_student_basic(self, student_id: str) -> Dict[str, Any]:
        """查询学生基础信息"""
        return self.student_basic_data.get(student_id, {})
    
    def query_resource(self, **kwargs) -> Dict[str, Any]:
        """按条件查询资源（知识点/难度/格式）"""
        knowledge_point = kwargs.get("knowledge_point")
        difficulty = kwargs.get("difficulty_level")
        format_type = kwargs.get("format")
        
        for resource in self.resource_lib:
            match = True
            if knowledge_point and resource["knowledge_point"] != knowledge_point:
                match = False
            if difficulty is not None and resource["difficulty_level"] != difficulty:
                match = False
            if format_type and resource["format"] != format_type:
                match = False
            if match:
                return resource
        return self.resource_lib[0]  # 默认返回第一个资源
    
    def desensitize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """数据脱敏（隐藏隐私信息）"""
        if "phone" in raw_data:
            raw_data["phone"] = raw_data["phone"][:3] + "****" + raw_data["phone"][7:]
        if "name" in raw_data:
            raw_data["name"] = raw_data["name"][0] + "同学"
        return raw_data