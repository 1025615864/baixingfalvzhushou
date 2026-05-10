"""数据库查询优化工具

提供 N+1 查询检测、批量加载和查询优化功能。
"""
import logging
from datetime import datetime
from typing import Any, Optional, TypeVar, Protocol

from sqlalchemy import select, func, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class QueryCounter:
    """查询计数器（用于检测 N+1）"""

    def __init__(self):
        self.query_count = 0
        self.queries: list[dict[str, Any]] = []
        self.enabled = False

    def reset(self) -> None:
        """重置计数器"""
        self.query_count = 0
        self.queries = []

    def enable(self) -> None:
        """启用计数"""
        self.enabled = True
        self.reset()

    def disable(self) -> None:
        """禁用计数"""
        self.enabled = False

    def record(self, query: str,
               params: Optional[dict[str, Any]] = None) -> None:
        """记录查询"""
        if self.enabled:
            self.query_count += 1
            self.queries.append({
                "query": query,
                "params": params,
                "time": datetime.now().isoformat(),
            })

    def get_report(self) -> dict[str, Any]:
        """获取报告"""
        return {
            "total_queries": self.query_count,
            "queries": self.queries,
        }


query_counter = QueryCounter()


async def batch_load_related(
    db: AsyncSession,
    model: type,
    ids: list[int],
    relation_attr: str,
) -> dict[int, list[Any]]:
    """批量加载关联数据

    Args:
        db: 数据库会话
        model: 主模型类
        ids: 主模型 ID 列表
        relation_attr: 关联属性名

    Returns:
        字典，key 为主模型 ID，value 为关联对象列表
    """
    if not ids:
        return {}

    mapper = inspect(model)
    relationship = mapper.relationships.get(relation_attr)
    if relationship is None:
        logger.warning(f"Relation '{relation_attr}' not found on model {model.__name__}")
        return {}

    related_model = relationship.entity.class_
    related_id_attr = list(relationship.local_columns)[0].name

    stmt = select(related_model).where(
        getattr(related_model, related_id_attr).in_(ids)
    )
    result = await db.execute(stmt)
    related_items = result.scalars().all()

    result_map: dict[int, list[Any]] = {id_: [] for id_ in ids}
    for item in related_items:
        foreign_key_value = getattr(item, related_id_attr, None)
        if foreign_key_value is not None:
            result_map.setdefault(int(foreign_key_value), []).append(item)

    return result_map


async def optimize_list_query(
    db: AsyncSession,
    main_query: Any,
    count_query: Any,
    relations: list[str] | None = None,
) -> tuple[list[Any], int]:
    """优化列表查询（包含关联预加载）

    Args:
        db: 数据库会话
        main_query: 主查询（已包含过滤和分页）
        count_query: 计数查询
        relations: 需要预加载的关联关系列表

    Returns:
        (结果列表, 总数)
    """
    if relations:
        for relation in relations:
            main_query = main_query.options(selectinload(relation))

    result = await db.execute(main_query)
    items = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = int(count_result.scalar() or 0)

    return items, total


T = TypeVar('T')


class HasId(Protocol):
    id: Any


async def optimized_withdrawal_list(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
) -> tuple[list["WithdrawalRequest"], int, dict[int, int]]:
    """优化后的提现记录查询（解决 N+1 问题）

    原始问题：
    1. 查询 WithdrawalRequest 列表
    2. 循环中查询每个 Lawyer 信息

    优化方案：
    1. 使用 selectinload 预加载 Lawyer 关联
    2. 使用聚合查询统计咨询数量
    """
    from backend.app.models.settlement import WithdrawalRequest
    from backend.app.models.lawfirm import LawyerConsultation

    query = select(WithdrawalRequest)

    query = query.options(selectinload(WithdrawalRequest.lawyer))

    if status_filter:
        query = query.where(WithdrawalRequest.status == status_filter)

    count_query = select(func.count(WithdrawalRequest.id))
    if status_filter:
        count_query = count_query.where(
            WithdrawalRequest.status == status_filter)

    result = await db.execute(
        query.order_by(WithdrawalRequest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    withdrawals = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = int(count_result.scalar() or 0)

    lawyer_ids = list({int(w.lawyer_id)
                      for w in withdrawals if w.lawyer_id is not None})
    consultation_counts: dict[int, int] = {}
    if lawyer_ids:
        agg_query = (
            select(
                LawyerConsultation.lawyer_id,
                func.count(
                    LawyerConsultation.id))
            .where(
                LawyerConsultation.lawyer_id.in_(lawyer_ids),
                LawyerConsultation.status == "completed",
            )
            .group_by(LawyerConsultation.lawyer_id)
        )
        agg_result = await db.execute(agg_query)
        for row in agg_result.all():
            consultation_counts[int(row[0])] = int(row[1])

    return withdrawals, total, consultation_counts
