"""用户兴趣标签提取服务"""
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.analytics import UserBehaviorLog


class UserInterestService:
    """用户兴趣标签提取服务"""

    # 预定义的兴趣标签分类
    INTEREST_CATEGORIES = {
        "legal": ["律师", "咨询", "法律", "合同", "纠纷", "诉讼", "仲裁", "赔偿", "维权"],
        "family": ["婚姻", "离婚", "抚养", "赡养", "继承", "遗嘱", "家庭", "子女"],
        "labor": ["劳动", "工资", "加班", "社保", "工伤", "辞退", "裁员", "劳动合同"],
        "property": ["房产", "房屋", "买卖", "租赁", "抵押", "拆迁", "物业", "产权"],
        "criminal": ["刑事", "犯罪", "辩护", "取保", "缓刑", "减刑", "假释", "量刑"],
        "business": ["公司", "企业", "股权", "投资", "融资", "破产", "并购", "上市"],
        "intellectual": ["专利", "商标", "版权", "著作权", "知识产权", "侵权", "许可"],
        "traffic": ["交通", "事故", "违章", "酒驾", "醉驾", "赔偿", "责任", "保险"],
        "debt": ["债务", "借贷", "欠款", "催收", "担保", "抵押", "质押", "执行"],
        "consumer": ["消费", "维权", "退货", "退款", "质量", "欺诈", "虚假宣传", "三包"],
    }

    @staticmethod
    async def extract_user_interests(
        db: AsyncSession,
        user_id: int,
        days: int = 30,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        提取用户兴趣标签

        Args:
            db: 数据库会话
            user_id: 用户ID
            days: 查询天数
            limit: 返回标签数量

        Returns:
            兴趣标签列表，包含标签名称、分类、权重
        """
        from datetime import datetime, timedelta, timezone

        # 获取用户最近的行为日志
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = await db.execute(
            select(UserBehaviorLog)
            .where(
                UserBehaviorLog.user_id == user_id,
                UserBehaviorLog.created_at >= start_date,
            )
            .order_by(desc(UserBehaviorLog.created_at))
        )
        behaviors = list(result.scalars().all())

        # 提取关键词
        keywords: list[str] = []
        for behavior in behaviors:
            # 从metadata中提取关键词
            if behavior.metadata_json:
                try:
                    metadata = json.loads(behavior.metadata_json)
                    if isinstance(metadata, dict):
                        # 提取各种可能的关键词字段
                        for key in ["keywords", "tags",
                                    "category", "subject", "title"]:
                            if key in metadata:
                                value = metadata[key]  # pyright: ignore
                                if isinstance(value, str):
                                    keywords.append(value)  # pyright: ignore
                                elif isinstance(value, list):
                                    keywords.extend(value)  # pyright: ignore
                except (json.JSONDecodeError, TypeError):
                    pass

            # 从resource_type中提取
            if behavior.resource_type:
                keywords.append(behavior.resource_type)

        # 统计关键词频率
        keyword_counter = Counter(keywords)

        # 匹配兴趣分类
        interest_scores: dict[str, dict[str, Any]] = {}

        for category, category_keywords in UserInterestService.INTEREST_CATEGORIES.items():
            score = 0
            matched_keywords: list[str] = []

            for keyword, count in keyword_counter.items():
                keyword_lower = keyword.lower()
                for category_keyword in category_keywords:
                    if category_keyword in keyword_lower or keyword_lower in category_keyword:
                        score += count
                        if category_keyword not in matched_keywords:
                            matched_keywords.append(category_keyword)

            if score > 0:
                interest_scores[category] = {
                    "category": category,
                    "score": score,
                    "matched_keywords": matched_keywords,
                }

        # 按分数排序
        sorted_interests = sorted(
            interest_scores.values(),
            key=lambda x: x["score"],
            reverse=True,
        )

        # 返回前N个兴趣标签
        return sorted_interests[:limit]

    @staticmethod
    async def get_user_interest_tags(
        db: AsyncSession,
        user_id: int,
        days: int = 30,
    ) -> list[str]:
        """
        获取用户兴趣标签（简化版，只返回标签名称）

        Args:
            db: 数据库会话
            user_id: 用户ID
            days: 查询天数

        Returns:
            兴趣标签列表
        """
        interests = await UserInterestService.extract_user_interests(db, user_id, days)
        return [interest["category"] for interest in interests]

    @staticmethod
    async def get_similar_users(
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> list[int]:
        """
        获取兴趣相似的用户

        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 返回数量

        Returns:
            相似用户ID列表
        """
        # 获取当前用户的兴趣标签
        current_interests = await UserInterestService.get_user_interest_tags(db, user_id)

        if not current_interests:
            return []

        # 获取其他用户的兴趣标签
        # 这里简化实现，实际应该使用更复杂的相似度算法
        # (user_id, similarity_score)
        similar_users: list[tuple[int, float]] = []

        # 查询最近活跃的用户
        start_date = datetime.now(timezone.utc) - timedelta(days=30)

        result = await db.execute(
            select(UserBehaviorLog.user_id)
            .where(UserBehaviorLog.created_at >= start_date)
            .where(UserBehaviorLog.user_id != user_id)
            .distinct()
            .limit(100)  # 限制查询数量
        )
        user_ids = [row[0] for row in result.all()]

        # 计算相似度
        for other_user_id in user_ids:
            other_interests = await UserInterestService.get_user_interest_tags(db, other_user_id)

            if not other_interests:
                continue

            # 计算Jaccard相似度
            intersection = len(set(current_interests) & set(other_interests))
            union = len(set(current_interests) | set(other_interests))

            if union > 0:
                similarity = intersection / union
                if similarity > 0.3:  # 相似度阈值
                    similar_users.append((other_user_id, similarity))

        # 按相似度排序
        similar_users.sort(key=lambda x: x[1], reverse=True)

        return [user_id for user_id, _ in similar_users[:limit]]


user_interest_service = UserInterestService()
