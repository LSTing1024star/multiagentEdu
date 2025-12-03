import os
import sys
import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from termcolor import colored
import json

# 项目路径配置
current_path = os.path.abspath(__file__)
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.append(parent_path)

# agents/Agent_nlu.py（调整导入）
from src.agents_wrapper import AgentsManager  # 确保AgentsManager能正确实例化
from src.Clinet_LLM import LLMClient  # 修正拼写错误（原代码中是Clinet_LLM）
from agents.Agent_dbmanager import DatabaseManagerAgent
from utils.utils import format_result  # 复用现有结果格式化工具

# 意图类型枚举
class IntentType(Enum):
    ASSESSMENT = "学业评估"  # 分析成绩、薄弱点、能力等级
    PLANNING = "学习规划"     # 制定计划、调整目标、安排任务
    GUIDANCE = "问题引导"     # 解题指导、知识点讲解、场景分析
    COORDINATION = "智能协调" # 解决计划冲突、优化方案
    UNKNOWN = "未知意图"

# 实体类型定义
class EntityKeys:
    STUDENT_ID = "student_id"
    SUBJECT = "subject"
    QUESTION = "question"
    GOAL = "long_term_goal"
    FEEDBACK_TASK_ID = "feedback_task_id"
    FEEDBACK_RATE = "feedback_completion_rate"
    FEEDBACK_NOTE = "feedback_note"
    GOAL = "goal"              # 长期目标
    GOAL_SCORE = "goal_score"  # 目标分数（新增，解决当前错误

