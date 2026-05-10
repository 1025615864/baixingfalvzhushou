from __future__ import annotations

import time
from datetime import datetime
from typing import Any


async def get_detailed_health(settings: object) -> dict[str, Any]:
    checks: dict[str, object] = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }

    checks_detail = checks.get("checks")
    if not isinstance(checks_detail, dict):
        checks_detail = {}
        checks["checks"] = checks_detail

    try:
        from sqlalchemy import text
        from app.database import engine
        start = time.time()
        async with engine.connect() as conn:
            _ = await conn.execute(text("SELECT 1"))
        db_time = (time.time() - start) * 1000
        checks_detail["database"] = {
            "status": "ok",
            "response_time_ms": round(db_time, 2)
        }
    except Exception as e:
        checks["status"] = "degraded"
        checks_detail["database"] = {
            "status": "error",
            "error": str(e)
        }

    if getattr(settings, "openai_api_key", None):
        checks_detail["ai_service"] = {"status": "configured"}
    else:
        checks_detail["ai_service"] = {"status": "not_configured"}

    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        rss_bytes = int(getattr(mem_info, "rss", 0) or 0)
        memory_mb = float(rss_bytes) / 1024.0 / 1024.0
        checks_detail["memory"] = {
            "status": "ok",
            "usage_mb": round(memory_mb, 2)
        }
    except ImportError:
        checks_detail["memory"] = {"status": "unknown"}

    return checks
