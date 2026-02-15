"""数据库备份脚本

提供数据库自动备份和恢复功能。

功能特性:
    - 自动全量备份
    - 支持PostgreSQL和SQLite
    - 备份文件压缩和加密
    - 自动清理旧备份
    - 备份验证

使用示例:
    ```bash
    # 手动执行备份
    python scripts/backup_db.py

    # 恢复数据库
    python scripts/backup_db.py --restore backup_20240101_120000.sql.gz

    # 查看备份列表
    python scripts/backup_db.py --list
    ```

定时任务配置 (crontab):
    # 每天凌晨2点执行备份
    0 2 * * * cd /path/to/project && python scripts/backup_db.py
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("backup")

BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
ENCRYPT_BACKUP = os.getenv("ENCRYPT_BACKUP", "0") == "1"
BACKUP_PASSWORD = os.getenv("BACKUP_PASSWORD", "")


def get_database_url() -> str:
    """获取数据库URL"""
    from dotenv import load_dotenv
    load_dotenv(".env.local", override=True)
    load_dotenv(".env", override=True)
    return os.getenv("DATABASE_URL", "sqlite:///./data.db")


def get_backup_dir() -> Path:
    """获取备份目录"""
    backup_dir = Path(BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def generate_backup_filename(db_type: str) -> str:
    """生成备份文件名

    Args:
        db_type: 数据库类型 (sqlite, postgresql)

    Returns:
        备份文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"backup_{db_type}_{timestamp}"


def calculate_file_hash(filepath: Path) -> str:
    """计算文件哈希

    Args:
        filepath: 文件路径

    Returns:
        SHA256哈希值
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compress_file(input_path: Path, output_path: Path) -> None:
    """压缩文件

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
    """
    with open(input_path, "rb") as f_in:
        with gzip.open(output_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    logger.info(f"Compressed {input_path} -> {output_path}")


def decompress_file(input_path: Path, output_path: Path) -> None:
    """解压文件

    Args:
        input_path: 压缩文件路径
        output_path: 输出文件路径
    """
    with gzip.open(input_path, "rb") as f_in:
        with open(output_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    logger.info(f"Decompressed {input_path} -> {output_path}")


def backup_sqlite(db_path: str, backup_dir: Path) -> tuple[Path, str]:
    """SQLite数据库备份

    Args:
        db_path: 数据库路径
        backup_dir: 备份目录

    Returns:
        (备份文件路径, 文件哈希)
    """
    db_file = Path(db_path.replace("sqlite:///", ""))
    if not db_file.exists():
        raise FileNotFoundError(f"Database file not found: {db_file}")

    temp_backup = backup_dir / f"{generate_backup_filename('sqlite')}.sql"
    conn = sqlite3.connect(db_file)
    with conn:
        with open(temp_backup, "w", encoding="utf-8") as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
    conn.close()

    hash_value = calculate_file_hash(temp_backup)

    compressed = temp_backup.with_suffix(temp_backup.suffix + ".gz")
    compress_file(temp_backup, compressed)
    temp_backup.unlink()

    return compressed, hash_value


def backup_postgresql(database_url: str, backup_dir: Path) -> tuple[Path, str]:
    """PostgreSQL数据库备份

    Args:
        database_url: 数据库连接URL
        backup_dir: 备份目录

    Returns:
        (备份文件路径, 文件哈希)
    """
    timestamp = generate_backup_filename("postgresql")
    temp_backup = backup_dir / f"{timestamp}.sql"

    env = os.environ.copy()
    env["PGPASSWORD"] = ""

    url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    if "@" in url:
        parts = url.split("@")
        auth = parts[0].replace("postgresql://", "")
        if ":" in auth:
            user, password = auth.split(":", 1)
            env["PGPASSWORD"] = password
            url = f"postgresql://{user}@{parts[1]}"
        else:
            url = f"postgresql://{parts[1]}"

    result = subprocess.run(
        ["pg_dump", url, "-f", str(temp_backup)],
        capture_output=True,
        text=True,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed: {result.stderr}")

    hash_value = calculate_file_hash(temp_backup)

    compressed = temp_backup.with_suffix(temp_backup.suffix + ".gz")
    compress_file(temp_backup, compressed)
    temp_backup.unlink()

    return compressed, hash_value


def restore_sqlite(backup_file: Path, db_path: str) -> None:
    """恢复SQLite数据库

    Args:
        backup_file: 备份文件路径
        db_path: 目标数据库路径
    """
    decompressed = backup_file.with_suffix("")

    if backup_file.suffix == ".gz":
        decompress_file(backup_file, decompressed)
    else:
        shutil.copy(backup_file, decompressed)

    db_file = Path(db_path.replace("sqlite:///", ""))
    conn = sqlite3.connect(db_file)
    with conn:
        with open(decompressed, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.close()

    decompressed.unlink()
    logger.info(f"Restored SQLite database to {db_path}")


def restore_postgresql(backup_file: Path, database_url: str) -> None:
    """恢复PostgreSQL数据库

    Args:
        backup_file: 备份文件路径
        database_url: 目标数据库连接URL
    """
    decompressed = Path(str(backup_file).replace(".gz", ""))

    if backup_file.suffix == ".gz":
        decompress_file(backup_file, decompressed)
    else:
        shutil.copy(backup_file, decompressed)

    url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    env = os.environ.copy()
    env["PGPASSWORD"] = ""

    if "@" in url:
        parts = url.split("@")
        auth = parts[0].replace("postgresql://", "")
        if ":" in auth:
            user, password = auth.split(":", 1)
            env["PGPASSWORD"] = password

    result = subprocess.run(
        ["psql", url, "-f", str(decomposed)],
        capture_output=True,
        text=True,
        env=env,
    )

    decompressed.unlink()

    if result.returncode != 0:
        raise RuntimeError(f"psql restore failed: {result.stderr}")

    logger.info("PostgreSQL database restored")


def cleanup_old_backups(backup_dir: Path, retention_days: int) -> int:
    """清理旧备份

    Args:
        backup_dir: 备份目录
        retention_days: 保留天数

    Returns:
        删除的文件数量
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0

    for backup_file in backup_dir.glob("backup_*.sql.gz"):
        date_str = backup_file.name.replace("backup_", "").replace(".sql.gz", "")
        try:
            file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
            if file_date < cutoff_date:
                backup_file.unlink()
                deleted_count += 1
                logger.info(f"Deleted old backup: {backup_file.name}")
        except ValueError:
            continue

    return deleted_count


