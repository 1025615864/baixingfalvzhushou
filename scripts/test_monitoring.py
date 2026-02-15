#!/usr/bin/env python3
"""
测试监控脚本
定期检查测试覆盖率、通过率、执行时间，并生成度量报告
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class TestMonitor:
    """测试监控类"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports" / "monitoring"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def run_pytest(self, args: List[str]) -> subprocess.CompletedProcess:
        """运行pytest命令"""
        cmd = ["py", "-m", "pytest"] + args
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        return result
    
    def get_test_coverage(self) -> Dict[str, Any]:
        """获取测试覆盖率"""
        print("Checking test coverage...")
        
        result = self.run_pytest([
            "--cov=backend",
            "--cov-report=json",
            "--cov-report=term",
            "-q"
        ])
        
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
            
            return {
                "total_coverage": total_coverage,
                "target": 70,
                "status": "PASS" if total_coverage >= 70 else "FAIL",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "total_coverage": 0,
            "target": 70,
            "status": "FAIL",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_test_pass_rate(self) -> Dict[str, Any]:
        """获取测试通过率"""
        print("Checking test pass rate...")
        
        result = self.run_pytest([
            "--tb=no",
            "-q"
        ])
        
        # 解析pytest输出
        output = result.stdout
        lines = output.split('\n')
        
        for line in lines:
            if 'passed' in line and 'failed' in line:
                # 解析类似 "123 passed, 45 failed" 的输出
                parts = line.split(',')
                passed = 0
                failed = 0
                total = 0
                
                for part in parts:
                    part = part.strip()
                    if 'passed' in part:
                        passed = int(part.split()[0])
                    elif 'failed' in part:
                        failed = int(part.split()[0])
                
                total = passed + failed
                pass_rate = (passed / total * 100) if total > 0 else 0
                
                return {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": pass_rate,
                    "target": 98,
                    "status": "PASS" if pass_rate >= 98 else "FAIL",
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0,
            "target": 98,
            "status": "FAIL",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_test_execution_time(self) -> Dict[str, Any]:
        """获取测试执行时间"""
        print("Checking test execution time...")
        
        start_time = datetime.now()
        result = self.run_pytest([
            "--tb=no",
            "-q"
        ])
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        return {
            "execution_time_seconds": execution_time,
            "execution_time_minutes": execution_time / 60,
            "target_minutes": 10,
            "status": "PASS" if execution_time <= 600 else "FAIL",
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_metrics_report(self) -> Dict[str, Any]:
        """生成测试度量报告"""
        print("Generating test metrics report...")
        
        coverage = self.get_test_coverage()
        pass_rate = self.get_test_pass_rate()
        execution_time = self.get_test_execution_time()
        
        report = {
            "report_date": datetime.now().isoformat(),
            "metrics": {
                "coverage": coverage,
                "pass_rate": pass_rate,
                "execution_time": execution_time
            },
            "summary": {
                "overall_status": self._get_overall_status(coverage, pass_rate, execution_time),
                "issues": self._get_issues(coverage, pass_rate, execution_time)
            }
        }
        
        return report
    
    def _get_overall_status(self, coverage: Dict, pass_rate: Dict, execution_time: Dict) -> str:
        """获取总体状态"""
        if (coverage.get('total_coverage', 0) >= 70 and
            pass_rate.get('pass_rate', 0) >= 98 and
            execution_time.get('execution_time_seconds', 0) <= 600):
            return "PASS"
        return "FAIL"
    
    def _get_issues(self, coverage: Dict, pass_rate: Dict, execution_time: Dict) -> List[str]:
        """获取问题列表"""
        issues = []
        
        if coverage.get('total_coverage', 0) < 70:
            issues.append(f"测试覆盖率未达标（当前：{coverage.get('total_coverage', 0):.1f}%，目标：70%）")
        
        if pass_rate.get('pass_rate', 0) < 98:
            issues.append(f"测试通过率未达标（当前：{pass_rate.get('pass_rate', 0):.1f}%，目标：98%）")
        
        if execution_time.get('execution_time_seconds', 0) > 600:
            issues.append(f"测试执行时间过长（当前：{execution_time.get('execution_time_minutes', 0):.1f}分钟，目标：10分钟）")
        
        return issues
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """保存报告"""
        if filename is None:
            filename = f"test_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_path = self.reports_dir / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Report saved to: {report_path}")
        return report_path
    
    def print_summary(self, report: Dict[str, Any]):
        """打印摘要"""
        print("\n" + "="*60)
        print("Test Metrics Report Summary")
        print("="*60)
        
        metrics = report['metrics']
        
        print(f"\nTest Coverage: {metrics['coverage']['total_coverage']:.1f}%")
        print(f"   Status: {metrics['coverage']['status']}")
        print(f"   Target: {metrics['coverage']['target']}%")
        
        print(f"\nTest Pass Rate: {metrics['pass_rate']['pass_rate']:.1f}%")
        print(f"   Status: {metrics['pass_rate']['status']}")
        print(f"   Target: {metrics['pass_rate']['target']}%")
        print(f"   Total: {metrics['pass_rate']['total']} (Passed: {metrics['pass_rate']['passed']}, Failed: {metrics['pass_rate']['failed']})")
        
        print(f"\nTest Execution Time: {metrics['execution_time']['execution_time_minutes']:.1f} minutes")
        print(f"   Status: {metrics['execution_time']['status']}")
        print(f"   Target: {metrics['execution_time']['target_minutes']} minutes")
        
        print(f"\nOverall Status: {report['summary']['overall_status']}")
        
        if report['summary']['issues']:
            print("\nIssues Found:")
            for issue in report['summary']['issues']:
                print(f"   - {issue}")
        
        print("="*60)


def main():
    """主函数"""
    print("Starting test monitoring...")
    
    monitor = TestMonitor()
    report = monitor.generate_metrics_report()
    
    # 保存报告
    monitor.save_report(report)
    
    # 打印摘要
    monitor.print_summary(report)
    
    # 保存历史记录
    history_file = monitor.reports_dir / "history.json"
    history = []
    
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    history.append(report)
    
    # 只保留最近30天的记录
    cutoff_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)
    history = [r for r in history if 
                datetime.fromisoformat(r['report_date']).timestamp() > cutoff_date]
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    print(f"\nMonitoring completed, history saved to: {history_file}")


if __name__ == "__main__":
    main()
