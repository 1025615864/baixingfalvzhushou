"""日志分析工具

提供日志查询、统计和可视化功能。
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: str
    logger: str
    message: str
    extra: dict[str, Any] | None = None


@dataclass
class LogStats:
    """日志统计"""
    total_count: int
    level_counts: dict[str, int]
    logger_counts: dict[str, int]
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int


class LogAnalyzer:
    """日志分析器"""

    # 日志级别
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

    def __init__(self, log_dir: str = "logs"):
        """初始化日志分析器

        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)

    def parse_log_line(self, line: str) -> LogEntry | None:
        """解析日志行

        Args:
            line: 日志行

        Returns:
            日志条目
        """
        # 匹配标准日志格式: 2024-01-01 12:00:00 - logger_name - LEVEL - message
        pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\S+) - (DEBUG|INFO|WARNING|ERROR|CRITICAL) - (.+)$'
        match = re.match(pattern, line.strip())

        if not match:
            return None

        timestamp_str, logger_name, level, message = match.groups()

        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

        return LogEntry(
            timestamp=timestamp,
            level=level,
            logger=logger_name,
            message=message,
            extra={}
        )

    def parse_log_file(self, file_path: Path) -> list[LogEntry]:
        """解析日志文件

        Args:
            file_path: 日志文件路径

        Returns:
            日志条目列表
        """
        entries = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = self.parse_log_line(line)
                    if entry:
                        entries.append(entry)
        except Exception as e:
            logger.error(f"解析日志文件失败 {file_path}: {str(e)}")

        return entries

    def query_logs(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        level: str | None = None,
        logger: str | None = None,
        keyword: str | None = None,
        limit: int = 1000
    ) -> list[LogEntry]:
        """查询日志

        Args:
            start_time: 开始时间
            end_time: 结束时间
            level: 日志级别
            logger: 日志记录器名称
            keyword: 关键词
            limit: 返回数量限制

        Returns:
            日志条目列表
        """
        all_entries = []

        # 解析所有日志文件
        for log_file in self.log_dir.glob("*.log"):
            entries = self.parse_log_file(log_file)
            all_entries.extend(entries)

        # 过滤日志
        filtered = []

        for entry in all_entries:
            # 时间过滤
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue

            # 级别过滤
            if level and entry.level != level:
                continue

            # 日志记录器过滤
            if logger and entry.logger != logger:
                continue

            # 关键词过滤
            if keyword and keyword.lower() not in entry.message.lower():
                continue

            filtered.append(entry)

            # 限制数量
            if len(filtered) >= limit:
                break

        # 按时间排序
        filtered.sort(key=lambda x: x.timestamp, reverse=True)

        return filtered

    def get_log_stats(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None
    ) -> LogStats:
        """获取日志统计

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            日志统计
        """
        entries = self.query_logs(
            start_time=start_time,
            end_time=end_time,
            limit=100000
        )

        total_count = len(entries)
        level_counts = Counter(entry.level for entry in entries)
        logger_counts = Counter(entry.logger for entry in entries)

        return LogStats(
            total_count=total_count,
            level_counts=dict(level_counts),
            logger_counts=dict(logger_counts),
            error_count=level_counts.get('ERROR', 0),
            warning_count=level_counts.get('WARNING', 0),
            info_count=level_counts.get('INFO', 0),
            debug_count=level_counts.get('DEBUG', 0)
        )

    def get_error_logs(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100
    ) -> list[LogEntry]:
        """获取错误日志

        Args:
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制

        Returns:
            错误日志列表
        """
        return self.query_logs(
            start_time=start_time,
            end_time=end_time,
            level='ERROR',
            limit=limit
        )

    def get_error_summary(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        top_n: int = 10
    ) -> list[tuple[str, int]]:
        """获取错误摘要

        Args:
            start_time: 开始时间
            end_time: 结束时间
            top_n: 返回前N个错误

        Returns:
            错误消息及其出现次数
        """
        error_logs = self.get_error_logs(
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )

        # 统计错误消息
        error_messages = [entry.message for entry in error_logs]
        error_counter = Counter(error_messages)

        # 返回前N个错误
        return error_counter.most_common(top_n)

    def get_log_trends(
        self,
        hours: int = 24
    ) -> dict[str, list[tuple[datetime, int]]]:
        """获取日志趋势

        Args:
            hours: 统计小时数

        Returns:
            各级别日志的趋势数据
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        entries = self.query_logs(
            start_time=start_time,
            end_time=end_time,
            limit=100000
        )

        # 按小时和级别统计
        trends = {level: [] for level in self.LOG_LEVELS}

        for entry in entries:
            hour = entry.timestamp.replace(minute=0, second=0, microsecond=0)
            trends[entry.level].append((hour, 1))

        # 按小时聚合
        for level in self.LOG_LEVELS:
            if trends[level]:
                counter = Counter(hour for hour, _ in trends[level])
                trends[level] = sorted(counter.items())
            else:
                trends[level] = []

        return trends


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="日志分析工具")
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="日志目录"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="统计小时数"
    )
    parser.add_argument(
        "--level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="日志级别"
    )
    parser.add_argument(
        "--keyword",
        help="关键词"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="返回数量限制"
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建日志分析器
    analyzer = LogAnalyzer(log_dir=args.log_dir)

    # 查询日志
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=args.hours)

    logs = analyzer.query_logs(
        start_time=start_time,
        end_time=end_time,
        level=args.level,
        keyword=args.keyword,
        limit=args.limit
    )

    # 输出结果
    print(f"\n找到 {len(logs)} 条日志:")
    for log in logs:
        print(f"{log.timestamp} - {log.logger} - {log.level} - {log.message}")

    # 输出统计
    stats = analyzer.get_log_stats(start_time=start_time, end_time=end_time)
    print(f"\n日志统计:")
    print(f"  总数: {stats.total_count}")
    print(f"  错误: {stats.error_count}")
    print(f"  警告: {stats.warning_count}")
    print(f"  信息: {stats.info_count}")
    print(f"  调试: {stats.debug_count}")


if __name__ == "__main__":
    main()