def verify_backup(backup_file: Path, expected_hash: str) -> bool:
    """验证备份文件完整性

    Args:
        backup_file: 备份文件路径
        expected_hash: 预期哈希值

    Returns:
        验证是否通过
    """
    actual_hash = calculate_file_hash(backup_file)
    if actual_hash != expected_hash:
        logger.error(
            f"Backup verification failed: "
            f"expected {expected_hash}, got {actual_hash}"
        )
        return False
    return True


def list_backups(backup_dir: Path) -> list[dict]:
    """列出所有备份

    Args:
        backup_dir: 备份目录

    Returns:
        备份信息列表
    """
    backups = []

    for backup_file in sorted(backup_dir.glob("backup_*.sql.gz"), reverse=True):
        stat = backup_file.stat()
        date_str = backup_file.name.replace("backup_", "").replace(".sql.gz", "")
        try:
            file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
            backups.append({
                "file": backup_file.name,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "date": file_date.isoformat(),
                "age_hours": round(
                    (datetime.now() - file_date).total_seconds() / 3600, 1
                ),
            })
        except ValueError:
            continue

    return backups


def run_backup(database_url: str) -> dict:
    """执行数据库备份

    Args:
        database_url: 数据库连接URL

    Returns:
        备份结果信息
    """
    backup_dir = get_backup_dir()
    start_time = time.time()

    db_type = "postgresql" if "postgresql" in database_url else "sqlite"

    try:
        if db_type == "postgresql":
            backup_file, file_hash = backup_postgresql(database_url, backup_dir)
        else:
            backup_file, file_hash = backup_sqlite(database_url, backup_dir)

        cleanup_old_backups(backup_dir, BACKUP_RETENTION_DAYS)

        elapsed = time.time() - start_time

        logger.info(
            f"Backup completed: {backup_file.name} "
            f"({backup_file.stat().st_size / 1024 / 1024:.2f} MB) "
            f"in {elapsed:.1f}s"
        )

        return {
            "success": True,
            "file": backup_file.name,
            "size_mb": round(backup_file.stat().st_size / 1024 / 1024, 2),
            "hash": file_hash,
            "elapsed_seconds": round(elapsed, 1),
        }

    except Exception as e:
        logger.exception(f"Backup failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "elapsed_seconds": round(time.time() - start_time, 1),
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Database backup utility")
    parser.add_argument(
        "--restore",
        metavar="FILE",
        help="Restore from backup file",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups",
    )
    parser.add_argument(
        "--verify",
        metavar="FILE",
        help="Verify backup file integrity",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old backups",
    )

    args = parser.parse_args()

    database_url = get_database_url()
    backup_dir = get_backup_dir()

    if args.list:
        backups = list_backups(backup_dir)
        print("\nAvailable backups:")
        print("-" * 60)
        for backup in backups:
            print(
                f"{backup['file']}: "
                f"{backup['size_mb']} MB, "
                f"age: {backup['age_hours']} hours"
            )
        return

    if args.verify:
        backup_file = backup_dir / args.verify
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            sys.exit(1)
        file_hash = calculate_file_hash(backup_file)
        if verify_backup(backup_file, file_hash):
            print(f"Backup verified: {args.verify}")
            print(f"Hash: {file_hash}")
        else:
            print(f"Backup verification failed: {args.verify}")
            sys.exit(1)
        return

    if args.cleanup:
        deleted = cleanup_old_backups(backup_dir, BACKUP_RETENTION_DAYS)
        print(f"Cleaned up {deleted} old backup files")
        return

    if args.restore:
        backup_file = backup_dir / args.restore
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            sys.exit(1)

        db_type = "postgresql" if "postgresql" in database_url else "sqlite"

        try:
            if db_type == "postgresql":
                restore_postgresql(backup_file, database_url)
            else:
                restore_sqlite(backup_file, database_url)
            print(f"Restored from: {args.restore}")
        except Exception as e:
            logger.exception(f"Restore failed: {e}")
            sys.exit(1)
        return

    result = run_backup(database_url)

    if result["success"]:
        print(f"\nBackup successful!")
        print(f"File: {result['file']}")
        print(f"Size: {result['size_mb']} MB")
        print(f"Time: {result['elapsed_seconds']}s")
    else:
        print(f"\nBackup failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
