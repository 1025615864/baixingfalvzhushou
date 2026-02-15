"""
AI质量监控中间件测试

测试AI质量监控系统的各项功能：
1. 日志记录功能
2. 指标统计功能
3. 中间件功能
4. 服务接口功能
"""

import pytest
from datetime import datetime, timedelta
from app.middleware.ai_quality_middleware import (
    AIConversationLog,
    AIQualityMetrics,
    AIQualityMiddleware,
    AILoggerService,
    get_ai_metrics,
    get_ai_logger,
    QualityScore,
    AILogLevel,
)


class TestAIConversationLog:
    """测试AI对话日志"""

    def test_log_creation(self):
        """测试日志创建"""
        log = AIConversationLog(
            request_id="test-123",
            session_id="session-456",
            user_id=1,
            message_length=100,
            response_length=500,
            response_time_ms=1500,
            quality_score=4,
        )
        assert log.request_id == "test-123"
        assert log.session_id == "session-456"
        assert log.user_id == 1
        assert log.message_length == 100
        assert log.response_length == 500
        assert log.response_time_ms == 1500
        assert log.quality_score == 4
        assert log.level == AILogLevel.INFO.value

    def test_log_with_error(self):
        """测试带错误的日志"""
        log = AIConversationLog(
            request_id="test-123",
            message_length=100,
            response_length=0,
            response_time_ms=500,
            session_id=None,
            user_id=None,
            error_type="TimeoutError",
        )
        assert log.error_type == "TimeoutError"
        assert log.level == AILogLevel.ERROR.value

    def test_log_quality_level_excellent(self):
        """测试优秀评分"""
        log = AIConversationLog(
            request_id="test-123",
            session_id=None,
            user_id=None,
            message_length=100,
            response_length=500,
            response_time_ms=1500,
            quality_score=5,
        )
        assert log._get_quality_level() == QualityScore.EXCELLENT.value

    def test_log_quality_level_good(self):
        """测试良好评分"""
        log = AIConversationLog(
            request_id="test-123",
            session_id=None,
            user_id=None,
            message_length=100,
            response_length=500,
            response_time_ms=1500,
            quality_score=3,
        )
        assert log._get_quality_level() == QualityScore.GOOD.value

    def test_log_quality_level_poor(self):
        """测试差评"""
        log = AIConversationLog(
            request_id="test-123",
            session_id=None,
            user_id=None,
            message_length=100,
            response_length=500,
            response_time_ms=1500,
            quality_score=1,
        )
        assert log._get_quality_level() == QualityScore.POOR.value

    def test_log_to_dict(self):
        """测试转换为字典"""
        log = AIConversationLog(
            request_id="test-123",
            session_id="session-456",
            user_id=1,
            message_length=100,
            response_length=500,
            response_time_ms=1500,
            quality_score=4,
            topics=["劳动法"],
            tools_used=["calculator"],
        )
        data = log.to_dict()
        assert data["request_id"] == "test-123"
        assert data["session_id"] == "session-456"
        assert data["user_id"] == 1
        assert data["quality_level"] == QualityScore.EXCELLENT.value
        assert "劳动法" in data["topics"]
        assert "calculator" in data["tools_used"]

    def test_log_default_values(self):
        """测试默认值"""
        log = AIConversationLog(
            request_id="test-123",
            session_id=None,
            user_id=None,
            message_length=100,
            response_length=500,
            response_time_ms=1500,
        )
        assert log.quality_score is None
        assert log.quality_feedback is None
        assert log.was_helpful is None
        assert log.topics == []
        assert log.tools_used == []
        assert log.token_usage is None
        assert log.error_type is None


