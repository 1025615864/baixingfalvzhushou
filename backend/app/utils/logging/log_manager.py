"""日志管理工具

提供日志保留、清理和归档功能。
"""
from __future__ import annotations

import gzip
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class LogManager:
    """日志管理器"""

    def __init__(
        self,
        log_dir: str = "logs",
        retention_days: int = 30,
        max_size_mb: int = 100,
        max_files: int = 10
    ):
        """初始化日志管理器

        Args:
            log_dir: 日志目录
            retention_days: 日志保留天数
            max_size_mb: 单个日志文件最大大小（MB）
            max_files: 保留的日志文件数量
        """
        self.log_dir = Path(log_dir)
        self.retention_days = retention_days
        self.max_size_mb = max_size_mb
        self.max_files = max_files

    def cleanup_old_logs(self) -> None:
        """清理过期日志"""
        if not self.log_dir.exists():
            logger.info(f"日志目录不存在: {self.log_dir}")
            return

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        for log_file in self.log_dir.glob("**/*.log*"):
            try:
                # 获取文件修改时间
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

                # 如果文件过期，删除
                if file_mtime < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"删除过期日志: {log_file}")
            except Exception as e:
                logger.error(f"删除日志文件失败 {log_file}: {str(e)}")

        logger.info(f"清理完成，共删除 {deleted_count} 个过期日志文件")

    def archive_logs(self) -> None:
        """归档日志文件"""
        if not self.log_dir.exists():
            return

        archive_dir = self.log_dir / "archive"
        archive_dir.mkdir(exist_ok=True)

        for log_file in self.log_dir.glob("*.log"):
            if log_file.is_file():
                try:
                    # 创建归档文件名
                    archive_name = f"{log_file.stem}_{datetime.now().strftime('%Y%m%d')}.log.gz"
                    archive_path = archive_dir / archive_name

                    # 压缩日志
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(archive_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # 删除原文件
                    log_file.unlink()
                    logger.info(f"归档日志: {log_file} -> {archive_path}")
                except Exception as e:
                    logger.error(f"归档日志失败 {log_file}: {str(e)}")

    def rotate_logs(self) -> None:
        """轮转日志文件"""
        if not self.log_dir.exists():
            return

        for log_file in self.log_dir.glob("*.log"):
            if log_file.is_file():
                try:
                    # 检查文件大小
                    file_size_mb = log_file.stat().st_size / (1024 * 1024)

                    if file_size_mb > self.max_size_mb:
                        # 轮转日志
                        archive_name = f"{log_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                        archive_path = self.log_dir / archive_name

                        # 重命名原文件
                        log_file.rename(archive_path)
                        logger.info(f"轮转日志: {log_file} -> {archive_path}")
                except Exception as e:
                    logger.error(f"轮转日志失败 {log_file}: {str(e)}")

    def limit_log_files(self) -> None:
        """限制日志文件数量"""
        if not self.log_dir.exists():
            return

        # 获取所有日志文件
        log_files = list(self.log_dir.glob("*.log*"))

        # 按修改时间排序
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # 删除超出数量限制的文件
        if len(log_files) > self.max_files:
            for log_file in log_files[self.max_files:]:
                try:
                    log_file.unlink()
                    logger.info(f"删除多余日志: {log_file}")
                except Exception as e:
                    logger.error(f"删除日志文件失败 {log_file}: {str(e)}")

    def run_maintenance(self) -> None:
        """执行日志维护"""
        logger.info("开始日志维护")

        try:
            # 清理过期日志
            self.cleanup_old_logs()

            # 轮转日志
            self.rotate_logs()

            # 限制文件数量
            self.limit_log_files()

            # 归档日志
            self.archive_logs()

            logger.info("日志维护完成")
        except Exception as e:
            logger.error(f"日志维护失败: {str(e)}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="日志管理工具")
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="日志目录"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="日志保留天数"
    )
    parser.add_argument(
        "--max-size-mb",
        type=int,
        default=100,
        help="单个日志文件最大大小（MB）"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=10,
        help="保留的日志文件数量"
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建日志管理器
    manager = LogManager(
        log_dir=args.log_dir,
        retention_days=args.retention_days,
        max_size_mb=args.max_size_mb,
        max_files=args.max_files
    )

    # 执行维护
    manager.run_maintenance()


if __name__ == "__main__":
    main()
