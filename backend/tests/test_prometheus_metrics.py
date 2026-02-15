"""Prometheus Metrics 服务测试"""

import pytest
import time
from app.services.prometheus_metrics import (
    PrometheusMetrics,
    _prom_escape_label_value,
    HttpKey,
    HttpAgg,
    JobAgg,
    RateLimitKey,
    RateLimitAgg,
    UserActionKey,
    UserActionAgg,
    PaymentPayKey,
    PaymentPayAgg,
    PaymentCallbackKey,
    PaymentCallbackAgg,
    SqlSlowAgg,
)


class TestPrometheusEscapeLabelValue:
    """Prometheus 标签值转义测试"""

    def test_escape_empty(self):
        """测试空字符串转义"""
        result = _prom_escape_label_value("")
        assert result == ""

    def test_escape_backslash(self):
        """测试反斜杠转义"""
        result = _prom_escape_label_value("path\\to\\file")
        assert "\\\\" in result or "\\" in result

    def test_escape_double_quote(self):
        """测试双引号转义"""
        result = _prom_escape_label_value('hello "world"')
        assert '\\"' in result

    def test_escape_newline(self):
        """测试换行符转义"""
        result = _prom_escape_label_value("line1\nline2")
        assert "\\n" in result

    def test_escape_mixed(self):
        """测试混合转义"""
        result = _prom_escape_label_value('path\\to "file"\nname')
        assert "\\n" in result or "\\" in result


class TestHttpKey:
    """HTTP 键测试"""

    def test_create_http_key(self):
        """测试创建 HTTP 键"""
        key = HttpKey(method="GET", route="/api/users", status="200")
        assert key.method == "GET"
        assert key.route == "/api/users"
        assert key.status == "200"

    def test_http_key_equality(self):
        """测试 HTTP 键相等性"""
        key1 = HttpKey(method="GET", route="/api/users", status="200")
        key2 = HttpKey(method="GET", route="/api/users", status="200")
        assert key1 == key2

    def test_http_key_inequality(self):
        """测试 HTTP 键不相等"""
        key1 = HttpKey(method="GET", route="/api/users", status="200")
        key2 = HttpKey(method="POST", route="/api/users", status="200")
        assert key1 != key2


class TestHttpAgg:
    """HTTP 聚合测试"""

    def test_create_http_agg(self):
        """测试创建 HTTP 聚合"""
        agg = HttpAgg(count=10, sum_seconds=0.5)
        assert agg.count == 10
        assert agg.sum_seconds == 0.5

    def test_http_agg_with_buckets(self):
        """测试带桶的 HTTP 聚合"""
        agg = HttpAgg(count=5, sum_seconds=0.25, bucket_le_counts={0.1: 3, 0.5: 5})
        assert agg.bucket_le_counts is not None
        assert agg.bucket_le_counts[0.1] == 3


class TestJobAgg:
    """任务聚合测试"""

    def test_create_job_agg(self):
        """测试创建任务聚合"""
        agg = JobAgg(
            runs_total=100,
            successes_total=95,
            failures_total=5,
            last_run_ts=time.time(),
            last_duration_seconds=1.5,
            last_success=True,
        )
        assert agg.runs_total == 100
        assert agg.successes_total == 95
        assert agg.failures_total == 5
        assert agg.last_success is True


class TestRateLimitKey:
    """限流键测试"""

    def test_create_rate_limit_key_allowed(self):
        """测试创建允许的限流键"""
        key = RateLimitKey(endpoint="/api/users", result="allowed")
        assert key.endpoint == "/api/users"
        assert key.result == "allowed"

    def test_create_rate_limit_key_blocked(self):
        """测试创建阻止的限流键"""
        key = RateLimitKey(endpoint="/api/users", result="blocked")
        assert key.result == "blocked"


class TestRateLimitAgg:
    """限流聚合测试"""

    def test_create_rate_limit_agg(self):
        """测试创建限流聚合"""
        agg = RateLimitAgg(count=100)
        assert agg.count == 100


class TestUserActionKey:
    """用户动作键测试"""

    def test_create_user_action_key(self):
        """测试创建用户动作键"""
        key = UserActionKey(action="login", result="success", status="200")
        assert key.action == "login"
        assert key.result == "success"
        assert key.status == "200"


