"""性能基准测试"""
import pytest
import asyncio
import time
from typing import List
from httpx import AsyncClient


class BenchmarkResult:
    """基准测试结果"""
    def __init__(self, name: str):
        self.name = name
        self.latencies: List[float] = []
        self.errors = 0
        self.start_time = None
        self.end_time = None

    def add_latency(self, latency: float):
        self.latencies.append(latency)

    def add_error(self):
        self.errors += 1

    @property
    def total_requests(self) -> int:
        return len(self.latencies) + self.errors

    @property
    def avg_latency(self) -> float:
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    @property
    def p50_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.5)
        return sorted_latencies[idx]

    @property
    def p95_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[idx]

    @property
    def p99_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[idx]

    @property
    def throughput(self) -> float:
        if not self.start_time or not self.end_time:
            return 0.0
        duration = self.end_time - self.start_time
        if duration == 0:
            return 0.0
        return len(self.latencies) / duration

    def report(self) -> dict:
        return {
            "name": self.name,
            "total_requests": self.total_requests,
            "successful": len(self.latencies),
            "errors": self.errors,
            "avg_latency_ms": round(self.avg_latency * 1000, 2),
            "p50_latency_ms": round(self.p50_latency * 1000, 2),
            "p95_latency_ms": round(self.p95_latency * 1000, 2),
            "p99_latency_ms": round(self.p99_latency * 1000, 2),
            "throughput_rps": round(self.throughput, 2),
        }


async def run_benchmark(
    client: AsyncClient,
    method: str,
    url: str,
    concurrency: int = 10,
    total_requests: int = 100,
    **kwargs
) -> BenchmarkResult:
    """运行基准测试"""
    result = BenchmarkResult(f"{method} {url}")
    result.start_time = time.time()

    async def make_request():
        try:
            start = time.time()
            response = await client.request(method, url, **kwargs)
            latency = time.time() - start
            if response.status_code < 500:
                result.add_latency(latency)
            else:
                result.add_error()
        except Exception:
            result.add_error()

    tasks = []
    for _ in range(total_requests):
        if len(tasks) >= concurrency:
            done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        tasks.append(asyncio.create_task(make_request()))

    if tasks:
        await asyncio.wait(tasks)

    result.end_time = time.time()
    return result


@pytest.mark.asyncio
async def test_health_endpoint_benchmark(client: AsyncClient):
    """健康检查端点基准测试"""
    result = await run_benchmark(client, "GET", "/health", concurrency=20, total_requests=100)
    report = result.report()
    print(f"\n{report}")
    assert result.errors == 0
    assert result.avg_latency < 0.1


@pytest.mark.asyncio
async def test_public_endpoints_benchmark(client: AsyncClient):
    """公开端点基准测试"""
    endpoints = [
        ("GET", "/api/v1/legal/lawyers/"),
        ("GET", "/api/v1/legal/firms/"),
    ]

    for method, url in endpoints:
        result = await run_benchmark(client, method, url, concurrency=10, total_requests=50)
        report = result.report()
        print(f"\n{report}")
        assert result.errors == 0


@pytest.mark.asyncio
async def test_concurrent_read_benchmark(client: AsyncClient):
    """并发读取基准测试"""
    result = await run_benchmark(
        client, "GET",
        "/api/v1/legal/lawyers/",
        concurrency=15,
        total_requests=60
    )
    report = result.report()
    print(f"\n{report}")
    assert result.avg_latency < 0.5


@pytest.mark.asyncio
async def test_authenticated_endpoint_benchmark(client: AsyncClient):
    """认证端点基准测试（需要token）"""
    headers = {"Authorization": "Bearer test-token"}

    result = await run_benchmark(
        client, "GET",
        "/api/v1/legal/consultations/",
        headers=headers,
        concurrency=10,
        total_requests=50
    )
    report = result.report()
    print(f"\n{report}")


@pytest.mark.asyncio
async def test_database_query_performance(client: AsyncClient):
    """数据库查询性能测试"""
    result = await run_benchmark(
        client, "GET",
        "/api/v1/legal/lawyers/?skip=0&limit=20",
        concurrency=10,
        total_requests=30
    )
    report = result.report()
    print(f"\n{report}")
    assert result.p95_latency < 1.0


@pytest.mark.asyncio
async def test_redis_cache_performance(client: AsyncClient):
    """Redis缓存性能测试（重复请求）"""
    url = "/api/v1/legal/lawyers/"

    warmup = await run_benchmark(client, "GET", url, concurrency=5, total_requests=10)
    print(f"\nWarmup: {warmup.report()}")

    cached = await run_benchmark(client, "GET", url, concurrency=10, total_requests=50)
    report = cached.report()
    print(f"Cached: {report}")

    if cached.avg_latency < warmup.avg_latency:
        print("Cache is working (subsequent requests faster)")


@pytest.mark.asyncio
async def test_endpoint_latency_distribution(client: AsyncClient):
    """端点延迟分布测试"""
    latencies = []
    for _ in range(20):
        start = time.time()
        response = await client.get("/api/v1/legal/lawyers/")
        latencies.append(time.time() - start)
        assert response.status_code == 200

    sorted_latencies = sorted(latencies)
    p50 = sorted_latencies[9]
    p95 = sorted_latencies[18]
    p99 = sorted_latencies[19]

    print(f"\nLatency distribution:")
    print(f"  p50: {p50*1000:.2f}ms")
    print(f"  p95: {p95*1000:.2f}ms")
    print(f"  p99: {p99*1000:.2f}ms")

    assert p99 < 1.0
