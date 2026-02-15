"""积分系统服务

提供积分获取、消耗、兑换等功能。
"""

from .points_service import (
    PointsService,
    PointsAction,
    PointsRule,
    PointsHistoryItem,
    POINTS_RULES,
    get_points_service,
    award_points,
    redeem_points,
    get_balance,
)

from .points_service_base import (
    PointsAction,
    PointsRule,
    POINTS_RULES,
    get_vip_multiplier,
    get_points_rule,
)

from .points_service_db import (
    PointsServiceDB,
    get_balance_db,
    award_points_db,
    redeem_points_db,
)

from .product_service import (
    PointsProductService,
    PointsProduct,
    PointsExchangeOrder,
    get_points_product_service,
)

from .scheduled_tasks import (
    PointsScheduledTasks,
    get_points_scheduled_tasks,
)

__all__ = [
    # 内存版积分服务 (兼容)
    "PointsService",
    "PointsAction",
    "PointsRule",
    "PointsHistoryItem",
    "POINTS_RULES",
    "get_points_service",
    "award_points",
    "redeem_points",
    "get_balance",

    # 基础定义
    "get_vip_multiplier",
    "get_points_rule",

    # 数据库版积分服务
    "PointsServiceDB",
    "get_balance_db",
    "award_points_db",
    "redeem_points_db",

    # 商品服务
    "PointsProductService",
    "PointsProduct",
    "PointsExchangeOrder",
    "get_points_product_service",

    # 定时任务
    "PointsScheduledTasks",
    "get_points_scheduled_tasks",
]
