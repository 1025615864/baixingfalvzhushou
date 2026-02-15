"""
AI会话管理和核心工具测试

测试覆盖：
- SessionManager类的所有公共方法
- AICore类的公共工具函数
- 边界条件和错误处理
"""
import pytest
import time
import uuid
from datetime import timedelta

from app.services.ai.session import SessionManager
from app.services.ai.core import AICore


class TestSessionManagerPublicAPI:
    """SessionManager公共API测试类"""

    @pytest.fixture
    def session_manager(self):
        """创建会话管理器实例"""
        return SessionManager(
            max_sessions=10,
            max_messages_per_session=5
        )

    def test_get_or_create_session_without_id(self, session_manager):
        """测试不提供session_id时创建新会话"""
        # Act
        session_id = session_manager.get_or_create_session()
        
        # Assert
        assert isinstance(session_id, str)
        assert len(session_id) == 32  # uuid hex length
        assert session_id in session_manager.conversation_histories
        assert session_id in session_manager._last_seen
        assert session_manager.conversation_histories[session_id] == []

    def test_get_or_create_session_with_new_id(self, session_manager):
        """测试提供新的session_id时创建会话"""
        # Arrange
        new_id = "test_session_001"
        
        # Act
        session_id = session_manager.get_or_create_session(new_id)
        
        # Assert
        assert session_id == new_id
        assert session_id in session_manager.conversation_histories
        assert session_id in session_manager._last_seen

    def test_get_or_create_session_existing(self, session_manager):
        """测试获取已存在的会话"""
        # Arrange
        session_id = "test_session_002"
        session_manager.get_or_create_session(session_id)
        initial_history = session_manager.conversation_histories[session_id]
        
        # Act
        returned_id = session_manager.get_or_create_session(session_id)
        
        # Assert
        assert returned_id == session_id
        # 历史记录应该保持不变
        assert session_manager.conversation_histories[session_id] is initial_history

    def test_get_or_create_session_with_initial_history(self, session_manager):
        """测试创建会话时初始化历史记录"""
        # Arrange
        session_id = "test_session_003"
        initial_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        # Act
        returned_id = session_manager.get_or_create_session(
            session_id,
            initial_history=initial_history
        )
        
        # Assert
        assert returned_id == session_id
        history = session_manager.conversation_histories[session_id]
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_get_or_create_session_overwrite_existing(self, session_manager):
        """测试对已存在会话提供initial_history时不覆盖"""
        # Arrange
        session_id = "test_session_004"
        session_manager.get_or_create_session(session_id)
        session_manager.add_message(session_id, "user", "Existing message")
        
        initial_history = [{"role": "user", "content": "New message"}]
        
        # Act
        returned_id = session_manager.get_or_create_session(
            session_id,
            initial_history=initial_history
        )
        
        # Assert - 不应该覆盖已有历史
        assert returned_id == session_id
        history = session_manager.conversation_histories[session_id]
        assert len(history) == 1
        assert history[0]["content"] == "Existing message"

    def test_clear_session(self, session_manager):
        """测试清除会话"""
        # Arrange
        session_id = "test_session_005"
        session_manager.get_or_create_session(session_id)
        session_manager.add_message(session_id, "user", "Test message")
        
        # Act
        session_manager.clear_session(session_id)
        
        # Assert
        assert session_id not in session_manager.conversation_histories
        assert session_id not in session_manager._last_seen

    def test_clear_nonexistent_session(self, session_manager):
        """测试清除不存在的会话（不应报错）"""
        # Arrange
        session_id = "test_session_nonexistent"
        
        # Act - 不应抛出异常
        session_manager.clear_session(session_id)
        
        # Assert - 只是静默失败
        assert session_id not in session_manager.conversation_histories

    def test_add_message(self, session_manager):
        """测试添加消息"""
        # Arrange
        session_id = "test_session_006"
        
        # Act
        session_manager.add_message(session_id, "user", "Hello, AI!")
        
        # Assert
        assert session_id in session_manager.conversation_histories
        history = session_manager.get_history(session_id)
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello, AI!"

    def test_add_message_to_nonexistent_session(self, session_manager):
        """测试向不存在的会话添加消息"""
        # Arrange
        session_id = "test_session_007"
        
        # Act
        session_manager.add_message(session_id, "user", "Auto create")
        
        # Assert - 应该自动创建会话
        assert session_id in session_manager.conversation_histories
        history = session_manager.get_history(session_id)
        assert len(history) == 1

    def test_add_multiple_messages(self, session_manager):
        """测试添加多条消息"""
        # Arrange
        session_id = "test_session_008"
        
        # Act
        session_manager.add_message(session_id, "user", "Question 1")
        session_manager.add_message(session_id, "assistant", "Answer 1")
        session_manager.add_message(session_id, "user", "Question 2")
        
        # Assert
        history = session_manager.get_history(session_id)
        assert len(history) == 3
        assert history[0]["content"] == "Question 1"
        assert history[1]["content"] == "Answer 1"
        assert history[2]["content"] == "Question 2"

    def test_add_message_truncates_history(self, session_manager):
        """测试添加消息时截断超过限制的历史记录"""
        # Arrange
        session_id = "test_session_009"
        max_messages = 5
        
        # Act - 添加超过限制的消息
        for i in range(10):
            session_manager.add_message(session_id, "user", f"Message {i}")
        
        # Assert - 应该只保留最近的消息
        history = session_manager.get_history(session_id)
        assert len(history) == max_messages
        assert history[0]["content"] == "Message 5"
        assert history[-1]["content"] == "Message 9"

    def test_get_history(self, session_manager):
        """测试获取会话历史"""
        # Arrange
        session_id = "test_session_010"
        session_manager.add_message(session_id, "user", "Message 1")
        session_manager.add_message(session_id, "assistant", "Response 1")
        
        # Act
        history = session_manager.get_history(session_id)
        
        # Assert
        assert len(history) == 2
        assert history[0]["content"] == "Message 1"
        assert history[1]["content"] == "Response 1"

    def test_get_history_nonexistent_session(self, session_manager):
        """测试获取不存在会话的历史"""
        # Arrange
        session_id = "test_session_011"
        
        # Act
        history = session_manager.get_history(session_id)
        
        # Assert - 应该返回空列表
        assert history == []

    def test_get_recent_history_default_limit(self, session_manager):
        """测试获取最近历史记录（默认限制10条）"""
        # Arrange
        session_id = "test_session_012"
        for i in range(15):
            session_manager.add_message(session_id, "user", f"Message {i}")
        
        # Act
        recent = session_manager.get_recent_history(session_id)
        
        # Assert - 应该返回所有可用的历史(受max_messages_per_session限制)
        assert len(recent) == 5  # 受max_messages_per_session=5限制
        assert recent[0]["content"] == "Message 10"
        assert recent[-1]["content"] == "Message 14"

    def test_get_recent_history_custom_limit(self, session_manager):
        """测试获取最近历史记录（自定义限制）"""
        # Arrange
        session_id = "test_session_013"
        for i in range(15):
            session_manager.add_message(session_id, "user", f"Message {i}")
        
        # Act
        recent = session_manager.get_recent_history(session_id, limit=5)
        
        # Assert
        assert len(recent) == 5
        assert recent[0]["content"] == "Message 10"
        assert recent[-1]["content"] == "Message 14"

    def test_get_recent_history_more_than_available(self, session_manager):
        """测试请求数量超过可用数量"""
        # Arrange
        session_id = "test_session_014"
        session_manager.add_message(session_id, "user", "Only one message")
        
        # Act
        recent = session_manager.get_recent_history(session_id, limit=10)
        
        # Assert - 应该返回所有可用的消息
        assert len(recent) == 1
        assert recent[0]["content"] == "Only one message"

    def test_eviction_disabled_when_under_limit(self, session_manager):
        """测试会话数量未超过限制时不驱逐"""
        # Arrange
        session_manager._max_sessions = 5
        session_sessions = []
        
        # Act - 创建5个会话（恰好达到限制）
        for i in range(5):
            sid = session_manager.get_or_create_session(f"session_{i}")
            session_sessions.append(sid)
        
        # Assert - 所有会话都应该存在
        assert len(session_manager.conversation_histories) == 5
        for sid in session_sessions:
            assert sid in session_manager.conversation_histories

    def test_eviction_activates_when_over_limit(self, session_manager):
        """测试会话数量超过限制时驱逐最旧的会话"""
        # Arrange
        session_manager._max_sessions = 3
        session_sessions = []
        
        # Act - 创建5个会话（超过限制）
        for i in range(5):
            sid = session_manager.get_or_create_session(f"session_{i}")
            session_sessions.append(sid)
            # 添加延迟以确保_last_seen时间戳不同
            time.sleep(0.1)
        
        # Assert - 应该只有3个会话存在（最新的3个）
        assert len(session_manager.conversation_histories) == 3
        # 最早的2个会话应该被驱逐
        assert session_sessions[0] not in session_manager.conversation_histories
        assert session_sessions[1] not in session_manager.conversation_histories
        # 最新的3个会话应该存在
        assert session_sessions[2] in session_manager.conversation_histories
        assert session_sessions[3] in session_manager.conversation_histories
        assert session_sessions[4] in session_manager.conversation_histories

    def test_eviction_updates_last_seen(self, session_manager):
        """测试会话访问更新最后访问时间"""
        # Arrange
        session_id = "test_session_015"
        session_manager.get_or_create_session(session_id)
        initial_time = session_manager._last_seen[session_id]
        
        # Act
        time.sleep(0.1)
        session_manager.get_or_create_session(session_id)
        updated_time = session_manager._last_seen[session_id]
        
        # Assert - 时间应该更新
        assert updated_time > initial_time

    def test_normalize_history_valid(self, session_manager):
        """测试规范化有效的历史记录"""
        # Arrange
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        # Act
        normalized = session_manager._normalize_history(history)
        
        # Assert
        assert len(normalized) == 2
        assert normalized[0]["role"] == "user"
        assert normalized[1]["role"] == "assistant"

    def test_normalize_history_empty_role(self, session_manager):
        """测试规范化包含空角色的历史记录"""
        # Arrange
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "", "content": "Should be filtered"},
            {"role": "assistant", "content": "Response"}
        ]
        
        # Act
        normalized = session_manager._normalize_history(history)
        
        # Assert
        assert len(normalized) == 2
        assert normalized[0]["role"] == "user"
        assert normalized[1]["role"] == "assistant"

    def test_normalize_history_invalid_role(self, session_manager):
        """测试规范化包含无效角色的历史记录"""
        # Arrange
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "system", "content": "Should be filtered"},
            {"role": "assistant", "content": "Response"}
        ]
        
        # Act
        normalized = session_manager._normalize_history(history)
        
        # Assert
        assert len(normalized) == 2
        assert all(msg["role"] in {"user", "assistant"} for msg in normalized)

    def test_normalize_history_empty_content(self, session_manager):
        """测试规范化包含空内容的历史记录"""
        # Arrange
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": ""},
            {"role": "user", "content": "World"}
        ]
        
        # Act
        normalized = session_manager._normalize_history(history)
        
        # Assert
        assert len(normalized) == 2
        assert all(msg["content"] for msg in normalized)

    def test_normalize_history_whitespace_role(self, session_manager):
        """测试规范化包含空白字符角色的历史记录"""
        # Arrange
        history = [
            {"role": "  user  ", "content": "Hello"},
            {"role": "\tASSISTANT\n", "content": "Response"}
        ]
        
        # Act
        normalized = session_manager._normalize_history(history)
        
        # Assert
        assert len(normalized) == 2
        assert normalized[0]["role"] == "user"
        assert normalized[1]["role"] == "assistant"

    def test_normalize_history_whitespace_content(self, session_manager):
        """测试规范化包含空白字符内容的历史记录"""
        # Arrange
        history = [
            {"role": "user", "content": "  Hello  "},
            {"role": "assistant", "content": " \t  \n  "}
        ]
        
        # Act
        normalized = session_manager._normalize_history(history)
        
        # Assert
        assert len(normalized) == 1
        assert normalized[0]["content"] == "Hello"

    def test_normalize_history_empty_list(self, session_manager):
        """测试规范化空列表"""
        # Act
        normalized = session_manager._normalize_history([])
        
        # Assert
        assert normalized == []

    def test_normalize_history_truncates_to_max(self, session_manager):
        """测试规范化时截断到最大消息数量"""
        # Arrange
        history = [{"role": "user", "content": f"Message {i}"} for i in range(10)]
        session_manager._max_messages_per_session = 5
        
        # Act
        normalized = session_manager._normalize_history(history)
        
        # Assert
        assert len(normalized) == 5
        assert normalized[0]["content"] == "Message 5"
        assert normalized[-1]["content"] == "Message 9"


