"""E2E测试工具 - 集成Playwright进行端到端测试"""

import logging
import os
import re
import subprocess
import asyncio
from typing import Any, Dict, Optional, List
from pathlib import Path
from datetime import datetime

from ..base import BaseTool, ToolResult, ToolCategory, ToolPermission

logger = logging.getLogger(__name__)


# 允许的文件名字符白名单
ALLOWED_TEST_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.\/]+$')
ALLOWED_BROWSER_NAMES = {"chromium", "firefox", "webkit", "all"}


def _validate_test_filename(filename: str) -> bool:
    """
    验证测试文件名是否合法
    
    Args:
        filename: 测试文件名
        
    Returns:
        bool: 是否合法
    """
    if not filename:
        return False
    
    # 检查是否包含路径遍历
    if ".." in filename:
        logger.warning(f"Test file rejected: path traversal detected in {filename}")
        return False
    
    # 检查是否匹配允许的模式
    if not ALLOWED_TEST_FILENAME_PATTERN.match(filename):
        logger.warning(f"Test file rejected: invalid characters in {filename}")
        return False
    
    return True


def _validate_browser(browser: str) -> str:
    """
    验证浏览器名称是否合法
    
    Args:
        browser: 浏览器名称
        
    Returns:
        合法的浏览器名称
    """
    browser_lower = str(browser).lower().strip()
    if browser_lower in ALLOWED_BROWSER_NAMES:
        return browser_lower
    logger.warning(f"Invalid browser: {browser}, defaulting to chromium")
    return "chromium"


