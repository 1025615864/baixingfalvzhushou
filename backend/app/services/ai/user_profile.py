"""用户画像服务"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ...models.consultation import Consultation, ChatMessage, ConsultationCategory
from ...models.user import User

logger = logging.getLogger(__name__)


class UserProfileService:
    """用户画像服务"""

    @classmethod
    async def analyze_consultation_history(
        cls,
        db: AsyncSession,
        user_id: int,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        分析用户咨询历史

        Args:
            days: 分析最近多少天的数据

        Returns:
            分析结果字典
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # 获取用户的咨询记录
        result = await db.execute(
            select(Consultation)
            .where(
                Consultation.user_id == user_id,
                Consultation.created_at >= cutoff_date
            )
            .order_by(desc(Consultation.created_at))
        )
        consultations = result.scalars().all()

        if not consultations:
            return {
                "total_consultations": 0,
                "primary_categories": [],
                "interests": [],
                "activity_level": "low",
                "summary": "暂无咨询记录"
            }

        # 分类统计
        categories = [c.category for c in consultations]
        category_counts = Counter(categories)
        primary_categories = [
            {"category": cat, "count": count, "percentage": round(count / len(categories) * 100, 1)}
            for cat, count in category_counts.most_common(3)
        ]

        # 计算活跃度
        total_consultations = len(consultations)
        if total_consultations >= 20:
            activity_level = "high"
        elif total_consultations >= 5:
            activity_level = "medium"
        else:
            activity_level = "low"

        # 分析关注领域（基于分类）
        interest_mapping = {
            ConsultationCategory.LABOR: "劳动权益保护",
            ConsultationCategory.MARRIAGE: "婚姻家庭法律",
            ConsultationCategory.CONTRACT: "合同纠纷处理",
            ConsultationCategory.PROPERTY: "房产法律问题",
            ConsultationCategory.CRIMINAL: "刑事法律辩护",
            ConsultationCategory.TRAFFIC: "交通事故处理",
            ConsultationCategory.INTELLECTUAL: "知识产权保护",
            ConsultationCategory.GENERAL: "一般法律咨询",
            ConsultationCategory.OTHER: "其他法律问题",
        }

        interests = []
        for cat_info in primary_categories:
            cat = cat_info["category"]
            if cat in interest_mapping:
                interests.append({
                    "area": interest_mapping[cat],
                    "level": "high" if cat_info["percentage"] > 50 else "medium"
                })

        # 生成摘要
        if primary_categories:
            top_category = primary_categories[0]
            summary = f"用户主要关注{interest_mapping.get(top_category['category'], '法律问题')}，"
            summary += f"近期共咨询{total_consultations}次"
            if len(primary_categories) > 1:
                summary += f"，次要关注{interest_mapping.get(primary_categories[1]['category'], '其他问题')}"
        else:
            summary = "用户咨询记录较少"

        return {
            "total_consultations": total_consultations,
            "analysis_period_days": days,
            "primary_categories": primary_categories,
            "interests": interests,
            "activity_level": activity_level,
            "summary": summary,
            "last_consultation_at": consultations[0].created_at.isoformat() if consultations else None
        }

    @classmethod
    async def extract_keywords_from_consultations(
        cls,
        db: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> List[str]:
        """
        从用户咨询中提取关键词

        简单实现：从咨询标题和消息中提取常见法律关键词
        """
        # 常见法律关键词
        legal_keywords = [
            "劳动合同", "工资", "加班", "离职", "赔偿", "工伤",
            "离婚", "财产分割", "抚养权", "继承", "遗嘱",
            "合同", "违约", "定金", "违约金", "履行",
            "房产", "租房", "买卖", "产权", "抵押",
            "交通事故", "责任认定", "保险理赔", "医疗费",
            "侵权", "名誉", "隐私", "知识产权", "商标", "专利",
            "借款", "欠条", "债务", "利息", "担保",
            "公司", "股权", "股东", "合伙", "破产",
            "刑事", "犯罪", "拘留", "逮捕", "辩护",
            "消费", "维权", "退款", "假货", "欺诈"
        ]

        # 获取用户的所有咨询标题和消息内容
        result = await db.execute(
            select(Consultation.title)
            .where(Consultation.user_id == user_id)
        )
        titles = [t[0] or "" for t in result.all()]

        result = await db.execute(
            select(ChatMessage.content)
            .join(Consultation)
            .where(Consultation.user_id == user_id)
        )
        contents = [c[0] or "" for c in result.all()]

        all_text = " ".join(titles + contents)

        # 统计关键词出现频率
        keyword_counts = {}
        for keyword in legal_keywords:
            count = all_text.count(keyword)
            if count > 0:
                keyword_counts[keyword] = count

        # 返回出现频率最高的关键词
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, _ in sorted_keywords[:limit]]

    @classmethod
    async def generate_user_legal_profile(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """
        生成用户法律画像

        综合用户的咨询历史、关注领域等信息，生成用户画像
        """
        # 分析咨询历史
        history_analysis = await cls.analyze_consultation_history(db, user_id)

        # 提取关键词
        keywords = await cls.extract_keywords_from_consultations(db, user_id)

        # 获取用户基本信息
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        # 构建画像
        profile = {
            "user_id": user_id,
            "user_type": cls._determine_user_type(history_analysis),
            "legal_needs": cls._determine_legal_needs(history_analysis, keywords),
            "risk_awareness": cls._assess_risk_awareness(history_analysis),
            "preferred_consultation_style": cls._determine_consultation_style(history_analysis),
            "keywords": keywords,
            "consultation_history": history_analysis,
            "generated_at": datetime.now().isoformat()
        }

        return profile

    @staticmethod
    def _determine_user_type(history_analysis: Dict[str, Any]) -> str:
        """判断用户类型"""
        total = history_analysis.get("total_consultations", 0)
        activity = history_analysis.get("activity_level", "low")

        if total == 0:
            return "new_user"
        elif activity == "high":
            return "active_user"
        elif activity == "medium":
            return "regular_user"
        else:
            return "occasional_user"

    @staticmethod
    def _determine_legal_needs(history_analysis: Dict[str, Any], keywords: List[str]) -> List[Dict[str, Any]]:
        """确定用户法律需求"""
        needs = []

        # 基于主要分类确定需求
        for cat_info in history_analysis.get("primary_categories", []):
            category = cat_info["category"]
            if category == ConsultationCategory.LABOR:
                needs.append({
                    "area": "劳动权益",
                    "description": "关注劳动合同、工资、加班、离职补偿等问题",
                    "urgency": "medium"
                })
            elif category == ConsultationCategory.MARRIAGE:
                needs.append({
                    "area": "婚姻家庭",
                    "description": "关注离婚、财产分割、子女抚养等家庭法律问题",
                    "urgency": "high"
                })
            elif category == ConsultationCategory.CONTRACT:
                needs.append({
                    "area": "合同事务",
                    "description": "需要合同审查、违约处理等法律服务",
                    "urgency": "medium"
                })
            elif category == ConsultationCategory.PROPERTY:
                needs.append({
                    "area": "房产事务",
                    "description": "关注房产买卖、租赁、产权等房产法律问题",
                    "urgency": "medium"
                })

        return needs

    @staticmethod
    def _assess_risk_awareness(history_analysis: Dict[str, Any]) -> str:
        """评估用户风险意识"""
        total = history_analysis.get("total_consultations", 0)
        activity = history_analysis.get("activity_level", "low")

        if total > 10 and activity == "high":
            return "high"  # 经常咨询，风险意识强
        elif total > 3:
            return "medium"  # 有一定风险意识
        else:
            return "low"  # 风险意识较弱

    @staticmethod
    def _determine_consultation_style(history_analysis: Dict[str, Any]) -> str:
        """判断用户咨询偏好"""
        activity = history_analysis.get("activity_level", "low")

        if activity == "high":
            return "proactive"  # 主动型，经常咨询
        elif activity == "medium":
            return "reactive"  # 被动型，有问题才咨询
        else:
            return "reserved"  # 保守型，很少咨询

    @classmethod
    async def get_profile_summary_for_prompt(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> str:
        """
        生成用于Prompt的用户画像摘要

        将用户画像转换为适合添加到AI Prompt的文本格式
        """
        profile = await cls.generate_user_legal_profile(db, user_id)

        summary_parts = []

        # 用户类型
        user_type_desc = {
            "new_user": "新用户",
            "active_user": "活跃用户",
            "regular_user": "常规用户",
            "occasional_user": "偶尔咨询用户"
        }
        summary_parts.append(f"用户类型：{user_type_desc.get(profile['user_type'], '普通用户')}")

        # 关注领域
        if profile["legal_needs"]:
            areas = [need["area"] for need in profile["legal_needs"]]
            summary_parts.append(f"主要关注：{', '.join(areas)}")

        # 咨询历史
        history = profile["consultation_history"]
        if history["total_consultations"] > 0:
            summary_parts.append(f"历史咨询：{history['total_consultations']}次")

        # 关键词
        if profile["keywords"]:
            summary_parts.append(f"相关关键词：{', '.join(profile['keywords'][:5])}")

        return " | ".join(summary_parts) if summary_parts else ""


# 全局实例
user_profile_service = UserProfileService()