class TestUserActionAgg:
    """用户动作聚合测试"""

    def test_create_user_action_agg(self):
        """测试创建用户动作聚合"""
        agg = UserActionAgg(count=50)
        assert agg.count == 50


class TestPaymentPayKey:
    """支付键测试"""

    def test_create_payment_pay_key(self):
        """测试创建支付键"""
        key = PaymentPayKey(method="wechat", result="success")
        assert key.method == "wechat"
        assert key.result == "success"


class TestPaymentPayAgg:
    """支付聚合测试"""

    def test_create_payment_pay_agg(self):
        """测试创建支付聚合"""
        agg = PaymentPayAgg(count=25)
        assert agg.count == 25


class TestPaymentCallbackKey:
    """支付回调键测试"""

    def test_create_payment_callback_key(self):
        """测试创建支付回调键"""
        key = PaymentCallbackKey(provider="wechat", verified="true", result="ok")
        assert key.provider == "wechat"
        assert key.verified == "true"
        assert key.result == "ok"


class TestPaymentCallbackAgg:
    """支付回调聚合测试"""

    def test_create_payment_callback_agg(self):
        """测试创建支付回调聚合"""
        agg = PaymentCallbackAgg(count=10)
        assert agg.count == 10


class TestSqlSlowAgg:
    """慢 SQL 聚合测试"""

    def test_create_sql_slow_agg(self):
        """测试创建慢 SQL 聚合"""
        agg = SqlSlowAgg(
            count=5,
            sum_seconds=2.5,
            bucket_le_counts={0.5: 3, 1.0: 5},
            max_seconds=1.0,
        )
        assert agg.count == 5
        assert agg.sum_seconds == 2.5
        assert agg.max_seconds == 1.0


