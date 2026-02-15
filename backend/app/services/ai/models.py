"""AI模型配置"""


class AIModelConfig:
    """AI模型配置类"""

    def __init__(
        self,
        model_id: str,
        api_key: str | None = None,
        base_url: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        weight: int = 1,
    ):
        self.model_id = model_id
        self.api_key = api_key
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.weight = weight
