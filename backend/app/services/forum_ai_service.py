"""论坛AI服务"""
from __future__ import annotations

import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from ..models.forum import Post, Comment
from ..models.user import User
from ..models.consultation import Consultation, ChatMessage

logger = logging.getLogger(__name__)


class ForumAIService:
    """论坛AI服务"""

    # 常见法律问题类型和回复模板
    REPLY_TEMPLATES = {
        "labor": {
            "keywords": ["劳动合同", "工资", "加班", "离职", "辞退", "赔偿", "工伤", "社保", "公积金"],
            "templates": [
                "根据《劳动合同法》相关规定，用人单位{action}需要{requirement}。建议您：\n1. 收集相关证据（{evidence}）\n2. 与用人单位协商\n3. 如协商不成，可向劳动仲裁委员会申请仲裁",
                "您遇到的{issue}问题，建议先查看劳动合同中的相关条款。如果单位存在违法行为，您可以：\n1. 向劳动监察部门投诉\n2. 申请劳动仲裁\n3. 必要时寻求律师帮助",
            ]
        },
        "marriage": {
            "keywords": ["离婚", "财产分割", "抚养权", "抚养费", "出轨", "家暴", "继承", "遗嘱"],
            "templates": [
                "关于{issue}问题，根据《民法典》婚姻家庭编：\n1. {legal_point}\n2. 建议您收集{evidence}\n3. 可以考虑通过{approach}解决",
                "您的情况涉及{issue}，建议：\n1. 先与对方协商\n2. 协商不成可寻求调解\n3. 必要时向法院提起诉讼\n注意保留{evidence}等证据",
            ]
        },
        "contract": {
            "keywords": ["合同", "违约", "定金", "违约金", "履行", "解除", "撤销"],
            "templates": [
                "关于合同纠纷，根据《民法典》合同编：\n1. 首先确认合同效力\n2. 审查{clause}条款\n3. 对方{action}构成违约，您可以要求{remedy}",
                "您遇到的合同问题，建议：\n1. 仔细审查合同条款\n2. 收集对方{action}的证据\n3. 先发律师函催告\n4. 必要时提起诉讼",
            ]
        },
        "property": {
            "keywords": ["房产", "租房", "房东", "租客", "买卖", "产权", "抵押", "物业"],
            "templates": [
                "关于{issue}问题：\n1. 查看相关合同和产权证明\n2. 根据《民法典》物权编，{legal_point}\n3. 建议通过{approach}解决",
                "您的情况涉及房产{issue}，建议：\n1. 收集{evidence}\n2. 与对方协商\n3. 协商不成可向{authority}投诉或起诉",
            ]
        },
        "traffic": {
            "keywords": ["交通事故", "责任认定", "保险理赔", "医疗费", "误工费", "伤残"],
            "templates": [
                "关于交通事故{issue}：\n1. 及时报警并获取事故认定书\n2. 保存{evidence}\n3. 根据责任比例，可要求赔偿{compensation}",
                "您遇到的交通事故问题，建议：\n1. 确认责任认定\n2. 联系保险公司\n3. 如协商不成，可起诉要求赔偿",
            ]
        },
        "general": {
            "keywords": [],
            "templates": [
                "感谢您的提问。根据您描述的情况，建议：\n1. 收集和保存相关证据\n2. 咨询专业律师获取针对性建议\n3. 必要时通过法律途径维护权益",
                "您的问题涉及法律{area}领域，建议：\n1. 详细梳理事情经过\n2. 准备相关证据材料\n3. 寻求专业法律帮助",
            ]
        }
    }

    @classmethod
    async def generate_smart_reply_suggestions(
        cls,
        db: AsyncSession,
        post_id: int,
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        生成智能回复建议

        基于帖子内容分析，生成相关的回复建议
        """
        # 获取帖子内容
        result = await db.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            return []

        # 分析帖子内容确定问题类型
        content = f"{post.title} {post.content}"
        issue_type = cls._analyze_issue_type(content)

        # 获取模板
        templates = cls.REPLY_TEMPLATES.get(issue_type, cls.REPLY_TEMPLATES["general"])["templates"]

        # 提取关键信息
        key_info = cls._extract_key_info(content)

        # 生成建议
        suggestions = []
        for i, template in enumerate(templates[:count]):
            # 填充模板
            filled_content = cls._fill_template(template, key_info, issue_type)

            suggestions.append({
                "id": f"suggestion-{post_id}-{i}",
                "content": filled_content,
                "confidence": 0.85 - i * 0.05,
                "category": issue_type,
                "context": post.title[:50],
                "tags": cls._get_tags_for_issue(issue_type),
                "created_at": datetime.now().isoformat(),
            })

        return suggestions

    @classmethod
    def _analyze_issue_type(cls, content: str) -> str:
        """分析问题类型"""
        content_lower = content.lower()

        # 统计各类型关键词匹配数
        scores = {}
        for issue_type, data in cls.REPLY_TEMPLATES.items():
            if issue_type == "general":
                continue
            score = sum(1 for kw in data["keywords"] if kw in content_lower)
            if score > 0:
                scores[issue_type] = score

        if not scores:
            return "general"

        # 返回匹配度最高的类型
        return max(scores, key=scores.get)

    @classmethod
    def _extract_key_info(cls, content: str) -> Dict[str, str]:
        """提取关键信息"""
        info = {
            "action": "采取的行动",
            "requirement": "需要满足的条件",
            "evidence": "相关证据",
            "issue": "问题",
            "legal_point": "法律要点",
            "approach": "解决途径",
            "clause": "相关条款",
            "remedy": "救济方式",
            "authority": "主管部门",
            "compensation": "赔偿项目",
            "area": "相关领域",
        }

        # 简单的关键词提取（实际可以使用NLP）
        if "工资" in content:
            info["issue"] = "工资拖欠"
            info["evidence"] = "劳动合同、工资条、银行流水"
            info["action"] = "拖欠工资"
            info["requirement"] = "按时足额支付劳动报酬"

        elif "离婚" in content:
            info["issue"] = "离婚纠纷"
            info["evidence"] = "结婚证、财产证明、子女信息"
            info["legal_point"] = "夫妻共同财产平均分割"

        elif "合同" in content:
            info["issue"] = "合同纠纷"
            info["evidence"] = "合同文本、履行记录、沟通记录"
            info["action"] = "不履行合同义务"

        return info

    @classmethod
    def _fill_template(cls, template: str, info: Dict[str, str], issue_type: str) -> str:
        """填充模板"""
        try:
            return template.format(**info)
        except KeyError:
            # 如果有缺失的key，使用默认值
            for key in ["action", "requirement", "evidence", "issue", "legal_point",
                       "approach", "clause", "remedy", "authority", "compensation", "area"]:
                if f"{{{key}}}" in template and key not in info:
                    info[key] = "相关" + key
            return template.format(**info)

    @classmethod
    def _get_tags_for_issue(cls, issue_type: str) -> List[str]:
        """获取问题类型对应的标签"""
        tags_map = {
            "labor": ["劳动法", "劳动合同", "工资", "赔偿"],
            "marriage": ["婚姻法", "离婚", "财产分割", "抚养权"],
            "contract": ["合同法", "违约", "赔偿"],
            "property": ["房产", "物权法", "租赁"],
            "traffic": ["交通事故", "保险理赔", "侵权责任"],
            "general": ["法律咨询", "权益保护"],
        }
        return tags_map.get(issue_type, tags_map["general"])

    @classmethod
    async def get_content_recommendations(
        cls,
        db: AsyncSession,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取内容推荐

        基于用户兴趣和热门内容推荐相关帖子
        """
        recommendations = []

        # 1. 获取热门帖子
        hot_posts = await cls._get_hot_posts(db, limit=limit // 2, offset=offset)
        recommendations.extend(hot_posts)

        # 2. 如果有用户信息，获取个性化推荐
        if user_id:
            personalized = await cls._get_personalized_recommendations(
                db, user_id, limit=limit // 2, offset=offset
            )
            recommendations.extend(personalized)

        # 3. 按相关度排序
        recommendations.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return recommendations[:limit]

    @classmethod
    async def _get_hot_posts(
        cls,
        db: AsyncSession,
        limit: int = 5,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取热门帖子"""
        # 基于浏览量、点赞数、评论数计算热度
        result = await db.execute(
            select(Post)
            .where(Post.status == "approved")
            .order_by(desc(Post.view_count + Post.like_count * 2 + Post.comment_count * 3))
            .offset(offset)
            .limit(limit)
        )
        posts = result.scalars().all()

        recommendations = []
        for i, post in enumerate(posts):
            # 计算热度分数
            hot_score = min(1.0, (post.view_count + post.like_count * 2 + post.comment_count * 3) / 1000)

            recommendations.append({
                "item": {
                    "id": str(post.id),
                    "type": "post",
                    "title": post.title,
                    "summary": post.content[:100] + "..." if len(post.content) > 100 else post.content,
                    "author": {
                        "id": str(post.author_id),
                        "name": post.author.username if post.author else "匿名用户",
                    },
                    "tags": post.keywords.split(",") if post.keywords else [],
                    "relevance_score": hot_score,
                    "view_count": post.view_count,
                    "like_count": post.like_count,
                    "reply_count": post.comment_count,
                    "created_at": post.created_at.isoformat() if post.created_at else "",
                },
                "reason": {
                    "type": "trending",
                    "description": "热门内容",
                },
                "rank": i + 1,
            })

        return recommendations

    @classmethod
    async def _get_personalized_recommendations(
        cls,
        db: AsyncSession,
        user_id: int,
        limit: int = 5,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取个性化推荐"""
        # 获取用户感兴趣的关键词（从咨询历史）
        result = await db.execute(
            select(Consultation.category)
            .where(Consultation.user_id == user_id)
            .order_by(desc(Consultation.created_at))
            .limit(10)
        )
        categories = [r[0] for r in result.all()]

        if not categories:
            return []

        # 基于用户关注的分类推荐帖子
        from collections import Counter
        category_counts = Counter(categories)
        top_category = category_counts.most_common(1)[0][0]

        # 映射到论坛标签
        category_tag_map = {
            "labor": "劳动法",
            "marriage": "婚姻家庭",
            "contract": "合同纠纷",
            "property": "房产",
            "traffic": "交通事故",
            "criminal": "刑事",
            "intellectual": "知识产权",
        }
        target_tag = category_tag_map.get(top_category, "法律咨询")

        # 查找相关帖子
        result = await db.execute(
            select(Post)
            .where(
                and_(
                    Post.status == "approved",
                    Post.keywords.contains(target_tag)
                )
            )
            .order_by(desc(Post.created_at))
            .offset(offset)
            .limit(limit)
        )
        posts = result.scalars().all()

        recommendations = []
        for i, post in enumerate(posts):
            recommendations.append({
                "item": {
                    "id": str(post.id),
                    "type": "post",
                    "title": post.title,
                    "summary": post.content[:100] + "..." if len(post.content) > 100 else post.content,
                    "author": {
                        "id": str(post.author_id),
                        "name": post.author.username if post.author else "匿名用户",
                    },
                    "tags": post.keywords.split(",") if post.keywords else [],
                    "relevance_score": 0.8 - i * 0.05,
                    "view_count": post.view_count,
                    "like_count": post.like_count,
                    "reply_count": post.comment_count,
                    "created_at": post.created_at.isoformat() if post.created_at else "",
                },
                "reason": {
                    "type": "user_interest",
                    "description": f"根据您关注的{target_tag}领域推荐",
                    "matched_tags": [target_tag],
                },
                "rank": i + 1,
            })

        return recommendations

    @classmethod
    async def get_trending_topics(
        cls,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取热门话题"""
        # 从帖子关键词统计热门话题
        result = await db.execute(
            select(Post.keywords)
            .where(Post.status == "approved")
            .order_by(desc(Post.created_at))
            .limit(100)
        )
        all_keywords = []
        for row in result.all():
            if row[0]:
                all_keywords.extend(row[0].split(","))

        # 统计词频
        from collections import Counter
        keyword_counts = Counter([kw.strip() for kw in all_keywords if kw.strip()])

        # 返回热门话题
        topics = []
        for i, (keyword, count) in enumerate(keyword_counts.most_common(limit)):
            topics.append({
                "id": f"topic-{i}",
                "name": keyword,
                "hot_score": min(100, count * 10),
                "post_count": count,
            })

        return topics

    @classmethod
    async def record_feedback(
        cls,
        db: AsyncSession,
        user_id: int,
        recommendation_id: str,
        feedback: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        记录用户反馈

        用于优化推荐算法
        """
        # TODO: 将反馈保存到数据库或发送到分析系统
        logger.info(
            f"User {user_id} feedback on {recommendation_id}: {feedback}, reason: {reason}"
        )
        return True


# 全局实例
forum_ai_service = ForumAIService()