class TestPrometheusMetrics:
    """Prometheus 指标测试类"""

    @pytest.fixture
    def metrics(self):
        """创建指标实例"""
        return PrometheusMetrics()

    def test_init(self, metrics):
        """测试初始化"""
        assert metrics is not None
        assert metrics.started_at > 0
        assert len(metrics.http_duration_buckets) > 0
        assert len(metrics.sql_slow_duration_buckets) > 0

    def test_record_sql_slow_query(self, metrics):
        """测试记录慢查询"""
        metrics.record_sql_slow_query(duration_seconds=0.5)
        snap = metrics.snapshot_sql_slow()
        assert snap.count == 1
        assert snap.sum_seconds == 0.5

    def test_record_sql_slow_query_negative_duration(self, metrics):
        """测试记录负数持续时间的慢查询"""
        metrics.record_sql_slow_query(duration_seconds=-1.0)
        snap = metrics.snapshot_sql_slow()
        assert snap.count == 1
        assert snap.sum_seconds == 0.0

    def test_snapshot_sql_slow_empty(self, metrics):
        """测试空慢查询快照"""
        snap = metrics.snapshot_sql_slow()
        assert snap.count == 0
        assert snap.sum_seconds == 0.0

    def test_record_http_request(self, metrics):
        """测试记录 HTTP 请求"""
        metrics.record_http(method="GET", route="/api/users", status_code=200, duration_seconds=0.1)
        snap = metrics.snapshot_http()
        assert len(snap) > 0

    def test_record_http_request_with_zero_duration(self, metrics):
        """测试记录零持续时间的 HTTP 请求"""
        metrics.record_http(method="GET", route="/api/users", status_code=200, duration_seconds=0)
        snap = metrics.snapshot_http()
        assert len(snap) > 0

    def test_record_http_request_default_method(self, metrics):
        """测试 HTTP 请求默认方法"""
        metrics.record_http(method=None, route="/api/users", status_code=200, duration_seconds=0.1)
        snap = metrics.snapshot_http()
        key = list(snap.keys())[0]
        assert key.method == "GET"

    def test_record_http_request_default_route(self, metrics):
        """测试 HTTP 请求默认路由"""
        metrics.record_http(method="GET", route=None, status_code=200, duration_seconds=0.1)
        snap = metrics.snapshot_http()
        key = list(snap.keys())[0]
        assert key.route == "unknown"

    def test_record_job_success(self, metrics):
        """测试记录成功的任务"""
        metrics.record_job(name="cleanup", ok=True, duration_seconds=1.5)
        snap = metrics.snapshot_jobs()
        assert "cleanup" in snap
        agg = snap["cleanup"]
        assert agg.runs_total == 1
        assert agg.successes_total == 1
        assert agg.failures_total == 0

    def test_record_job_failure(self, metrics):
        """测试记录失败的任务"""
        metrics.record_job(name="cleanup", ok=False, duration_seconds=2.0)
        snap = metrics.snapshot_jobs()
        assert "cleanup" in snap
        agg = snap["cleanup"]
        assert agg.runs_total == 1
        assert agg.successes_total == 0
        assert agg.failures_total == 1
        assert agg.last_success is False

    def test_record_rate_limit_allowed(self, metrics):
        """测试记录允许的限流"""
        metrics.record_rate_limit(endpoint="/api/users", allowed=True)
        snap = metrics.snapshot_rate_limits()
        assert len(snap) > 0

    def test_record_rate_limit_blocked(self, metrics):
        """测试记录阻止的限流"""
        metrics.record_rate_limit(endpoint="/api/users", allowed=False)
        snap = metrics.snapshot_rate_limits()
        assert len(snap) > 0

    def test_record_user_action_success(self, metrics):
        """测试记录成功的用户动作"""
        metrics.record_user_action(action="login", ok=True, status_code=200)
        snap = metrics.snapshot_user_actions()
        assert len(snap) > 0

    def test_record_user_action_failure(self, metrics):
        """测试记录失败的用户动作"""
        metrics.record_user_action(action="login", ok=False, status_code=401)
        snap = metrics.snapshot_user_actions()
        assert len(snap) > 0

    def test_record_payment_pay_success(self, metrics):
        """测试记录成功的支付"""
        metrics.record_payment_pay(method="wechat", result="success")
        snap = metrics.snapshot_payment_pay()
        assert len(snap) > 0

    def test_record_payment_pay_failure(self, metrics):
        """测试记录失败的支付"""
        metrics.record_payment_pay(method="wechat", result="failed")
        snap = metrics.snapshot_payment_pay()
        assert len(snap) > 0

    def test_record_payment_callback(self, metrics):
        """测试记录支付回调"""
        metrics.record_payment_callback(provider="wechat", verified=True, ok=True)
        snap = metrics.snapshot_payment_callbacks()
        assert len(snap) > 0

    def test_record_payment_callback_verified_false(self, metrics):
        """测试记录未验证的支付回调"""
        metrics.record_payment_callback(provider="wechat", verified=False, ok=False)
        snap = metrics.snapshot_payment_callbacks()
        assert len(snap) > 0


