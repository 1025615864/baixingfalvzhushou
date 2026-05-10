"""性能基准测试工具

提供性能基准测试和回归检测功能。
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# 允许的HTTP方法白名单
ALLOWED_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


def _validate_endpoint(endpoint: str) -> bool:
    """
    验证端点路径是否合法
    
    Args:
        endpoint: API端点路径
        
    Returns:
        bool: 是否合法
    """
    if not endpoint:
        return False
    # 只允许以 / 开头的路径，且只能包含字母、数字、下划线、连字符、斜杠
    if not endpoint.startswith("/"):
        return False
    # 禁止路径遍历
    if ".." in endpoint:
        return False
    # 只允许合法URL路径字符
    pattern = r'^[\/a-zA-Z0-9_\-\.]+$'
    return bool(re.match(pattern, endpoint))


def _validate_http_method(method: str) -> bool:
    """
    验证HTTP方法是否合法
    
    Args:
        method: HTTP方法
        
    Returns:
        bool: 是否合法
    """
    return method.upper() in ALLOWED_HTTP_METHODS


@dataclass
class PerformanceMetrics:
    """性能指标"""
    endpoint: str
    method: str
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    requests_per_second: float
    error_rate: float
    timestamp: datetime


@dataclass
class PerformanceBaseline:
    """性能基准"""
    endpoint: str
    method: str
    baseline_p50: float
    baseline_p95: float
    baseline_p99: float
    baseline_rps: float
    baseline_error_rate: float
    thresholds: dict[str, float]
    created_at: datetime


class PerformanceBenchmark:
    """性能基准测试器"""

    def __init__(self, project_root: str = "."):
        """初始化性能基准测试器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.baseline_file = self.project_root / "performance_baselines.json"

    def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        duration: int = 60,
        rate: int = 10
    ) -> PerformanceMetrics:
        """运行负载测试

        Args:
            endpoint: API端点
            method: HTTP方法
            duration: 测试持续时间（秒）
            rate: 每秒请求数

        Returns:
            性能指标
        """
        # 使用locust运行负载测试
        try:
            # 创建临时locustfile
            locustfile = self._create_locustfile(endpoint, method, rate)

            # 运行locust
            result = subprocess.run(
                ["py", "-m", "locust", "-f", str(locustfile), "--headless", f"--run-time={duration}s"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            # 解析结果
            metrics = self._parse_locust_output(result.stdout)

            return PerformanceMetrics(
                endpoint=endpoint,
                method=method,
                response_time_p50=metrics.get('p50', 0),
                response_time_p95=metrics.get('p95', 0),
                response_time_p99=metrics.get('p99', 0),
                requests_per_second=metrics.get('rps', 0),
                error_rate=metrics.get('error_rate', 0),
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"运行负载测试失败: {str(e)}")
            raise

    def _create_locustfile(self, endpoint: str, method: str, rate: int) -> Path:
        """创建locustfile

        Args:
            endpoint: API端点
            method: HTTP方法
            rate: 每秒请求数

        Returns:
            locustfile路径
            
        Raises:
            ValueError: 参数验证失败
        """
        # 验证参数安全性
        if not _validate_endpoint(endpoint):
            raise ValueError(f"非法的API端点: {endpoint}")
        if not _validate_http_method(method):
            raise ValueError(f"非法的HTTP方法: {method}")
        if not isinstance(rate, int) or rate <= 0 or rate > 1000:
            raise ValueError(f"非法的请求速率: {rate}")
        
        # 转义端点字符串，防止代码注入
        safe_endpoint = endpoint.replace('"', '\\"').replace('\\', '\\\\')
        safe_method = method.lower()

        locustfile_content = f"""
from locust import HttpUser, task, between

class TestUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def test_endpoint(self):
        self.client.{safe_method}("{safe_endpoint}")
"""

        # 使用安全的临时文件
        temp_dir = tempfile.mkdtemp(prefix="locust_")
        locustfile = Path(temp_dir) / "temp_locustfile.py"
        with open(locustfile, 'w', encoding='utf-8') as f:
            f.write(locustfile_content)

        return locustfile

    def _parse_locust_output(self, output: str) -> dict[str, float]:
        """解析locust输出

        Args:
            output: locust输出

        Returns:
            性能指标字典
        """
        metrics = {}

        # 简化解析，实际应该使用locust的JSON输出
        lines = output.split('\n')
        for line in lines:
            if '50%' in line:
                metrics['p50'] = float(line.split()[-2])
            elif '95%' in line:
                metrics['p95'] = float(line.split()[-2])
            elif '99%' in line:
                metrics['p99'] = float(line.split()[-2])
            elif 'Requests/s' in line:
                metrics['rps'] = float(line.split()[-1])
            elif 'Failures' in line:
                total = float(line.split()[-1])
                metrics['error_rate'] = total / 100.0

        return metrics

    def set_baseline(
        self,
        endpoint: str,
        method: str,
        baseline: PerformanceMetrics
    ) -> None:
        """设置性能基准

        Args:
            endpoint: API端点
            method: HTTP方法
            baseline: 性能指标
        """
        baselines = self._load_baselines()

        baselines[f"{method}:{endpoint}"] = PerformanceBaseline(
            endpoint=endpoint,
            method=method,
            baseline_p50=baseline.response_time_p50,
            baseline_p95=baseline.response_time_p95,
            baseline_p99=baseline.response_time_p99,
            baseline_rps=baseline.requests_per_second,
            baseline_error_rate=baseline.error_rate,
            thresholds={
                'p50_threshold': baseline.response_time_p50 * 1.2,
                'p95_threshold': baseline.response_time_p95 * 1.5,
                'p99_threshold': baseline.response_time_p99 * 2.0,
                'rps_threshold': baseline.requests_per_second * 0.8,
                'error_rate_threshold': baseline.error_rate * 2.0,
            },
            created_at=datetime.now()
        )

        self._save_baselines(baselines)

    def _load_baselines(self) -> dict[str, PerformanceBaseline]:
        """加载性能基准

        Returns:
            性能基准字典
        """
        if not self.baseline_file.exists():
            return {}

        try:
            with open(self.baseline_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            baselines = {}
            for key, value in data.items():
                baselines[key] = PerformanceBaseline(**value)

            return baselines
        except json.JSONDecodeError as e:
            logger.error(f"性能基准文件JSON格式错误: {e}")
            return {}
        except (IOError, OSError) as e:
            logger.error(f"读取性能基准文件失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"加载性能基准失败: {e}")
            return {}

    def _save_baselines(self, baselines: dict[str, PerformanceBaseline]) -> None:
        """保存性能基准

        Args:
            baselines: 性能基准字典
        """
        try:
            # 确保目录存在
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {key: asdict(value) for key, value in baselines.items()}
            with open(self.baseline_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except (IOError, OSError) as e:
            logger.error(f"写入性能基准文件失败: {e}")
        except Exception as e:
            logger.error(f"保存性能基准失败: {e}")

    def check_regression(
        self,
        metrics: PerformanceMetrics
    ) -> dict[str, Any]:
        """检查性能回归

        Args:
            metrics: 性能指标

        Returns:
            回归检测结果
        """
        key = f"{metrics.method}:{metrics.endpoint}"
        baselines = self._load_baselines()

        if key not in baselines:
            return {
                'has_regression': False,
                'message': '未找到性能基准'
            }

        baseline = baselines[key]
        thresholds = baseline.thresholds

        regressions = []

        # 检查P50
        if metrics.response_time_p50 > thresholds['p50_threshold']:
            regressions.append({
                'metric': 'p50',
                'baseline': baseline.baseline_p50,
                'current': metrics.response_time_p50,
                'threshold': thresholds['p50_threshold'],
                'regression': (metrics.response_time_p50 - baseline.baseline_p50) / baseline.baseline_p50 * 100
            })

        # 检查P95
        if metrics.response_time_p95 > thresholds['p95_threshold']:
            regressions.append({
                'metric': 'p95',
                'baseline': baseline.baseline_p95,
                'current': metrics.response_time_p95,
                'threshold': thresholds['p95_threshold'],
                'regression': (metrics.response_time_p95 - baseline.baseline_p95) / baseline.baseline_p95 * 100
            })

        # 检查P99
        if metrics.response_time_p99 > thresholds['p99_threshold']:
            regressions.append({
                'metric': 'p99',
                'baseline': baseline.baseline_p99,
                'current': metrics.response_time_p99,
                'threshold': thresholds['p99_threshold'],
                'regression': (metrics.response_time_p99 - baseline.baseline_p99) / baseline.baseline_p99 * 100
            })

        # 检查RPS
        if metrics.requests_per_second < thresholds['rps_threshold']:
            regressions.append({
                'metric': 'rps',
                'baseline': baseline.baseline_rps,
                'current': metrics.requests_per_second,
                'threshold': thresholds['rps_threshold'],
                'regression': (metrics.requests_per_second - baseline.baseline_rps) / baseline.baseline_rps * 100
            })

        # 检查错误率
        if metrics.error_rate > thresholds['error_rate_threshold']:
            regressions.append({
                'metric': 'error_rate',
                'baseline': baseline.baseline_error_rate,
                'current': metrics.error_rate,
                'threshold': thresholds['error_rate_threshold'],
                'regression': (metrics.error_rate - baseline.baseline_error_rate) / baseline.baseline_error_rate * 100
            })

        return {
            'has_regression': len(regressions) > 0,
            'regressions': regressions,
            'baseline': asdict(baseline),
            'current': asdict(metrics)
        }

    def generate_report(self, metrics: PerformanceMetrics) -> str:
        """生成性能报告

        Args:
            metrics: 性能指标

        Returns:
            性能报告文本
        """
        regression_check = self.check_regression(metrics)

        report = []
        report.append("=" * 60)
        report.append("性能基准测试报告")
        report.append("=" * 60)
        report.append("")
        report.append(f"端点: {metrics.endpoint}")
        report.append(f"方法: {metrics.method}")
        report.append(f"时间: {metrics.timestamp}")
        report.append("")
        report.append("性能指标:")
        report.append(f"  P50响应时间: {metrics.response_time_p50:.2f}ms")
        report.append(f"  P95响应时间: {metrics.response_time_p95:.2f}ms")
        report.append(f"  P99响应时间: {metrics.response_time_p99:.2f}ms")
        report.append(f"  每秒请求数: {metrics.requests_per_second:.2f}")
        report.append(f"  错误率: {metrics.error_rate:.2%}")
        report.append("")

        if regression_check['has_regression']:
            report.append("⚠️ 检测到性能回归:")
            for regression in regression_check['regressions']:
                report.append(f"  {regression['metric']}: {regression['regression']:.2f}%")
        else:
            report.append("✅ 未检测到性能回归")

        return "\n".join(report)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="性能基准测试工具")
    parser.add_argument(
        "--endpoint",
        required=True,
        help="API端点"
    )
    parser.add_argument(
        "--method",
        default="GET",
        help="HTTP方法"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="测试持续时间（秒）"
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=10,
        help="每秒请求数"
    )
    parser.add_argument(
        "--set-baseline",
        action="store_true",
        help="设置性能基准"
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建性能基准测试器
    benchmark = PerformanceBenchmark()

    # 运行负载测试
    print(f"运行负载测试: {args.method} {args.endpoint}")
    metrics = benchmark.run_load_test(
        endpoint=args.endpoint,
        method=args.method,
        duration=args.duration,
        rate=args.rate
    )

    # 设置基准
    if args.set_baseline:
        benchmark.set_baseline(args.endpoint, args.method, metrics)
        print("性能基准已设置")

    # 生成报告
    report = benchmark.generate_report(metrics)
    print(report)


if __name__ == "__main__":
    main()
