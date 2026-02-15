"""
AI质量监控负载测试

测试AI质量监控系统在高并发场景下的性能表现
"""

import asyncio
import time
import pytest
from app.middleware.ai_quality_middleware import (
    AIQualityMetrics,
    AILoggerService,
    AIConversationLog,
)


class TestAILoadPerformance:
    """AI质量监控性能测试"""

    @pytest.fixture
    def metrics(self):
        """创建指标实例"""
        return AIQualityMetrics()

    @pytest.fixture
    def logger_service(self, metrics):
        """创建日志服务"""
        return AILoggerService(metrics)

    def test_high_throughput_counter(self, metrics):
        """测试高吞吐量计数器性能"""
        start = time.perf_counter()

        # 模拟高并发场景：10000次计数器操作
        for i in range(10000):
            metrics.increment_counter(f"request_{i % 100}")

        elapsed = time.perf_counter() - start

        # 验证结果
        assert metrics._counters["request_0"] == 100  # 每100次出现一次

        # 性能要求：10000次操作应该在1秒内完成
        assert elapsed < 1.0, f"Counter throughput too slow: {elapsed:.2f}s for 10000 ops"
        print(f"Counter throughput: {10000 / elapsed:.0f} ops/sec")

    def test_high_throughput_response_time(self, metrics):
        """测试高吞吐量响应时间记录性能"""
        start = time.perf_counter()

        # 模拟高并发场景：10000次响应时间记录
        for i in range(10000):
            metrics.record_response_time(100 + i % 100)

        elapsed = time.perf_counter() - start

        # 验证结果
        assert len(metrics._response_times) == 10000

        # 性能要求：10000次操作应该在1秒内完成
        assert elapsed < 1.0, f"Response time recording too slow: {elapsed:.2f}s for 10000 ops"
        print(f"Response time throughput: {10000 / elapsed:.0f} ops/sec")

    def test_high_throughput_quality_score(self, metrics):
        """测试高吞吐量质量评分记录性能"""
        start = time.perf_counter()

        # 模拟高并发场景：10000次质量评分记录
        for i in range(10000):
            metrics.record_quality_score((i % 5) + 1)

        elapsed = time.perf_counter() - start

        # 验证结果
        assert len(metrics._quality_scores) == 10000

        # 性能要求：10000次操作应该在1秒内完成
        assert elapsed < 1.0, f"Quality score recording too slow: {elapsed:.2f}s for 10000 ops"
        print(f"Quality score throughput: {10000 / elapsed:.0f} ops/sec")

    def test_concurrent_logging(self, logger_service):
        """测试并发日志记录性能"""
        start = time.perf_counter()

        # 并发记录10000条日志
        logs = []
        for i in range(10000):
            log = logger_service.log_conversation(
                request_id=f"req-{i}",
                session_id=f"sess-{i % 100}",
                user_id=i % 1000,
                message_length=100,
                response_length=500,
                response_time_ms=100 + i % 100,
                topics=["劳动法"],
                tools_used=["calculator"],
            )
            logs.append(log)

        elapsed = time.perf_counter() - start

        # 验证结果
        # recent_logs 最大限制为 1000
        recent_logs = logger_service.get_recent_logs(10000)
        assert len(recent_logs) == 1000  # 受限于 max_recent_logs = 1000

        # 性能要求：10000次日志记录应该在2秒内完成
        assert elapsed < 2.0, f"Concurrent logging too slow: {elapsed:.2f}s for 10000 logs"
        print(f"Concurrent logging throughput: {10000 / elapsed:.0f} logs/sec")

    def test_get_stats_performance(self, logger_service):
        """测试获取统计信息的性能"""
        # 先记录一些数据
        for i in range(1000):
            logger_service.log_conversation(
                request_id=f"req-{i}",
                session_id=None,
                user_id=i % 100,
                message_length=100,
                response_length=500,
                response_time_ms=100 + i % 100,
                quality_score=(i % 5) + 1,
                topics=["劳动法"],
                tools_used=["calculator"],
            )

        start = time.perf_counter()

        # 并发获取统计信息
        for _ in range(100):
            stats = logger_service.get_stats()

        elapsed = time.perf_counter() - start

        # 验证结果
        assert stats["total_conversations"] == 1000

        # 性能要求：100次统计查询应该在0.5秒内完成
        assert elapsed < 0.5, f"Get stats too slow: {elapsed:.2f}s for 100 queries"
        print(f"Get stats throughput: {100 / elapsed:.0f} queries/sec")

    def test_memory_usage(self, metrics):
        """测试内存使用情况"""
        import sys

        initial_size = sys.getsizeof(metrics._counters)
        initial_counters_size = sys.getsizeof(metrics._counters)
        initial_times_size = sys.getsizeof(metrics._response_times)
        initial_scores_size = sys.getsizeof(metrics._quality_scores)

        # 添加大量数据
        for i in range(10000):
            metrics.increment_counter(f"key_{i}")
            metrics.record_response_time(100 + i)
            metrics.record_quality_score((i % 5) + 1)

        final_size = sys.getsizeof(metrics._counters)
        final_counters_size = sys.getsizeof(metrics._counters)
        final_times_size = sys.getsizeof(metrics._response_times)
        final_scores_size = sys.getsizeof(metrics._quality_scores)

        # 验证数据已添加
        assert len(metrics._counters) == 10000
        assert len(metrics._response_times) == 10000
        assert len(metrics._quality_scores) == 10000

        # 内存增长应该在合理范围内
        counters_growth = final_counters_size - initial_counters_size
        times_growth = final_times_size - initial_times_size
        scores_growth = final_scores_size - initial_scores_size

        print(f"Counters memory growth: {counters_growth / 1024:.2f} KB")
        print(f"Response times memory growth: {times_growth / 1024:.2f} KB")
        print(f"Quality scores memory growth: {scores_growth / 1024:.2f} KB")

        # 内存增长应该在合理范围内（每个元素大约8字节）
        assert counters_growth < 500 * 1024, "Counters memory growth too high"
        assert times_growth < 500 * 1024, "Response times memory growth too high"
        assert scores_growth < 500 * 1024, "Quality scores memory growth too high"

    def test_burst_traffic_simulation(self, logger_service):
        """模拟突发流量场景"""
        # 模拟100个并发用户，每个用户发送100条消息
        num_users = 100
        messages_per_user = 100

        start = time.perf_counter()

        # 使用asyncio模拟并发
        async def simulate_user(user_id: int):
            for i in range(messages_per_user):
                logger_service.log_conversation(
                    request_id=f"user-{user_id}-msg-{i}",
                    session_id=f"session-{user_id}",
                    user_id=user_id,
                    message_length=100,
                    response_length=500,
                    response_time_ms=100,
                    quality_score=4,
                    topics=["劳动法"],
                    tools_used=["calculator"],
                )

        # 并发执行所有用户的模拟
        async def run_all_users():
            tasks = [simulate_user(i) for i in range(num_users)]
            await asyncio.gather(*tasks)

        asyncio.run(run_all_users())

        elapsed = time.perf_counter() - start

        # 验证结果
        total_messages = num_users * messages_per_user
        stats = logger_service.get_stats()

        assert stats["total_conversations"] == total_messages

        # 性能要求：10000条消息应该在5秒内处理完成
        assert elapsed < 5.0, f"Burst traffic too slow: {elapsed:.2f}s for {total_messages} messages"
        print(f"Burst traffic: {total_messages} messages in {elapsed:.2f}s ({total_messages / elapsed:.0f} msgs/sec)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