class E2ETestTool(BaseTool):
    """E2E测试工具
    
    提供端到端测试能力，支持:
    - 运行Playwright测试
    - 生成测试报告
    - 截图和录制
    - 测试结果分析
    """

    name = "e2e_test"
    description = """提供端到端测试功能:
    - 运行Playwright测试套件
    - 生成HTML和JSON测试报告
    - 支持截图和视频录制
    - 执行特定的测试用例
    - 测试结果分析和汇总

    使用场景:
    - 验证前端功能完整性
    - 检测UI交互问题
    - 回归测试自动化
    - 性能测试辅助
    """

    version = "1.0.0"
    category = ToolCategory.SYSTEM
    tags = ["测试", "E2E", "Playwright", "自动化", "质量保障"]
    permission = ToolPermission.ADMIN_REQUIRED

    def __init__(self):
        super().__init__()
        # E2E测试默认路径
        self.e2e_root = Path(__file__).parent.parent.parent.parent / "tests" / "e2e"
        self.playwright_config = self.e2e_root / "playwright.config.ts"
        self.reports_dir = self.e2e_root / "reports"

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["run", "list_tests", "generate_report", "setup", "run_test"],
                    "description": "操作类型: run(运行所有测试), list_tests(列出测试), generate_report(生成报告), setup(初始化), run_test(运行特定测试)",
                },
                "test_file": {
                    "type": "string",
                    "description": "测试文件路径（用于run_test操作）",
                },
                "browser": {
                    "type": "string",
                    "enum": ["chromium", "firefox", "webkit", "all"],
                    "description": "浏览器类型，默认chromium",
                },
                "headless": {
                    "type": "boolean",
                    "description": "是否无头模式运行，默认true",
                },
                "report_format": {
                    "type": "string",
                    "enum": ["html", "json", "both"],
                    "description": "报告格式，默认html",
                },
                "timeout": {
                    "type": "number",
                    "description": "超时时间（毫秒），默认30000",
                },
                "workers": {
                    "type": "number",
                    "description": "并行工作进程数，默认1",
                },
            },
            "required": ["action"],
        }

    async def execute(
        self,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """执行E2E测试工具"""
        action = params.get("action")

        try:
            if action == "run":
                return await self._run_tests(params)
            elif action == "list_tests":
                return await self._list_tests(params)
            elif action == "generate_report":
                return await self._generate_report(params)
            elif action == "setup":
                return await self._setup(params)
            elif action == "run_test":
                return await self._run_test(params)
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作类型: {action}"
                )
        except Exception as e:
            logger.exception("E2E测试工具执行失败")
            return ToolResult(
                success=False,
                error=f"执行失败: {str(e)}"
            )

    async def _run_tests(self, params: Dict[str, Any]) -> ToolResult:
        """运行所有E2E测试"""
        browser = params.get("browser", "chromium")
        headless = params.get("headless", True)
        timeout = params.get("timeout", 30000)
        workers = params.get("workers", 1)

        # 检查E2E测试目录是否存在
        if not self.e2e_root.exists():
            return ToolResult(
                success=False,
                error=f"E2E测试目录不存在: {self.e2e_root}，请先执行setup操作"
            )

        # 检查Playwright配置文件
        if not self.playwright_config.exists():
            return ToolResult(
                success=False,
                error=f"Playwright配置文件不存在: {self.playwright_config}"
            )

        # 构建命令
        cmd = [
            "npx",
            "playwright",
            "test",
            "--config", str(self.playwright_config)
        ]

        if browser != "all":
            cmd.extend(["--project", browser])

        if headless:
            cmd.append("--headed=false")
        else:
            cmd.append("--headed=true")

        cmd.extend(["--timeout", str(timeout)])
        cmd.extend(["--workers", str(workers)])

        try:
            # 在e2e目录下执行命令
            result = subprocess.run(
                cmd,
                cwd=str(self.e2e_root),
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            return ToolResult(
                success=result.returncode == 0,
                data={
                    "action": "run_tests",
                    "browser": browser,
                    "headless": headless,
                    "timeout": timeout,
                    "workers": workers,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "reports_dir": str(self.reports_dir),
                },
                metadata={
                    "cmd": " ".join(cmd),
                    "execution_time": datetime.now().isoformat(),
                }
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error="测试执行超时（5分钟）"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"测试执行失败: {str(e)}"
            )

    async def _run_test(self, params: Dict[str, Any]) -> ToolResult:
        """运行特定的测试文件"""
        test_file = params.get("test_file")
        browser = params.get("browser", "chromium")
        headless = params.get("headless", True)

        if not test_file:
            return ToolResult(
                success=False,
                error="缺少必需参数: test_file"
            )

        # 验证文件名安全性
        if not _validate_test_filename(test_file):
            return ToolResult(
                success=False,
                error=f"测试文件名包含非法字符: {test_file}"
            )
        
        # 验证浏览器名称
        safe_browser = _validate_browser(browser)

        # 检查测试文件是否存在
        test_path = self.e2e_root / test_file
        # 验证路径在 e2e_root 目录内，防止路径遍历
        try:
            test_path_resolved = test_path.resolve()
            e2e_root_resolved = self.e2e_root.resolve()
            if not str(test_path_resolved).startswith(str(e2e_root_resolved)):
                return ToolResult(
                    success=False,
                    error=f"测试文件路径非法: {test_file}"
                )
        except (OSError, ValueError) as e:
            logger.warning(f"Path validation failed: {e}")
            return ToolResult(
                success=False,
                error=f"测试文件路径验证失败: {test_file}"
            )
        
        if not test_path.exists():
            return ToolResult(
                success=False,
                error=f"测试文件不存在: {test_path}"
            )

        # 构建命令
        cmd = [
            "npx",
            "playwright",
            "test",
            test_file,
            "--config", str(self.playwright_config),
            "--project", safe_browser
        ]

        if headless:
            cmd.append("--headed=false")
        else:
            cmd.append("--headed=true")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.e2e_root),
                capture_output=True,
                text=True,
                timeout=300
            )

            return ToolResult(
                success=result.returncode == 0,
                data={
                    "action": "run_test",
                    "test_file": test_file,
                    "browser": browser,
                    "headless": headless,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
                metadata={
                    "cmd": " ".join(cmd),
                    "execution_time": datetime.now().isoformat(),
                }
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error=f"测试执行超时: {test_file}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"测试执行失败: {str(e)}"
            )

    async def _list_tests(self, params: Dict[str, Any]) -> ToolResult:
        """列出所有可用的测试文件"""
        if not self.e2e_root.exists():
            return ToolResult(
                success=False,
                error=f"E2E测试目录不存在: {self.e2e_root}"
            )

        test_files = list(self.e2e_root.glob("**/*.spec.ts")) + list(self.e2e_root.glob("**/*.spec.js"))

        tests_info = []
        for test_file in test_files:
            rel_path = test_file.relative_to(self.e2e_root)
            tests_info.append({
                "path": str(rel_path),
                "full_path": str(test_file),
                "size": test_file.stat().st_size,
            })

        return ToolResult(
            success=True,
            data={
                "action": "list_tests",
                "total_tests": len(tests_info),
                "tests": tests_info,
                "e2e_root": str(self.e2e_root),
            }
        )

    async def _generate_report(self, params: Dict[str, Any]) -> ToolResult:
        """生成测试报告"""
        report_format = params.get("report_format", "html")

        # 检查报告目录
        if not self.reports_dir.exists():
            self.reports_dir.mkdir(parents=True, exist_ok=True)

        report_files = []
        if report_format in ["html", "both"]:
            html_report = self.reports_dir / "index.html"
            report_files.append({
                "type": "html",
                "path": str(html_report),
                "exists": html_report.exists()
            })

        if report_format in ["json", "both"]:
            json_report = self.reports_dir / "results.json"
            report_files.append({
                "type": "json",
                "path": str(json_report),
                "exists": json_report.exists()
            })

        return ToolResult(
            success=True,
            data={
                "action": "generate_report",
                "report_format": report_format,
                "reports_dir": str(self.reports_dir),
                "report_files": report_files,
                "note": "报告文件由Playwright测试执行时自动生成",
            }
        )

    async def _setup(self, params: Dict[str, Any]) -> ToolResult:
        """初始化E2E测试环境"""
        # 创建必要的目录结构
        directories = [
            self.e2e_root,
            self.e2e_root / "specs",
            self.e2e_root / "pages",
            self.e2e_root / "helpers",
            self.e2e_root / "fixtures",
            self.reports_dir,
            self.e2e_root / "test-results",
        ]

        created_dirs = []
        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(directory))

        # 检查package.json（如果存在）
        package_json = self.e2e_root.parent / "package.json"
        has_playwright = False

        if package_json.exists():
            try:
                import json
                with open(package_json, 'r', encoding='utf-8') as f:
                    pkg_data = json.load(f)
                    deps = pkg_data.get("dependencies", {})
                    dev_deps = pkg_data.get("devDependencies", {})
                    has_playwright = "@playwright/test" in deps or "@playwright/test" in dev_deps
            except Exception:
                pass

        return ToolResult(
            success=True,
            data={
                "action": "setup",
                "e2e_root": str(self.e2e_root),
                "created_directories": created_dirs,
                "directories": [
                    "specs/ - 测试用例文件",
                    "pages/ - 页面对象模型",
                    "helpers/ - 测试辅助函数",
                    "fixtures/ - 测试数据",
                    "reports/ - 测试报告",
                    "test-results/ - 测试结果",
                ],
                "has_playwright": has_playwright,
                "next_steps": [
                    "1. 确保已安装Playwright: npm install -D @playwright/test",
                    "2. 安装浏览器: npx playwright install",
                    "3. 创建playwright.config.ts配置文件",
                    "4. 编写测试用例文件",
                ],
            },
            metadata={
                "setup_time": datetime.now().isoformat(),
            }
        )