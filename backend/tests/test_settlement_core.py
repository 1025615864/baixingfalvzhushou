"""
结算服务核心模块测试

覆盖settlement/core.py中的所有主要功能：
- 加密/解密功能
- 费率计算
- 钱包管理
- 结算记录管理
- 金额计算
"""
import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.lawfirm import Lawyer
from app.models.settlement import LawyerIncomeRecord
from app.services.settlement.core import (
    SettlementService,
    _mask_account_no,
    _quantize_amount,
    _decimal_to_cents,
    _get_float_env,
    _get_int_env,
    _get_int_set_env,
    _now,
    SETTLEMENT_PLATFORM_FEE_RATE,
    SETTLEMENT_FREEZE_DAYS,
    SETTLEMENT_WITHDRAW_MIN_AMOUNT,
    SETTLEMENT_WITHDRAW_MAX_AMOUNT,
    SETTLEMENT_WITHDRAW_FEE,
    SETTLEMENT_VERIFIED_MIN_COMPLETED,
    SETTLEMENT_VERIFIED_MIN_RATING,
    SETTLEMENT_VERIFIED_PLATFORM_FEE_RATE,
    SETTLEMENT_VERIFIED_FREEZE_DAYS,
    SETTLEMENT_GOLD_MIN_COMPLETED,
    SETTLEMENT_GOLD_MIN_RATING,
    SETTLEMENT_GOLD_PLATFORM_FEE_RATE,
    SETTLEMENT_GOLD_FREEZE_DAYS,
    SETTLEMENT_PARTNER_LAWYER_IDS,
    SETTLEMENT_PARTNER_PLATFORM_FEE_RATE,
    SETTLEMENT_PARTNER_FREEZE_DAYS,
)

from tests.helpers.test_data_factory import UserFactory
from tests.helpers.assertion_helpers import (
    assert_not_none,
    assert_equals,
    assert_in_range,
    assert_greater_than,
)


@pytest.fixture
def settlement_service():
    """创建结算服务实例"""
    return SettlementService()


@pytest.fixture
async def lawyer_user(db: AsyncSession) -> User:
    """创建测试律师用户"""
    return await UserFactory.create_user(db, role="lawyer")


@pytest.fixture
async def lawyer(db: AsyncSession, lawyer_user: User) -> Lawyer:
    """创建测试律师资料"""
    lawyer = Lawyer(user_id=lawyer_user.id, name="测试律师", is_active=True, rating=4.5)
    db.add(lawyer)
    await db.commit()
    await db.refresh(lawyer)
    return lawyer


# ==================== 第一组：加密/解密功能 (4个测试) ====================

class TestEncryptionFunctionality:
    """测试加密和解密功能"""
    
    def test_encrypt_secret_basic(self, settlement_service):
        """测试基本加密功能"""
        original = "1234567890123456"
        encrypted = settlement_service.encrypt_secret(original)
        
        assert_not_none(encrypted)
        assert encrypted.startswith("enc:")
        assert encrypted != original
    
    def test_decrypt_secret_success(self, settlement_service):
        """测试成功解密"""
        original = "test_secret_123"
        encrypted = settlement_service.encrypt_secret(original)
        decrypted = settlement_service.decrypt_secret(encrypted)
        
        assert_equals(decrypted, original)
    
    def test_decrypt_secret_invalid_token(self, settlement_service):
        """测试解密无效token"""
        invalid_encrypted = "enc:invalid_token_data_12345"
        decrypted = settlement_service.decrypt_secret(invalid_encrypted)
        
        assert decrypted == ""
    
    def test_encrypt_decrypt_edge_cases(self, settlement_service):
        """测试加密解密边界情况"""
        # 测试空字符串
        assert settlement_service.encrypt_secret("") == ""
        assert settlement_service.decrypt_secret("") == ""
        
        # 测试None
        assert settlement_service.encrypt_secret(None) == ""
        assert settlement_service.decrypt_secret(None) == ""
        
        # 测试已加密的字符串
        already_encrypted = "enc:some_token"
        result = settlement_service.encrypt_secret(already_encrypted)
        assert_equals(result, already_encrypted)


# ==================== 第二组：费率与冻结天数选择 (2个测试) ====================

