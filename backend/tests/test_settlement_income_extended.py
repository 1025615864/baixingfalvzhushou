"""
IncomeService扩展测试用例
目标：将income.py的覆盖率从33%提升至65%+
"""
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.payment import PaymentOrder, PaymentStatus, OrderType
from app.models.lawfirm import Lawyer, LawyerConsultation
from app.models.settlement import LawyerIncomeRecord, LawyerWallet
from app.models.user import User
from app.services.settlement.income import IncomeService
from app.services.settlement.core import SettlementService
from app.database import Base


# 测试数据库配置
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """设置测试数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db():
    """创建数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def test_user(db: AsyncSession):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
        role="user",
        phone="13800138000",
        nickname="测试用户",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_lawyer(db: AsyncSession, test_user: User):
    """创建测试律师"""
    lawyer = Lawyer(
        user_id=test_user.id,
        name="测试律师",
        phone="13800138000",
        license_no="LIC123456",
        specialties="民法,刑法",
        experience_years=5,
        rating=4.5,
        is_verified=True,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(lawyer)
    await db.commit()
    await db.refresh(lawyer)
    return lawyer


@pytest.fixture
async def test_consultation(db: AsyncSession, test_user: User, test_lawyer: Lawyer):
    """创建测试咨询"""
    consultation = LawyerConsultation(
        user_id=test_user.id,
        lawyer_id=test_lawyer.id,
        subject="测试咨询",
        description="测试描述",
        status="completed",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(consultation)
    await db.commit()
    await db.refresh(consultation)
    return consultation


@pytest.fixture
async def income_service(db: AsyncSession):
    """创建IncomeService实例"""
    settlement_service = SettlementService()
    return IncomeService(settlement_service)


@pytest.fixture
async def paid_order(db: AsyncSession, test_consultation: LawyerConsultation, test_user: User):
    """创建已支付订单"""
    order = PaymentOrder(
        user_id=test_user.id,
        order_no="ORDER001",
        order_type=OrderType.CONSULTATION.value,
        amount=100.0,
        actual_amount=100.0,
        amount_cents=10000,
        actual_amount_cents=10000,
        status=PaymentStatus.PAID.value,
        payment_method="alipay",
        title="咨询订单",
        description="测试订单",
        related_id=test_consultation.id,
        related_type="consultation",
        paid_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(order)
    return order


@pytest.fixture
async def review_order(db: AsyncSession, test_lawyer: Lawyer, test_user: User):
    """创建审核订单"""
    order = await _create_order(
        db,
        user_id=test_user.id,
        order_no="REVIEW001",
        order_type=OrderType.LIGHT_CONSULT_REVIEW.value,
        amount=50.0,
        status=PaymentStatus.PAID.value,
        title="律师复核订单",
        payment_method="wechat",
    )
    return order


async def _create_order(
    db: AsyncSession,
    *,
    user_id: int,
    order_no: str,
    order_type: str,
    amount: float,
    status: str,
    title: str,
    payment_method: str | None = None,
    description: str | None = None,
    related_id: int | None = None,
    related_type: str | None = None,
    amount_cents: int | None = None,
    actual_amount: float | None = None,
    actual_amount_cents: int | None = None,
    paid_at: datetime | None = None,
) -> PaymentOrder:
    """创建测试订单"""
    actual_amount_value = amount if actual_amount is None else actual_amount
    if amount_cents is None:
        amount_cents = int(round(amount * 100))
    if actual_amount_cents is None and actual_amount_value is not None:
        actual_amount_cents = int(round(actual_amount_value * 100))

    now = datetime.now(timezone.utc)
    order = PaymentOrder(
        user_id=user_id,
        order_no=order_no,
        order_type=order_type,
        amount=amount,
        actual_amount=actual_amount_value,
        amount_cents=amount_cents,
        actual_amount_cents=actual_amount_cents,
        status=status,
        payment_method=payment_method,
        title=title,
        description=description,
        related_id=related_id,
        related_type=related_type,
        paid_at=paid_at,
        created_at=now,
        updated_at=now,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


class TestIncomeServiceExtended:
    """IncomeService扩展测试类"""

    # ==================== Test ensure_income_record_for_completed_consultation ====================

    async def test_ensure_income_record_order_is_none(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation):
        """测试：order为None时返回None"""
        result = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, None
        )
        assert result is None

    async def test_ensure_income_record_order_not_paid(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation, test_user: User):
        """测试：订单未支付时返回None"""
        order = await _create_order(
            db,
            user_id=test_user.id,
            order_no="ORDER002",
            order_type=OrderType.CONSULTATION.value,
            amount=100.0,
            status=PaymentStatus.PENDING.value,
            title="待支付订单",
        )
        
        result = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, order
        )
        assert result is None

    async def test_ensure_income_record_already_exists(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation, paid_order: PaymentOrder):
        """测试：收入记录已存在时返回现有记录"""
        # 第一次调用创建记录
        first_record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, paid_order
        )
        assert first_record is not None
        
        # 第二次调用应返回现有记录
        second_record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, paid_order
        )
        assert second_record is not None
        assert second_record.id == first_record.id

    async def test_ensure_income_record_normal_case(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation, paid_order: PaymentOrder):
        """测试：正常创建收入记录"""
        record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, paid_order
        )
        
        assert record is not None
        assert record.lawyer_id == test_consultation.lawyer_id
        assert record.consultation_id == test_consultation.id
        assert record.order_no == paid_order.order_no
        assert record.user_paid_amount == 100.0
        assert record.user_paid_amount_cents == 10000
        assert record.status == "pending"
        assert record.withdrawn_amount == 0.0
        assert record.withdrawn_amount_cents == 0
        assert record.settle_time is not None

    async def test_ensure_income_record_zero_amount(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation, test_user: User):
        """测试：金额为0的收入记录"""
        order = await _create_order(
            db,
            user_id=test_user.id,
            order_no="ORDER003",
            order_type=OrderType.CONSULTATION.value,
            amount=0.0,
            status=PaymentStatus.PAID.value,
            title="0元订单",
            amount_cents=0,
            actual_amount_cents=0,
        )
        
        record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, order
        )
        
        assert record is not None
        assert record.user_paid_amount == 0.0
        assert record.lawyer_income >= 0.0

    async def test_ensure_income_record_decimal_amount(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation, test_user: User):
        """测试：小数金额的收入记录"""
        order = await _create_order(
            db,
            user_id=test_user.id,
            order_no="ORDER004",
            order_type=OrderType.CONSULTATION.value,
            amount=99.99,
            status=PaymentStatus.PAID.value,
            title="小数金额订单",
            amount_cents=9999,
            actual_amount_cents=9999,
        )
        
        record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, order
        )
        
        assert record is not None
        assert record.user_paid_amount == 99.99
        assert record.user_paid_amount_cents == 9999

    async def test_ensure_income_record_large_amount(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation, test_user: User):
        """测试：大额收入记录"""
        order = await _create_order(
            db,
            user_id=test_user.id,
            order_no="ORDER005",
            order_type=OrderType.CONSULTATION.value,
            amount=99999.99,
            status=PaymentStatus.PAID.value,
            title="大额订单",
            amount_cents=9999999,
            actual_amount_cents=9999999,
        )
        
        record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, order
        )
        
        assert record is not None
        assert record.user_paid_amount == 99999.99

    async def test_ensure_income_record_wallet_updated(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation, paid_order: PaymentOrder):
        """测试：钱包余额正确更新"""
        record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, paid_order
        )
        
        # 查询钱包
        result = await db.execute(
            select(LawyerWallet).where(LawyerWallet.lawyer_id == test_consultation.lawyer_id)
        )
        wallet = result.scalar_one_or_none()
        
        assert wallet is not None
        assert wallet.lawyer_id == test_consultation.lawyer_id
        assert wallet.total_income > 0
        assert wallet.pending_amount > 0
        assert wallet.available_amount == 0
        assert wallet.withdrawn_amount == 0.0

    async def test_ensure_income_record_platform_fee_validation(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation, paid_order: PaymentOrder):
        """测试：平台费计算和验证"""
        record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, paid_order
        )
        
        # 平台费应该在0到实付金额之间
        assert record.platform_fee >= 0.0
        assert record.platform_fee <= record.user_paid_amount
        assert record.lawyer_income == record.user_paid_amount - record.platform_fee
        assert record.platform_fee_cents == int(record.platform_fee * 100)
        assert record.lawyer_income_cents == int(record.lawyer_income * 100)

    # ==================== Test ensure_income_record_for_paid_review_order ====================

    async def test_ensure_review_record_order_not_paid(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, review_order: PaymentOrder):
        """测试：审核订单未支付时返回None"""
        review_order.status = PaymentStatus.PENDING.value
        db.add(review_order)
        await db.commit()
        
        result = await income_service.ensure_income_record_for_paid_review_order(
            db, lawyer_id=test_lawyer.id, order=review_order
        )
        assert result is None

    async def test_ensure_review_record_wrong_order_type(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_user: User):
        """测试：订单类型不正确时返回None"""
        order = await _create_order(
            db,
            user_id=test_user.id,
            order_no="ORDER006",
            order_type=OrderType.CONSULTATION.value,
            amount=50.0,
            status=PaymentStatus.PAID.value,
            title="错误类型订单",
        )
        
        result = await income_service.ensure_income_record_for_paid_review_order(
            db, lawyer_id=test_lawyer.id, order=order
        )
        assert result is None

    async def test_ensure_review_record_no_order_no(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_user: User):
        """测试：订单号为空时返回None"""
        order = await _create_order(
            db,
            user_id=test_user.id,
            order_no="",
            order_type=OrderType.LIGHT_CONSULT_REVIEW.value,
            amount=50.0,
            status=PaymentStatus.PAID.value,
            title="无订单号",
        )
        
        result = await income_service.ensure_income_record_for_paid_review_order(
            db, lawyer_id=test_lawyer.id, order=order
        )
        assert result is None

    async def test_ensure_review_record_already_exists(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, review_order: PaymentOrder):
        """测试：审核收入记录已存在"""
        # 第一次调用
        first_record = await income_service.ensure_income_record_for_paid_review_order(
            db, lawyer_id=test_lawyer.id, order=review_order
        )
        assert first_record is not None
        
        # 第二次调用应返回现有记录
        second_record = await income_service.ensure_income_record_for_paid_review_order(
            db, lawyer_id=test_lawyer.id, order=review_order
        )
        assert second_record is not None
        assert second_record.id == first_record.id

    async def test_ensure_review_record_normal_case(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, review_order: PaymentOrder):
        """测试：正常创建审核收入记录"""
        record = await income_service.ensure_income_record_for_paid_review_order(
            db, lawyer_id=test_lawyer.id, order=review_order
        )
        
        assert record is not None
        assert record.lawyer_id == test_lawyer.id
        assert record.consultation_id is None
        assert record.order_no == review_order.order_no
        assert record.user_paid_amount == 50.0
        assert record.user_paid_amount_cents == 5000
        assert record.status == "pending"
        assert record.settle_time is not None

    async def test_ensure_review_record_zero_amount(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_user: User):
        """测试：审核订单0金额"""
        order = await _create_order(
            db,
            user_id=test_user.id,
            order_no="REVIEW002",
            order_type=OrderType.LIGHT_CONSULT_REVIEW.value,
            amount=0.0,
            status=PaymentStatus.PAID.value,
            title="0元审核订单",
            payment_method="wechat",
            amount_cents=0,
            actual_amount_cents=0,
        )
        
        record = await income_service.ensure_income_record_for_paid_review_order(
            db, lawyer_id=test_lawyer.id, order=order
        )
        
        assert record is not None
        assert record.user_paid_amount == 0.0

    async def test_ensure_review_record_decimal_amount(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_user: User):
        """测试：审核订单小数金额"""
        order = await _create_order(
            db,
            user_id=test_user.id,
            order_no="REVIEW003",
            order_type=OrderType.LIGHT_CONSULT_REVIEW.value,
            amount=49.99,
            status=PaymentStatus.PAID.value,
            title="小数审核订单",
            payment_method="wechat",
            amount_cents=4999,
            actual_amount_cents=4999,
        )
        
        record = await income_service.ensure_income_record_for_paid_review_order(
            db, lawyer_id=test_lawyer.id, order=order
        )
        
        assert record is not None
        assert record.user_paid_amount == 49.99
        assert record.user_paid_amount_cents == 4999

    # ==================== Test settle_due_income_records ====================

    async def test_settle_due_records_empty(self, income_service: IncomeService, db: AsyncSession):
        """测试：无到期记录时返回0"""
        result = await income_service.settle_due_income_records(db)
        assert result == {"settled": 0}

    async def test_settle_due_records_future_settle_time(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_consultation: LawyerConsultation):
        """测试：未来的结算时间不应该被结算"""
        # 创建未来才到期的记录
        record = LawyerIncomeRecord(
            lawyer_id=test_lawyer.id,
            consultation_id=test_consultation.id,
            order_no="ORDER007",
            user_paid_amount=100.0,
            platform_fee=15.0,
            lawyer_income=85.0,
            user_paid_amount_cents=10000,
            platform_fee_cents=1500,
            lawyer_income_cents=8500,
            withdrawn_amount=0.0,
            withdrawn_amount_cents=0,
            status="pending",
            settle_time=datetime.now(timezone.utc) + timedelta(days=30),  # 30天后
        )
        db.add(record)
        await db.commit()
        
        result = await income_service.settle_due_income_records(db)
        assert result == {"settled": 0}

    async def test_settle_due_records_zero_income(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_consultation: LawyerConsultation):
        """测试：收入为0的记录结算"""
        record = LawyerIncomeRecord(
            lawyer_id=test_lawyer.id,
            consultation_id=test_consultation.id,
            order_no="ORDER008",
            user_paid_amount=0.0,
            platform_fee=0.0,
            lawyer_income=0.0,
            user_paid_amount_cents=0,
            platform_fee_cents=0,
            lawyer_income_cents=0,
            withdrawn_amount=0.0,
            withdrawn_amount_cents=0,
            status="pending",
            settle_time=datetime.now(timezone.utc) - timedelta(days=1),  # 已过期
        )
        db.add(record)
        await db.commit()
        
        result = await income_service.settle_due_income_records(db)
        assert result == {"settled": 1}
        
        # 验证状态已更新
        await db.refresh(record)
        assert record.status == "settled"

    async def test_settle_due_records_normal(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_consultation: LawyerConsultation):
        """测试：正常结算到期记录"""
        # 创建钱包
        wallet = LawyerWallet(
            lawyer_id=test_lawyer.id,
            total_income=100.0,
            pending_amount=85.0,
            frozen_amount=0.0,
            available_amount=0.0,
            withdrawn_amount=15.0,
        )
        db.add(wallet)
        await db.commit()
        
        # 创建到期的收入记录
        record = LawyerIncomeRecord(
            lawyer_id=test_lawyer.id,
            consultation_id=test_consultation.id,
            order_no="ORDER009",
            user_paid_amount=100.0,
            platform_fee=15.0,
            lawyer_income=85.0,
            user_paid_amount_cents=10000,
            platform_fee_cents=1500,
            lawyer_income_cents=8500,
            withdrawn_amount=0.0,
            withdrawn_amount_cents=0,
            status="pending",
            settle_time=datetime.now(timezone.utc) - timedelta(hours=1),  # 1小时前到期
        )
        db.add(record)
        await db.commit()
        
        result = await income_service.settle_due_income_records(db)
        assert result == {"settled": 1}
        
        # 验证记录状态
        await db.refresh(record)
        assert record.status == "settled"
        
        # 验证钱包更新
        await db.refresh(wallet)
        assert wallet.pending_amount == 0.0
        assert wallet.available_amount == 85.0

    async def test_settle_due_records_multiple(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_consultation: LawyerConsultation):
        """测试：批量结算多条到期记录"""
        # 创建钱包
        wallet = LawyerWallet(
            lawyer_id=test_lawyer.id,
            total_income=300.0,
            pending_amount=255.0,
            frozen_amount=0.0,
            available_amount=0.0,
            withdrawn_amount=0.0,
        )
        db.add(wallet)
        await db.commit()
        
        # 创建多条到期记录
        for i in range(5):
            record = LawyerIncomeRecord(
                lawyer_id=test_lawyer.id,
                consultation_id=test_consultation.id,
                order_no=f"ORDER{i}",
                user_paid_amount=100.0,
                platform_fee=15.0,
                lawyer_income=85.0,
                user_paid_amount_cents=10000,
                platform_fee_cents=1500,
                lawyer_income_cents=8500,
                withdrawn_amount=0.0,
                withdrawn_amount_cents=0,
                status="pending",
                settle_time=datetime.now(timezone.utc) - timedelta(hours=i+1),
            )
            db.add(record)
        await db.commit()
        
        result = await income_service.settle_due_income_records(db)
        assert result == {"settled": 5}
        
        # 验证钱包
        await db.refresh(wallet)
        assert wallet.available_amount == 300.0  # 等于total_income
        assert wallet.pending_amount == 0.0

    async def test_settle_due_records_negative_pending(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_consultation: LawyerConsultation):
        """测试：pending_amount为负时的处理"""
        # 创建负pending的钱包
        wallet = LawyerWallet(
            lawyer_id=test_lawyer.id,
            total_income=100.0,
            pending_amount=-10.0,  # 负数
            frozen_amount=0.0,
            available_amount=0.0,
            withdrawn_amount=0.0,
        )
        db.add(wallet)
        await db.commit()
        
        # 创建到期记录
        record = LawyerIncomeRecord(
            lawyer_id=test_lawyer.id,
            consultation_id=test_consultation.id,
            order_no="ORDER010",
            user_paid_amount=100.0,
            platform_fee=15.0,
            lawyer_income=85.0,
            user_paid_amount_cents=10000,
            platform_fee_cents=1500,
            lawyer_income_cents=8500,
            withdrawn_amount=0.0,
            withdrawn_amount_cents=0,
            status="pending",
            settle_time=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(record)
        await db.commit()
        
        result = await income_service.settle_due_income_records(db)
        assert result == {"settled": 1}
        
        # 验证钱包pending被重置为0
        await db.refresh(wallet)
        assert wallet.pending_amount == 0.0

    async def test_settle_due_records_wallet_fields_recalc(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_consultation: LawyerConsultation):
        """测试：结算后钱包字段重新计算"""
        # 创建完整信息的钱包
        wallet = LawyerWallet(
            lawyer_id=test_lawyer.id,
            total_income=200.0,
            pending_amount=170.0,
            frozen_amount=20.0,
            available_amount=10.0,
            withdrawn_amount=0.0,
        )
        db.add(wallet)
        await db.commit()
        
        # 创建到期记录
        record = LawyerIncomeRecord(
            lawyer_id=test_lawyer.id,
            consultation_id=test_consultation.id,
            order_no="ORDER011",
            user_paid_amount=100.0,
            platform_fee=15.0,
            lawyer_income=85.0,
            user_paid_amount_cents=10000,
            platform_fee_cents=1500,
            lawyer_income_cents=8500,
            withdrawn_amount=0.0,
            withdrawn_amount_cents=0,
            status="pending",
            settle_time=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(record)
        await db.commit()
        
        result = await income_service.settle_due_income_records(db)
        assert result == {"settled": 1}
        
        # 验证字段重新计算
        await db.refresh(wallet)
        assert wallet.available_amount == wallet.total_income - wallet.pending_amount - wallet.frozen_amount - wallet.withdrawn_amount

    # ==================== Test Additional Edge Cases ====================

    async def test_ensure_income_record_order_no_whitespace(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation, test_user: User):
        """测试：订单号包含空格时被正确处理"""
        order = await _create_order(
            db,
            user_id=test_user.id,
            order_no="  ORDER012  ",
            order_type=OrderType.CONSULTATION.value,
            amount=100.0,
            status=PaymentStatus.PAID.value,
            title="空格订单号",
            amount_cents=10000,
            actual_amount_cents=10000,
        )
        
        record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, order
        )
        
        assert record is not None
        assert record.order_no == "ORDER012"  # 空格被去除

    async def test_ensure_income_record_actual_amount_none(self, income_service: IncomeService, db: AsyncSession, test_consultation: LawyerConsultation, test_user: User):
        """测试：actual_amount为None时使用0"""
        order = PaymentOrder(
            user_id=test_user.id,
            order_no="ORDER013",
            order_type=OrderType.CONSULTATION.value,
            amount=100.0,
            actual_amount=None,  # None
            status=PaymentStatus.PAID.value,
            title="None金额",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        # 不写入数据库，直接使用对象模拟
        
        record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, order
        )
        
        assert record is not None
        assert record.user_paid_amount == 0.0

    async def test_ensure_review_record_getattr_none_order_no(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer):
        """测试：使用getattr获取order_no为None的情况"""
        # 创建不包含order_no属性的订单对象模拟
        class MockOrder:
            status = PaymentStatus.PAID
            order_type = OrderType.LIGHT_CONSULT_REVIEW.value
            # 没有 order_no 属性
        
        mock_order = MockOrder()
        result = await income_service.ensure_income_record_for_paid_review_order(
            db, lawyer_id=test_lawyer.id, order=mock_order
        )
        assert result is None

    async def test_settle_due_records_already_settled(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_consultation: LawyerConsultation):
        """测试：已结算的记录不应再次结算"""
        # 创建已结算的记录
        record = LawyerIncomeRecord(
            lawyer_id=test_lawyer.id,
            consultation_id=test_consultation.id,
            order_no="ORDER014",
            user_paid_amount=100.0,
            platform_fee=15.0,
            lawyer_income=85.0,
            user_paid_amount_cents=10000,
            platform_fee_cents=1500,
            lawyer_income_cents=8500,
            withdrawn_amount=0.0,
            withdrawn_amount_cents=0,
            status="settled",  # 已结算
            settle_time=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(record)
        await db.commit()
        
        result = await income_service.settle_due_income_records(db)
        # 应该不结算已结算的记录
        assert result == {"settled": 0}

    async def test_settle_due_records_no_settle_time(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_consultation: LawyerConsultation):
        """测试：没有结算时间的记录不应被结算"""
        record = LawyerIncomeRecord(
            lawyer_id=test_lawyer.id,
            consultation_id=test_consultation.id,
            order_no="ORDER015",
            user_paid_amount=100.0,
            platform_fee=15.0,
            lawyer_income=85.0,
            user_paid_amount_cents=10000,
            platform_fee_cents=1500,
            lawyer_income_cents=8500,
            withdrawn_amount=0.0,
            withdrawn_amount_cents=0,
            status="pending",
            settle_time=None,  # 没有结算时间
        )
        db.add(record)
        await db.commit()
        
        result = await income_service.settle_due_income_records(db)
        assert result == {"settled": 0}

    async def test_wallet_creation_if_not_exists(self, income_service: IncomeService, db: AsyncSession, test_lawyer: Lawyer, test_consultation: LawyerConsultation, paid_order: PaymentOrder):
        """测试：创建收入记录时自动创建钱包"""
        # 确保钱包不存在
        result = await db.execute(
            select(LawyerWallet).where(LawyerWallet.lawyer_id == test_lawyer.id)
        )
        existing_wallet = result.scalar_one_or_none()
        if existing_wallet:
            await db.delete(existing_wallet)
            await db.commit()
        
        # 调用方法应自动创建钱包
        record = await income_service.ensure_income_record_for_completed_consultation(
            db, test_consultation, paid_order
        )
        
        # 验证钱包已创建
        result = await db.execute(
            select(LawyerWallet).where(LawyerWallet.lawyer_id == test_lawyer.id)
        )
        wallet = result.scalar_one_or_none()
        assert wallet is not None
        assert wallet.total_income > 0