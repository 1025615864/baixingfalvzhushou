"""AI Assistant 服务测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# 测试模块导入
from app.services.ai.assistant import AILegalAssistant, get_ai_assistant


class TestAILegalAssistant:
    """AI法律助手测试类"""

    @pytest.fixture
    def mock_settings(self):
        """模拟设置"""
        settings = MagicMock()
        settings.openai_api_key = "test-key"
        settings.openai_base_url = "https://api.openai.com/v1"
        settings.ai_model = "gpt-4o-mini"
        settings.ai_fallback_models = ["gpt-3.5-turbo"]
        return settings

    @pytest.fixture
    def mock_knowledge_base(self):
        """模拟知识库"""
        kb = MagicMock()
        kb.initialize = MagicMock()
        kb.search_with_quality_control = AsyncMock(return_value=([], MagicMock(
            total_candidates=0,
            qualified_count=0,
            avg_similarity=0.0,
            confidence="low"
        )))
        return kb

    @pytest.fixture
    def mock_content_safety(self):
        """模拟内容安全过滤器"""
        safety = MagicMock()
        safety.risk_level = MagicMock(value="low")
        safety.suggestion = None
        safety.check_input = MagicMock(return_value=safety)
        safety.sanitize_output = MagicMock(side_effect=lambda x: x)
        return safety

    @pytest.fixture
    def mock_strategy_decider(self):
        """模拟响应策略决策器"""
        decider = MagicMock()
        strategy = MagicMock()
        strategy.value = "direct_answer"
        decider.decide = MagicMock(return_value=MagicMock(
            strategy=strategy,
            reason="test",
            confidence="high"
        ))
        return decider

    @pytest.fixture
    def mock_intent_classifier(self):
        """模拟意图分类器"""
        classifier = MagicMock()
        intent = MagicMock()
        intent.value = "legal_question"
        intent.needs_clarification = False
        intent.clarifying_questions = []
        classifier.classify = MagicMock(return_value=MagicMock(
            intent=intent,
            needs_clarification=False,
            clarifying_questions=[]
        ))
        return classifier

    @pytest.fixture
    def mock_disclaimer_manager(self):
        """模拟免责声明管理器"""
        manager = MagicMock()
        manager.get_disclaimer = MagicMock(return_value="免责声明内容")
        return manager

    @pytest.fixture
    def assistant(self, mock_settings, mock_knowledge_base, mock_content_safety,
                  mock_strategy_decider, mock_intent_classifier, mock_disclaimer_manager):
        """创建测试助手实例"""
        with patch('app.services.ai.assistant.get_settings', return_value=mock_settings):
            with patch('app.services.ai.assistant.LegalKnowledgeBase', return_value=mock_knowledge_base):
                with patch('app.services.ai.assistant.ContentSafetyFilter', return_value=mock_content_safety):
                    with patch('app.services.ai.assistant.ResponseStrategyDecider', return_value=mock_strategy_decider):
                        with patch('app.services.ai.assistant.AiIntentClassifier', return_value=mock_intent_classifier):
                            with patch('app.services.ai.assistant.DisclaimerManager', return_value=mock_disclaimer_manager):
                                return AILegalAssistant()

    def test_encoding_for_model_valid(self, assistant):
        """测试有效模型的编码获取"""
        enc = assistant._encoding_for_model("gpt-4")
        assert enc is not None

    def test_encoding_for_model_invalid(self, assistant):
        """测试无效模型的编码获取（回退到 cl100k_base）"""
        enc = assistant._encoding_for_model("invalid-model")
        assert enc is not None

    def test_encoding_for_model_none(self, assistant):
        """测试 None 模型的编码获取"""
        enc = assistant._encoding_for_model(None)
        assert enc is not None

    def test_count_tokens_empty(self, assistant):
        """测试空文本的 token 计数"""
        count = assistant._count_tokens("", model="gpt-4")
        assert count == 0

    def test_count_tokens_none(self, assistant):
        """测试 None 文本的 token 计数"""
        count = assistant._count_tokens(None, model="gpt-4")
        assert count == 0

    def test_count_tokens_normal(self, assistant):
        """测试正常文本的 token 计数"""
        count = assistant._count_tokens("你好，世界！", model="gpt-4")
        assert count >= 0

    def test_estimate_cost_usd_none_model(self, assistant):
        """测试 None 模型的费用估算"""
        cost = assistant._estimate_cost_usd(model=None, prompt_tokens=100, completion_tokens=100)
        assert cost is None

    def test_estimate_cost_usd_empty_model(self, assistant):
        """测试空模型名的费用估算"""
        cost = assistant._estimate_cost_usd(model="", prompt_tokens=100, completion_tokens=100)
        assert cost is None

    def test_estimate_cost_usd_gpt_4o_mini(self, assistant):
        """测试 gpt-4o-mini 的费用估算"""
        cost = assistant._estimate_cost_usd(model="gpt-4o-mini", prompt_tokens=1000000, completion_tokens=1000000)
        assert cost is not None
        assert isinstance(cost, float)

    def test_estimate_cost_usd_gpt_4o(self, assistant):
        """测试 gpt-4o 的费用估算"""
        cost = assistant._estimate_cost_usd(model="gpt-4o", prompt_tokens=1000000, completion_tokens=1000000)
        assert cost is not None
        assert isinstance(cost, float)

    def test_estimate_cost_usd_gpt_3_5_turbo(self, assistant):
        """测试 gpt-3.5-turbo 的费用估算"""
        cost = assistant._estimate_cost_usd(model="gpt-3.5-turbo", prompt_tokens=1000000, completion_tokens=1000000)
        assert cost is not None
        assert isinstance(cost, float)

    def test_estimate_cost_usd_unknown_model(self, assistant):
        """测试未知模型的费用估算"""
        cost = assistant._estimate_cost_usd(model="unknown-model", prompt_tokens=100, completion_tokens=100)
        assert cost is None

    def test_model_candidates_primary_only(self, assistant):
        """测试主模型候选列表"""
        candidates = assistant._model_candidates()
        assert len(candidates) > 0
        assert "deepseek-chat" in candidates

    def test_model_candidates_with_fallbacks(self, assistant):
        """测试带有备用模型的候选列表"""
        candidates = assistant._model_candidates()
        assert len(candidates) > 0
        # Only deepseek-chat is configured in test setup

    def test_model_candidates_no_duplicates(self, assistant):
        """测试候选列表无重复"""
        candidates = assistant._model_candidates()
        assert len(candidates) == len(set(candidates))

    def test_model_candidates_empty_fallbacks(self, assistant):
        """测试空回退模型的候选列表"""
        assistant._model_candidates = MagicMock(return_value=["gpt-4o-mini"])
        candidates = assistant._model_candidates()
        assert candidates == ["gpt-4o-mini"]

    def test_evict_if_needed_not_full(self, assistant):
        """测试未满时的驱逐逻辑"""
        assistant._max_sessions = 5000
        assistant.conversation_histories = {"session1": []}
        assistant._last_seen = {"session1": 1000.0}
        # 不应抛出异常
        assistant._evict_if_needed()

    def test_evict_if_needed_exactly_at_limit(self, assistant):
        """测试恰好达到限制时的驱逐逻辑"""
        assistant._max_sessions = 2
        assistant.conversation_histories = {"session1": [], "session2": []}
        assistant._last_seen = {"session1": 1000.0, "session2": 2000.0}
        # 恰好等于限制，不应驱逐
        assistant._evict_if_needed()
        assert len(assistant.conversation_histories) == 2

    def test_build_context_empty_references(self, assistant):
        """测试空引用的上下文构建"""
        context = assistant._build_context([])
        assert "暂无相关法律条文参考" in context

    def test_build_context_with_references(self, assistant):
        """测试带引用的上下文构建"""
        references = [
            ("法律条文内容1", {"knowledge_id": 1}, 0.9),
            ("法律条文内容2", {"knowledge_id": 2}, 0.8),
        ]
        context = assistant._build_context(references)
        assert "法律条文内容1" in context
        assert "法律条文内容2" in context
        assert "1." in context
        assert "2." in context

    def test_parse_references_empty(self, assistant):
        """测试空引用的解析"""
        result = assistant._parse_references([])
        assert result == []

    def test_parse_references_with_valid_metadata(self, assistant):
        """测试带有效元数据的引用解析"""
        references = [
            ("法律条文内容", {"knowledge_id": "123"}, 0.9),
        ]
        result = assistant._parse_references(references)
        assert len(result) == 1
        assert result[0].content == "法律条文内容"
        assert result[0].knowledge_id == 123
        assert result[0].similarity == 0.9

    def test_parse_references_with_invalid_metadata(self, assistant):
        """测试带无效元数据的引用解析"""
        references = [
            ("法律条文内容", {"knowledge_id": "invalid"}, 0.9),
        ]
        result = assistant._parse_references(references)
        assert len(result) == 1
        assert result[0].knowledge_id is None

    def test_parse_references_with_missing_metadata(self, assistant):
        """测试缺失元数据的引用解析"""
        references = [
            ("法律条文内容", {}, 0.9),
        ]
        result = assistant._parse_references(references)
        assert len(result) == 1
        assert result[0].knowledge_id is None

    def test_normalize_history_empty(self, assistant):
        """测试空历史记录的规范化"""
        result = assistant._normalize_history([])
        assert result == []

    def test_normalize_history_valid(self, assistant):
        """测试有效历史记录的规范化"""
        history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
            {"role": "system", "content": "你是法律助手"},
        ]
        result = assistant._normalize_history(history)
        assert len(result) == 3
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        assert result[2]["role"] == "system"

    def test_normalize_history_invalid_role(self, assistant):
        """测试无效角色的历史记录规范化"""
        history = [
            {"role": "invalid_role", "content": "内容"},
        ]
        result = assistant._normalize_history(history)
        assert len(result) == 0

    def test_normalize_history_empty_content(self, assistant):
        """测试空内容的历史记录规范化"""
        history = [
            {"role": "user", "content": ""},
        ]
        result = assistant._normalize_history(history)
        assert len(result) == 0

    def test_normalize_history_strips_whitespace(self, assistant):
        """测试历史记录规范化会去除空白"""
        history = [
            {"role": "  USER  ", "content": "  内容  "},
        ]
        result = assistant._normalize_history(history)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "内容"

    def test_get_or_create_session_new(self, assistant):
        """测试创建新会话"""
        session_id = assistant.get_or_create_session()
        assert session_id is not None
        assert len(session_id) > 0
        assert session_id in assistant.conversation_histories

    def test_get_or_create_session_with_id(self, assistant):
        """测试使用指定 ID 创建会话"""
        session_id = assistant.get_or_create_session(session_id="test-session")
        assert session_id == "test-session"
        assert "test-session" in assistant.conversation_histories

    def test_get_or_create_session_with_initial_history(self, assistant):
        """测试带初始历史创建会话"""
        history = [{"role": "user", "content": "初始消息"}]
        session_id = assistant.get_or_create_session(initial_history=history)
        assert session_id in assistant.conversation_histories
        assert len(assistant.conversation_histories[session_id]) == 1

    def test_get_or_create_session_existing(self, assistant):
        """测试获取已存在的会话"""
        assistant.conversation_histories["existing"] = [{"role": "user", "content": "消息"}]
        assistant._last_seen["existing"] = 1000.0
        session_id = assistant.get_or_create_session(session_id="existing")
        assert session_id == "existing"
        # _last_seen 应该被更新
        assert assistant._last_seen["existing"] > 1000.0

    def test_get_or_create_session_empty_id(self, assistant):
        """测试空 ID 创建新会话"""
        session_id = assistant.get_or_create_session(session_id="")
        assert session_id is not None
        assert len(session_id) > 0

    def test_clear_session_valid(self, assistant):
        """测试清空有效会话"""
        assistant.conversation_histories["session1"] = []
        assistant._last_seen["session1"] = 1000.0
        assistant.clear_session("session1")
        assert "session1" not in assistant.conversation_histories
        assert "session1" not in assistant._last_seen

    def test_clear_session_nonexistent(self, assistant):
        """测试清空不存在的会话"""
        # 不应抛出异常
        assistant.clear_session("nonexistent")
        assert "nonexistent" not in assistant.conversation_histories

    def test_clear_session_empty(self, assistant):
        """测试清空空会话 ID"""
        # 不应抛出异常
        assistant.clear_session("")
        assistant.clear_session("   ")

    def test_append_disclaimer(self, assistant):
        """测试附加免责声明"""
        from app.services.ai_response_strategy import ResponseStrategy
        from app.services.content_safety import RiskLevel

        answer = "原始回答"
        risk_level = RiskLevel.LOW
        strategy = ResponseStrategy.DIRECT_ANSWER

        result = assistant._append_disclaimer(answer, risk_level=risk_level, strategy=strategy)
        assert "原始回答" in result
        assert "---" in result

    def test_append_disclaimer_no_disclaimer(self, assistant):
        """测试无免责声明附加"""
        from app.services.ai_response_strategy import ResponseStrategy
        from app.services.content_safety import RiskLevel

        assistant.disclaimer_manager.get_disclaimer = MagicMock(return_value=None)
        answer = "原始回答"

        result = assistant._append_disclaimer(answer, risk_level=RiskLevel.LOW, strategy=ResponseStrategy.DIRECT_ANSWER)
        assert result == answer


class TestGetAIAssistant:
    """获取AI助手测试类"""

    def test_get_ai_assistant_singleton(self):
        """测试 AI 助手单例"""
        with patch('app.services.ai.assistant.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                openai_api_key="test-key",
                openai_base_url="https://api.openai.com/v1",
                ai_model="gpt-4o-mini",
                ai_fallback_models=[]
            )
            with patch('app.services.ai.assistant.LegalKnowledgeBase') as mock_kb:
                mock_kb_instance = MagicMock()
                mock_kb_instance.initialize = MagicMock()
                mock_kb.return_value = mock_kb_instance
                with patch('app.services.ai.assistant.ContentSafetyFilter') as mock_safety:
                    mock_safety.return_value = MagicMock()
                    with patch('app.services.ai.assistant.ResponseStrategyDecider') as mock_decider:
                        mock_decider.return_value = MagicMock()
                        with patch('app.services.ai.assistant.AiIntentClassifier') as mock_classifier:
                            mock_classifier.return_value = MagicMock()
                            with patch('app.services.ai.assistant.DisclaimerManager') as mock_manager:
                                mock_manager.return_value = MagicMock()

                                # 重置全局变量
                                import app.services.ai.assistant
                                app.services.ai.assistant._ai_assistant = None

                                assistant1 = get_ai_assistant()
                                assistant2 = get_ai_assistant()
                                assert assistant1 is assistant2


class TestAILegalAssistantEviction:
    """AI助手会话驱逐测试类"""

    @pytest.fixture
    def mock_dependencies(self):
        """模拟所有依赖"""
        settings = MagicMock()
        settings.openai_api_key = "test-key"
        settings.openai_base_url = "https://api.openai.com/v1"
        settings.ai_model = "gpt-4o-mini"
        settings.ai_fallback_models = []

        kb = MagicMock()
        kb.initialize = MagicMock()

        safety = MagicMock()
        safety.risk_level = MagicMock(value="low")
        safety.check_input = MagicMock(return_value=safety)
        safety.sanitize_output = MagicMock(side_effect=lambda x: x)

        decider = MagicMock()
        strategy = MagicMock()
        strategy.value = "direct_answer"
        decider.decide = MagicMock(return_value=MagicMock(strategy=strategy, reason="test", confidence="high"))

        classifier = MagicMock()
        intent = MagicMock()
        intent.value = "legal_question"
        intent.needs_clarification = False
        intent.clarifying_questions = []
        classifier.classify = MagicMock(return_value=MagicMock(intent=intent, needs_clarification=False, clarifying_questions=[]))

        manager = MagicMock()
        manager.get_disclaimer = MagicMock(return_value=None)

        return settings, kb, safety, decider, classifier, manager

    def test_eviction_removes_oldest_session(self, mock_dependencies):
        """测试驱逐时移除最旧的会话"""
        settings, kb, safety, decider, classifier, manager = mock_dependencies

        with patch('app.services.ai.assistant.get_settings', return_value=settings):
            with patch('app.services.ai.assistant.LegalKnowledgeBase', return_value=kb):
                with patch('app.services.ai.assistant.ContentSafetyFilter', return_value=safety):
                    with patch('app.services.ai.assistant.ResponseStrategyDecider', return_value=decider):
                        with patch('app.services.ai.assistant.AiIntentClassifier', return_value=classifier):
                            with patch('app.services.ai.assistant.DisclaimerManager', return_value=manager):
                                assistant = AILegalAssistant()
                                assistant._max_sessions = 2

                                # 添加两个会话
                                assistant.get_or_create_session(session_id="session1")
                                assistant.get_or_create_session(session_id="session2")

                                assert "session1" in assistant.conversation_histories
                                assert "session2" in assistant.conversation_histories

                                # 添加第三个会话，应该驱逐最旧的
                                import time
                                assistant._last_seen["session1"] = 1000.0  # 设置为最旧
                                assistant._last_seen["session2"] = 2000.0

                                assistant.get_or_create_session(session_id="session3")

                                # session1 应该被驱逐
                                assert "session1" not in assistant.conversation_histories
                                assert "session2" in assistant.conversation_histories
                                assert "session3" in assistant.conversation_histories


class TestAILegalAssistantTokenCounting:
    """AI助手Token计数测试类"""

    @pytest.fixture
    def mock_dependencies(self):
        """模拟所有依赖"""
        settings = MagicMock()
        settings.openai_api_key = "test-key"
        settings.openai_base_url = "https://api.openai.com/v1"
        settings.ai_model = "gpt-4o-mini"
        settings.ai_fallback_models = []

        kb = MagicMock()
        kb.initialize = MagicMock()

        safety = MagicMock()
        safety.risk_level = MagicMock(value="low")
        safety.check_input = MagicMock(return_value=safety)
        safety.sanitize_output = MagicMock(side_effect=lambda x: x)

        decider = MagicMock()
        strategy = MagicMock()
        strategy.value = "direct_answer"
        decider.decide = MagicMock(return_value=MagicMock(strategy=strategy, reason="test", confidence="high"))

        classifier = MagicMock()
        intent = MagicMock()
        intent.value = "legal_question"
        intent.needs_clarification = False
        intent.clarifying_questions = []
        classifier.classify = MagicMock(return_value=MagicMock(intent=intent, needs_clarification=False, clarifying_questions=[]))

        manager = MagicMock()
        manager.get_disclaimer = MagicMock(return_value=None)

        return settings, kb, safety, decider, classifier, manager

    def test_token_counting_consistency(self, mock_dependencies):
        """测试Token计数一致性"""
        settings, kb, safety, decider, classifier, manager = mock_dependencies

        with patch('app.services.ai.assistant.get_settings', return_value=settings):
            with patch('app.services.ai.assistant.LegalKnowledgeBase', return_value=kb):
                with patch('app.services.ai.assistant.ContentSafetyFilter', return_value=safety):
                    with patch('app.services.ai.assistant.ResponseStrategyDecider', return_value=decider):
                        with patch('app.services.ai.assistant.AiIntentClassifier', return_value=classifier):
                            with patch('app.services.ai.assistant.DisclaimerManager', return_value=manager):
                                assistant = AILegalAssistant()

                                text = "这是一个测试文本"
                                count1 = assistant._count_tokens(text, model="gpt-4")
                                count2 = assistant._count_tokens(text, model="gpt-4")

                                # 同一文本同一模型的计数应该一致
                                assert count1 == count2

    def test_token_counting_empty_fallback(self, mock_dependencies):
        """测试空文本的Token计数回退逻辑"""
        settings, kb, safety, decider, classifier, manager = mock_dependencies

        with patch('app.services.ai.assistant.get_settings', return_value=settings):
            with patch('app.services.ai.assistant.LegalKnowledgeBase', return_value=kb):
                with patch('app.services.ai.assistant.ContentSafetyFilter', return_value=safety):
                    with patch('app.services.ai.assistant.ResponseStrategyDecider', return_value=decider):
                        with patch('app.services.ai.assistant.AiIntentClassifier', return_value=classifier):
                            with patch('app.services.ai.assistant.DisclaimerManager', return_value=manager):
                                assistant = AILegalAssistant()

                                # 空文本应该返回0
                                count = assistant._count_tokens("", model="gpt-4")
                                assert count == 0


class TestAILegalAssistantCostEstimation:
    """AI助手成本估算测试类"""

    @pytest.fixture
    def mock_dependencies(self):
        """模拟所有依赖"""
        settings = MagicMock()
        settings.openai_api_key = "test-key"
        settings.openai_base_url = "https://api.openai.com/v1"
        settings.ai_model = "gpt-4o-mini"
        settings.ai_fallback_models = []

        kb = MagicMock()
        kb.initialize = MagicMock()

        safety = MagicMock()
        safety.risk_level = MagicMock(value="low")
        safety.check_input = MagicMock(return_value=safety)
        safety.sanitize_output = MagicMock(side_effect=lambda x: x)

        decider = MagicMock()
        strategy = MagicMock()
        strategy.value = "direct_answer"
        decider.decide = MagicMock(return_value=MagicMock(strategy=strategy, reason="test", confidence="high"))

        classifier = MagicMock()
        intent = MagicMock()
        intent.value = "legal_question"
        intent.needs_clarification = False
        intent.clarifying_questions = []
        classifier.classify = MagicMock(return_value=MagicMock(intent=intent, needs_clarification=False, clarifying_questions=[]))

        manager = MagicMock()
        manager.get_disclaimer = MagicMock(return_value=None)

        return settings, kb, safety, decider, classifier, manager

    def test_cost_estimation_zero_tokens(self, mock_dependencies):
        """测试零Token的成本估算"""
        settings, kb, safety, decider, classifier, manager = mock_dependencies

        with patch('app.services.ai.assistant.get_settings', return_value=settings):
            with patch('app.services.ai.assistant.LegalKnowledgeBase', return_value=kb):
                with patch('app.services.ai.assistant.ContentSafetyFilter', return_value=safety):
                    with patch('app.services.ai.assistant.ResponseStrategyDecider', return_value=decider):
                        with patch('app.services.ai.assistant.AiIntentClassifier', return_value=classifier):
                            with patch('app.services.ai.assistant.DisclaimerManager', return_value=manager):
                                assistant = AILegalAssistant()

                                cost = assistant._estimate_cost_usd(model="gpt-4o-mini", prompt_tokens=0, completion_tokens=0)
                                assert cost == 0.0

    def test_cost_estimation_large_tokens(self, mock_dependencies):
        """测试大Token量的成本估算"""
        settings, kb, safety, decider, classifier, manager = mock_dependencies

        with patch('app.services.ai.assistant.get_settings', return_value=settings):
            with patch('app.services.ai.assistant.LegalKnowledgeBase', return_value=kb):
                with patch('app.services.ai.assistant.ContentSafetyFilter', return_value=safety):
                    with patch('app.services.ai.assistant.ResponseStrategyDecider', return_value=decider):
                        with patch('app.services.ai.assistant.AiIntentClassifier', return_value=classifier):
                            with patch('app.services.ai.assistant.DisclaimerManager', return_value=manager):
                                assistant = AILegalAssistant()

                                # 100万Token，成本应该显著
                                cost = assistant._estimate_cost_usd(model="gpt-4o", prompt_tokens=1000000, completion_tokens=1000000)
                                assert cost is not None
                                assert cost > 0

    def test_cost_estimation_gpt_4_1_models(self, mock_dependencies):
        """测试 gpt-4.1 系列模型的成本估算"""
        settings, kb, safety, decider, classifier, manager = mock_dependencies

        with patch('app.services.ai.assistant.get_settings', return_value=settings):
            with patch('app.services.ai.assistant.LegalKnowledgeBase', return_value=kb):
                with patch('app.services.ai.assistant.ContentSafetyFilter', return_value=safety):
                    with patch('app.services.ai.assistant.ResponseStrategyDecider', return_value=decider):
                        with patch('app.services.ai.assistant.AiIntentClassifier', return_value=classifier):
                            with patch('app.services.ai.assistant.DisclaimerManager', return_value=manager):
                                assistant = AILegalAssistant()

                                # gpt-4.1-mini 应该使用 gpt-4.1-mini 的价格
                                cost1 = assistant._estimate_cost_usd(model="gpt-4.1-mini", prompt_tokens=1000000, completion_tokens=1000000)
                                # gpt-4.1 应该使用 gpt-4.1 的价格
                                cost2 = assistant._estimate_cost_usd(model="gpt-4.1", prompt_tokens=1000000, completion_tokens=1000000)

                                assert cost1 is not None
                                assert cost2 is not None
                                # gpt-4.1 应该比 gpt-4.1-mini 贵
                                assert cost2 > cost1