class TestFeeRateAndFreezeDays:
    """测试费率和冻结天数选择逻辑"""

    @pytest.mark.parametrize(
        "rating,completed,expected",
        [
            (4.0, 5, SETTLEMENT_PLATFORM_FEE_RATE),
            (float(SETTLEMENT_VERIFIED_MIN_RATING), int(SETTLEMENT_VERIFIED_MIN_COMPLETED), SETTLEMENT_VERIFIED_PLATFORM_FEE_RATE),
            (float(SETTLEMENT_GOLD_MIN_RATING), int(SETTLEMENT_GOLD_MIN_COMPLETED), SETTLEMENT_GOLD_PLATFORM_FEE_RATE),
        ],
    )
    def test_choose_platform_fee_rate(self, settlement_service, rating, completed, expected):
        """测试平台费率选择"""
        lawyer_id = 999  # 非合伙人律师
        rate = settlement_service.choose_platform_fee_rate(lawyer_id, rating, completed)
        assert_equals(rate, float(expected))
    
    @pytest.mark.asyncio
    async def test_choose_freeze_days_partner(self, settlement_service, monkeypatch):
        """测试合伙人律师冻结天数(优先级最高)"""
        # 使用monkeypatch设置合伙人律师ID
        monkeypatch.setenv("SETTLEMENT_PARTNER_LAWYER_IDS", "12345")
        
        lawyer_id = 12345
        rating = 5.0
        completed = 100
        
        freeze_days = settlement_service.choose_freeze_days(lawyer_id, rating, completed)
        assert_equals(freeze_days, 3)  # SETTLEMENT_PARTNER_FREEZE_DAYS默认值为3


# ==================== 第三组：钱包管理 (4个测试) ====================

@pytest.mark.asyncio
class TestWalletManagement:
    """测试钱包管理功能"""
    
    async def test_get_or_create_wallet_new(self, settlement_service, db: AsyncSession, lawyer: Lawyer):
        """测试创建新钱包"""
        # 获取或创建钱包
        wallet = await settlement_service.get_or_create_wallet(db, lawyer.id)
        
        assert_not_none(wallet)
        assert_equals(wallet.lawyer_id, lawyer.id)
        assert_equals(wallet.total_income, 0.0)
        assert_equals(wallet.available_amount, 0.0)
    
    async def test_get_or_create_wallet_existing(self, settlement_service, db: AsyncSession, lawyer: Lawyer):
        """测试获取已存在的钱包"""
        # 创建钱包
        wallet1 = await settlement_service.get_or_create_wallet(db, lawyer.id)
        wallet1.total_income = 1000.0
        await db.commit()
        
        # 再次获取，应该是同一个钱包
        wallet2 = await settlement_service.get_or_create_wallet(db, lawyer.id)
        
        assert_equals(wallet2.id, wallet1.id)
        assert_equals(wallet2.lawyer_id, lawyer.id)
    
    async def test_wallet_fields_recalculation(self, settlement_service, db: AsyncSession, lawyer: Lawyer):
        """测试钱包字段重新计算"""
        # 创建钱包并设置值
        wallet = await settlement_service.get_or_create_wallet(db, lawyer.id)
        wallet.total_income = 1000.0
        wallet.withdrawn_amount = 200.0
        wallet.pending_amount = 100.0
        wallet.frozen_amount = 50.0
        await db.commit()
        
        # 重新获取，验证计算
        wallet = await settlement_service.get_or_create_wallet(db, lawyer.id)
        
        expected_available = 1000.0 - 200.0 - 100.0 - 50.0  # 650.0
        assert_equals(wallet.available_amount, expected_available)
        assert_greater_than(wallet.available_amount_cents, 0)
    
    async def test_get_current_lawyer(self, settlement_service, db: AsyncSession, lawyer: Lawyer):
        """测试获取当前律师"""
        # 获取当前律师
        current_lawyer = await settlement_service.get_current_lawyer(db, lawyer.user_id)
        
        assert_not_none(current_lawyer)
        assert_equals(current_lawyer.id, lawyer.id)
        assert_equals(current_lawyer.user_id, lawyer.user_id)


# ==================== 第四组：结算记录管理 (5个测试) ====================

