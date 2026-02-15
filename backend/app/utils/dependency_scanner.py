"""依赖安全扫描工具

提供依赖安全漏洞扫描和修复功能。
"""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Vulnerability:
    """安全漏洞"""
    package: str
    version: str
    vulnerability_id: str
    severity: str
    description: str
    affected_versions: str | None = None
    fixed_versions: str | None = None


class DependencySecurityScanner:
    """依赖安全扫描器"""

    def __init__(self, project_root: str = "."):
        """初始化依赖安全扫描器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.requirements_file = self.project_root / "requirements.txt"

    def scan_vulnerabilities(self) -> list[Vulnerability]:
        """扫描安全漏洞

        Returns:
            安全漏洞列表
        """
        vulnerabilities = []

        # 使用safety扫描
        try:
            result = subprocess.run(
                ["py", "-m", "safety", "check", "--json"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.warning(f"safety扫描失败: {result.stderr}")

            # 解析safety输出
            if result.stdout:
                vulnerabilities.extend(self._parse_safety_output(result.stdout))

        except Exception as e:
            logger.error(f"safety扫描失败: {str(e)}")

        # 使用bandit扫描
        try:
            result = subprocess.run(
                ["py", "-m", "bandit", "-r", "backend", "-f", "json"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.warning(f"bandit扫描失败: {result.stderr}")

            # 解析bandit输出
            if result.stdout:
                vulnerabilities.extend(self._parse_bandit_output(result.stdout))

        except Exception as e:
            logger.error(f"bandit扫描失败: {str(e)}")

        return vulnerabilities

    def _parse_safety_output(self, output: str) -> list[Vulnerability]:
        """解析safety输出

        Args:
            output: safety输出

        Returns:
            安全漏洞列表
        """
        vulnerabilities = []

        try:
            data = json.loads(output)

            if isinstance(data, list):
                for item in data:
                    vulnerabilities.append(Vulnerability(
                        package=item.get('package', ''),
                        version=item.get('version', ''),
                        vulnerability_id=item.get('advisory_id', ''),
                        severity=item.get('severity', 'unknown'),
                        description=item.get('advisory', ''),
                        affected_versions=item.get('affected_versions'),
                        fixed_versions=item.get('fixed_versions')
                    ))

        except json.JSONDecodeError:
            logger.error("解析safety输出失败")

        return vulnerabilities

    def _parse_bandit_output(self, output: str) -> list[Vulnerability]:
        """解析bandit输出

        Args:
            output: bandit输出

        Returns:
            安全漏洞列表
        """
        vulnerabilities = []

        try:
            data = json.loads(output)

            if 'results' in data:
                for result in data['results']:
                    for issue in result.get('results', []):
                        vulnerabilities.append(Vulnerability(
                            package=result.get('filename', ''),
                            version='',
                            vulnerability_id=issue.get('test_id', ''),
                            severity=issue.get('issue_severity', 'unknown'),
                            description=issue.get('issue_text', ''),
                            affected_versions=None,
                            fixed_versions=None
                        ))

        except json.JSONDecodeError:
            logger.error("解析bandit输出失败")

        return vulnerabilities

    def get_security_report(self) -> str:
        """获取安全报告

        Returns:
            安全报告文本
        """
        vulnerabilities = self.scan_vulnerabilities()

        report = []
        report.append("=" * 60)
        report.append("依赖安全扫描报告")
        report.append("=" * 60)
        report.append("")

        # 按严重程度分组
        critical = [v for v in vulnerabilities if v.severity == 'critical']
        high = [v for v in vulnerabilities if v.severity == 'high']
        medium = [v for v in vulnerabilities if v.severity == 'medium']
        low = [v for v in vulnerabilities if v.severity == 'low']

        if critical:
            report.append(f"严重漏洞 ({len(critical)}):")
            for v in critical:
                report.append(f"  {v.package} {v.version}")
                report.append(f"    {v.vulnerability_id}")
                report.append(f"    {v.description}")
                report.append("")

        if high:
            report.append(f"高危漏洞 ({len(high)}):")
            for v in high:
                report.append(f"  {v.package} {v.version}")
                report.append(f"    {v.vulnerability_id}")
                report.append(f"    {v.description}")
                report.append("")

        if medium:
            report.append(f"中危漏洞 ({len(medium)}):")
            for v in medium:
                report.append(f"  {v.package} {v.version}")
                report.append(f"    {v.vulnerability_id}")
                report.append(f"    {v.description}")
                report.append("")

        if low:
            report.append(f"低危漏洞 ({len(low)}):")
            for v in low:
                report.append(f"  {v.package} {v.version}")
                report.append(f"    {v.vulnerability_id}")
                report.append(f"    {v.description}")
                report.append("")

        if not vulnerabilities:
            report.append("✅ 未发现安全漏洞")

        return "\n".join(report)

    def get_fix_suggestions(self, vulnerabilities: list[Vulnerability]) -> dict[str, list[str]]:
        """获取修复建议

        Args:
            vulnerabilities: 安全漏洞列表

        Returns:
            修复建议字典
        """
        suggestions = {}

        for vulnerability in vulnerabilities:
            package = vulnerability.package
            package_suggestions = []

            if vulnerability.fixed_versions:
                package_suggestions.append(f"升级到安全版本: {vulnerability.fixed_versions}")

            if vulnerability.severity in ['critical', 'high']:
                package_suggestions.append("立即修复该漏洞")
                package_suggestions.append("检查是否有替代包")
            elif vulnerability.severity == 'medium':
                package_suggestions.append("在下次更新时修复")
            else:
                package_suggestions.append("在方便时修复")

            if package_suggestions:
                suggestions[package] = package_suggestions

        return suggestions


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="依赖安全扫描工具")
    parser.add_argument(
        "--project-root",
        default=".",
        help="项目根目录"
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建依赖安全扫描器
    scanner = DependencySecurityScanner(project_root=args.project_root)

    # 扫描漏洞
    print("扫描依赖安全漏洞...")
    vulnerabilities = scanner.scan_vulnerabilities()

    # 生成报告
    report = scanner.get_security_report()
    print(report)

    # 提供修复建议
    if vulnerabilities:
        print("\n修复建议:")
        suggestions = scanner.get_fix_suggestions(vulnerabilities)

        for package, package_suggestions in suggestions.items():
            print(f"\n{package}:")
            for suggestion in package_suggestions:
                print(f"  - {suggestion}")


if __name__ == "__main__":
    main()
