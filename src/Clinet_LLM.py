from openai import OpenAI
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
            self.llm = OpenAI(
                # api_key=os.environ.get(''),
                api_key="sk-3f32a7a2e0b34fe1b9d6439770cdd2b9",
                base_url="https://api.deepseek.com")
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
            You are a professional educational AI. Please follow these rules:
            1. Subject knowledge must strictly comply with {self._get_subject_standard()} (e.g., High School Mathematics Curriculum Standards).
            2. The output format must be JSON with no missing fields or syntax errors.
            3. Language should be easy to understand, suitable for students from K12 to university level.
            Core Task: {prompt}
        """

        response = self.llm.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a expert in the field of education"},
                {"role": "user", "content": edu_enhanced_prompt},
            ],
            stream=False,
            temperature=temperature 
        )
        return response.choices[0].message.content

    def _get_subject_standard(self) -> str:
        """私有方法：获取对应学段学科标准（简化实现，实际对接edu_standard数据库）"""
        return "《普通高中数学课程标准（2017年版2020年修订）》"

if __name__=="__main__":
    # 全局实例化
    global_llm = LLMClient(model_type="cloud", model_name="llama3-edu")

    # 场景1: 需要高度准确和稳定的答案（例如，解答一道数学题）
    math_prompt = "请详细解答以下数学题：已知函数 f(x) = x^2 - 4x + 3，求其最小值。"
    print("--- 场景1: 低温度 (高准确性) ---")
    response_stable = global_llm.generate_edu_response(math_prompt, temperature=0.2)
    print(response_stable)

    print("\n" + "="*20 + "\n")

    # 场景2: 需要一些创意和多样性（例如，为一篇关于环保的作文构思几个不同的开头）
    creative_prompt = "为一篇题为《环保，从我做起》的议论文，构思3个不同风格的开头段落。"
    print("--- 场景2: 中高温度 (高创造性) ---")
    response_creative = global_llm.generate_edu_response(creative_prompt, temperature=0.9)
    print(response_creative)

