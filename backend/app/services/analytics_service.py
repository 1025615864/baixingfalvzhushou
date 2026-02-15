"""用户行为埋点SDK服务（向后兼容）

该模块已重构，核心组件已拆分到 analytics/ 目录：
- from ..services.analytics.core import AnalyticsService  # 用户行为分析服务

向后兼容导入仍然可用。
"""

# 重新导出核心组件（向后兼容）
from .analytics import (
    AnalyticsService,
)

# 保持原有文件的完整内容（向后兼容）
# 这样可以确保向后兼容，不需要修改任何调用方

_analytics_service = None


def get_analytics_service() -> AnalyticsService:
    """获取分析服务实例（懒加载）"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


# 实例化单例（保持原有使用方式）
analytics_service = AnalyticsService()
