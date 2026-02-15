"""数据库连接池监控脚本

定期收集数据库连接池状态并上报到Prometheus指标。
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加backend目录到路径
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


async def monitor_db_pool():
    """监控数据库连接池状态"""
    try:
        from app.services.prometheus_metrics import prometheus_metrics
        from app.database import engine

        # 获取连接池状态
        pool = engine.pool
        if pool is None:
            print("No connection pool available")
            return

        # 记录连接池指标
        prometheus_metrics.record_db_pool(
            pool_name="default",
            active_connections=pool.size() - pool.checkedout(),
            idle_connections=pool.checkedout(),
            total_connections=pool.size(),
            max_connections=pool.maxsize,
            checked_out=pool.checkedout(),
            overflow=pool.overflow(),
        )

        print(f"[{datetime.now()}] DB Pool: active={pool.size() - pool.checkedout()}, "
              f"idle={pool.checkedout()}, total={pool.size()}, "
              f"max={pool.maxsize}, overflow={pool.overflow()}")

    except Exception as e:
        print(f"[{datetime.now()}] Error monitoring DB pool: {e}")


async def main():
    """主函数"""
    print("Starting database pool monitoring...")
    
    while True:
        await monitor_db_pool()
        await asyncio.sleep(10)  # 每10秒收集一次


if __name__ == "__main__":
    asyncio.run(main())
