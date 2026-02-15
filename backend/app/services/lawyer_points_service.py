"""律师积分服务"""
from typing import TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

if TYPE_CHECKING:
    from ..models.lawfirm import Lawyer, LawyerReview


class LawyerPointsService:
    """律师积分服务"""

    # 积分规则
    POINTS_PER_RATING = {
        5: 10,  # 5星评价奖励10积分
        4: 5,   # 4星评价奖励5积分
        3: 2,   # 3星评价奖励2积分
        2: 0,   # 2星评价不奖励
        1: 0,   # 1星评价不奖励
    }

    # 多维度评价额外积分
    DIMENSION_BONUS_POINTS = 5  # 完整多维度评价额外奖励5积分

    # 标签额外积分
    TAG_BONUS_POINTS = 2  # 每个标签额外奖励2积分

    async def calculate_review_points(
        self,
        review: "LawyerReview",
    ) -> int:
        """
        计算评价积分

        Args:
            review: 评价记录

        Returns:
            积分值
        """
        points = 0

        # 基础积分：根据评分
        points += self.POINTS_PER_RATING.get(review.rating, 0)

        # 多维度评价额外积分
        if (
            review.professionalism is not None
            and review.responsiveness is not None
            and review.attitude is not None
        ):
            points += self.DIMENSION_BONUS_POINTS

        # 标签额外积分
        if review.tags:
            import json
            try:
                tags = json.loads(review.tags)
                if isinstance(tags, list):
                    points += len(tags) * self.TAG_BONUS_POINTS
            except (json.JSONDecodeError, TypeError):
                pass

        return points

    async def award_review_points(
        self,
        db: AsyncSession,
        lawyer_id: int,
        review: "LawyerReview",
    ) -> int:
        """
        奖励评价积分

        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            review: 评价记录

        Returns:
            奖励的积分值
        """
        from ..models.lawfirm import Lawyer

        # 计算积分
        points = await self.calculate_review_points(review)

        if points <= 0:
            return 0

        # 获取律师记录
        result = await db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = result.scalar_one_or_none()
        if not lawyer:
            return 0

        # 更新律师积分（这里假设Lawyer模型有points字段，如果没有需要添加）
        # 如果Lawyer模型没有points字段，可以创建一个LawyerPoints表来记录积分
        # 这里暂时不做实际积分存储，只返回计算结果

        return points

    async def get_lawyer_total_points(
        self,
        db: AsyncSession,
        lawyer_id: int,
    ) -> int:
        """
        获取律师总积分

        Args:
            db: 数据库会话
            lawyer_id: 律师ID

        Returns:
            总积分
        """
        from ..models.lawfirm import LawyerReview

        # 计算所有评价的积分总和
        reviews_result = await db.execute(
            select(LawyerReview).where(LawyerReview.lawyer_id == lawyer_id)
        )
        reviews = reviews_result.scalars().all()

        total_points = 0
        for review in reviews:
            total_points += await self.calculate_review_points(review)

        return total_points


# 创建全局实例
lawyer_points_service = LawyerPointsService()
