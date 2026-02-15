#!/usr/bin/env python3
"""
测试持续监控脚本
定期检查测试覆盖率、通过率和执行时间
"""
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def run_command(cmd: list, cwd: str = None) -> tuple:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_test_coverage(backend_dir: str) -> Dict[str, Any]:
    """获取测试覆盖率"""
    print("=" * 60)
    print("检查测试覆盖率...")
    print("=" * 60)
    
    cmd = ["py", "-m", "pytest", "--cov=app", "--cov-report=json", "--cov-report=term", "tests/"]
    returncode, stdout, stderr = run_command(cmd, cwd=backend_dir)
    
    coverage_data = {
        "status": "unknown",
        "coverage": 0.0,
        "details": {}
    }
    
    # 尝试读取覆盖率JSON报告
    coverage_file = Path(backend_dir) / "coverage.json"
    if coverage_file.exists():
        try:
            with open(coverage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                coverage_data["coverage"] = data.get("totals", {}).get("percent_covered", 0.0)
                coverage_data["details"] = data.get("files", [])
                coverage_data["status"] = "success"
        except Exception as e:
            print(f"[WARNING] 读取覆盖率报告失败: {e}")
            coverage_data["status"] = "error"
    else:
        print("[WARNING] 未找到覆盖率报告")
        coverage_data["status"] = "not_found"
    
    print(f"测试覆盖率: {coverage_data['coverage']:.1f}%")
    return coverage_data


def get_test_results(backend_dir: str) -> Dict[str, Any]:
    """获取测试结果"""
    print("\n" + "=" * 60)
    print("检查测试结果...")
    print("=" * 60)
    
    cmd = ["py", "-m", "pytest", "-v", "--tb=no", "tests/"]
    returncode, stdout, stderr = run_command(cmd, cwd=backend_dir)
    
    test_results = {
        "status": "unknown",
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "error": 0,
        "pass_rate": 0.0
    }
    
    # 解析pytest输出
    lines = stdout.split('\n')
    for line in lines:
        if " passed" in line or " failed" in line:
            parts = line.split()
            for part in parts:
                if "passed" in part:
                    test_results["passed"] = int(part.split()[0])
                elif "failed" in part:
                    test_results["failed"] = int(part.split()[0])
                elif "skipped" in part:
                    test_results["skipped"] = int(part.split()[0])
                elif "error" in part:
                    test_results["error"] = int(part.split()[0])
    
    test_results["total"] = test_results["passed"] + test_results["failed"] + test_results["error"]
    
    if test_results["total"] > 0:
        test_results["pass_rate"] = (test_results["passed"] / test_results["total"]) * 100
        test_results["status"] = "success" if test_results["failed"] == 0 and test_results["error"] == 0 else "failure"
    
    print(f"测试总数: {test_results['total']}")
    print(f"通过: {test_results['passed']}")
    print(f"失败: {test_results['failed']}")
    print(f"跳过: {test_results['skipped']}")
    print(f"错误: {test_results['error']}")
    print(f"通过率: {test_results['pass_rate']:.1f}%")
    
    return test_results


def get_test_execution_time(backend_dir: str) -> Dict[str, Any]:
    """获取测试执行时间"""
    print("\n" + "=" * 60)
    print("检查测试执行时间...")
    print("=" * 60)
    
    cmd = ["py", "-m", "pytest", "-v", "--tb=no", "--durations=10", "tests/"]
    returncode, stdout, stderr = run_command(cmd, cwd=backend_dir)
    
    execution_time = {
        "status": "unknown",
        "total_time": 0.0,
        "slowest_tests": []
    }
    
    # 解析pytest输出中的执行时间
    lines = stdout.split('\n')
    found_duration = False
    for line in lines:
        if "slowest 10 durations" in line:
            found_duration = True
            continue
        if found_duration and line.strip():
            # 解析慢测试
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    test_name = parts[0]
                    time_str = parts[-1]
                    if time_str.endswith('s'):
                        time_val = float(time_str[:-1])
                        execution_time["slowest_tests"].append({
                            "test": test_name,
                            "time": time_val
                        })
                except ValueError:
                    pass
        if found_duration and line.strip() == "":
            break
    
    # 估算总执行时间（基于慢测试）
    if execution_time["slowest_tests"]:
        execution_time["total_time"] = sum(t["time"] for t in execution_time["slowest_tests"][:5])
        execution_time["status"] = "success"
    
    print(f"总执行时间: {execution_time['total_time']:.1f}秒")
    print(f"最慢的5个测试:")
    for i, test in enumerate(execution_time["slowest_tests"][:5], 1):
        print(f"  {i}. {test['test']}: {test['time']:.1f}秒")
    
    return execution_time


def generate_report(coverage_data: Dict, test_results: Dict, execution_time: Dict) -> str:
    """生成监控报告"""
    report = []
    report.append("=" * 60)
    report.append("测试监控报告")
    report.append("=" * 60)
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 测试覆盖率
    report.append("## 测试覆盖率")
    report.append(f"当前覆盖率: {coverage_data['coverage']:.1f}%")
    report.append(f"目标覆盖率: 70.0%")
    coverage_status = "[PASS] 达标" if coverage_data["coverage"] >= 70 else "[FAIL] 未达标"
    report.append(f"状态: {coverage_status}")
    report.append("")
    
    # 测试结果
    report.append("## 测试结果")
    report.append(f"测试总数: {test_results['total']}")
    report.append(f"通过: {test_results['passed']}")
    report.append(f"失败: {test_results['failed']}")
    report.append(f"跳过: {test_results['skipped']}")
    report.append(f"错误: {test_results['error']}")
    report.append(f"通过率: {test_results['pass_rate']:.1f}%")
    report.append(f"目标通过率: 98.0%")
    pass_rate_status = "[PASS] 达标" if test_results["pass_rate"] >= 98 else "[FAIL] 未达标"
    report.append(f"状态: {pass_rate_status}")
    report.append("")
    
    # 测试执行时间
    report.append("## 测试执行时间")
    report.append(f"总执行时间: {execution_time['total_time']:.1f}秒")
    report.append(f"目标执行时间: 600秒（10分钟）")
    time_status = "[PASS] 达标" if execution_time["total_time"] < 600 else "[FAIL] 未达标"
    report.append(f"状态: {time_status}")
    report.append("")
    
    # 最慢测试
    if execution_time["slowest_tests"]:
        report.append("## 最慢测试（前5个）")
        for i, test in enumerate(execution_time["slowest_tests"][:5], 1):
            report.append(f"{i}. {test['test']}: {test['time']:.1f}秒")
        report.append("")
    
    # 总体评估
    report.append("## 总体评估")
    all_passed = (
        coverage_data["coverage"] >= 70 and
        test_results["pass_rate"] >= 98 and
        execution_time["total_time"] < 600
    )
    overall_status = "[PASS] 全部达标" if all_passed else "[WARN] 部分未达标"
    report.append(f"状态: {overall_status}")
    report.append("")
    
    # 改进建议
    report.append("## 改进建议")
    if coverage_data["coverage"] < 70:
        report.append("- 测试覆盖率未达标，建议补充测试用例")
    if test_results["pass_rate"] < 98:
        report.append(f"- 测试通过率未达标，有{test_results['failed']}个失败测试需要修复")
    if execution_time["total_time"] >= 600:
        report.append("- 测试执行时间过长，建议优化慢测试或使用并行测试")
    if not all_passed:
        report.append("- 建议每周运行此监控脚本，跟踪改进情况")
    else:
        report.append("- 所有指标达标，继续保持")
    
    return "\n".join(report)


def save_report(report: str, output_dir: str):
    """保存监控报告"""
    output_path = Path(output_dir) / "test_monitoring"
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 保存最新报告
    latest_file = output_path / "latest.md"
    with open(latest_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 保存历史报告（按日期）
    date_str = datetime.now().strftime('%Y-%m-%d')
    history_file = output_path / f"{date_str}.md"
    with open(history_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已保存到: {latest_file}")
    print(f"历史报告已保存到: {history_file}")


def main():
    """主函数"""
    print("[TEST MONITOR] 开始测试监控...")
    
    # 获取项目根目录
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    
    # 检查测试覆盖率
    coverage_data = get_test_coverage(str(backend_dir))
    
    # 检查测试结果
    test_results = get_test_results(str(backend_dir))
    
    # 检查测试执行时间
    execution_time = get_test_execution_time(str(backend_dir))
    
    # 生成监控报告
    report = generate_report(coverage_data, test_results, execution_time)
    
    # 保存报告
    output_dir = backend_dir / "reports"
    save_report(report, str(output_dir))
    
    # 打印报告
    print("\n" + report)
    
    # 返回退出码
    all_passed = (
        coverage_data["coverage"] >= 70 and
        test_results["pass_rate"] >= 98 and
        execution_time["total_time"] < 600
    )
    
    if all_passed:
        print("\n✅ 所有监控指标达标")
        sys.exit(0)
    else:
        print("\n⚠️  部分监控指标未达标")
        sys.exit(1)


if __name__ == "__main__":
    main()
