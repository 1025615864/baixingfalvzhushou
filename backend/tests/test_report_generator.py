"""
测试报告生成器

生成可集成到 Grafana 的测试报告
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, output_dir: Path = Path("test_reports")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.report_data: dict[str, Any] = {}
    
    def run_tests(self, test_path: str = "tests/") -> dict[str, Any]:
        """运行测试并收集结果"""
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                test_path, "--tb=no", "-q", "--no-header",
                "--json-report", "--json-report-file=temp_report.json"
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        # 读取 JSON 报告
        report_file = Path("temp_report.json")
        if report_file.exists():
            with open(report_file) as f:
                self.report_data = json.load(f)
            report_file.unlink()
        else:
            self.report_data = {}
        
        return self.report_data
    
    def generate_grafana_metrics(self) -> dict[str, Any]:
        """生成 Grafana 指标格式"""
        summary = self.report_data.get("summary", {})
        
        metrics = {
            "measurement": "test_results",
            "tags": {
                "project": "百姓助手",
                "environment": "test",
            },
            "time": datetime.now(timezone.utc).isoformat(),
            "fields": {
                "total_tests": summary.get("total", 0),
                "passed": summary.get("passed", 0),
                "failed": summary.get("failed", 0),
                "skipped": summary.get("skipped", 0),
                "error": summary.get("error", 0),
                "duration_seconds": self.report_data.get("duration", 0),
            },
            "metrics": {
                "success_rate": self._calculate_success_rate(summary),
                "tests_per_second": self._calculate_tps(summary),
                "failure_rate": self._calculate_failure_rate(summary),
            }
        }
        
        return metrics
    
    def _calculate_success_rate(self, summary: dict) -> float:
        total = summary.get("total", 0)
        passed = summary.get("passed", 0)
        return (passed / total * 100) if total > 0 else 0
    
    def _calculate_tps(self, summary: dict) -> float:
        duration = self.report_data.get("duration", 0)
        total = summary.get("total", 0)
        return (total / duration) if duration > 0 else 0
    
    def _calculate_failure_rate(self, summary: dict) -> float:
        total = summary.get("total", 0)
        failed = summary.get("failed", 0)
        return (failed / total * 100) if total > 0 else 0
    
    def save_report(self, filename: str = "test_report.json") -> Path:
        """保存测试报告"""
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)
        return output_path
    
    def save_grafana_metrics(self, filename: str = "grafana_metrics.json") -> Path:
        """保存 Grafana 指标"""
        metrics = self.generate_grafana_metrics()
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        return output_path
    
    def save_prometheus_metrics(self, filename: str = "prometheus_metrics.prom") -> Path:
        """保存 Prometheus 指标"""
        metrics = self.generate_prometheus_metrics()
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(metrics)
        return output_path
    
    def generate_prometheus_metrics(self) -> str:
        """生成 Prometheus 指标格式"""
        summary = self.report_data.get("summary", {})
        
        metrics_lines = [
            "# HELP test_results_total Total number of tests",
            "# TYPE test_results_total counter",
            f'test_results_total{{status="total"}} {summary.get("total", 0)}',
            f'test_results_total{{status="passed"}} {summary.get("passed", 0)}',
            f'test_results_total{{status="failed"}} {summary.get("failed", 0)}',
            f'test_results_total{{status="skipped"}} {summary.get("skipped", 0)}',
            f'test_results_total{{status="error"}} {summary.get("error", 0)}',
            "",
            "# HELP test_success_rate Test success rate percentage",
            "# TYPE test_success_rate gauge",
            f'test_success_rate {self._calculate_success_rate(summary)}',
            "",
            "# HELP test_duration_seconds Test execution duration",
            "# TYPE test_duration_seconds gauge",
            f'test_duration_seconds {self.report_data.get("duration", 0)}',
        ]
        
        return "\n".join(metrics_lines)
    
    def print_summary(self):
        """打印测试摘要"""
        summary = self.report_data.get("summary", {})
        
        print("\n" + "=" * 50)
        print("测试报告摘要")
        print("=" * 50)
        print(f"总测试数: {summary.get('total', 0)}")
        print(f"通过: {summary.get('passed', 0)}")
        print(f"失败: {summary.get('failed', 0)}")
        print(f"跳过: {summary.get('skipped', 0)}")
        print(f"错误: {summary.get('error', 0)}")
        print(f"成功率: {self._calculate_success_rate(summary):.2f}%")
        print(f"执行时间: {self.report_data.get('duration', 0):.2f}秒")
        print("=" * 50)


def main():
    """主函数"""
    generator = ReportGenerator()
    
    print("运行测试...")
    generator.run_tests()
    
    print("生成报告...")
    generator.save_report()
    generator.save_grafana_metrics()
    generator.save_prometheus_metrics()
    
    generator.print_summary()
    
    print(f"\n报告已保存到: {generator.output_dir}")


if __name__ == "__main__":
    main()
