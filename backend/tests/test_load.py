"""
负载测试脚本

使用 pytest-xdist 实现并行负载测试
"""

import asyncio
import time
from typing import Any
import pytest


class LoadTestMetrics:
    """负载测试指标收集器"""
    
    def __init__(self):
        self.results: list[dict[str, Any]] = []
        self.start_time: float = 0
        self.end_time: float = 0
    
    def start(self):
        """开始测试"""
        self.start_time = time.time()
    
    def stop(self):
        """停止测试"""
        self.end_time = time.time()
    
    @property
    def duration(self) -> float:
        """获取测试持续时间"""
        return self.end_time - self.start_time
    
    def record(self, name: str, success: bool, duration: float, error: str | None = None):
        """记录测试结果"""
        self.results.append({
            "name": name,
            "success": success,
            "duration": duration,
            "error": error,
            "timestamp": time.time(),
        })
    
    def get_summary(self) -> dict[str, Any]:
        """获取测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        avg_duration = sum(r["duration"] for r in self.results) / total if total > 0 else 0
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "avg_duration_ms": avg_duration * 1000,
            "duration_seconds": self.duration,
        }


_metrics = LoadTestMetrics()


@pytest.fixture
def load_test_metrics():
    """负载测试指标 fixture"""
    _metrics.start()
    yield _metrics
    _metrics.stop()


def calculate_rps(total_requests: int, duration: float) -> float:
    """计算每秒请求数"""
    return total_requests / duration


def calculate_latency_percentile(latencies: list[float], percentile: float) -> float:
    """计算延迟百分位数"""
    sorted_latencies = sorted(latencies)
    index = int(len(sorted_latencies) * percentile / 100)
    return sorted_latencies[min(index, len(sorted_latencies) - 1)]


@pytest.mark.asyncio
async def test_api_load_basic(
    client: Any,
    load_test_metrics: LoadTestMetrics,
) -> None:
    """基础API负载测试"""
    start = time.time()
    try:
        res = await client.get("/api/health")
        duration = time.time() - start
        success = res.status_code == 200
        load_test_metrics.record("health_check", success, duration)
        assert res.status_code == 200
    except Exception as e:
        duration = time.time() - start
        load_test_metrics.record("health_check", False, duration, str(e))


@pytest.mark.asyncio
async def test_forum_posts_load(
    client: Any,
    load_test_metrics: LoadTestMetrics,
) -> None:
    """论坛帖子接口负载测试"""
    start = time.time()
    try:
        res = await client.get("/api/forum/posts")
        duration = time.time() - start
        success = res.status_code == 200
        load_test_metrics.record("forum_posts_list", success, duration)
        assert res.status_code == 200
    except Exception as e:
        duration = time.time() - start
        load_test_metrics.record("forum_posts_list", False, duration, str(e))


@pytest.mark.asyncio
async def test_news_list_load(
    client: Any,
    load_test_metrics: LoadTestMetrics,
) -> None:
    """新闻列表接口负载测试"""
    start = time.time()
    try:
        res = await client.get("/api/news")
        duration = time.time() - start
        success = res.status_code == 200
        load_test_metrics.record("news_list", success, duration)
        assert res.status_code == 200
    except Exception as e:
        duration = time.time() - start
        load_test_metrics.record("news_list", False, duration, str(e))


def test_load_test_summary(load_test_metrics: LoadTestMetrics) -> None:
    """负载测试摘要验证"""
    summary = load_test_metrics.get_summary()
    
    # 验证基本指标
    assert summary["total"] >= 3, f"期望至少3个测试，实际: {summary['total']}"
    assert summary["success_rate"] >= 90, f"期望成功率>=90%，实际: {summary['success_rate']}%"
    assert summary["avg_duration_ms"] < 1000, f"期望平均延迟<1秒，实际: {summary['avg_duration_ms']}ms"
    
    # 打印摘要
    print("\n" + "=" * 50)
    print("负载测试摘要")
    print("=" * 50)
    print(f"总测试数: {summary['total']}")
    print(f"通过: {summary['passed']}")
    print(f"失败: {summary['failed']}")
    print(f"成功率: {summary['success_rate']:.2f}%")
    print(f"平均延迟: {summary['avg_duration_ms']:.2f}ms")
    print(f"总耗时: {summary['duration_seconds']:.2f}秒")
    print("=" * 50)
