"""自动化运维脚本

提供备份、恢复、扩缩容等关键运维操作功能。
"""
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _sanitize_filename(filename: str) -> str:
    """
    清理文件名，防止路径遍历攻击
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
        
    Raises:
        ValueError: 文件名包含非法字符
    """
    # 移除路径分隔符和危险字符
    sanitized = re.sub(r'[\\/<>"|?*\x00-\x1f]', '', filename)
    # 移除 .. 序列
    sanitized = sanitized.replace('..', '')
    # 移除首尾空格和点
    sanitized = sanitized.strip('. ')
    
    if not sanitized:
        raise ValueError("文件名不能为空或只包含特殊字符")
    
    return sanitized


def _validate_backup_path(backup_path: Path, backup_dir: Path) -> bool:
    """
    验证备份文件路径是否在允许的备份目录内，防止路径遍历
    
    Args:
        backup_path: 待验证的备份文件路径
        backup_dir: 允许的备份目录
        
    Returns:
        bool: 路径是否有效
    """
    try:
        # 解析为绝对路径
        backup_path = backup_path.resolve()
        backup_dir = backup_dir.resolve()
        
        # 检查文件是否在备份目录内
        return str(backup_path).startswith(str(backup_dir))
    except (OSError, ValueError) as e:
        logger.warning(f"备份路径验证失败: {e}")
        return False