@pytest.mark.asyncio
class TestSettlementManagement:
    """测试结算记录管理"""
    
    async def test_create_settlement(self, settlement_service, db: AsyncSession, lawyer_user: User):
        """测试创建结算记录"""
        # 创建结算记录
        settlement = await settlement_service.create_settlement(
            db,
            user_id=lawyer_user.id,
            amount=500.0,
            period="2024-01",
            description="一月结算"
        )
        
        assert_not_none(settlement)
        assert_equals(settlement.user_id, lawyer_user.id)
        assert_equals(settlement.amount, 500.0)
        assert_equals(settlement.period, "2024-01")
        assert_equals(settlement.status, "pending")
    
    async def test_get_settlement_detail(self, settlement_service, db: AsyncSession, lawyer_user: User):
        """测试获取结算详情"""
        # 创建用户和结算记录
        settlement = await settlement_service.create_settlement(
            db,
            user_id=lawyer_user.id,
            amount=300.0,
            period="2024-02"
        )
        
        # 获取详情
        detail = await settlement_service.get_settlement_detail(db, settlement_id=settlement.id)
        
        assert_not_none(detail)
        assert_equals(detail.id, settlement.id)
        assert_equals(detail.amount, 300.0)
    
    async def test_update_settlement_status(self, settlement_service, db: AsyncSession, lawyer_user: User):
        """测试更新结算状态"""
        # 创建结算记录
        settlement = await settlement_service.create_settlement(
            db,
            user_id=lawyer_user.id,
            amount=200.0,
            period="2024-03"
        )
        
        # 更新状态
        updated = await settlement_service.update_status(
            db,
            settlement_id=settlement.id,
            new_status="completed"
        )
        
        assert_equals(updated.status, "completed")
    
    async def test_get_settlement_list_pagination(self, settlement_service, db: AsyncSession, lawyer_user: User):
        """测试获取结算列表（分页）"""
        # 创建多个结算记录
        for i in range(25):
            await settlement_service.create_settlement(
                db,
                user_id=lawyer_user.id,
                amount=100.0 * (i + 1),
                period=f"2024-{i+1:02d}"
            )
        
        # 获取第一页
        page1 = await settlement_service.get_settlement_list(
            db,
            user_id=lawyer_user.id,
            page=1,
            page_size=10
        )
        
        assert_equals(len(page1.items), 10)
        assert_equals(page1.total, 25)
        assert_equals(page1.page, 1)
        assert_equals(page1.page_size, 10)
        
        # 获取第二页
        page2 = await settlement_service.get_settlement_list(
            db,
            user_id=lawyer_user.id,
            page=2,
            page_size=10
        )
        
        assert_equals(len(page2.items), 10)
    
    @pytest.mark.asyncio
    async def test_calculate_amount(self, settlement_service, db: AsyncSession, lawyer: Lawyer):
        """测试计算结算金额"""
        # 创建收入记录
        for i in range(5):
            income = LawyerIncomeRecord(
                lawyer_id=lawyer.id,
                lawyer_income=100.0 * (i + 1),
                platform_fee=15.0 * (i + 1),
                user_paid_amount=115.0 * (i + 1),
                status="settled"
            )
            db.add(income)
        await db.commit()
        
        # 计算金额
        calculated = await settlement_service.calculate_amount(
            db,
            lawyer_id=lawyer.id,
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        
        # 总收入应该是 100 + 200 + 300 + 400 + 500 = 1500
        assert_equals(calculated, 1500.0)


# ==================== 第五组：金额计算与报告 (4个测试) ====================

class TestAmountCalculationAndReport:
    """测试金额计算和报告生成"""
    
    def test_calculate_platform_fee(self, settlement_service):
        """测试计算平台费"""
        amount = 1000.0
        expected_fee = amount * float(SETTLEMENT_PLATFORM_FEE_RATE)
        
        actual_fee = settlement_service.calculate_platform_fee(amount)
        
        assert_equals(actual_fee, expected_fee)
    
    def test_calculate_tax_deduction(self, settlement_service):
        """测试计算税费扣减（固定3%）"""
        amount = 1000.0
        expected_tax = amount * 0.03  # 固定3%
        
        actual_tax = settlement_service.calculate_tax_deduction(amount)
        
        assert_equals(actual_tax, expected_tax)
    
    def test_calculate_net_amount(self, settlement_service):
        """测试计算净到账金额"""
        amount = 1000.0
        platform_fee = settlement_service.calculate_platform_fee(amount)
        tax = settlement_service.calculate_tax_deduction(amount)
        expected_net = amount - platform_fee - tax
        
        net = settlement_service.calculate_net_amount(amount)
        
        assert_equals(net, expected_net)
        assert_greater_than(net, 0)
    
    def test_calculate_net_amount_edge_case(self, settlement_service):
        """测试计算净金额边界情况（不会为负）"""
        # 使用一个小金额，确保扣除后不会为负
        amount = 10.0
        
        net = settlement_service.calculate_net_amount(amount)
        
        # 即使费用很高，净金额也不应该为负
        assert_in_range(net, 0.0, amount)


# ==================== 工具函数测试 ====================

class TestUtilityFunctions:
    """测试工具函数"""
    
    def test_mask_account_no(self):
        """测试账号脱敏"""
        # 长账号
        account = "1234567890123456"
        masked = _mask_account_no(account)
        assert_equals(masked, "****3456")
        
        # 短账号
        short = "1234"
        masked_short = _mask_account_no(short)
        assert_equals(masked_short, "****")
        
        # None或空
        assert_equals(_mask_account_no(None), "****")
        assert_equals(_mask_account_no(""), "****")
    
    def test_quantize_amount(self):
        """测试金额量化（保留两位小数）"""
        amount = _quantize_amount(100.12345)
        assert_equals(float(amount), 100.12)
        
        amount2 = _quantize_amount(100.125)  # 四舍五入
        assert_equals(float(amount2), 100.13)
    
    def test_decimal_to_cents(self):
        """测试金额转分"""
        amount = Decimal("100.50")
        cents = _decimal_to_cents(amount)
        assert_equals(cents, 10050)
        
        amount2 = Decimal("99.99")
        cents2 = _decimal_to_cents(amount2)
        assert_equals(cents2, 9999)
    
    def test_now_function(self):
        """测试当前时间函数"""
        now = _now()
        assert isinstance(now, datetime)
        assert now.tzinfo is not None  # 确保是UTC时间
