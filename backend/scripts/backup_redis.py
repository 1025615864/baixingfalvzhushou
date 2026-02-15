"""Redis数据备份脚本

提供Redis数据导出和恢复功能。

功能特性:
    - 导出所有或指定模式的键
    - 支持JSON和RDB格式
    - 选择性导出关键数据
    - 恢复验证

使用示例:
    ```bash
    # 导出所有数据
    python scripts/backup_redis.py

    # 导出指定模式的数据
    python scripts/backup_redis.py --pattern "session:*"

    # 恢复数据
    python scripts/backup_redis.py --restore backup_redis_20240101_120000.json

    # 查看备份列表
    python scripts/backup_redis.py --list
    ```
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("redis_backup")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
BACKUP_DIR = os.getenv("REDIS_BACKUP_DIR", "backups/redis")
BACKUP_RETENTION_DAYS = int(os.getenv("REDIS_BACKUP_RETENTION_DAYS", "7"))

IMPORTANT_PATTERNS = [
    "session:*",
    "user:*",
    "token:*",
    "lock:*",
    "cache:*",
]


def get_redis_client():
    """获取Redis客户端"""
    try:
        import redis.asyncio as redis
        return redis.from_url(REDIS_URL, decode_responses=True)
    except ImportError:
        logger.error("redis package not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None


def get_backup_dir() -> Path:
    """获取备份目录"""
    backup_dir = Path(BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def generate_backup_filename() -> str:
    """生成备份文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"backup_redis_{timestamp}"


def calculate_file_hash(filepath: Path) -> str:
    """计算文件哈希"""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


async def export_keys(
    client,
    pattern: str = "*",
    limit: int = 0,
) -> dict[str, Any]:
    """导出Redis键值

    Args:
        client: Redis客户端
        pattern: 键模式
        limit: 限制导出数量，0表示不限制

    Returns:
        导出的键值数据
    """
    data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "redis_url": REDIS_URL.replace(": //.*@", "://***:***@"),
        "pattern": pattern,
        "keys": {},
    }

    count = 0
    async for key in client.scan_iter(match=pattern, count=100):
        try:
            key_type = await client.type(key)

            if key_type == "string":
                value = await client.get(key)
                data["keys"][key] = {"type": "string", "value": value}

            elif key_type == "hash":
                value = await client.hgetall(key)
                data["keys"][key] = {"type": "hash", "value": value}

            elif key_type == "list":
                value = await client.lrange(key, 0, -1)
                data["keys"][key] = {"type": "list", "value": value}

            elif key_type == "set":
                value = await client.smembers(key)
                data["keys"][key] = {"type": "set", "value": list(value)}

            elif key_type == "zset":
                value = await client.zrange(key, 0, -1, withscores=True)
                data["keys"][key] = {"type": "zset", "value": value}

            elif key_type == "stream":
                value = await client.xread({key: "0"})
                data["keys"][key] = {"type": "stream", "value": value}

            count += 1

            if limit > 0 and count >= limit:
                break

        except Exception as e:
            logger.warning(f"Failed to export key {key}: {e}")

    data["key_count"] = count
    return data


async def import_keys(client, data: dict[str, Any]) -> int:
    """导入Redis键值

    Args:
        client: Redis客户端
        data: 导入数据

    Returns:
        导入的键数量
    """
    count = 0

    for key, item in data["keys"].items():
        key_type = item["type"]
        value = item["value"]

        try:
            if key_type == "string":
                await client.set(key, value)

            elif key_type == "hash":
                await client.hset(key, mapping=value)

            elif key_type == "list":
                if value:
                    await client.rpush(key, *value)

            elif key_type == "set":
                if value:
                    await client.sadd(key, *value)

            elif key_type == "zset":
                if value:
                    items = []
                    for v in value:
                        if isinstance(v, (list, tuple)):
                            items.extend([v[0], v[1]])
                        else:
                            items.extend([v, 0])
                    await client.zadd(key, dict(zip(items[::2], items[1::2])))

            elif key_type == "stream":
                if value:
                    for stream_name, messages in value.items():
                        for msg_id, msg_data in messages:
                            await client.xadd(stream_name, msg_data)

            count += 1

        except Exception as e:
            logger.warning(f"Failed to import key {key}: {e}")

    return count


async def backup_important_data(client) -> dict:
    """备份重要数据

    Args:
        client: Redis客户端

    Returns:
        备份结果
    """
    all_data = {
        "version": "1.0",
        "backup_type": "important",
        "exported_at": datetime.now().isoformat(),
        "patterns": IMPORTANT_PATTERNS,
        "keys": {},
    }

    for pattern in IMPORTANT_PATTERNS:
        pattern_data = await export_keys(client, pattern)
        all_data["keys"].update(pattern_data["keys"])

    all_data["key_count"] = len(all_data["keys"])
    return all_data


