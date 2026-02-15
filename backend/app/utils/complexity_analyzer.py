"""代码复杂度检查工具

提供代码复杂度分析和告警功能。
"""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ComplexityMetrics:
    """复杂度指标"""
    file: str
    function: str
    line: int
    complexity: int
    type: str


class ComplexityAnalyzer:
    """代码复杂度分析器"""

    def __init__(self, project_root: str = "."):
        """初始化复杂度分析器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)

    def analyze_complexity(
        self,
        threshold: int = 10
    ) -> list[ComplexityMetrics]:
        """分析代码复杂度

        Args:
            threshold: 复杂度阈值

        Returns:
            高复杂度函数列表
        """
        try:
            # 使用radon分析复杂度
            result = subprocess.run(
                ["py", "-m", "radon", "cc", "backend", "-a"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"radon分析失败: {result.stderr}")
                return []

            # 解析radon输出
            metrics = self._parse_radon_output(result.stdout, threshold)

            return metrics

        except Exception as e:
            logger.error(f"分析复杂度失败: {str(e)}")
            return []

    def _parse_radon_output(
        self,
        output: str,
        threshold: int
    ) -> list[ComplexityMetrics]:
        """解析radon输出

        Args:
            output: radon输出
            threshold: 复杂度阈值

        Returns:
            复杂度指标列表
        """
        metrics = []

        lines = output.split('\n')
        for line in lines:
            # radon输出格式: file.py:function_name line_number complexity
            parts = line.split()

            if len(parts) >= 4:
                try:
                    file = parts[0]
                    function = parts[1]
                    line_num = int(parts[2])
                    complexity = int(parts[3])

                    if complexity > threshold:
                        metrics.append(ComplexityMetrics(
                            file=file,
                            function=function,
                            line=line_num,
                            complexity=complexity,
                            type='cyclomatic'
                        ))

                except (ValueError, IndexError):
                    continue

        return metrics

    def get_complexity_report(
        self,
        threshold: int = 10
    ) -> str:
        """获取复杂度报告

        Args:
            threshold: 复杂度阈值

        Returns:
            复杂度报告文本
        """
        metrics = self.analyze_complexity(threshold)

        report = []
        report.append("=" * 60)
        report.append("代码复杂度报告")
        report.append("=" * 60)
        report.append("")
        report.append(f"复杂度阈值: {threshold}")
        report.append(f"高复杂度函数数量: {len(metrics)}")
        report.append("")

        if metrics:
            report.append("高复杂度函数:")
            report.append("")

            for metric in metrics:
                report.append(f"  {metric.file}:{metric.line}")
                report.append(f"    {metric.function} - 复杂度: {metric.complexity}")
        else:
            report.append("✅ 未发现高复杂度函数")

        return "\n".join(report)

    def suggest_refactoring(
        self,
        metrics: list[ComplexityMetrics]
    ) -> dict[str, list[str]]:
        """建议重构方案

        Args:
            metrics: 复杂度指标列表

        Returns:
            重构建议字典
        """
        suggestions = {}

        for metric in metrics:
            file_path = self.project_root / metric.file
            if not file_path.exists():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_suggestions = []

                # 根据复杂度给出建议
                if metric.complexity > 20:
                    file_suggestions.append("函数过于复杂，建议拆分为多个小函数")
                    file_suggestions.append("考虑使用策略模式或模板方法模式重构")
                elif metric.complexity > 15:
                    file_suggestions.append("函数复杂度较高，建议提取辅助函数")
                    file_suggestions.append("考虑使用早期返回减少嵌套层级")
                elif metric.complexity > 10:
                    file_suggestions.append("函数复杂度略高，建议简化逻辑")
                    file_suggestions.append("考虑使用卫语句减少嵌套")

                if file_suggestions:
                    suggestions[f"{metric.file}:{metric.line}"] = file_suggestions

            except Exception as e:
                logger.error(f"分析文件失败 {metric.file}: {str(e)}")

        return suggestions


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="代码复杂度检查工具")
    parser.add_argument(
        "--project-root",
        default=".",
        help="项目根目录"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=10,
        help="复杂度阈值"
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建复杂度分析器
    analyzer = ComplexityAnalyzer(project_root=args.project_root)

    # 分析复杂度
    print("分析代码复杂度...")
    metrics = analyzer.analyze_complexity(threshold=args.threshold)

    # 生成报告
    report = analyzer.get_complexity_report(threshold=args.threshold)
    print(report)

    # 提供重构建议
    if metrics:
        print("\n重构建议:")
        suggestions = analyzer.suggest_refactoring(metrics)

        for key, file_suggestions in suggestions.items():
            print(f"\n{key}:")
            for suggestion in file_suggestions:
                print(f"  - {suggestion}")


if __name__ == "__main__":
    main()