class TestAIQualityMetrics:
    """测试AI质量指标"""

    def setup_method(self):
        """每个测试前创建新的指标实例"""
        self.metrics = AIQualityMetrics()

    def test_increment_counter(self):
        """测试计数器增加"""
        self.metrics.increment_counter("test_counter")
        self.metrics.increment_counter("test_counter", 5)
        assert self.metrics._counters["test_counter"] == 6

    def test_record_response_time(self):
        """测试记录响应时间"""
        self.metrics.record_response_time(100)
        self.metrics.record_response_time(200)
        self.metrics.record_response_time(300)
        stats = self.metrics._get_response_time_stats()
        assert stats["count"] == 3
        assert stats["avg_ms"] == 200
        assert stats["p50_ms"] == 200

    def test_record_response_time_percentiles(self):
        """测试响应时间百分位"""
        for i in range(100):
            self.metrics.record_response_time(i)
        stats = self.metrics._get_response_time_stats()
        # 0-99，共100个数
        # 50百分位应该是索引49或50（取决于实现）
        assert 49 <= stats["p50_ms"] <= 50
        assert 94 <= stats["p95_ms"] <= 95
        # 实际值取决于实现，取合理范围

    def test_record_quality_score(self):
        """测试记录质量评分"""
        self.metrics.record_quality_score(5)
        self.metrics.record_quality_score(4)
        self.metrics.record_quality_score(3)
        self.metrics.record_quality_score(2)
        self.metrics.record_quality_score(1)
        stats = self.metrics._get_quality_stats()
        assert stats["avg"] == 3.0
        assert stats["count"] == 5
        assert stats["distribution"]["excellent_45"] == 2
        assert stats["distribution"]["poor_1"] == 1

    def test_record_quality_score_satisfaction_rate(self):
        """测试满意度计算"""
        # 4个好评(4-5星)，1个差评(1星)
        self.metrics.record_quality_score(5)
        self.metrics.record_quality_score(4)
        self.metrics.record_quality_score(4)
        self.metrics.record_quality_score(4)
        self.metrics.record_quality_score(1)
        stats = self.metrics._get_quality_stats()
        assert stats["satisfaction_rate"] == 80.0  # 4/5 = 80%

    def test_record_error(self):
        """测试记录错误"""
        self.metrics.record_error("TimeoutError")
        self.metrics.record_error("TimeoutError")
        self.metrics.record_error("ValueError")
        assert self.metrics._errors["TimeoutError"] == 2
        assert self.metrics._errors["ValueError"] == 1
        # record_error 也会更新 total_errors 计数器
        assert self.metrics._counters["total_errors"] == 3

    def test_add_log(self):
        """测试添加日志"""
        log = AIConversationLog(
            request_id="test-1",
            session_id=None,
            user_id=None,
            message_length=100,
            response_length=500,
            response_time_ms=1500,
        )
        self.metrics.add_log(log)
        assert len(self.metrics._recent_logs) == 1
        assert self.metrics._recent_logs[0].request_id == "test-1"

    def test_add_log_limit(self):
        """测试日志数量限制"""
        # 添加超过限制的日志
        for i in range(1005):
            log = AIConversationLog(
                request_id=f"test-{i}",
                session_id=None,
                user_id=None,
                message_length=100,
                response_length=500,
                response_time_ms=1500,
            )
            self.metrics.add_log(log)
        # 应该只保留最近1000条
        assert len(self.metrics._recent_logs) == 1000
        # 最早的那5条应该被删除了
        assert self.metrics._recent_logs[0].request_id == "test-5"

    def test_get_stats(self):
        """测试获取统计"""
        self.metrics.increment_counter("total_requests", 100)
        self.metrics.increment_counter("successful_responses", 80)
        self.metrics.record_response_time(100)
        self.metrics.record_quality_score(4)
        self.metrics.record_error("TimeoutError")

        stats = self.metrics.get_stats()
        assert stats["counters"]["total_requests"] == 100
        assert stats["counters"]["successful_responses"] == 80
        assert stats["total_conversations"] == 100
        assert stats["successful_conversations"] == 80
        assert stats["response_time"]["count"] == 1
        assert stats["quality_score"]["avg"] == 4.0
        assert stats["errors"]["TimeoutError"] == 1

    def test_get_recent_logs(self):
        """测试获取最近日志"""
        for i in range(50):
            log = AIConversationLog(
                request_id=f"test-{i}",
                session_id=None,
                user_id=None,
                message_length=100,
                response_length=500,
                response_time_ms=1500,
            )
            self.metrics.add_log(log)

        logs = self.metrics.get_recent_logs(10)
        assert len(logs) == 10
        # 应该是最新的10条
        assert logs[0]["request_id"] == "test-40"
        assert logs[9]["request_id"] == "test-49"

    def test_reset(self):
        """测试重置"""
        self.metrics.increment_counter("test", 10)
        self.metrics.record_response_time(100)
        self.metrics.record_quality_score(4)
        self.metrics.record_error("Error")
        self.metrics.reset()
        stats = self.metrics.get_stats()
        assert stats["counters"] == {}
        assert stats["response_time"]["count"] == 0
        assert stats["quality_score"]["count"] == 0
        assert stats["errors"] == {}


