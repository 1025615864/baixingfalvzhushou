"""监控指标路由 - Prometheus 格式"""
import time
from fastapi import APIRouter, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)

router = APIRouter()

REQUEST_COUNT = Counter(
    "legal_service_requests_total",
    "Total requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "legal_service_request_latency_seconds",
    "Request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
)

ACTIVE_REQUESTS = Gauge(
    "legal_service_active_requests",
    "Active requests",
    ["method", "endpoint"],
)

CONSULTATION_COUNT = Counter(
    "legal_service_consultations_total",
    "Total consultations",
    ["status"],
)

LAWYER_COUNT = Gauge(
    "legal_service_lawyers_total",
    "Total lawyers",
    ["status"],
)

REVIEW_COUNT = Counter(
    "legal_service_reviews_total",
    "Total reviews submitted",
)

APPOINTMENT_COUNT = Counter(
    "legal_service_appointments_total",
    "Total appointments",
    ["status"],
)


def track_request(method: str, endpoint: str, status: int, latency: float):
    """记录请求指标"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)


def increment_consultation(status: str):
    """增加咨询计数"""
    CONSULTATION_COUNT.labels(status=status).inc()


def increment_review():
    """增加评价计数"""
    REVIEW_COUNT.inc()


def increment_appointment(status: str):
    """增加预约计数"""
    APPOINTMENT_COUNT.labels(status=status).inc()


def set_lawyer_count(status: str, count: int):
    """设置律师计数"""
    LAWYER_COUNT.labels(status=status).set(count)


@router.get("/metrics")
async def metrics():
    """Prometheus 指标端点"""
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@router.get("/metrics/counters")
async def get_counters():
    """获取当前计数器值（JSON格式）"""
    return {
        "consultations": {
            status: CONSULTATION_COUNT.labels(status=status)._value.get()
            for status in ["pending", "processing", "answered", "closed"]
        },
        "reviews": REVIEW_COUNT._value.get(),
        "appointments": {
            status: APPOINTMENT_COUNT.labels(status=status)._value.get()
            for status in ["pending", "confirmed", "cancelled", "completed"]
        },
    }