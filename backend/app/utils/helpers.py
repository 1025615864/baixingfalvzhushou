"""通用工具函数

提供项目中重复使用的工具函数统一实现。
从多个 services/ 和 routers/ 中提取的公共函数。
"""

from datetime import datetime
import os
from typing import Any


def _get_int_env(key: str, default: int) -> int:
    """从环境变量获取整数配置

    Args:
        key: 环境变量名
        default: 默认值

    Returns:
        整数配置值

    Example:
        >>> _get_int_env("PORT", 8000)
        8000
    """
    raw = os.getenv(key, "").strip()
    if not raw:
        return int(default)
    try:
        return int(raw)
    except (ValueError, TypeError) as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to parse int from env {key}: {e}")
        return int(default)


def _coerce_int(value: Any, default: int = 0) -> int:
    """将任意值转换为整数

    Args:
        value: 要转换的值
        default: 默认值（转换失败时使用）

    Returns:
        整数结果

    Example:
        >>> _coerce_int("42")
        42
        >>> _coerce_int(None, 10)
        10
    """
    if value is None:
        return int(default)
    if isinstance(value, bool):
        return int(default)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return int(default)
        try:
            # 先转float再转int，支持 "3.0" 这种格式
            return int(float(s))
        except (ValueError, TypeError) as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to coerce int from value {value}: {e}")
            return int(default)
    return int(default)


def _truncate(value: str | None, max_len: int) -> str | None:
    """截断字符串到指定长度

    Args:
        value: 原始字符串
        max_len: 最大长度

    Returns:
        截断后的字符串（可能为 None）

    Example:
        >>> _truncate("hello world", 5)
        'hello'
    """
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    if len(v) <= int(max_len):
        return v
    return v[:max_len]


def _parse_dt_param(
    raw: str | None, *, field: str, end_of_day: bool = False
) -> datetime | None:
    """解析日期时间参数

    Args:
        raw: 原始字符串
        field: 字段名（用于错误信息）
        end_of_day: 是否自动调整为当天结束时间

    Returns:
        datetime 对象或 None

    Example:
        >>> _parse_dt_param("2024-01-15", field="created_at")
        datetime(2024, 1, 15, 0, 0, 0)
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # 处理 ISO 格式的 Z 后缀
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        # 如果只有日期部分且 end_of_day=True，自动调整为当天结束
        if (
            end_of_day
            and len(s) == 10
            and s[4:5] == "-"
            and s[7:8] == "-"
            and dt.hour == 0
            and dt.minute == 0
            and dt.second == 0
            and dt.microsecond == 0
        ):
            return dt.replace(hour=23, minute=59,
                              second=59, microsecond=999999)
        return dt
    except (ValueError, TypeError) as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to parse datetime for field {field}: {e}")
        
        # 抛出 ValueError 而不是 HTTPException，避免与 Web 框架耦合
        raise ValueError(f"Invalid datetime format for field {field}")
