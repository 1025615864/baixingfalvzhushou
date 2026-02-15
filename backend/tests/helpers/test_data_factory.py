"""
测试数据工厂

提供统一的测试数据生成工具，简化测试代码编写。
"""
import asyncio
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.lawfirm import Lawyer
from app.models.consultation import Consultation
from app.models.payment import PaymentOrder
from app.models.forum import Post, Comment
from app.models.news import News


class UserFactory:
    """用户数据工厂"""
    
    @staticmethod
    def create_user_data(
        username: str = "testuser",
        email: str = None,
        role: str = "user",
        is_active: bool = True,
    ) -> dict[str, Any]:
        """创建用户数据字典
        
        Args:
            username: 用户名
            email: 邮箱
            role: 角色类型
            is_active: 是否激活
            
        Returns:
            用户数据字典
        """
        return {
            "username": username,
            "email": email or f"{username}@example.com",
            "hashed_password": "hashed_password_123",
            "is_active": is_active,
            "role": role,
            "phone": "13800138000",
            "nickname": f"测试用户_{username}",
        }
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str = None,
        email: str = None,
        role: str = "user",
    ) -> User:
        """创建数据库用户实例
        
        Args:
            db: 数据库会话
            username: 用户名（如果未提供则自动生成）
            email: 邮箱（如果未提供则自动生成）
            role: 角色类型
            
        Returns:
            用户实例
        """
        username = username or f"testuser_{asyncio.get_event_loop().time()}"
        email = email or f"{username}@example.com"
        
        user = User(
            username=username,
            email=email,
            hashed_password="hashed_password",
            is_active=True,
            role=role,
            phone="13800138000",
            nickname=f"测试用户_{username}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    def create_admin_data() -> dict[str, Any]:
        """创建管理员数据"""
        return UserFactory.create_user_data(
            username="admin",
            role="admin",
            is_active=True,
        )


class OrderFactory:
    """订单数据工厂"""
    
    @staticmethod
    def create_order_data(
        user_id: int = 1,
        amount: Decimal = None,
        provider: str = "alipay",
        status: str = "pending",
    ) -> dict[str, Any]:
        """创建订单数据字典
        
        Args:
            user_id: 用户ID
            amount: 订单金额
            provider: 支付提供商
            status: 订单状态
            
        Returns:
            订单数据字典
        """
        return {
            "user_id": user_id,
            "order_no": f"ORDER{asyncio.get_event_loop().time()}",
            "amount": amount or Decimal("100.00"),
            "currency": "CNY",
            "description": "测试订单",
            "provider": provider,
            "provider_order_no": f"PROV{asyncio.get_event_loop().time()}",
            "status": status,
            "paid_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    
    @staticmethod
    async def create_order(
        db: AsyncSession,
        user_id: int,
        amount: Decimal = None,
    ) -> PaymentOrder:
        """创建数据库订单实例
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            amount: 订单金额
            
        Returns:
            订单实例
        """
        order = PaymentOrder(
            user_id=user_id,
            order_no=f"ORDER{asyncio.get_event_loop().time()}",
            amount=amount or Decimal("100.00"),
            actual_amount=amount or Decimal("100.00"),
            status="pending",
            order_type="consultation",
            title="测试订单",
        )
        
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order


class PaymentFactory:
    """支付数据工厂"""
    
    @staticmethod
    def create_callback_data(
        order_no: str = "ORDER001",
        amount: str = "100.00",
        status: str = "success",
    ) -> dict[str, Any]:
        """创建支付回调数据
        
        Args:
            order_no: 订单号
            amount: 支付金额
            status: 支付状态
            
        Returns:
            回调数据字典
        """
        return {
            "order_no": order_no,
            "amount": amount,
            "status": status,
            "trade_no": f"TRADE{asyncio.get_event_loop().time()}",
            "paid_at": datetime.now(timezone.utc).isoformat(),
            "signature": "test_signature",
        }
    
    @staticmethod
    def create_wechat_callback(
        order_no: str,
        total_fee: str = "10000",
        code: str = "SUCCESS",
    ) -> dict[str, Any]:
        """创建微信支付回调数据
        
        Args:
            order_no: 订单号
            total_fee: 总金额（分）
            code: 支付状态码
            
        Returns:
            微信回调数据字典
        """
        return {
            "out_trade_no": order_no,
            "transaction_id": f"WX{asyncio.get_event_loop().time()}",
            "total_fee": total_fee,
            "code": code,
            "time_end": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        }


class ConsultationFactory:
    """咨询数据工厂"""
    
    @staticmethod
    def create_consultation_data(
        user_id: int = 1,
        lawyer_id: int = 1,
        title: str = None,
        description: str = None,
    ) -> dict[str, Any]:
        """创建咨询数据字典
        
        Args:
            user_id: 用户ID
            lawyer_id: 律师ID
            title: 咨询标题
            description: 咨询描述
            
        Returns:
            咨询数据字典
        """
        return {
            "user_id": user_id,
            "lawyer_id": lawyer_id,
            "title": title or "咨询标题",
            "description": description or "咨询描述内容",
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    
    @staticmethod
    async def create_consultation(
        db: AsyncSession,
        user_id: int,
        lawyer_id: int = None,
    ) -> Consultation:
        """创建数据库咨询实例
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            lawyer_id: 律师ID
            
        Returns:
            咨询实例
        """
        consultation = Consultation(
            user_id=user_id,
            lawyer_id=lawyer_id or 1,
            title="咨询标题",
            description="咨询描述内容",
            status="pending",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        db.add(consultation)
        await db.commit()
        await db.refresh(consultation)
        return consultation


class PostFactory:
    """论坛帖子数据工厂"""
    
    @staticmethod
    def create_post_data(
        user_id: int = 1,
        title: str = None,
        content: str = None,
        category: str = "general",
    ) -> dict[str, Any]:
        """创建论坛帖子数据字典
        
        Args:
            user_id: 用户ID
            title: 帖子标题
            content: 帖子内容
            category: 帖子分类
            
        Returns:
            帖子数据字典（用于API请求，不包含datetime字段）
        """
        return {
            "title": title or "测试帖子标题",
            "content": content or "测试帖子内容，这是一个关于法律咨询的帖子",
            "category": category,
        }
    
    @staticmethod
    async def create_forum_post(
        db: AsyncSession,
        user_id: int,
        title: str = None,
    ) -> Post:
        """创建数据库论坛帖子实例
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            title: 帖子标题
            
        Returns:
            帖子实例
        """
        post = Post(
            user_id=user_id,
            title=title or "测试帖子标题",
            content="测试帖子内容，这是一个关于法律咨询的帖子",
            category="general",
            review_status="approved",
            view_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post


class NewsFactory:
    """新闻数据工厂"""
    
    @staticmethod
    def create_news_data(
        title: str = None,
        content: str = None,
        category: str = "general",
        is_published: bool = True,
        is_deleted: bool = False,
        author: str = "测试作者",
    ) -> dict[str, Any]:
        """创建新闻数据字典
        
        Args:
            title: 新闻标题
            content: 新闻内容
            category: 新闻分类
            is_published: 是否发布
            is_deleted: 是否删除
            author: 作者名称
            
        Returns:
            新闻数据字典
        """
        return {
            "title": title or "测试新闻标题",
            "content": content or "测试新闻内容，这是一条关于法律新闻的消息",
            "summary": "新闻摘要",
            "category": category,
            "is_published": is_published,
            "is_deleted": is_deleted,
            "author": author,
            "source": None,
            "source_url": None,
            "cover_image": None,
            "view_count": 0,
            "is_top": False,
            "review_status": "approved",
        }
    
    @staticmethod
    async def create_news(
        db: AsyncSession,
        title: str = None,
        category: str = "general",
        is_published: bool = True,
        is_deleted: bool = False,
        author: str = "测试作者",
    ) -> News:
        """创建数据库新闻实例
        
        Args:
            db: 数据库会话
            title: 新闻标题
            category: 新闻分类
            is_published: 是否发布
            is_deleted: 是否删除
            author: 作者名称
            
        Returns:
            新闻实例
        """
        article = News(
            title=title or "测试新闻标题",
            content="测试新闻内容，这是一条关于法律新闻的消息",
            summary="新闻摘要",
            category=category,
            is_published=is_published,
            is_deleted=is_deleted,
            author=author,
            source=None,
            source_url=None,
            cover_image=None,
            view_count=0,
            is_top=False,
            review_status="approved",
        )
        
        db.add(article)
        await db.commit()
        await db.refresh(article)
        return article


class TestDataFactory:
    """统一测试数据工厂"""
    
    def __init__(self, db: AsyncSession):
        """初始化测试数据工厂
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self._users: list[User] = []
        self._orders: list[PaymentOrder] = []
        self._consultations: list[Consultation] = []
        self._posts: list[Post] = []
        self._news: list[News] = []
    
    async def create_user(
        self,
        username: str = None,
        role: str = "user",
    ) -> User:
        """创建测试用户
        
        Args:
            username: 用户名
            role: 角色类型
            
        Returns:
            用户实例
        """
        user = await UserFactory.create_user(self.db, username, role=role)
        self._users.append(user)
        return user
    
    async def create_admin(self) -> User:
        """创建测试管理员"""
        admin = await UserFactory.create_user(self.db, "test_admin", "admin")
        self._users.append(admin)
        return admin
    
    async def create_lawyer(
        self,
        user_id: int = None,
        name: str = "测试律师",
        specialties: str = "劳动法",
    ) -> Lawyer:
        """创建测试律师
        
        Args:
            user_id: 用户ID
            name: 律师姓名
            specialties: 专业领域
            
        Returns:
            律师实例
        """
        if user_id is None and self._users:
            user_id = self._users[0].id
        
        lawyer = Lawyer(
            user_id=user_id or 1,
            name=name,
            license_no="1234567890123456",
            specialties=specialties,
            experience_years=10,
            is_verified=True,
            is_active=True,
            description="律师简介",
        )
        
        self.db.add(lawyer)
        await self.db.commit()
        await self.db.refresh(lawyer)
        return lawyer
    
    async def create_order(
        self,
        user_id: int = None,
        amount: Decimal = Decimal("100.00"),
    ) -> PaymentOrder:
        """创建测试订单"""
        if user_id is None and self._users:
            user_id = self._users[0].id
        
        order = await OrderFactory.create_order(self.db, user_id, amount)
        self._orders.append(order)
        return order
    
    async def create_consultation(
        self,
        user_id: int = None,
        lawyer_id: int = None,
    ) -> Consultation:
        """创建测试咨询"""
        if user_id is None and self._users:
            user_id = self._users[0].id
        
        consultation = await ConsultationFactory.create_consultation(
            self.db, user_id, lawyer_id
        )
        self._consultations.append(consultation)
        return consultation
    
    async def create_forum_post(
        self,
        user_id: int = None,
        title: str = None,
    ) -> Post:
        """创建测试论坛帖子"""
        if user_id is None and self._users:
            user_id = self._users[0].id
        
        post = await PostFactory.create_forum_post(self.db, user_id, title)
        self._posts.append(post)
        return post
    
    async def create_news_article(
        self,
        title: str = None,
        category: str = "general",
        is_published: bool = True,
    ) -> News:
        """创建测试新闻文章"""
        article = await NewsFactory.create_news(
            self.db, title, category, is_published
        )
        self._news.append(article)
        return article
    
    async def cleanup(self):
        """清理测试数据"""
        for user in self._users:
            await self.db.delete(user)
        
        for order in self._orders:
            await self.db.delete(order)
        
        for consultation in self._consultations:
            await self.db.delete(consultation)
        
        for post in self._posts:
            await self.db.delete(post)
        
        for news in self._news:
            await self.db.delete(news)
        
        await self.db.commit()
        
        self._users.clear()
        self._orders.clear()
        self._consultations.clear()
        self._posts.clear()
        self._news.clear()


# ========== Settlement模块专用辅助函数 ==========

async def create_test_lawyer_with_user(
    db: AsyncSession,
    username: str = None,
    email: str = None,
) -> Lawyer:
    """创建测试律师和关联用户
    
    Args:
        db: 数据库会话
        username: 用户名（可选）
        email: 邮箱（可选）
    
    Returns:
        律师实例
    """
    # 创建用户（律师角色）
    username = username or f"lawyer_{asyncio.get_event_loop().time()}"
    email = email or f"{username}@example.com"
    
    user = User(
        username=username,
        email=email,
        hashed_password="hashed_password",
        is_active=True,
        phone="13800138000",
        nickname=f"律师_{username}",
        role="lawyer",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建律师档案
    lawyer = Lawyer(
        user_id=user.id,
        name=f"律师_{username}",
        license_no="1234567890123456",
        specialties="劳动法",
        experience_years=10,
        is_verified=True,
        is_active=True,
        rating=4.5,
        review_count=20,
        consultation_fee=200.0,
        description="测试律师简介",
    )
    
    db.add(lawyer)
    await db.commit()
    await db.refresh(lawyer)
    
    return lawyer


async def create_income_record(
    db: AsyncSession,
    lawyer_id: int,
    amount: float,
    status: str = "pending",
    consultation_id: int = None,
) -> 'LawyerIncomeRecord':
    """创建律师收入记录
    
    Args:
        db: 数据库会话
        lawyer_id: 律师ID
        amount: 用户支付金额
        status: 收入状态
        consultation_id: 关联的咨询ID
    
    Returns:
        收入记录实例
    """
    from app.models.settlement import LawyerIncomeRecord
    
    platform_fee = amount * 0.1  # 10%平台费
    lawyer_income = amount * 0.9  # 90%律师收入
    
    income_record = LawyerIncomeRecord(
        lawyer_id=lawyer_id,
        consultation_id=consultation_id,
        user_paid_amount=amount,
        platform_fee=platform_fee,
        lawyer_income=lawyer_income,
        status=status,
        order_no=f"ORDER-{int(datetime.now(timezone.utc).timestamp())}",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    db.add(income_record)
    await db.commit()
    await db.refresh(income_record)
    
    return income_record


async def create_withdrawal(
    db: AsyncSession,
    lawyer_id: int,
    amount: float,
    status: str = "pending",
    withdraw_method: str = "bank",
) -> 'WithdrawalRequest':
    """创建提现请求记录
    
    Args:
        db: 数据库会话
        lawyer_id: 律师ID
        amount: 提现金额
        status: 提现状态
        withdraw_method: 提现方式
    
    Returns:
        提现请求实例
    """
    from app.models.settlement import WithdrawalRequest
    
    fee = 10.0  # 固定手续费
    actual_amount = amount - fee
    
    withdrawal = WithdrawalRequest(
        lawyer_id=lawyer_id,
        request_no=f"WD-{int(datetime.now(timezone.utc).timestamp())}",
        amount=amount,
        fee=fee,
        actual_amount=actual_amount,
        withdraw_method=withdraw_method,
        account_info='{"bank":"测试银行","account_no":"6222000000000000","name":"测试用户"}',
        status=status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    db.add(withdrawal)
    await db.commit()
    await db.refresh(withdrawal)
    
    return withdrawal


async def create_wallet(
    db: AsyncSession,
    lawyer_id: int,
    total_income: float = 0.0,
    available_amount: float = 0.0,
) -> 'LawyerWallet':
    """创建律师钱包
    
    Args:
        db: 数据库会话
        lawyer_id: 律师ID
        total_income: 总收入
        available_amount: 可用金额
    
    Returns:
        钱包实例
    """
    from app.models.settlement import LawyerWallet
    
    wallet = LawyerWallet(
        lawyer_id=lawyer_id,
        total_income=total_income,
        available_amount=available_amount,
        withdrawn_amount=0.0,
        pending_amount=0.0,
        frozen_amount=0.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    
    return wallet