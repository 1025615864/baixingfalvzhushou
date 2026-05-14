from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ..models.points import PointsUser, PointsHistory, PointsExchangeItem


def _points_user_to_dict(pu: PointsUser) -> dict:
    return {
        "user_id": pu.user_id,
        "balance": pu.balance,
        "total_earned": pu.total_earned,
        "total_spent": pu.total_spent,
        "continuous_signin_days": pu.continuous_signin_days,
        "last_signin_at": pu.last_signin_at.isoformat() if pu.last_signin_at else None,
        "created_at": pu.created_at.isoformat() if pu.created_at else None,
    }


def _points_history_to_dict(ph: PointsHistory) -> dict:
    return {
        "id": ph.id,
        "user_id": ph.user_id,
        "type": ph.action,
        "amount": ph.points,
        "balance_after": ph.balance_after,
        "description": ph.description,
        "created_at": ph.created_at.isoformat() if ph.created_at else None,
    }


def _exchange_item_to_dict(item: PointsExchangeItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "original_price": item.original_price,
        "category": item.category,
        "stock": item.stock,
        "image_url": item.image_url,
        "is_active": item.is_active,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


class PointsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_balance(self, user_id: int) -> dict:
        result = await self.db.execute(
            select(PointsUser).where(PointsUser.user_id == user_id)
        )
        pu = result.scalar_one_or_none()
        if pu is None:
            return {
                "user_id": user_id,
                "balance": 0,
                "total_earned": 0,
                "total_spent": 0,
                "continuous_signin_days": 0,
                "last_signin_at": None,
                "created_at": None,
            }
        return _points_user_to_dict(pu)

    async def get_transactions(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        trans_type: str | None = None,
    ) -> dict:
        query = select(PointsHistory).where(PointsHistory.user_id == user_id)
        count_query = select(func.count()).select_from(PointsHistory).where(PointsHistory.user_id == user_id)

        if trans_type:
            query = query.where(PointsHistory.action == trans_type)
            count_query = count_query.where(PointsHistory.action == trans_type)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(PointsHistory.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = [_points_history_to_dict(ph) for ph in result.scalars().all()]

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def earn_points(
        self,
        user_id: int,
        points: int,
        type: str,
        description: str | None = None,
        source: str | None = None,
        reference_id: str | None = None,
    ) -> dict:
        result = await self.db.execute(
            select(PointsUser).where(PointsUser.user_id == user_id)
        )
        pu = result.scalar_one_or_none()

        if pu is None:
            pu = PointsUser(
                user_id=user_id,
                balance=points,
                total_earned=points,
                total_spent=0,
            )
            self.db.add(pu)
            await self.db.flush()
            balance_after = points
        else:
            pu.balance += points
            pu.total_earned += points
            balance_after = pu.balance

        desc = description or f"获得{points}积分"
        history = PointsHistory(
            user_id=user_id,
            action=type,
            points=points,
            balance_after=balance_after,
            description=desc,
        )
        self.db.add(history)
        await self.db.flush()

        tx = _points_history_to_dict(history)
        tx["source"] = source
        tx["reference_id"] = reference_id

        balance_data = await self.get_balance(user_id)

        await self.db.commit()
        return {"balance": balance_data, "transaction": tx}

    async def get_transaction_stats(self, user_id: int) -> dict:
        earned_result = await self.db.execute(
            select(func.coalesce(func.sum(PointsHistory.points), 0)).where(
                PointsHistory.user_id == user_id,
                PointsHistory.points > 0,
            )
        )
        total_earned = earned_result.scalar() or 0

        spent_result = await self.db.execute(
            select(func.coalesce(func.sum(PointsHistory.points), 0)).where(
                PointsHistory.user_id == user_id,
                PointsHistory.points < 0,
            )
        )
        total_spent = abs(spent_result.scalar() or 0)

        count_result = await self.db.execute(
            select(func.count()).select_from(PointsHistory).where(
                PointsHistory.user_id == user_id,
            )
        )
        total_transactions = count_result.scalar() or 0

        balance_data = await self.get_balance(user_id)

        return {
            "total_points_earned": total_earned,
            "total_points_spent": total_spent,
            "total_transactions": total_transactions,
            "current_balance": balance_data["balance"],
        }

    async def get_exchange_items(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
    ) -> dict:
        query = select(PointsExchangeItem).where(PointsExchangeItem.is_active == True)
        count_query = (
            select(func.count())
            .select_from(PointsExchangeItem)
            .where(PointsExchangeItem.is_active == True)
        )

        if category:
            query = query.where(PointsExchangeItem.category == category)
            count_query = count_query.where(PointsExchangeItem.category == category)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(PointsExchangeItem.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = [_exchange_item_to_dict(item) for item in result.scalars().all()]

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def get_exchange_item(self, item_id: int) -> dict:
        result = await self.db.execute(
            select(PointsExchangeItem).where(PointsExchangeItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise HTTPException(status_code=404, detail="兑换项目不存在")
        return _exchange_item_to_dict(item)

    async def redeem_item(self, user_id: int, item_id: int) -> dict:
        result = await self.db.execute(
            select(PointsExchangeItem).where(PointsExchangeItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise HTTPException(status_code=404, detail="兑换项目不存在")

        if not item.is_active:
            raise HTTPException(status_code=400, detail="该兑换项目已下架")

        if item.stock <= 0:
            raise HTTPException(status_code=400, detail="库存不足")

        pu_result = await self.db.execute(
            select(PointsUser).where(PointsUser.user_id == user_id)
        )
        pu = pu_result.scalar_one_or_none()
        if pu is None or pu.balance < item.price:
            available = pu.balance if pu else 0
            raise HTTPException(
                status_code=400,
                detail="积分不足以兑换",
            )

        pu.balance -= item.price
        pu.total_spent += item.price
        item.stock -= 1

        history = PointsHistory(
            user_id=user_id,
            action="exchange",
            points=-item.price,
            balance_after=pu.balance,
            description=f"兑换{item.name}",
        )
        self.db.add(history)
        await self.db.flush()

        record = {
            "id": history.id,
            "user_id": user_id,
            "exchange_item_id": item_id,
            "exchange_item_name": item.name,
            "points_spent": item.price,
            "status": "completed",
            "shipment_info": "已兑换",
            "created_at": history.created_at.isoformat() if history.created_at else None,
        }

        balance_data = await self.get_balance(user_id)

        await self.db.commit()
        return {"message": "兑换成功", "exchange_record": record, "balance": balance_data}

    async def get_exchange_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        query = select(PointsHistory).where(
            PointsHistory.user_id == user_id,
            PointsHistory.action == "exchange",
        )
        count_query = (
            select(func.count())
            .select_from(PointsHistory)
            .where(
                PointsHistory.user_id == user_id,
                PointsHistory.action == "exchange",
            )
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(PointsHistory.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = []
        for ph in result.scalars().all():
            items.append({
                "id": ph.id,
                "user_id": ph.user_id,
                "exchange_item_id": None,
                "exchange_item_name": (ph.description or "").replace("兑换", "") if ph.description else None,
                "points_spent": abs(ph.points),
                "status": "completed",
                "shipment_info": "已兑换",
                "created_at": ph.created_at.isoformat() if ph.created_at else None,
            })

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def get_rules(self) -> dict:
        return {
            "earn_rules": [
                {"action": "每日签到", "points": 10, "limit": "每天1次"},
                {"action": "邀请好友注册", "points": 50, "limit": "每月10次"},
                {"action": "完成法律咨询", "points": 20, "limit": "每次"},
                {"action": "发表法律问答", "points": 30, "limit": "每天3次"},
                {"action": "合同审查", "points": 50, "limit": "每次"},
                {"action": "浏览法律文章", "points": 5, "limit": "每天5次"},
                {"action": "分享文章", "points": 15, "limit": "每天3次"},
            ],
            "exchange_rules": [
                {"item": "免费法律咨询", "points": 500, "description": "兑换一次30分钟在线法律咨询"},
                {"item": "合同审查", "points": 800, "description": "专业律师审查一份合同"},
                {"item": "律师优先预约", "points": 300, "description": "享受律师优先预约服务一次"},
            ],
            "expiration": "积分有效期为365天，过期自动清零",
        }