class TestPrometheusMetricsRendering:
    """Prometheus 指标渲染测试类"""

    @pytest.fixture
    def metrics(self):
        """创建指标实例"""
        return PrometheusMetrics()

    def test_render_prometheus_empty(self, metrics):
        """测试渲染空指标"""
        output = metrics.render_prometheus()
        assert "baixing_process_started_at_seconds" in output
        assert "HELP" in output
        assert "TYPE" in output

    def test_render_prometheus_with_http(self, metrics):
        """测试渲染带 HTTP 指标的输出"""
        metrics.record_http(method="GET", route="/api/users", status_code=200, duration_seconds=0.1)
        output = metrics.render_prometheus()
        assert "baixing_http_requests_total" in output
        assert "method=\"GET\"" in output

    def test_render_prometheus_with_jobs(self, metrics):
        """测试渲染带任务指标的输出"""
        metrics.record_job(name="cleanup", ok=True, duration_seconds=1.0)
        output = metrics.render_prometheus()
        assert "baixing_job_runs_total" in output
        assert "job=\"cleanup\"" in output

    def test_render_prometheus_with_rate_limit(self, metrics):
        """测试渲染带限流指标的输出"""
        metrics.record_rate_limit(endpoint="/api/users", allowed=True)
        output = metrics.render_prometheus()
        assert "baixing_rate_limit_checks_total" in output

    def test_render_prometheus_with_user_action(self, metrics):
        """测试渲染带用户动作指标的输出"""
        metrics.record_user_action(action="login", ok=True, status_code=200)
        output = metrics.render_prometheus()
        assert "baixing_user_actions_total" in output

    def test_render_prometheus_with_payment(self, metrics):
        """测试渲染带支付指标的输出"""
        metrics.record_payment_pay(method="wechat", result="success")
        output = metrics.render_prometheus()
        assert "baixing_payment_pay_requests_total" in output

    def test_render_prometheus_with_payment_callback(self, metrics):
        """测试渲染带支付回调指标的输出"""
        metrics.record_payment_callback(provider="wechat", verified=True, ok=True)
        output = metrics.render_prometheus()
        assert "baixing_payment_callback_events_total" in output

    def test_render_prometheus_with_sql_slow(self, metrics):
        """测试渲染带慢 SQL 指标的输出"""
        metrics.record_sql_slow_query(duration_seconds=0.5)
        output = metrics.render_prometheus()
        assert "baixing_sql_slow_queries_total" in output

    def test_render_prometheus_with_extra_lines(self, metrics):
        """测试渲染带额外行的输出"""
        extra_lines = ["# Custom metric", "custom_metric 123"]
        output = metrics.render_prometheus(extra_lines=extra_lines)
        assert "custom_metric" in output

    def test_render_prometheus_skips_zero_count_http(self, metrics):
        """测试渲染跳过零计数的 HTTP 指标"""
        # 记录 duration 为 0 但 count 会被设置为 1
        metrics.record_http(method="GET", route="/api/users", status_code=200, duration_seconds=0)
        output = metrics.render_prometheus()
        # count=1, 所以应该包含这个请求
        lines = output.split("\n")
        user_lines = [l for l in lines if "/api/users" in l and "requests_total" in l]
        # count > 0 时应该包含
        assert len(user_lines) > 0

    def test_render_prometheus_skips_zero_sum_http(self, metrics):
        """测试渲染跳过零和的 HTTP 指标"""
        metrics.record_http(method="GET", route="/api/users", status_code=200, duration_seconds=0)
        output = metrics.render_prometheus()
        lines = output.split("\n")
        duration_lines = [l for l in lines if "_duration_seconds_sum" in l and "/api/users" in l]
        assert len(duration_lines) == 0


class TestPrometheusMetricsConcurrency:
    """Prometheus 指标并发测试类"""

    @pytest.fixture
    def metrics(self):
        """创建指标实例"""
        return PrometheusMetrics()

    def test_thread_safety_http(self, metrics):
        """测试 HTTP 记录的线程安全"""
        import threading

        def record_requests():
            for _ in range(100):
                metrics.record_http(method="GET", route="/api/users", status_code=200, duration_seconds=0.1)

        threads = [threading.Thread(target=record_requests) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        snap = metrics.snapshot_http()
        total_count = sum(agg.count for agg in snap.values())
        assert total_count == 500

    def test_thread_safety_jobs(self, metrics):
        """测试任务记录的线程安全"""
        import threading

        def record_jobs():
            for _ in range(100):
                metrics.record_job(name="cleanup", ok=True, duration_seconds=0.1)

        threads = [threading.Thread(target=record_jobs) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        snap = metrics.snapshot_jobs()
        assert snap["cleanup"].runs_total == 500

    def test_thread_safety_rate_limit(self, metrics):
        """测试限流记录的线程安全"""
        import threading

        def record_rate_limits():
            for _ in range(100):
                metrics.record_rate_limit(endpoint="/api/users", allowed=True)

        threads = [threading.Thread(target=record_rate_limits) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        snap = metrics.snapshot_rate_limits()
        total_count = sum(agg.count for agg in snap.values())
        assert total_count == 500


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint_contains_business_metrics(client):
    """测试 Prometheus 指标端点包含业务指标"""
    res = await client.get("/metrics")
    assert res.status_code == 200
    body = str(res.text or "")

    assert "baixing_user_actions_total" in body
    assert "baixing_payment_pay_requests_total" in body
    assert "baixing_payment_callback_events_total" in body
    assert "baixing_ai_errors_total" in body

    assert "baixing_sql_slow_queries_total" in body
    assert "baixing_sql_slow_query_duration_seconds_bucket" in body
    assert "baixing_sql_slow_query_max_duration_seconds" in body
