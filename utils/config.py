import json

# 模拟LLM调用（实际替换为Ollama/OpenAI官方SDK）
class MockOllama:
    def __init__(self, model: str, base_url: str):
        self.model = model
    def invoke(self, prompt: str, temperature: float) -> str:
        # 模拟LLM返回结构化JSON（实际为真实模型调用）
        return json.dumps({"mock_response": "edu_optimized_result"})

class MockOpenAI:
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
    def invoke(self, prompt: str, temperature: float) -> str:
        return json.dumps({"mock_response": "cloud_edu_result"})