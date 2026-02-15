"""告警规则配置

提供Prometheus告警规则配置。

告警级别:
    - critical: 严重，立即处理
    - warning: 警告，需要关注
    - info: 信息，仅记录

使用示例:
    ```yaml
    # prometheus/alert_rules.yml
    groups:
      - name:百姓助手
        rules:
          - alert: HighErrorRate
            expr: rate(api_errors_total[5m]) / rate(http_requests_total[5m]) > 0.05
            for: 3m
            labels:
              severity: critical
            annotations:
              summary: "API错误率过高"
    ```
"""
from __future__ import annotations

import os
from typing import Any

MONITORING_DIR = os.getenv("MONITORING_DIR", "monitoring")


def generate_alert_rules() -> dict[str, Any]:
    """生成告警规则配置

    Returns:
        Prometheus告警规则配置
    """
    rules = {
        "groups": [
            {
                "name": "百姓助手-critical",
                "interval": "30s",
                "rules": [
                    {
                        "alert": "HighErrorRate",
                        "expr": (
                            "sum(rate(api_errors_total[5m])) / "
                            "sum(rate(http_requests_total[5m])) > 0.05"
                        ),
                        "for": "3m",
                        "labels": {"severity": "critical"},
                        "annotations": {
                            "summary": "API错误率超过5%",
                            "description": "当前错误率: {{ $value | humanizePercentage }}",
                        },
                    },
                    {
                        "alert": "DatabasePoolExhausted",
                        "expr": "db_pool_utilization_percent > 90",
                        "for": "5m",
                        "labels": {"severity": "critical"},
                        "annotations": {
                            "summary": "数据库连接池即将耗尽",
                            "description": "当前使用率: {{ $value }}%",
                        },
                    },
                    {
                        "alert": "HighMemoryUsage",
                        "expr": (
                            "(1 - (node_memory_MemAvailable_bytes / "
                            "node_memory_MemTotal_bytes)) > 0.9"
                        ),
                        "for": "5m",
                        "labels": {"severity": "critical"},
                        "annotations": {
                            "summary": "内存使用率超过90%",
                            "description": "当前使用率: {{ $value | humanizePercentage }}",
                        },
                    },
                    {
                        "alert": "DiskSpaceCritical",
                        "expr": (
                            "(1 - (node_filesystem_avail_bytes{mountpoint='/'} / "
                            "node_filesystem_size_bytes{mountpoint='/'})) > 0.95"
                        ),
                        "for": "10m",
                        "labels": {"severity": "critical"},
                        "annotations": {
                            "summary": "磁盘空间严重不足",
                            "description": "当前使用率: {{ $value | humanizePercentage }}",
                        },
                    },
                    {
                        "alert": "ServiceDown",
                        "expr": "up == 0",
                        "for": "1m",
                        "labels": {"severity": "critical"},
                        "annotations": {
                            "summary": "服务不可用",
                            "description": "服务 {{ $labels.job }} 已停止",
                        },
                    },
                ],
            },
            {
                "name": "百姓助手-warning",
                "interval": "1m",
                "rules": [
                    {
                        "alert": "HighErrorRateWarning",
                        "expr": (
                            "sum(rate(api_errors_total[5m])) / "
                            "sum(rate(http_requests_total[5m])) > 0.01"
                        ),
                        "for": "5m",
                        "labels": {"severity": "warning"},
                        "annotations": {
                            "summary": "API错误率偏高",
                            "description": "当前错误率: {{ $value | humanizePercentage }}",
                        },
                    },
                    {
                        "alert": "DatabasePoolHighUtilization",
                        "expr": "db_pool_utilization_percent > 80",
                        "for": "10m",
                        "labels": {"severity": "warning"},
                        "annotations": {
                            "summary": "数据库连接池使用率偏高",
                            "description": "当前使用率: {{ $value }}%",
                        },
                    },
                    {
                        "alert": "HighLatency",
                        "expr": (
                            "histogram_quantile(0.99, "
                            "rate(http_request_duration_seconds_bucket[5m])) > 2"
                        ),
                        "for": "5m",
                        "labels": {"severity": "warning"},
                        "annotations": {
                            "summary": "API响应时间过长",
                            "description": "P99响应时间: {{ $value }}s",
                        },
                    },
                    {
                        "alert": "HighMemoryUsageWarning",
                        "expr": (
                            "(1 - (node_memory_MemAvailable_bytes / "
                            "node_memory_MemTotal_bytes)) > 0.85"
                        ),
                        "for": "10m",
                        "labels": {"severity": "warning"},
                        "annotations": {
                            "summary": "内存使用率偏高",
                            "description": "当前使用率: {{ $value | humanizePercentage }}",
                        },
                    },
                    {
                        "alert": "CacheMissRateHigh",
                        "expr": (
                            "rate(cache_misses_total[5m]) / "
                            "(rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) > 0.3"
                        ),
                        "for": "10m",
                        "labels": {"severity": "warning"},
                        "annotations": {
                            "summary": "缓存未命中率偏高",
                            "description": "当前未命中率: {{ $value | humanizePercentage }}",
                        },
                    },
                ],
            },
            {
                "name": "百姓助手-info",
                "interval": "5m",
                "rules": [
                    {
                        "alert": "DatabasePoolSize",
                        "expr": "db_pool_size",
                        "labels": {"severity": "info"},
                        "annotations": {
                            "summary": "数据库连接池状态",
                            "description": (
                                "池大小: {{ $value }}, "
                                "已检出: {{ $labels.db_pool_checked_out }}, "
                                "溢出: {{ $labels.db_pool_overflow }}"
                            ),
                        },
                    },
                    {
                        "alert": "UptimeNotification",
                        "expr": "time() - process_start_time_seconds > 86400",
                        "for": "1m",
                        "labels": {"severity": "info"},
                        "annotations": {
                            "summary": "服务已运行超过24小时",
                            "description": "运行时长: {{ $value | humanizeDuration }}",
                        },
                    },
                ],
            },
        ],
    }

    return rules


def save_alert_rules(filename: str = "alert_rules.yml") -> str:
    """保存告警规则到文件

    Args:
        filename: 文件名

    Returns:
        文件路径
    """
    import os
    import yaml

    os.makedirs(MONITORING_DIR, exist_ok=True)

    rules = generate_alert_rules()
    filepath = os.path.join(MONITORING_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(rules, f, default_flow_style=False, allow_unicode=True)

    return filepath


def get_alert_rules_summary() -> dict[str, Any]:
    """获取告警规则摘要

    Returns:
        告警规则摘要
    """
    rules = generate_alert_rules()

    summary = {
        "total_groups": len(rules["groups"]),
        "total_rules": 0,
        "by_severity": {"critical": 0, "warning": 0, "info": 0},
        "groups": [],
    }

    for group in rules["groups"]:
        group_info = {
            "name": group["name"],
            "rule_count": len(group["rules"]),
        }

        for rule in group["rules"]:
            severity = rule.get("labels", {}).get("severity", "info")
            summary["total_rules"] += 1
            summary["by_severity"][severity] += 1

        summary["groups"].append(group_info)

    return summary
