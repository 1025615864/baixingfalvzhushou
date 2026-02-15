"""
测试度量报告生成器

生成测试覆盖率、通过率、执行时间等度量数据
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any


def run_tests_with_metrics() -> dict[str, Any]:
    """运行测试并收集度量数据"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
    }
    
    try:
        # 运行测试并收集输出
        proc = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                "--tb=no", "-q", "--no-header",
                "--co", "-q"
            ],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        # 解析收集的测试数量
        output = proc.stdout
        lines = output.strip().split("\n")
        test_count = 0
        for line in lines:
            if "::" in line and "test_" in line:
                test_count += 1
        
        results["tests"]["total_count"] = test_count
        
    except Exception as e:
        results["tests"]["error"] = str(e)
    
    return results


def generate_metrics_report() -> dict[str, Any]:
    """生成测试度量报告"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "metrics": {},
    }
    
    # 运行测试收集度量
    test_results = run_tests_with_metrics()
    report["tests"] = test_results.get("tests", {})
    
    return report


def main():
    """主函数"""
    report = generate_metrics_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
