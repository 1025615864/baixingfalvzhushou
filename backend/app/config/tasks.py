"""定时任务配置

提供定时任务的配置管理，简化main.py中的lifespan函数。
"""
from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class PeriodicTaskConfig:
    """定时任务配置"""
    func: Callable[..., Any]
    interval_hours: int
    lock_key: str
    name: str


# 定时任务配置列表
PERIODIC_TASKS = [
    # 新闻发布任务
    PeriodicTaskConfig(
        func=lambda: None,  # 实际函数在运行时注入
        interval_hours=1,
        lock_key="news_publish",
        name="news_publish"
    ),
    # RSS采集任务
    PeriodicTaskConfig(
        func=lambda: None,
        interval_hours=2,
        lock_key="rss_ingest",
        name="rss_ingest"
    ),
    # News AI任务
    PeriodicTaskConfig(
        func=lambda: None,
        interval_hours=3,
        lock_key="news_ai",
        name="news_ai"
    ),
    # 结算任务
    PeriodicTaskConfig(
        func=lambda: None,
        interval_hours=6,
        lock_key="settlement",
        name="settlement"
    ),
    # 微信支付证书刷新
    PeriodicTaskConfig(
        func=lambda: None,
        interval_hours=24,
        lock_key="wechat_cert_refresh",
        name="wechat_cert_refresh"
    ),
    # SLA扫描任务
    PeriodicTaskConfig(
        func=lambda: None,
        interval_hours=12,
        lock_key="sla_scan",
        name="sla_scan"
    ),
    # 积分系统任务
    PeriodicTaskConfig(
        func=lambda: None,
        interval_hours=1,
        lock_key="points_system",
        name="points_system"
    ),
]
