"""搜索历史服务

提供搜索历史记录和管理功能
"""
from ...models.system import SearchHistory
import logging
from typing import cast
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as future_select

logger = logging.getLogger(__name__)

# 延迟导入以避免循环依赖


class SearchHistoryService:
    """搜索历史服务"""

    async def record_search(
        self,
        db: AsyncSession,
        keyword: str,
        user_id: int | None = None,
        ip_address: str | None = None
    ):
        """记录搜索历史

        Args:
            db: 数据库会话
            keyword: 搜索关键词
            user_id: 用户ID（可选）
            ip_address: IP地址（可选）
        """
        try:
            history = SearchHistory(
                keyword=keyword,
                user_id=user_id,
                ip_address=ip_address
            )
            db.add(history)
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record search history: {e}")

    async def get_user_search_history(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> list[str]:
        """获取用户搜索历史

        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            用户搜索关键词列表
        """
        try:
            query = (
                select(SearchHistory.keyword)
                .where(SearchHistory.user_id == user_id)
                .order_by(SearchHistory.created_at.desc())
                .limit(limit * 2)  # 多查询一些用于去重
            )
            result = await db.execute(query)
            keywords = cast(list[str], result.scalars().all())
            # 去重保持顺序
            seen: set[str] = set()
            unique: list[str] = []
            for k in keywords:
                if k not in seen:
                    seen.add(k)
                    unique.append(k)
                    if len(unique) >= limit:
                        break
            return unique
        except Exception:
            return []

    async def clear_user_search_history(
        self,
        db: AsyncSession,
        user_id: int
    ) -> bool:
        """清除用户搜索历史

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            是否清除成功
        """
        try:
            _ = await db.execute(
                delete(SearchHistory).where(SearchHistory.user_id == user_id)
            )
            await db.commit()
            return True
        except Exception:
            return False


# 单例实例
search_history_service = SearchHistoryService()
