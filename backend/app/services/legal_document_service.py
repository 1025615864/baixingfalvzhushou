"""法律文书商城服务

提供法律文书的列表、购买、积分兑换等功能。
支持会员权益集成。
"""

import logging
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.legal_document import (
    LegalDocument,
    LegalDocumentOrder,
    LegalDocumentFavorite,
)
from ..models.points import PointsUser
from ..services.membership_service import membership_service, MembershipTier
from ..services.points.points_service import get_points_service

logger = logging.getLogger(__name__)


class LegalDocumentService:
    """法律文书商城服务"""

    # 分类名称映射
    CATEGORY_NAMES = {
        # 合同范本
        "contract_rental": "租赁合同",
        "contract_purchase": "买卖合同",
        "contract_labor": "劳动合同",
        "contract_marriage": "婚姻家庭",
        "contract_enterprise": "企业合同",
        # 法律文书
        "legal_petition": "起诉状",
        "legal_answer": "答辩状",
        "legal_application": "申请书",
        "legal_agreement": "协议",
        # 企业文书
        "enterprise_charter": "公司章程",
        "enterprise_labor": "企业劳动合同模板",
        "enterprise_internal": "内部管理制度",
    }

    # 分类分组
    CATEGORY_GROUPS = {
        "合同范本": [
            "contract_rental",
            "contract_purchase",
            "contract_labor",
            "contract_marriage",
            "contract_enterprise",
        ],
        "法律文书": [
            "legal_petition",
            "legal_answer",
            "legal_application",
            "legal_agreement",
        ],
        "企业文书": [
            "enterprise_charter",
            "enterprise_labor",
            "enterprise_internal",
        ],
    }

    async def list_categories(self) -> list[dict[str, Any]]:
        """获取分类列表（带分组）"""
        result = []
        for group_name, categories in self.CATEGORY_GROUPS.items():
            items = []
            for cat in categories:
                items.append({
                    "key": cat,
                    "name": self.CATEGORY_NAMES.get(cat, cat),
                })
            result.append({
                "name": group_name,
                "categories": items,
            })
        return result

    async def get_documents(
        self,
        db: AsyncSession,
        *,
        category: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
        is_featured: bool | None = None,
        is_free: bool | None = None,
    ) -> dict[str, Any]:
        """获取法律文书列表"""
        query = select(LegalDocument).where(LegalDocument.is_active == True)

        if category:
            query = query.where(LegalDocument.category == category)

        if keyword:
            keyword_filter = f"%{keyword}%"
            query = query.where(
                or_(
                    LegalDocument.name.ilike(keyword_filter),
                    LegalDocument.description.ilike(keyword_filter),
                    LegalDocument.tags.ilike(keyword_filter),
                )
            )

        if is_featured is not None:
            query = query.where(LegalDocument.is_featured == is_featured)

        if is_free is not None:
            query = query.where(LegalDocument.is_free == is_free)

        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total: int = int(await db.scalar(count_query) or 0)

        # 分页
        query = query.order_by(LegalDocument.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        documents = result.scalars().all()

        items = [self._document_to_dict(doc) for doc in documents]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_document(
        self, db: AsyncSession, document_id: int
    ) -> dict[str, Any] | None:
        """获取法律文书详情"""
        result = await db.execute(
            select(LegalDocument).where(
                LegalDocument.id == document_id,
                LegalDocument.is_active == True,
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            return None

        # 增加浏览次数
        document.view_count = (document.view_count or 0) + 1
        db.add(document)
        await db.commit()

        return self._document_to_dict(document)

    async def get_document_content(
        self, db: AsyncSession, document_id: int, user_id: int
    ) -> dict[str, Any] | None:
        """获取文书内容（需要已购买）"""
        # 检查是否已购买
        order_result = await db.execute(
            select(LegalDocumentOrder).where(
                LegalDocumentOrder.user_id == user_id,
                LegalDocumentOrder.document_id == document_id,
                LegalDocumentOrder.status == "completed",
            )
        )
        order = order_result.scalar_one_or_none()

        if not order:
            return None

        # 获取文书
        doc_result = await db.execute(
            select(LegalDocument).where(LegalDocument.id == document_id)
        )
        document = doc_result.scalar_one_or_none()
        if not document:
            return None

        return {
            "id": document.id,
            "name": document.name,
            "content": document.content,
            "order_no": order.order_no,
            "purchased_at": order.completed_at.isoformat() if order.completed_at else None,
        }

    async def calculate_price(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
    ) -> dict[str, Any]:
        """计算价格（考虑会员权益）"""
        # 获取文书
        result = await db.execute(
            select(LegalDocument).where(LegalDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            return {"error": "文书不存在", "price": 0, "original_price": 0, "discount": 0}

        original_price = document.points_required

        # 如果免费，直接返回
        if document.is_free:
            return {
                "price": 0,
                "original_price": original_price,
                "discount": original_price,
                "is_free": True,
                "payment_method": "free",
            }

        # 获取用户会员等级
        from ..models.user import User

        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return {"error": "用户不存在", "price": original_price, "original_price": original_price, "discount": 0}

        tier = await membership_service.get_user_tier(db, user)

        # 计算会员价格
        member_prices = document.member_prices or {}
        member_discount = 0
        payment_method = "points"

        if tier == MembershipTier.LIFETIME.value and "lifetime" in member_prices:
            member_discount = original_price - member_prices["lifetime"]
            payment_method = "member_free" if member_prices["lifetime"] == 0 else "member"
            final_price = member_prices["lifetime"]
        elif tier == MembershipTier.ANNUAL.value and "annual" in member_prices:
            member_discount = original_price - member_prices["annual"]
            payment_method = "member_free" if member_prices["annual"] == 0 else "member"
            final_price = member_prices["annual"]
        elif tier == MembershipTier.MONTHLY.value and "monthly" in member_prices:
            member_discount = original_price - member_prices["monthly"]
            payment_method = "member"
            final_price = member_prices["monthly"]
        else:
            final_price = original_price

        return {
            "price": final_price,
            "original_price": original_price,
            "discount": member_discount,
            "is_free": final_price == 0,
            "payment_method": payment_method,
            "tier": tier,
        }

    async def purchase_document(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        payment_method: str = "points",
    ) -> dict[str, Any]:
        """购买法律文书"""
        # 获取文书
        result = await db.execute(
            select(LegalDocument).where(LegalDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            return {"success": False, "error": "文书不存在"}

        if not document.is_active:
            return {"success": False, "error": "文书已下架"}

        # 检查是否已购买
        existing_order = await db.execute(
            select(LegalDocumentOrder).where(
                LegalDocumentOrder.user_id == user_id,
                LegalDocumentOrder.document_id == document_id,
                LegalDocumentOrder.status == "completed",
            )
        )
        if existing_order.scalar_one_or_none():
            return {"success": False, "error": "您已购买过此文书"}

        # 计算价格
        price_info = await self.calculate_price(db, document_id, user_id)
        if "error" in price_info:
            return {"success": False, "error": price_info["error"]}

        points_required = price_info["price"]

        # 处理不同支付方式
        if payment_method == "free" or price_info["is_free"]:
            # 免费获取
            return await self._create_order(
                db, document, user_id, points_required, points_required, "free"
            )

        elif payment_method == "member_free":
            # 会员免费
            return await self._create_order(
                db, document, user_id, points_required, document.points_required, "member_free"
            )

        elif payment_method == "points":
            # 积分购买
            points_service = get_points_service()
            balance = points_service.get_balance(user_id)

            if balance < points_required:
                return {
                    "success": False,
                    "error": f"积分不足，需要 {points_required} 积分，当前余额 {balance}",
                    "balance": balance,
                    "required": points_required,
                }

            # 扣除积分
            success, error = await points_service.redeem_points(
                user_id=user_id,
                points=points_required,
                product_id=f"legal_doc_{document_id}",
                description=f"购买法律文书: {document.name}",
            )

            if not success:
                return {"success": False, "error": error}

            return await self._create_order(
                db, document, user_id, points_required, document.points_required, "points"
            )

        return {"success": False, "error": "不支持的支付方式"}

    async def _create_order(
        self,
        db: AsyncSession,
        document: LegalDocument,
        user_id: int,
        points_spent: int,
        original_points: int,
        payment_method: str,
    ) -> dict[str, Any]:
        """创建订单并返回"""
        order_no = f"LD{user_id}{int(datetime.now(timezone.utc).timestamp())}"

        order = LegalDocumentOrder(
            order_no=order_no,
            user_id=user_id,
            document_id=document.id,
            points_spent=points_spent,
            original_points=original_points,
            discount_amount=original_points - points_spent,
            payment_method=payment_method,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        )

        db.add(order)

        # 更新下载次数
        document.download_count = (document.download_count or 0) + 1
        db.add(document)

        await db.commit()
        await db.refresh(order)

        logger.info(
            f"用户 {user_id} 购买法律文书 {document.name}，消耗 {points_spent} 积分"
        )

        return {
            "success": True,
            "order_no": order_no,
            "document_id": document.id,
            "document_name": document.name,
            "points_spent": points_spent,
            "payment_method": payment_method,
        }

    async def get_user_orders(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """获取用户购买记录"""
        query = (
            select(LegalDocumentOrder)
            .where(
                LegalDocumentOrder.user_id == user_id,
                LegalDocumentOrder.status == "completed",
            )
            .order_by(LegalDocumentOrder.completed_at.desc())
        )

        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total: int = int(await db.scalar(count_query) or 0)

        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        orders = result.scalars().all()

        items = []
        for order in orders:
            # 获取文书信息
            doc_result = await db.execute(
                select(LegalDocument).where(LegalDocument.id == order.document_id)
            )
            document = doc_result.scalar_one_or_none()

            items.append({
                "order_no": order.order_no,
                "document_id": order.document_id,
                "document_name": document.name if document else "未知",
                "document_category": document.category if document else None,
                "points_spent": order.points_spent,
                "payment_method": order.payment_method,
                "completed_at": order.completed_at.isoformat() if order.completed_at else None,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def add_favorite(
        self, db: AsyncSession, user_id: int, document_id: int
    ) -> dict[str, Any]:
        """添加收藏"""
        # 检查文书是否存在
        doc_result = await db.execute(
            select(LegalDocument).where(LegalDocument.id == document_id)
        )
        if not doc_result.scalar_one_or_none():
            return {"success": False, "error": "文书不存在"}

        # 检查是否已收藏
        existing = await db.execute(
            select(LegalDocumentFavorite).where(
                LegalDocumentFavorite.user_id == user_id,
                LegalDocumentFavorite.document_id == document_id,
            )
        )
        if existing.scalar_one_or_none():
            return {"success": True, "message": "已收藏"}

        favorite = LegalDocumentFavorite(
            user_id=user_id, document_id=document_id
        )
        db.add(favorite)
        await db.commit()

        return {"success": True}

    async def remove_favorite(
        self, db: AsyncSession, user_id: int, document_id: int
    ) -> dict[str, Any]:
        """取消收藏"""
        result = await db.execute(
            select(LegalDocumentFavorite).where(
                LegalDocumentFavorite.user_id == user_id,
                LegalDocumentFavorite.document_id == document_id,
            )
        )
        favorite = result.scalar_one_or_none()
        if not favorite:
            return {"success": False, "error": "未收藏"}

        await db.delete(favorite)
        await db.commit()

        return {"success": True}

    async def get_user_favorites(
        self, db: AsyncSession, user_id: int
    ) -> list[dict[str, Any]]:
        """获取用户收藏列表"""
        result = await db.execute(
            select(LegalDocumentFavorite)
            .where(LegalDocumentFavorite.user_id == user_id)
            .order_by(LegalDocumentFavorite.created_at.desc())
        )
        favorites = result.scalars().all()

        items = []
        for fav in favorites:
            doc_result = await db.execute(
                select(LegalDocument).where(LegalDocument.id == fav.document_id)
            )
            document = doc_result.scalar_one_or_none()
            if document:
                items.append(self._document_to_dict(document))

        return items

    async def is_favorited(
        self, db: AsyncSession, user_id: int, document_id: int
    ) -> bool:
        """检查是否已收藏"""
        result = await db.execute(
            select(LegalDocumentFavorite).where(
                LegalDocumentFavorite.user_id == user_id,
                LegalDocumentFavorite.document_id == document_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_purchased(
        self, db: AsyncSession, user_id: int, document_id: int
    ) -> bool:
        """检查是否已购买"""
        result = await db.execute(
            select(LegalDocumentOrder).where(
                LegalDocumentOrder.user_id == user_id,
                LegalDocumentOrder.document_id == document_id,
                LegalDocumentOrder.status == "completed",
            )
        )
        return result.scalar_one_or_none() is not None

    def _document_to_dict(self, document: LegalDocument) -> dict[str, Any]:
        """转换文书为字典"""
        return {
            "id": document.id,
            "name": document.name,
            "description": document.description,
            "category": document.category,
            "category_name": self.CATEGORY_NAMES.get(document.category, document.category),
            "price": document.points_required,
            "is_free": document.is_free,
            "is_featured": document.is_featured,
            "view_count": document.view_count or 0,
            "download_count": document.download_count or 0,
            "rating": document.rating or 0,
            "tags": (document.tags or "").split(",") if document.tags else [],
            "custom_service_available": document.custom_service_available,
            "custom_service_price": document.custom_service_price,
            "member_prices": document.member_prices,
            "created_at": document.created_at.isoformat() if document.created_at else None,
        }

    async def get_featured_documents(
        self, db: AsyncSession, limit: int = 6
    ) -> list[dict[str, Any]]:
        """获取推荐文书"""
        result = await db.execute(
            select(LegalDocument)
            .where(
                LegalDocument.is_active == True,
                LegalDocument.is_featured == True,
            )
            .order_by(LegalDocument.download_count.desc())
            .limit(limit)
        )
        documents = result.scalars().all()
        return [self._document_to_dict(doc) for doc in documents]

    async def get_free_documents(
        self, db: AsyncSession, limit: int = 10
    ) -> list[dict[str, Any]]:
        """获取免费文书"""
        result = await db.execute(
            select(LegalDocument)
            .where(
                LegalDocument.is_active == True,
                LegalDocument.is_free == True,
            )
            .order_by(LegalDocument.download_count.desc())
            .limit(limit)
        )
        documents = result.scalars().all()
        return [self._document_to_dict(doc) for doc in documents]


# 服务单例
legal_document_service = LegalDocumentService()