class AgentNLU:
    """自然语言理解智能体（自主解析意图+调用功能）"""
    def __init__(self, data_path: str = "/home/lst/data/assistment2009/skill_builder_data.csv"):
        # 初始化依赖组件
        self.llm_client = LLMClient(model_type="cloud", model_name="llama3-edu")
        self.db_agent = DatabaseManagerAgent(data_path=data_path)
        self.agent_manager = AgentsManager(data_path=data_path)
        
        # 意图关键词库（规则+LLM混合识别）
        self.intent_keywords = {
            IntentType.ASSESSMENT: ["评估", "成绩", "薄弱点", "能力等级", "分析", "水平"],
            IntentType.PLANNING: ["计划", "规划", "目标", "任务", "安排", "学习计划"],
            IntentType.GUIDANCE: ["问题", "为什么", "怎么做", "解题", "讲解", "知识点"],
            IntentType.COORDINATION: ["冲突", "调整", "优化", "不匹配", "进度", "协调"]
        }
        
        # 在AgentNLU类的entity_patterns中补充
        # agents/Agent_nlu.py（实体模式定义部分）
        self.entity_patterns = {
            EntityKeys.STUDENT_ID: r"S\d+",
            EntityKeys.SUBJECT: r"(math|语文|英语)",
            EntityKeys.FEEDBACK_RATE: r"(\d+)%",
            EntityKeys.FEEDBACK_TASK_ID: r"T\d+|t_\w+",
            EntityKeys.GOAL: r".+",  # 可根据实际需求优化目标提取正则
            EntityKeys.GOAL_SCORE: r"(\d+)分"  # 此处引用需与枚举成员名一致
        }

    def _rule_based_intent_detect(self, text: str) -> IntentType:
        """基于规则的意图识别（快速匹配关键词）"""
        text_lower = text.lower()
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent
        return IntentType.UNKNOWN

    def _llm_based_intent_confirm(self, text: str, rule_intent: IntentType) -> IntentType:
        """基于LLM的意图确认（解决模糊场景）"""
        prompt = f"""
        请分析用户输入的意图，只能从以下选项中选择：{[i.value for i in IntentType]}
        用户输入：{text}
        初步识别结果：{rule_intent.value}
        若初步识别准确，直接返回该意图；否则修正为正确意图（仅返回意图名称）。
        """
        #########################这个地方重写一下,需要真的参考rule，+LLM分析意图###########################
        try:
            result = self.llm_client.generate_edu_response(prompt, temperature=0.1).strip()
            print(colored(result, "red"))
            
            # 解析JSON提取intent字段
            result_data = json.loads(result)
            intent_str = result_data.get("intent", "").strip()  # 获取intent值
            
            # 匹配IntentType
            return next((i for i in IntentType if i.value == intent_str), IntentType.UNKNOWN)
        
        except json.JSONDecodeError:
            # 若JSON解析失败，直接用原始字符串匹配（兼容非JSON返回）
            return next((i for i in IntentType if i.value == result), rule_intent)
        except Exception as e:
            print(f"⚠️ 意图解析异常：{e}")
            return rule_intent  # 兜底返回规则识别的意图
        #################################################################
    def detect_intent(self, text: str) -> IntentType:
        """意图识别主流程（规则+LLM混合）"""
        rule_intent = self._rule_based_intent_detect(text)
        return self._llm_based_intent_confirm(text, rule_intent)

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """实体提取（规则+语义理解）"""
        entities = {}
        
        # 规则提取结构化实体
        for key, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                if key == EntityKeys.FEEDBACK_RATE:
                    entities[key] = int(matches[0].replace("%", ""))  # 提取数字
                else:
                    entities[key] = matches[0]
        
        # 语义提取非结构化实体（通过LLM）
        prompt = f"""
        从用户输入中提取以下信息（若不存在则留空）：
        1. 学生ID（如S12345）
        2. 科目（math/语文/英语）
        3. 具体问题（如数学题、知识点疑问）
        4. 长期目标（如期末提分）
        5. 反馈备注（如任务完成情况）
        
        用户输入：{text}
        已提取的结构化信息：{entities}
        输出格式：JSON对象，键为{[k for k in EntityKeys.__dict__ if not k.startswith('__')]}
        """
        try:
            llm_entities = self.llm_client.generate_edu_response(prompt, temperature=0.1)
            if isinstance(llm_entities, dict):
                entities.update(llm_entities)
        except:
            pass
        
        return entities

    def check_entity_completeness(self, intent: IntentType, entities: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """检查实体完整性（根据意图判断必要信息）"""
        required_entities = {
            IntentType.ASSESSMENT: [EntityKeys.STUDENT_ID, EntityKeys.SUBJECT],
            IntentType.PLANNING: [EntityKeys.STUDENT_ID, EntityKeys.SUBJECT, EntityKeys.GOAL],
            IntentType.GUIDANCE: [EntityKeys.STUDENT_ID, EntityKeys.SUBJECT, EntityKeys.QUESTION],
            IntentType.COORDINATION: [EntityKeys.STUDENT_ID, EntityKeys.SUBJECT, EntityKeys.GOAL]
        }
        
        missing = [e for e in required_entities.get(intent, []) if e not in entities or not entities[e]]
        return len(missing) == 0, missing

    def generate_prompt_for_missing(self, missing_entities: List[str]) -> str:
        """生成缺失实体的追问话术"""
        entity_names = {
            EntityKeys.STUDENT_ID: "学生ID（如S12345）",
            EntityKeys.SUBJECT: "科目（math/语文/英语）",
            EntityKeys.QUESTION: "具体问题（如数学题、知识点疑问）",
            EntityKeys.GOAL: "长期目标（如期末提分）",
            EntityKeys.FEEDBACK_TASK_ID: "任务ID（如T001）",
            EntityKeys.FEEDBACK_RATE: "任务完成率（如60%）",
            EntityKeys.FEEDBACK_NOTE: "反馈备注（如学习困难）"
        }
        
        return f"请补充以下信息：{', '.join([entity_names[e] for e in missing_entities])}"

    def process_intent(self, intent: IntentType, entities: Dict[str, Any]) -> Dict[str, Any]:
        """根据意图调用对应功能模块"""
        if intent == IntentType.ASSESSMENT:
            return self.agent_manager.run_assessment(
                student_id=entities[EntityKeys.STUDENT_ID],
                subject=entities[EntityKeys.SUBJECT]
            )
        
        elif intent == IntentType.PLANNING:
            # 构建执行反馈（可选）
            feedback = None
            if all(k in entities for k in [EntityKeys.FEEDBACK_TASK_ID, EntityKeys.FEEDBACK_RATE]):
                feedback = {
                    "task_id": entities[EntityKeys.FEEDBACK_TASK_ID],
                    "completion_rate": entities[EntityKeys.FEEDBACK_RATE],
                    "feedback_note": entities.get(EntityKeys.FEEDBACK_NOTE, "")
                }
            return self.agent_manager.run_planning(
                student_id=entities[EntityKeys.STUDENT_ID],
                subject=entities[EntityKeys.SUBJECT],
                long_term_goal=entities[EntityKeys.GOAL],
                execution_feedback=feedback
            )
        
        elif intent == IntentType.GUIDANCE:
            # 问题引导支持多轮交互（追问回答）
            return self.agent_manager.run_guidance(
                student_id=entities[EntityKeys.STUDENT_ID],
                subject=entities[EntityKeys.SUBJECT],
                question_desc=entities[EntityKeys.QUESTION],
                inquiry_answers=entities.get("inquiry_answers")  # 多轮回答存储
            )
        
        elif intent == IntentType.COORDINATION:
            feedback = None
            if all(k in entities for k in [EntityKeys.FEEDBACK_TASK_ID, EntityKeys.FEEDBACK_RATE]):
                feedback = {
                    "task_id": entities[EntityKeys.FEEDBACK_TASK_ID],
                    "completion_rate": entities[EntityKeys.FEEDBACK_RATE]
                }
            return self.agent_manager.run_coordination(
                student_id=entities[EntityKeys.STUDENT_ID],
                subject=entities[EntityKeys.SUBJECT],
                long_term_goal=entities[EntityKeys.GOAL],
                execution_feedback=feedback
            )
        # 在process_intent的Planning分支中补充
        elif intent == IntentType.PLANNING:
            # 从实体中提取长期目标（兼容“期末提分20分”等描述）
            long_term_goal = entities.get(EntityKeys.GOAL, "")
            # 调用规划核心函数（与academic_planning_core.py的run_academic_planning对齐）
            return self.agent_manager.run_planning(
                student_id=entities[EntityKeys.STUDENT_ID],
                subject=entities[EntityKeys.SUBJECT],
                long_term_goal=long_term_goal,
                execution_feedback=feedback  # 与现有ExecutionFeedback模型兼容
            )

        else:
            return {"error": "无法理解意图，请重新描述你的需求"}

    def run_interactive_loop(self) -> None:
        """启动持续交互循环"""
        print("🎓 教育智能助手（自然语言交互模式）")
        print("💡 提示：请用自然语言描述你的需求（如“帮我评估S92523的数学水平”），输入“退出”结束")
        
        context_entities = {}  # 保存上下文实体（支持多轮对话）
        
        while True:
            user_input = input("\n你：").strip()
            if user_input.lower() in ["退出", "exit"]:
                print("👋 再见！")
                break
            
            # 1. 意图识别
            intent = self.detect_intent(user_input)
            print(f"（系统识别意图：{intent.value}）")
            
            # 2. 实体提取（结合上下文）
            current_entities = self.extract_entities(user_input)
            context_entities.update(current_entities)  # 上下文融合
            
            # 3. 检查实体完整性
            is_complete, missing = self.check_entity_completeness(intent, context_entities)
            if not is_complete:
                print(f"🤖 {self.generate_prompt_for_missing(missing)}")
                continue
            
            # 4. 执行对应功能
            try:
                result = self.process_intent(intent, context_entities)
                print("\n" + format_result(result, f"{intent.value}结果"))
            except Exception as e:
                print(f"❌ 操作失败：{str(e)}")
            
            # 5. 多轮对话支持（重置非上下文实体）
            context_entities = {k: v for k, v in context_entities.items() 
                              if k in [EntityKeys.STUDENT_ID, EntityKeys.SUBJECT]}

if __name__ == "__main__":
    # 启动自然语言交互
    nlu_agent = AgentNLU()
    nlu_agent.run_interactive_loop()