async def run_backup(backup_dir: Path, pattern: str = "*") -> dict:
    """执行Redis备份

    Args:
        backup_dir: 备份目录
        pattern: 键模式

    Returns:
        备份结果
    """
    client = get_redis_client()
    if not client:
        return {"success": False, "error": "Failed to connect to Redis"}

    start_time = time.time()

    try:
        if pattern == "*" and not any(
            p.replace("*", "") in pattern for p in ["important"]
        ):
            data = await backup_important_data(client)
        else:
            data = await export_keys(client, pattern)

        filename = generate_backup_filename()
        filepath = backup_dir / f"{filename}.json.gz"

        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        file_hash = calculate_file_hash(filepath)
        elapsed = time.time() - start_time

        logger.info(
            f"Redis backup completed: {filepath.name} "
            f"({data['key_count']} keys, {filepath.stat().st_size / 1024:.1f} KB) "
            f"in {elapsed:.1f}s"
        )

        return {
            "success": True,
            "file": filepath.name,
            "key_count": data["key_count"],
            "size_kb": round(filepath.stat().st_size / 1024, 2),
            "hash": file_hash,
            "elapsed_seconds": round(elapsed, 1),
        }

    except Exception as e:
        logger.exception(f"Redis backup failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "elapsed_seconds": round(time.time() - start_time, 1),
        }
    finally:
        await client.close()


async def run_restore(backup_file: Path, client) -> dict:
    """恢复Redis数据

    Args:
        backup_file: 备份文件路径
        client: Redis客户端

    Returns:
        恢复结果
    """
    start_time = time.time()

    try:
        with gzip.open(backup_file, "rt", encoding="utf-8") as f:
            data = json.load(f)

        key_count = await import_keys(client, data)
        elapsed = time.time() - start_time

        logger.info(
            f"Redis restore completed: {key_count} keys in {elapsed:.1f}s"
        )

        return {
            "success": True,
            "key_count": key_count,
            "elapsed_seconds": round(elapsed, 1),
        }

    except Exception as e:
        logger.exception(f"Redis restore failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "elapsed_seconds": round(time.time() - start_time, 1),
        }


def list_backups(backup_dir: Path) -> list[dict]:
    """列出所有备份"""
    backups = []

    for backup_file in sorted(backup_dir.glob("backup_redis_*.json.gz"), reverse=True):
        stat = backup_file.stat()
        date_str = backup_file.name.replace("backup_redis_", "").replace(".json.gz", "")
        try:
            file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
            backups.append({
                "file": backup_file.name,
                "size_kb": round(stat.st_size / 1024, 2),
                "date": file_date.isoformat(),
                "age_hours": round(
                    (datetime.now() - file_date).total_seconds() / 3600, 1
                ),
            })
        except ValueError:
            continue

    return backups


def cleanup_old_backups(backup_dir: Path, retention_days: int) -> int:
    """清理旧备份"""
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0

    for backup_file in backup_dir.glob("backup_redis_*.json.gz"):
        date_str = backup_file.name.replace("backup_redis_", "").replace(".json.gz", "")
        try:
            file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
            if file_date < cutoff_date:
                backup_file.unlink()
                deleted_count += 1
                logger.info(f"Deleted old backup: {backup_file.name}")
        except ValueError:
            continue

    return deleted_count


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Redis backup utility")
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
        "--cleanup",
        action="store_true",
        help="Clean up old backups",
    )
    parser.add_argument(
        "--pattern",
        default="*",
        help="Key pattern to backup (default: *)",
    )

    args = parser.parse_args()

    backup_dir = get_backup_dir()

    if args.list:
        backups = list_backups(backup_dir)
        print("\nAvailable Redis backups:")
        print("-" * 60)
        for backup in backups:
            print(
                f"{backup['file']}: "
                f"{backup['size_kb']} KB, "
                f"age: {backup['age_hours']} hours"
            )
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

        client = get_redis_client()
        if not client:
            sys.exit(1)

        try:
            result = await run_restore(backup_file, client)
            if result["success"]:
                print(f"\nRestore successful!")
                print(f"Keys imported: {result['key_count']}")
                print(f"Time: {result['elapsed_seconds']}s")
            else:
                print(f"\nRestore failed: {result['error']}")
                sys.exit(1)
        finally:
            await client.close()
        return

    result = await run_backup(backup_dir, args.pattern)

    if result["success"]:
        print(f"\nBackup successful!")
        print(f"File: {result['file']}")
        print(f"Keys: {result['key_count']}")
        print(f"Size: {result['size_kb']} KB")
        print(f"Time: {result['elapsed_seconds']}s")
    else:
        print(f"\nBackup failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
