#!/usr/bin/env python3
"""
百姓助手 - 测试运行脚本

提供统一的测试执行接口，支持：
- 不同测试类型（单元、集成、E2E）
- 覆盖率报告生成
- 并行测试执行
- 测试环境管理

Usage:
    python scripts/run_tests.py [options]

Options:
    --unit          运行单元测试
    --integration   运行集成测试
    --e2e           运行E2E测试
    --coverage      生成覆盖率报告
    --parallel      并行执行测试
    --verbose       详细输出
    --fail-fast     首次失败时停止
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import NoReturn


class Colors:
    """终端颜色"""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_header(message: str) -> None:
    """打印标题"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{message.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(message: str) -> None:
    """打印成功信息"""
    print(f"{Colors.GREEN}[OK] {message}{Colors.END}")


def print_warning(message: str) -> None:
    """打印警告信息"""
    print(f"{Colors.YELLOW}[WARN] {message}{Colors.END}")


def print_error(message: str) -> None:
    """打印错误信息"""
    print(f"{Colors.RED}[ERR] {message}{Colors.END}")


def run_command(cmd: list[str], cwd: Path | None = None) -> int:
    """
    执行命令
    
    Args:
        cmd: 命令列表
        cwd: 工作目录
        
    Returns:
        返回码
    """
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def setup_test_env() -> None:
    """设置测试环境"""
    # 设置测试环境变量
    env_vars = {
        "APP_ENV": "test",
        "TESTING": "true",
        "PAYMENT_WEBHOOK_SECRET": "test_secret",
        "JWT_SECRET_KEY": "test_secret_key",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    }
    
    for key, value in env_vars.items():
        os.environ.setdefault(key, value)
    
    print_success("测试环境已配置")


def run_unit_tests(args: argparse.Namespace) -> int:
    """
    运行单元测试
    
    Args:
        args: 命令行参数
        
    Returns:
        返回码
    """
    print_header("运行单元测试")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-m", "unit or not slow",
        "-v",
    ]
    
    if args.fail_fast:
        cmd.append("-x")
    
    if args.verbose:
        cmd.append("-vv")
    
    if args.coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_html",
            "--cov-report=xml:coverage.xml",
        ])
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    return run_command(cmd, cwd=Path(__file__).parent.parent)


def run_integration_tests(args: argparse.Namespace) -> int:
    """
    运行集成测试
    
    Args:
        args: 命令行参数
        
    Returns:
        返回码
    """
    print_header("运行集成测试")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-m", "integration",
        "-v",
    ]
    
    if args.fail_fast:
        cmd.append("-x")
    
    if args.verbose:
        cmd.append("-vv")
    
    if args.coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_html",
        ])
    
    return run_command(cmd, cwd=Path(__file__).parent.parent)


def run_e2e_tests(args: argparse.Namespace) -> int:
    """
    运行E2E测试
    
    Args:
        args: 命令行参数
        
    Returns:
        返回码
    """
    print_header("运行E2E测试")
    
    e2e_dir = Path(__file__).parent.parent / "tests" / "e2e"
    
    if not e2e_dir.exists():
        print_error(f"E2E测试目录不存在: {e2e_dir}")
        return 1
    
    # 检查node_modules是否存在
    if not (e2e_dir / "node_modules").exists():
        print_warning("E2E依赖未安装，正在安装...")
        result = run_command(["npm", "install"], cwd=e2e_dir)
        if result != 0:
            print_error("E2E依赖安装失败")
            return result
    
    cmd = ["npx", "playwright", "test"]
    
    if args.verbose:
        cmd.append("--verbose")
    
    if args.fail_fast:
        cmd.append("--max-failures=1")
    
    return run_command(cmd, cwd=e2e_dir)


def run_all_tests(args: argparse.Namespace) -> int:
    """
    运行所有测试
    
    Args:
        args: 命令行参数
        
    Returns:
        返回码
    """
    print_header("运行所有测试")
    
    results = []
    
    # 单元测试
    results.append(run_unit_tests(args))
    
    # 集成测试
    if results[-1] == 0:
        results.append(run_integration_tests(args))
    
    # E2E测试
    if results[-1] == 0 and not args.skip_e2e:
        results.append(run_e2e_tests(args))
    
    return max(results)


def generate_coverage_report() -> int:
    """
    生成覆盖率报告
    
    Returns:
        返回码
    """
    print_header("生成测试覆盖率报告")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=html:coverage_html",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term",
        "-v",
    ]
    
    result = run_command(cmd, cwd=Path(__file__).parent.parent)
    
    if result == 0:
        coverage_html = Path(__file__).parent.parent / "coverage_html" / "index.html"
        print_success(f"覆盖率报告已生成: {coverage_html}")
    
    return result


def main() -> NoReturn:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="百姓助手测试运行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 运行所有单元测试
    python scripts/run_tests.py --unit
    
    # 运行测试并生成覆盖率报告
    python scripts/run_tests.py --unit --coverage
    
    # 运行E2E测试
    python scripts/run_tests.py --e2e
    
    # 运行所有测试
    python scripts/run_tests.py --all
    
    # 快速失败模式
    python scripts/run_tests.py --unit --fail-fast
        """
    )
    
    # 测试类型选项
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--unit", "-u",
        action="store_true",
        help="运行单元测试"
    )
    test_group.add_argument(
        "--integration", "-i",
        action="store_true",
        help="运行集成测试"
    )
    test_group.add_argument(
        "--e2e", "-e",
        action="store_true",
        help="运行E2E测试"
    )
    test_group.add_argument(
        "--all", "-a",
        action="store_true",
        help="运行所有测试"
    )
    test_group.add_argument(
        "--coverage-only",
        action="store_true",
        help="仅生成覆盖率报告"
    )
    
    # 执行选项
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="生成覆盖率报告"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="并行执行测试"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="首次失败时停止"
    )
    parser.add_argument(
        "--skip-e2e",
        action="store_true",
        help="运行所有测试时跳过E2E"
    )
    
    args = parser.parse_args()
    
    # 设置测试环境
    setup_test_env()
    
    # 确定执行哪种测试
    if args.coverage_only:
        result = generate_coverage_report()
    elif args.unit:
        result = run_unit_tests(args)
    elif args.integration:
        result = run_integration_tests(args)
    elif args.e2e:
        result = run_e2e_tests(args)
    elif args.all:
        result = run_all_tests(args)
    else:
        # 默认运行单元测试
        print_warning("未指定测试类型，默认运行单元测试")
        result = run_unit_tests(args)
    
    # 输出结果
    print()
    if result == 0:
        print_success("所有测试通过!")
    else:
        print_error(f"测试失败 (返回码: {result})")
    
    sys.exit(result)


if __name__ == "__main__":
    main()