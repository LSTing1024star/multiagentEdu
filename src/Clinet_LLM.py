class LLMClient:
    """LLM客户端封装（创新点：支持多模型无缝切换+教育场景适配）
    设计意图：解决通用LLM在教育场景的学科知识不准确问题，同时降低模型替换成本
    """
    def __init__(self, model_type: str = "local", model_name: str = "llama3-edu"):
        """
        Args:
            model_type: 模型部署类型（local=本地Ollama，cloud=云端GPT-4）
            model_name: 模型名称（本地模型已通过教育语料微调）
        """
        if model_type == "local":
            # 本地部署：适配教育微调后的Llama 3
            self.llm = Ollama(model=model_name, base_url="http://localhost:11434")
        elif model_type == "cloud":
            # 云端部署：支持GPT-4等通用模型
            self.llm = OpenAI(model_name=model_name, api_key="your-api-key")
        else:
            raise ValueError("model_type must be 'local' or 'cloud'")

    def generate_edu_response(self, prompt: str, temperature: float = 0.3) -> str:
        """生成教育场景响应（低温度保障结果稳定性）
        Args:
            prompt: 教育场景专属Prompt（含学科知识约束、输出格式要求）
            temperature: 生成温度（0.3→确定性优先，适配评估/规划场景）
        Returns:
            str: 结构化响应（JSON格式）
        """
        # 教育场景增强：注入学科知识约束（创新点：避免通用LLM的学科错误）
        edu_enhanced_prompt = f"""
        你是专业教育AI，需遵循以下规则：
        1. 学科知识严格符合{self._get_subject_standard()}（如高中数学课标）；
        2. 输出格式为JSON，字段不缺失、无语法错误；
        3. 语言通俗易懂，适配K12-大学学段学生理解水平。
        核心任务：{prompt}
        """
        return self.llm.invoke(edu_enhanced_prompt, temperature=temperature)

    def _get_subject_standard(self) -> str:
        """私有方法：获取对应学段学科标准（简化实现，实际对接edu_standard数据库）"""
        return "《普通高中数学课程标准（2017年版2020年修订）》"

if __name__=="__main__":
    # 全局实例化（工程中通过配置文件动态切换）
    global_llm = LLMClient(model_type="local", model_name="llama3-edu")