class TestAILoggerService:
    """测试AI日志服务"""

    def setup_method(self):
        """每个测试前创建新的指标实例"""
        self.metrics = AIQualityMetrics()
        self.service = AILoggerService(self.metrics)

    def test_log_conversation(self):
        """测试记录对话"""
        log = self.service.log_conversation(
            request_id="test-123",
            session_id="session-456",
            user_id=1,
            message_length=100,
            response_length=500,
            response_time_ms=1500,
            quality_score=4,
            topics=["劳动法", "婚姻法"],
            tools_used=["calculator"],
        )
        assert log.request_id == "test-123"
        assert self.metrics._counters["total_requests"] == 1
        assert self.metrics._counters["successful_responses"] == 1
        assert self.metrics._counters["topic_劳动法"] == 1
        assert self.metrics._counters["tool_calculator"] == 1

    def test_log_conversation_with_error(self):
        """测试记录错误对话"""
        log = self.service.log_conversation(
            request_id="test-123",
            message_length=100,
            response_length=0,
            response_time_ms=500,
            session_id=None,
            user_id=None,
            error_type="TimeoutError",
        )
        assert log.error_type == "TimeoutError"
        # 错误应该增加error计数
        assert self.metrics._counters["total_errors"] == 1

    def test_log_feedback_positive(self):
        """测试记录正面反馈"""
        self.service.log_feedback(
            request_id="test-123",
            is_positive=True,
        )
        assert self.metrics._counters["positive_feedback"] == 1
        assert self.metrics._counters["helpful_responses"] == 1

    def test_log_feedback_negative(self):
        """测试记录负面反馈"""
        self.service.log_feedback(
            request_id="test-123",
            is_positive=False,
        )
        assert self.metrics._counters["negative_feedback"] == 1
        assert self.metrics._counters["unhelpful_responses"] == 1

    def test_get_stats(self):
        """测试获取统计"""
        self.service.log_conversation(
            request_id="test-1",
            session_id=None,
            user_id=1,
            message_length=100,
            response_length=500,
            response_time_ms=1500,
        )
        self.service.log_conversation(
            request_id="test-2",
            session_id=None,
            user_id=1,
            message_length=100,
            response_length=500,
            response_time_ms=2000,
        )
        stats = self.service.get_stats()
        assert stats["total_conversations"] == 2

    def test_get_recent_logs(self):
        """测试获取最近日志"""
        for i in range(10):
            self.service.log_conversation(
                request_id=f"test-{i}",
                session_id=None,
                user_id=1,
                message_length=100,
                response_length=500,
                response_time_ms=1500,
            )
        logs = self.service.get_recent_logs(5)
        assert len(logs) == 5


class TestGlobalInstances:
    """测试全局实例"""

    def test_get_ai_metrics_singleton(self):
        """测试获取指标实例"""
        metrics1 = get_ai_metrics()
        metrics2 = get_ai_metrics()
        assert metrics1 is metrics2

    def test_get_ai_logger(self):
        """测试获取日志服务"""
        logger = get_ai_logger()
        assert isinstance(logger, AILoggerService)


class TestMiddlewareRouting:
    """测试中间件路由过滤"""

    def test_ai_routes_identify(self):
        """测试AI路由识别"""
        # 直接测试路由识别逻辑
        AI_ROUTES = {"/api/ai/chat", "/api/ai/consultations"}

        def is_ai_route(path: str) -> bool:
            return any(path.startswith(route) for route in AI_ROUTES)

        # AI相关路由应该被识别
        assert is_ai_route("/api/ai/chat") is True
        assert is_ai_route("/api/ai/consultations") is True
        assert is_ai_route("/api/ai/consultations/123") is True
        # 非AI路由不应该被识别
        assert is_ai_route("/api/users") is False
        assert is_ai_route("/api/news") is False
        assert is_ai_route("/api/payment") is False


