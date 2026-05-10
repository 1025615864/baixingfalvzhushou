"""测试覆盖率工具

提供测试覆盖率分析和提升功能。
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """测试覆盖率分析器"""

    def __init__(self, project_root: str = "."):
        """初始化覆盖率分析器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)

    def run_coverage_report(self) -> dict[str, Any]:
        """运行覆盖率报告

        Returns:
            覆盖率报告数据
        """
        try:
            # 运行pytest覆盖率测试
            result = subprocess.run(
                ["py", "-m", "pytest", "--cov=backend", "--cov-report=term-missing", "--cov-report=json"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"覆盖率测试失败: {result.stderr}")
                return {}

            # 解析覆盖率报告
            coverage_file = self.project_root / "coverage.json"
            if not coverage_file.exists():
                logger.warning("覆盖率报告文件不存在")
                return {}

            import json
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)

            return coverage_data

        except Exception as e:
            logger.error(f"运行覆盖率报告失败: {str(e)}")
            return {}

    def get_coverage_summary(self) -> dict[str, float]:
        """获取覆盖率摘要

        Returns:
            覆盖率摘要
        """
        coverage_data = self.run_coverage_report()

        if not coverage_data or 'totals' not in coverage_data:
            return {}

        totals = coverage_data['totals']

        return {
            'line_coverage': totals.get('line_covered', 0) / totals.get('line_num', 1) * 100,
            'branch_coverage': totals.get('branch_covered', 0) / totals.get('branch_num', 1) * 100,
            'statement_coverage': totals.get('statement_covered', 0) / totals.get('statement_num', 1) * 100,
        }

    def get_low_coverage_files(
        self,
        threshold: float = 70.0
    ) -> list[dict[str, Any]]:
        """获取低覆盖率文件

        Args:
            threshold: 覆盖率阈值

        Returns:
            低覆盖率文件列表
        """
        coverage_data = self.run_coverage_report()

        if not coverage_data or 'files' not in coverage_data:
            return []

        low_coverage_files = []

        for file_data in coverage_data['files']:
            file_name = file_data.get('file', '')
            summary = file_data.get('summary', {})
            line_covered = summary.get('line_covered', 0)
            line_num = summary.get('line_num', 1)

            if line_num > 0:
                coverage = line_covered / line_num * 100
                if coverage < threshold:
                    low_coverage_files.append({
                        'file': file_name,
                        'coverage': coverage,
                        'line_covered': line_covered,
                        'line_num': line_num,
                    })

        return low_coverage_files

    def generate_coverage_report(self) -> str:
        """生成覆盖率报告

        Returns:
            覆盖率报告文本
        """
        summary = self.get_coverage_summary()
        low_coverage_files = self.get_low_coverage_files()

        report = []
        report.append("=" * 60)
        report.append("测试覆盖率报告")
        report.append("=" * 60)
        report.append("")
        report.append("总体覆盖率:")
        report.append(f"  行覆盖率: {summary.get('line_coverage', 0):.2f}%")
        report.append(f"  分支覆盖率: {summary.get('branch_coverage', 0):.2f}%")
        report.append(f"  语句覆盖率: {summary.get('statement_coverage', 0):.2f}%")
        report.append("")
        report.append(f"低覆盖率文件 (< 70%):")
        report.append("")

        for file_data in low_coverage_files:
            report.append(f"  {file_data['file']}: {file_data['coverage']:.2f}%")

        return "\n".join(report)

    def suggest_tests(self, file_path: str) -> list[str]:
        """建议测试用例

        Args:
            file_path: 文件路径

        Returns:
            测试建议列表
        """
        suggestions = []

        # 读取文件内容
        file_obj = Path(file_path)
        if not file_obj.exists():
            return suggestions

        try:
            with open(file_obj, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否有函数定义
            if 'def ' in content:
                suggestions.append("建议为函数添加单元测试")

            # 检查是否有类定义
            if 'class ' in content:
                suggestions.append("建议为类添加单元测试")

            # 检查是否有异常处理
            if 'except ' in content:
                suggestions.append("建议为异常处理添加测试用例")

            # 检查是否有数据库操作
            if 'db.execute' in content or 'select(' in content:
                suggestions.append("建议为数据库操作添加集成测试")

            # 检查是否有API路由
            if '@router' in content or '@app' in content:
                suggestions.append("建议为API端点添加测试用例")

        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {str(e)}")

        return suggestions


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="测试覆盖率工具")
    parser.add_argument(
        "--project-root",
        default=".",
        help="项目根目录"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=70.0,
        help="覆盖率阈值"
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建覆盖率分析器
    analyzer = CoverageAnalyzer(project_root=args.project_root)

    # 生成覆盖率报告
    report = analyzer.generate_coverage_report()
    print(report)

    # 获取低覆盖率文件
    low_coverage_files = analyzer.get_low_coverage_files(threshold=args.threshold)

    if low_coverage_files:
        print("\n测试建议:")
        for file_data in low_coverage_files[:10]:
            suggestions = analyzer.suggest_tests(file_data['file'])
            print(f"\n{file_data['file']} (覆盖率: {file_data['coverage']:.2f}%):")
            for suggestion in suggestions:
                print(f"  - {suggestion}")


if __name__ == "__main__":
    main()
