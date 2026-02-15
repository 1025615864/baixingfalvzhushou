"""积分商品服务

提供积分商品管理和兑换功能。
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class PointsProduct:
    """积分商品"""
    id: str
    name: str
    description: str
    points_required: int
    product_type: str  # coupon, vip, physical, virtual
    image_url: Optional[str] = None
    stock: int = -1  # -1 表示无限
    status: str = "active"  # active, inactive, sold_out
    metadata: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PointsExchangeOrder:
    """积分兑换订单"""
    id: int
    user_id: int
    product_id: str
    product_name: str
    points_spent: int
    status: str  # pending, completed, cancelled, expired
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict] = None


class PointsProductService:
    """积分商品服务"""

    # 默认商品列表
    DEFAULT_PRODUCTS: List[PointsProduct] = [
        PointsProduct(
            id="coupon_10",
            name="10元代金券",
            description="平台通用代金券，满50元可用",
            points_required=100,
            product_type="coupon",
            metadata={"discount_amount": 10, "min_order": 50},
        ),
        PointsProduct(
            id="coupon_30",
            name="30元代金券",
            description="平台通用代金券，满100元可用",
            points_required=280,
            product_type="coupon",
            metadata={"discount_amount": 30, "min_order": 100},
        ),
        PointsProduct(
            id="coupon_50",
            name="50元代金券",
            description="平台通用代金券，满200元可用",
            points_required=450,
            product_type="coupon",
            metadata={"discount_amount": 50, "min_order": 200},
        ),
        PointsProduct(
            id="vip_7days",
            name="VIP会员 7天",
            description="VIP会员权限体验 7 天",
            points_required=200,
            product_type="vip",
            metadata={"duration_days": 7},
        ),
        PointsProduct(
            id="vip_30days",
            name="VIP会员 30天",
            description="VIP会员权限体验 30 天",
            points_required=800,
            product_type="vip",
            metadata={"duration_days": 30},
        ),
        PointsProduct(
            id="ai_chat_10",
            name="AI 咨询 10 次",
            description="AI 法律咨询次数包",
            points_required=150,
            product_type="virtual",
            metadata={"chat_count": 10},
        ),
        PointsProduct(
            id="doc_gen_5",
            name="文书生成 5 次",
            description="文书生成次数包",
            points_required=120,
            product_type="virtual",
            metadata={"document_count": 5},
        ),
    ]

    def __init__(self):
        self._products: Dict[str, PointsProduct] = {}
        self._orders: List[PointsExchangeOrder] = []
        self._order_counter = 0

        # 初始化默认商品
        for product in self.DEFAULT_PRODUCTS:
            self._products[product.id] = product

    def list_products(
        self,
        product_type: Optional[str] = None,
        status: str = "active",
        limit: int = 50,
    ) -> List[PointsProduct]:
        """列出商品"""
        results = []
        for product in self._products.values():
            if product_type and product.product_type != product_type:
                continue
            if product.status != status:
                continue
            results.append(product)

        return results[:limit]

    def get_product(self, product_id: str) -> Optional[PointsProduct]:
        """获取商品详情"""
        return self._products.get(product_id)

    async def create_order(
        self,
        user_id: int,
        product_id: str,
        metadata: Optional[Dict] = None,
    ) -> tuple[Optional[PointsExchangeOrder], Optional[str]]:
        """创建兑换订单

        Returns:
            (订单, 错误信息)
        """
        from .points_service import get_points_service

        product = self._products.get(product_id)
        if not product:
            return None, "商品不存在"

        if product.status != "active":
            return None, "商品已下架"

        if product.stock == 0:
            return None, "商品已售罄"

        # 检查库存
        if product.stock > 0:
            product.stock -= 1

        # 获取积分服务
        points_service = get_points_service()
        balance = points_service.get_balance(user_id)

        if balance < product.points_required:
            return None, f"积分不足，需要 {product.points_required} 积分，当前余额 {balance}"

        # 扣除积分
        success, error = await points_service.redeem_points(
            user_id=user_id,
            points=product.points_required,
            product_id=product_id,
            description=f"兑换: {product.name}",
        )

        if not success:
            # 恢复库存
            if product.stock >= 0:
                product.stock += 1
            return None, error

        # 创建订单
        self._order_counter += 1
        order = PointsExchangeOrder(
            id=self._order_counter,
            user_id=user_id,
            product_id=product_id,
            product_name=product.name,
            points_spent=product.points_required,
            status="completed",
            completed_at=datetime.now(),
            metadata=metadata,
        )
        self._orders.append(order)

        logger.info(
            f"用户 {user_id} 兑换商品 {product.name}，消耗 {product.points_required} 积分")

        return order, None

    def get_user_orders(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[PointsExchangeOrder]:
        """获取用户兑换订单"""
        results = []
        for order in reversed(self._orders):
            if order.user_id != user_id:
                continue
            if status and order.status != status:
                continue
            results.append(order)
            if len(results) >= limit:
                break

        return results

    def add_product(self, product: PointsProduct) -> None:
        """添加商品"""
        self._products[product.id] = product
        logger.info(f"添加积分商品: {product.name}")

    def update_product(self, product_id: str, updates: Dict[str, Any]) -> bool:
        """更新商品"""
        product = self._products.get(product_id)
        if not product:
            return False

        for key, value in updates.items():
            if hasattr(product, key):
                setattr(product, key, value)

        return True

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        if product_id in self._products:
            del self._products[product_id]
            return True
        return False


# 积分商品服务单例
_product_service: Optional[PointsProductService] = None


def get_points_product_service() -> PointsProductService:
    """获取积分商品服务单例"""
    global _product_service
    if _product_service is None:
        _product_service = PointsProductService()
    return _product_service


class ProductService:
    """测试兼容的积分商品服务（DB 版）"""

    async def get_products(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
    ) -> list[Any]:
        from ...models.points import Product

        query = select(Product)
        if category and category != "all":
            query = query.where(Product.category == category)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_product_detail(self, db: AsyncSession, product_id: int):
        from ...models.points import Product

        result = await db.execute(select(Product).where(Product.id == int(product_id)))
        return result.scalar_one_or_none()

    async def redeem(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        product_id: int,
        quantity: int = 1,
    ) -> bool:
        from ...models.points import Product
        from .points_service import points_service

        result = await db.execute(select(Product).where(Product.id == int(product_id)))
        product = result.scalar_one_or_none()
        if not product or not bool(getattr(product, "is_active", True)):
            return False
        stock = int(getattr(product, "stock", 0) or 0)
        if stock < int(quantity):
            return False

        success = await points_service.deduct_points(
            db,
            int(user_id),
            int(getattr(product, "price", 0) or 0) * int(quantity),
            reason="兑换商品",
            order_no=f"redeem-{int(product_id)}",
        )
        if not success:
            return False

        setattr(product, "stock", stock - int(quantity))
        await db.commit()
        return True

    async def get_redemption_history(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Any]:
        from ...models.points import PointsExchangeOrder

        result = await db.execute(
            select(PointsExchangeOrder)
            .where(PointsExchangeOrder.user_id == int(user_id))
            .order_by(PointsExchangeOrder.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all())


product_service = ProductService()