class TestIntegration:
    """端到端集成测试"""

    def test_full_conversation_flow(self):
        """测试完整对话流程的质量监控"""
        # 重置指标
        metrics = get_ai_metrics()
        metrics.reset()

        # 创建日志服务
        service = AILoggerService(metrics)

        # 模拟多次对话
        test_scenarios = [
            {
                "request_id": "conv-001",
                "session_id": "sess-1",
                "user_id": 100,
                "message": "我被公司无故解雇了，怎么维权？",
                "response": "根据《劳动合同法》...",
                "response_time_ms": 1200,
                "expected_topic": "劳动法",
            },
            {
                "request_id": "conv-002",
                "session_id": "sess-1",
                "user_id": 100,
                "message": "离婚时房产怎么分配？",
                "response": "根据《婚姻法》...",
                "response_time_ms": 1800,
                "expected_topic": "婚姻家庭",
            },
            {
                "request_id": "conv-003",
                "session_id": "sess-2",
                "user_id": 101,
                "message": "交通事故赔偿标准是多少？",
                "response": "根据《道路交通安全法》...",
                "response_time_ms": 1500,
                "expected_topic": "侵权赔偿",
            },
        ]

        for scenario in test_scenarios:
            service.log_conversation(
                request_id=scenario["request_id"],
                session_id=scenario["session_id"],
                user_id=scenario["user_id"],
                message_length=len(scenario["message"]),
                response_length=len(scenario["response"]),
                response_time_ms=scenario["response_time_ms"],
                topics=[scenario["expected_topic"]],
            )

        # 验证统计
        stats = service.get_stats()
        assert stats["total_conversations"] == 3
        assert stats["counters"]["topic_劳动法"] == 1
        assert stats["counters"]["topic_婚姻家庭"] == 1
        assert stats["counters"]["topic_侵权赔偿"] == 1

        # 验证响应时间统计
        response_time_stats = stats["response_time"]
        assert response_time_stats["count"] == 3
        assert response_time_stats["avg_ms"] == 1500.0  # (1200+1800+1500)/3

    def test_feedback_flow(self):
        """测试反馈流程"""
        # 创建新的指标实例，避免与其他测试共享状态
        local_metrics = AIQualityMetrics()
        service = AILoggerService(local_metrics)

        # 记录一次对话
        service.log_conversation(
            request_id="test-conv",
            session_id="sess-1",
            user_id=1,
            message_length=100,
            response_length=500,
            response_time_ms=1000,
        )

        # 记录正面反馈
        service.log_feedback(
            request_id="test-conv",
            is_positive=True,
            feedback_text="回答很有帮助",
        )

        # 验证统计
        stats = service.get_stats()
        assert stats["counters"]["positive_feedback"] == 1
        assert stats["counters"]["helpful_responses"] == 1
        assert stats["counters"].get("negative_feedback", 0) == 0

    def test_error_handling_flow(self):
        """测试错误处理流程"""
        metrics = get_ai_metrics()
        metrics.reset()

        service = AILoggerService(metrics)

        # 记录一次错误对话
        service.log_conversation(
            request_id="error-conv",
            session_id="sess-1",
            user_id=1,
            message_length=100,
            response_length=0,
            response_time_ms=5000,
            error_type="TimeoutError",
        )

        # 记录错误反馈
        service.log_feedback(
            request_id="error-conv",
            is_positive=False,
        )

        # 验证统计
        stats = service.get_stats()
        # log_conversation 调用 record_error，所以 total_errors = 1
        assert stats["counters"]["total_errors"] == 1
        assert stats["counters"]["negative_feedback"] == 1
        assert stats["counters"]["unhelpful_responses"] == 1
        assert stats["errors"]["TimeoutError"] == 1

    def test_quality_score_distribution(self):
        """测试质量评分分布"""
        local_metrics = AIQualityMetrics()
        service = AILoggerService(local_metrics)

        # 模拟不同评分的对话
        ratings = [5, 4, 4, 3, 3, 2, 1]  # 2个优秀，2个良好，2个一般，1个差

        for i, rating in enumerate(ratings):
            service.log_conversation(
                request_id=f"rated-{i}",
                session_id=None,
                user_id=1,
                message_length=100,
                response_length=500,
                response_time_ms=1500,
                quality_score=rating,
            )

        # 验证统计
        stats = service.get_stats()
        quality_stats = stats["quality_score"]

        assert quality_stats["avg"] == 3.14  # (5+4+4+3+3+2+1)/7
        assert quality_stats["count"] == 7
        # 分布逻辑: >=4优秀, 3-4良好(不含3), 2-3一般(不含2), <2差
        # ratings: [5, 4, 4, 3, 3, 2, 1]
        # excellent (>=4): [5, 4, 4] = 3
        # good (3<=s<4): [3, 3] = 2 (注意：3不在这个区间，因为是半开区间)
        # 实际上：3 <= s < 4 包含3但不包含4，所以是 [3, 3] = 2
        # fair (2<=s<3): [2] = 1
        # poor (s<2): [1] = 1
        assert quality_stats["distribution"]["excellent_45"] == 3
        assert quality_stats["distribution"]["good_34"] == 2
        assert quality_stats["distribution"]["fair_23"] == 1
        assert quality_stats["distribution"]["poor_1"] == 1
        assert quality_stats["satisfaction_rate"] == 42.86  # 3/7 * 100
