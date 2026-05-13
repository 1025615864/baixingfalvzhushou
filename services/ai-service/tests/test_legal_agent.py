import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.legal_agent import LegalAgent


class TestLegalAgent:

    @pytest.mark.asyncio
    async def test_analyze_intent(self):
        agent = LegalAgent.__new__(LegalAgent)
        agent.model_name = "test-model"
        agent.api_key = "test-key"
        agent.api_base = "https://api.test.com"

        with patch.object(agent, '_call_llm', new_callable=AsyncMock, return_value='{"intent": "consultation", "confidence": 0.9}'):
            result = await agent.analyze_intent("我想咨询离婚问题")
            assert result is not None

    @pytest.mark.asyncio
    async def test_rewrite_query(self):
        agent = LegalAgent.__new__(LegalAgent)
        agent.model_name = "test-model"
        agent.api_key = "test-key"
        agent.api_base = "https://api.test.com"

        with patch.object(agent, '_call_llm', new_callable=AsyncMock, return_value="离婚财产分割"):
            result = await agent.rewrite_query("离婚怎么分财产")
            assert result is not None

    @pytest.mark.asyncio
    async def test_generate_draft(self):
        agent = LegalAgent.__new__(LegalAgent)
        agent.model_name = "test-model"
        agent.api_key = "test-key"
        agent.api_base = "https://api.test.com"

        with patch.object(agent, '_call_llm', new_callable=AsyncMock, return_value="根据相关法律规定..."):
            result = await agent.generate_draft("离婚财产分割", [{"content": "民法典相关条款", "score": 0.95}])
            assert result is not None

    @pytest.mark.asyncio
    async def test_check_hallucination(self):
        agent = LegalAgent.__new__(LegalAgent)
        agent.model_name = "test-model"
        agent.api_key = "test-key"
        agent.api_base = "https://api.test.com"

        with patch.object(agent, '_call_llm', new_callable=AsyncMock, return_value='{"is_hallucination": false, "confidence": 0.85}'):
            result = await agent.check_hallucination("根据民法典...", [{"content": "民法典条款", "score": 0.9}])
            assert result is not None

    @pytest.mark.asyncio
    async def test_recommend_lawyers(self):
        agent = LegalAgent.__new__(LegalAgent)
        agent.model_name = "test-model"
        agent.api_key = "test-key"
        agent.api_base = "https://api.test.com"

        with patch.object(agent, '_call_llm', new_callable=AsyncMock, return_value='{"lawyers": [{"name": "张律师", "specialty": "婚姻法"}]}'):
            result = await agent.recommend_lawyers("离婚咨询", "北京")
            assert result is not None

    @pytest.mark.asyncio
    async def test_chitchat_response(self):
        agent = LegalAgent.__new__(LegalAgent)
        agent.model_name = "test-model"
        agent.api_key = "test-key"
        agent.api_base = "https://api.test.com"

        with patch.object(agent, '_call_llm', new_callable=AsyncMock, return_value="您好，我是法律助手，请问有什么可以帮助您的？"):
            result = await agent.chitchat_response("你好")
            assert result is not None