class BackupManager:
    """备份管理器"""

    BACKUP_DIR = Path(__file__).parent.parent.parent / "backups"

    def __init__(self):
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    async def backup_database(
        self,
        db_url: str | None = None,
        backup_name: str | None = None,
    ) -> dict[str, Any]:
        """备份数据库

        Args:
            db_url: 数据库连接 URL
            backup_name: 备份名称（可选）

        Returns:
            备份结果
        """
        if backup_name is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_name = f"db_backup_{timestamp}"
        else:
            # 清理文件名，防止路径遍历
            try:
                backup_name = _sanitize_filename(backup_name)
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"无效的备份名称: {e}",
                }

        backup_file = self.BACKUP_DIR / f"{backup_name}.sql"

        try:
            cmd = [
                "pg_dump",
                "-h", "localhost",
                "-U", "postgres",
                "-d", "baixing_law",
                "-f", str(backup_file),
            ]

            env = os.environ.copy()
            if db_url:
                env["DATABASE_URL"] = db_url

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                file_size = backup_file.stat().st_size
                logger.info(f"Database backup completed: {backup_file}")
                return {
                    "success": True,
                    "backup_file": str(backup_file),
                    "file_size": file_size,
                    "backup_name": backup_name,
                }
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                }

        except subprocess.TimeoutExpired:
            logger.error("Database backup timed out")
            return {
                "success": False,
                "error": "Backup timed out after 300 seconds",
            }
        except Exception as e:
            logger.error(f"Database backup error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def restore_database(
        self,
        backup_file: str,
        db_url: str | None = None,
    ) -> dict[str, Any]:
        """恢复数据库

        Args:
            backup_file: 备份文件路径
            db_url: 数据库连接 URL

        Returns:
            恢复结果
        """
        backup_path = Path(backup_file)
        
        # 验证备份文件路径，防止路径遍历攻击
        if not _validate_backup_path(backup_path, self.BACKUP_DIR):
            logger.warning(f"非法的备份文件路径: {backup_file}")
            return {
                "success": False,
                "error": "非法的备份文件路径，必须在备份目录内",
            }

        if not backup_path.exists():
            return {
                "success": False,
                "error": f"Backup file not found: {backup_file}",
            }

        try:
            cmd = [
                "psql",
                "-h", "localhost",
                "-U", "postgres",
                "-d", "baixing_law",
                "-f", str(backup_path),
            ]

            env = os.environ.copy()
            if db_url:
                env["DATABASE_URL"] = db_url

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                logger.info(f"Database restore completed: {backup_file}")
                return {
                    "success": True,
                    "backup_file": backup_file,
                    "message": "Database restored successfully",
                }
            else:
                logger.error(f"Database restore failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                }

        except subprocess.TimeoutExpired:
            logger.error("Database restore timed out")
            return {
                "success": False,
                "error": "Restore timed out after 600 seconds",
            }
        except Exception as e:
            logger.error(f"Database restore error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def list_backups(self) -> dict[str, Any]:
        """列出所有备份

        Returns:
            备份列表
        """
        backups: list[dict[str, Any]] = []
        for backup_file in sorted(self.BACKUP_DIR.glob("*.sql"), reverse=True):
            backups.append({
                "name": backup_file.stem,
                "path": str(backup_file),
                "size": backup_file.stat().st_size,
                "created_at": datetime.fromtimestamp(
                    backup_file.stat().st_ctime,
                    tz=timezone.utc,
                ).isoformat(),
            })

        return {
            "backups": backups,
            "total_count": len(backups),
        }


class ScaleManager:
    """扩缩容管理器"""

    async def scale_service(
        self,
        service_name: str,
        replicas: int,
        compose_file: str = "docker-compose.yml",
    ) -> dict[str, Any]:
        """扩缩容服务

        Args:
            service_name: 服务名称
            replicas: 副本数
            compose_file: Docker Compose 文件

        Returns:
            操作结果
        """
        try:
            cmd = [
                "docker", "compose",
                "-f", compose_file,
                "up", "-d",
                "--scale", f"{service_name}={replicas}",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                logger.info(f"Scaled {service_name} to {replicas} replicas")
                return {
                    "success": True,
                    "service": service_name,
                    "replicas": replicas,
                    "message": f"Service scaled to {replicas} replicas",
                }
            else:
                logger.error(f"Scale failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                }

        except subprocess.TimeoutExpired:
            logger.error("Scale operation timed out")
            return {
                "success": False,
                "error": "Scale operation timed out after 120 seconds",
            }
        except Exception as e:
            logger.error(f"Scale error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_service_status(
        self,
        service_name: str,
    ) -> dict[str, Any]:
        """获取服务状态

        Args:
            service_name: 服务名称

        Returns:
            服务状态
        """
        try:
            cmd = [
                "docker", "ps",
                "--filter", f"name={service_name}",
                "--format", "{{.Names}} {{.Status}}",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines and lines[0]:
                    parts = lines[0].split()
                    return {
                        "service": service_name,
                        "running": True,
                        "status": " ".join(parts[1:]) if len(parts) > 1 else "unknown",
                    }

            return {
                "service": service_name,
                "running": False,
                "status": "not found",
            }

        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {
                "service": service_name,
                "running": False,
                "error": str(e),
            }


class HealthChecker:
    """健康检查器"""

    async def check_all_services(self) -> dict[str, Any]:
        """检查所有服务健康状态

        Returns:
            健康检查结果
        """
        services = ["backend", "db", "redis"]
        results: dict[str, Any] = {}

        for service in services:
            status = await ScaleManager().get_service_status(service)
            results[service] = status

        all_healthy = all(
            s.get("running", False) for s in results.values()
        )

        return {
            "healthy": all_healthy,
            "services": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# 单例实例
backup_manager = BackupManager()
scale_manager = ScaleManager()
health_checker = HealthChecker()


async def backup_database(
    db_url: str | None = None,
    backup_name: str | None = None,
) -> dict[str, Any]:
    """便捷函数：备份数据库

    Args:
        db_url: 数据库连接 URL
        backup_name: 备份名称

    Returns:
        备份结果
    """
    return await backup_manager.backup_database(db_url=db_url, backup_name=backup_name)


async def restore_database(
    backup_file: str,
    db_url: str | None = None,
) -> dict[str, Any]:
    """便捷函数：恢复数据库

    Args:
        backup_file: 备份文件路径
        db_url: 数据库连接 URL

    Returns:
        恢复结果
    """
    return await backup_manager.restore_database(backup_file=backup_file, db_url=db_url)


async def scale_service(
    service_name: str,
    replicas: int,
) -> dict[str, Any]:
    """便捷函数：扩缩容服务

    Args:
        service_name: 服务名称
        replicas: 副本数

    Returns:
        操作结果
    """
    return await scale_manager.scale_service(service_name=service_name, replicas=replicas)


async def check_services_health() -> dict[str, Any]:
    """便捷函数：检查所有服务健康状态

    Returns:
        健康检查结果
    """
    return await health_checker.check_all_services()