class TestAIACorePublicAPI:
    """AICore公共API测试类"""

    def test_system_prompt_for_version_none(self):
        """测试未指定版本时返回默认提示词"""
        # Act
        prompt = AICore._system_prompt_for_version(None)
        
        # Assert
        assert "你是\"百姓法律助手\"的AI法律咨询员" in prompt
        assert prompt == AICore.SYSTEM_PROMPT

    def test_system_prompt_for_version_v1(self):
        """测试v1版本返回默认提示词"""
        # Act
        prompt = AICore._system_prompt_for_version("v1")
        
        # Assert
        assert prompt == AICore.SYSTEM_PROMPT

    def test_system_prompt_for_version_v2(self):
        """测试v2版本返回v2提示词"""
        # Act
        prompt = AICore._system_prompt_for_version("v2")
        
        # Assert
        assert prompt == AICore.SYSTEM_PROMPT_V2
        assert "输出优先级" in prompt
        assert "结论摘要" in prompt

    def test_system_prompt_for_version_2(self):
        """测试'2'版本返回v2提示词"""
        # Act
        prompt = AICore._system_prompt_for_version("2")
        
        # Assert
        assert prompt == AICore.SYSTEM_PROMPT_V2

    def test_system_prompt_for_version_beta(self):
        """测试'beta'版本返回v2提示词"""
        # Act
        prompt = AICore._system_prompt_for_version("beta")
        
        # Assert
        assert prompt == AICore.SYSTEM_PROMPT_V2

    def test_system_prompt_for_version_invalid(self):
        """测试无效版本返回默认提示词"""
        # Act
        prompt = AICore._system_prompt_for_version("invalid")
        
        # Assert
        assert prompt == AICore.SYSTEM_PROMPT

    def test_system_prompt_for_version_with_whitespace(self):
        """测试带空白字符的版本"""
        # Act
        prompt = AICore._system_prompt_for_version("  V2  ")
        
        # Assert
        assert prompt == AICore.SYSTEM_PROMPT_V2

    def test_encoding_for_model_valid(self):
        """测试获取有效模型的编码"""
        # Act
        enc = AICore._encoding_for_model("gpt-4")
        
        # Assert
        assert enc is not None
        assert hasattr(enc, 'encode')
        assert hasattr(enc, 'decode')

    def test_encoding_for_model_invalid(self):
        """测试获取无效模型的编码（回退到cl100k_base）"""
        # Act
        enc = AICore._encoding_for_model("invalid-model")
        
        # Assert
        assert enc is not None
        assert enc.name == "cl100k_base"

    def test_encoding_for_model_none(self):
        """测试None模型的编码（回退到cl100k_base）"""
        # Act
        enc = AICore._encoding_for_model(None)
        
        # Assert
        assert enc is not None
        assert enc.name == "cl100k_base"

    def test_encoding_for_model_empty_string(self):
        """测试空字符串模型的编码（回退到cl100k_base）"""
        # Act
        enc = AICore._encoding_for_model("")
        
        # Assert
        assert enc is not None
        assert enc.name == "cl100k_base"

    def test_encoding_for_model_gpt_4o(self):
        """测试gpt-4o模型的编码"""
        # Act
        enc = AICore._encoding_for_model("gpt-4o")
        
        # Assert
        assert enc is not None

    def test_count_tokens_empty_string(self):
        """测试空字符串的token计数"""
        # Act
        count = AICore._count_tokens("", model="gpt-4")
        
        # Assert
        assert count == 0

    def test_count_tokens_none(self):
        """测试None的token计数"""
        # Act
        count = AICore._count_tokens(None, model="gpt-4")
        
        # Assert
        assert count == 0

    def test_count_tokens_simple_text(self):
        """测试简单文本的token计数"""
        # Act
        count = AICore._count_tokens("Hello, world!", model="gpt-4")
        
        # Assert
        assert count > 0

    def test_count_tokens_chinese_text(self):
        """测试中文文本的token计数"""
        # Act
        count = AICore._count_tokens("你好，世界！", model="gpt-4")
        
        # Assert
        assert count > 0

    def test_count_tokens_mixed_text(self):
        """测试混合文本的token计数"""
        # Act
        count = AICore._count_tokens("Hello 你好！", model="gpt-4")
        
        # Assert
        assert count > 0

    def test_count_tokens_long_text(self):
        """测试长文本的token计数"""
        # Arrange
        text = "这是一段很长的文本。" * 100
        
        # Act
        count = AICore._count_tokens(text, model="gpt-4")
        
        # Assert
        assert count > 0
        assert count > 100  # 应该比100多

    def test_count_tokens_with_model(self):
        """测试指定模型的token计数"""
        # Act
        count = AICore._count_tokens("Hello", model="gpt-4")
        
        # Assert
        assert count > 0

    def test_estimate_cost_usd_none_model(self):
        """测试None模型的费用估算"""
        # Act
        cost = AICore._estimate_cost_usd(model=None, prompt_tokens=100, completion_tokens=100)
        
        # Assert
        assert cost is None

    def test_estimate_cost_usd_empty_model(self):
        """测试空模型名的费用估算"""
        # Act
        cost = AICore._estimate_cost_usd(model="", prompt_tokens=100, completion_tokens=100)
        
        # Assert
        assert cost is None

    def test_estimate_cost_usd_gpt_4o_mini(self):
        """测试gpt-4o-mini的费用估算"""
        # Arrange
        prompt_tokens = 1_000_000
        completion_tokens = 1_000_000
        
        # Act
        cost = AICore._estimate_cost_usd(
            model="gpt-4o-mini",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        # Assert
        assert cost is not None
        assert isinstance(cost, float)
        # gpt-4o-mini: (0.15 + 0.60) = 0.75 per 1M tokens
        expected = 0.15 + 0.60
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_usd_gpt_4o(self):
        """测试gpt-4o的费用估算"""
        # Arrange
        prompt_tokens = 1_000_000
        completion_tokens = 1_000_000
        
        # Act
        cost = AICore._estimate_cost_usd(
            model="gpt-4o",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        # Assert
        assert cost is not None
        # gpt-4o: (5.00 + 15.00) = 20.00 per 1M tokens
        expected = 5.00 + 15.00
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_usd_gpt_3_5_turbo(self):
        """测试gpt-3.5-turbo的费用估算"""
        # Arrange
        prompt_tokens = 1_000_000
        completion_tokens = 1_000_000
        
        # Act
        cost = AICore._estimate_cost_usd(
            model="gpt-3.5-turbo",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        # Assert
        assert cost is not None
        # gpt-3.5-turbo: (0.50 + 1.50) = 2.00 per 1M tokens
        expected = 0.50 + 1.50
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_usd_unknown_model(self):
        """测试未知模型的费用估算"""
        # Act
        cost = AICore._estimate_cost_usd(
            model="unknown-model",
            prompt_tokens=100,
            completion_tokens=100
        )
        
        # Assert
        assert cost is None

    def test_estimate_cost_usd_zero_tokens(self):
        """测试零token的费用估算"""
        # Act
        cost = AICore._estimate_cost_usd(
            model="gpt-4o-mini",
            prompt_tokens=0,
            completion_tokens=0
        )
        
        # Assert
        assert cost == 0.0

    def test_estimate_cost_usd_only_prompt(self):
        """测试只有prompt的费用估算"""
        # Act
        cost = AICore._estimate_cost_usd(
            model="gpt-4o-mini",
            prompt_tokens=1_000_000,
            completion_tokens=0
        )
        
        # Assert
        assert cost is not None
        expected = 0.15  # gpt-4o-mini prompt price
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_usd_only_completion(self):
        """测试只有completion的费用估算"""
        # Act
        cost = AICore._estimate_cost_usd(
            model="gpt-4o-mini",
            prompt_tokens=0,
            completion_tokens=1_000_000
        )
        
        # Assert
        assert cost is not None
        expected = 0.60  # gpt-4o-mini completion price
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_usd_fractional_tokens(self):
        """测试分数token的费用估算"""
        # Act
        cost = AICore._estimate_cost_usd(
            model="gpt-4o-mini",
            prompt_tokens=500_000,
            completion_tokens=500_000
        )
        
        # Assert
        assert cost is not None
        expected = (0.15 + 0.60) / 2
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_usd_case_insensitive(self):
        """测试模型名大小写不敏感"""
        result1 = AICore._estimate_cost_usd(
            model="gpt-4o-mini",
            prompt_tokens=1_000_000,
            completion_tokens=0
        )
        result2 = AICore._estimate_cost_usd(
            model="GPT-4O-MINI",
            prompt_tokens=1_000_000,
            completion_tokens=0
        )
        result3 = AICore._estimate_cost_usd(
            model="Gpt-4o-Mini",
            prompt_tokens=1_000_000,
            completion_tokens=0
        )
        
        assert result1 == result2 == result3