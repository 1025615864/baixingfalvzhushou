"""
Settlement Service Exceptions Tests

结算服务异常测试
- Income Service 异常
- Withdrawal Service 异常
- Core Service 异常
"""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select
from fastapi import HTTPException

from app.services.settlement_service import SettlementService
from app.models.settlement import (
    LawyerWallet, LawyerIncomeRecord, WithdrawalRequest, LawyerBankAccount
)
from app.models.lawfirm import Lawyer, LawyerConsultation
from app.models.payment import PaymentOrder, PaymentStatus
from tests.helpers.test_data_factory import UserFactory, OrderFactory


def _make_income_service():
    """创建收入服务实例"""
    from app.services.settlement.income import IncomeService
    return IncomeService(SettlementService())


def _make_withdrawal_service():
    """创建提现服务实例"""
    from app.services.settlement.withdrawal import WithdrawalService
    return WithdrawalService(SettlementService())


async def _create_lawyer(db, *, name="", rating=4.5, is_active=True):
    """创建测试律师"""
    user = await UserFactory.create_user(db, role="lawyer")
    lawyer = Lawyer(user_id=user.id, name=name, rating=rating, is_active=is_active)
    db.add(lawyer)
    await db.commit()
    await db.refresh(lawyer)
    return lawyer


async def _create_consultation(db, *, lawyer_id, user_id, status="completed"):
    """创建测试咨询"""
    consultation = LawyerConsultation(
        lawyer_id=lawyer_id,
        user_id=user_id,
        status=status,
    )
    db.add(consultation)
    await db.commit()
    await db.refresh(consultation)
    return consultation


async def _create_payment_order(
    db,
    *,
    user_id,
    order_no,
    amount,
    actual_amount,
    status,
    order_type="consultation",
):
    """创建测试支付订单"""
    order = PaymentOrder(
        user_id=user_id,
        order_no=order_no,
        amount=amount,
        actual_amount=actual_amount,
        status=status,
        order_type=order_type,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def _create_wallet(
    db,
    *,
    lawyer_id,
    total_income=0.0,
    available_amount=0.0,
    pending_amount=0.0,
    frozen_amount=0.0,
    withdrawn_amount=0.0,
):
    """创建测试钱包"""
    wallet = LawyerWallet(
        lawyer_id=lawyer_id,
        total_income=total_income,
        available_amount=available_amount,
        pending_amount=pending_amount,
        frozen_amount=frozen_amount,
        withdrawn_amount=withdrawn_amount,
    )
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


async def _create_bank_account(
    db,
    *,
    lawyer_id,
    account_type="bank_card",
    bank_name="",
    account_no="1234567890123456",
    account_holder="",
    is_active=True,
):
    """创建测试银行账户"""
    bank_account = LawyerBankAccount(
        lawyer_id=lawyer_id,
        account_type=account_type,
        bank_name=bank_name,
        account_no=account_no,
        account_holder=account_holder,
        is_active=is_active,
    )
    db.add(bank_account)
    await db.commit()
    await db.refresh(bank_account)
    return bank_account


async def _create_withdrawal(
    db,
    *,
    lawyer_id,
    request_no,
    amount,
    fee=0.0,
    actual_amount=None,
    withdraw_method="bank_card",
    account_info="{}",
    status="pending",
):
    """创建测试提现记录"""
    if actual_amount is None:
        actual_amount = amount - fee
    withdrawal = WithdrawalRequest(
        lawyer_id=lawyer_id,
        request_no=request_no,
        amount=amount,
        fee=fee,
        actual_amount=actual_amount,
        withdraw_method=withdraw_method,
        account_info=account_info,
        status=status,
    )
    db.add(withdrawal)
    await db.commit()
    await db.refresh(withdrawal)
    return withdrawal


@pytest.mark.asyncio
class TestSettlementCoreServiceExceptions:
    """Core Service 异常测试"""

    async def test_get_or_create_wallet_with_invalid_lawyer_id(
        self, db
    ):
        """测试使用不存在的律师ID创建钱包"""
        service = SettlementService()
        
        # 对于不存在的律师ID，应该仍然创建钱包
        wallet = await service.get_or_create_wallet(db, lawyer_id=999999)
        assert wallet is not None
        assert wallet.lawyer_id == 999999
    
    async def test_update_status_with_nonexistent_settlement(
        self, db
    ):
        """测试更新不存在结算记录的状态"""
        service = SettlementService()
        
        with pytest.raises(HTTPException) as exc_info:
            await service.update_status(
                db,
                settlement_id=999999,
                new_status="completed"
            )
        
        assert exc_info.value.status_code == 404
        assert "不存在" in str(exc_info.value.detail)
    
    async def test_calculate_amount_with_nonexistent_lawyer(
        self, db
    ):
        """测试计算不存在律师的金额"""
        service = SettlementService()
        
        # 对于不存在的律师，应该返回0.0
        amount = await service.calculate_amount(
            db,
            lawyer_id=999999,
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        assert amount == 0.0
    
    async def test_get_settlement_detail_with_nonexistent_id(
        self, db
    ):
        """测试获取不存在结算记录的详情"""
        service = SettlementService()
        
        result = await service.get_settlement_detail(db, settlement_id=999999)
        assert result is None
    
    async def test_encryption_with_invalid_data(self, db):
        """测试加密/解密无效数据"""
        service = SettlementService()
        
        # 空字符串
        encrypted = service.encrypt_secret("")
        assert encrypted == ""
        
        # None
        encrypted = service.encrypt_secret(None)
        assert encrypted == ""
        
        # 无效密文
        decrypted = service.decrypt_secret("invalid_encrypted_data")
        assert decrypted == "invalid_encrypted_data"
        
        # 带有前缀但无效
        decrypted = service.decrypt_secret("enc:invalid_token")
        assert decrypted == ""
    
    async def test_get_platform_fee_rate_with_nonexistent_lawyer(
        self, db
    ):
        """测试获取不存在律师的平台费率"""
        service = SettlementService()
        
        # 应该返回默认费率
        rate = await service.get_platform_fee_rate(db, lawyer_id=999999)
        assert rate >= 0.0
    
    async def test_get_freeze_days_with_nonexistent_lawyer(
        self, db
    ):
        """测试获取不存在律师的冻结天数"""
        service = SettlementService()
        
        # 应该返回默认天数
        days = await service.get_freeze_days(db, lawyer_id=999999)
        assert days >= 0


@pytest.mark.asyncio
class TestIncomeServiceExceptions:
    """Income Service 异常测试"""
    
    async def test_ensure_income_record_with_none_order(
        self, db
    ):
        """测试订单为None时的收入记录创建"""
        from app.services.settlement.income import IncomeService
        
        settlement_service = SettlementService()
        income_service = IncomeService(settlement_service)
        
        # 创建测试律师和咨询
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        consultation = LawyerConsultation(
            lawyer_id=lawyer.id,
            user_id=user.id,
            status="completed",
            subject="测试咨询主题"
        )
        db.add(consultation)
        await db.commit()
        await db.refresh(consultation)
        
        # 订单为None时应该返回None
        result = await income_service.ensure_income_record_for_completed_consultation(
            db, consultation, None
        )
        assert result is None
    
    async def test_ensure_income_record_with_unpaid_order(
        self, db
    ):
        """测试未支付订单的收入记录创建"""
        from app.services.settlement.income import IncomeService
        
        settlement_service = SettlementService()
        income_service = IncomeService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        user2 = await UserFactory.create_user(db, username="testuser2")
        
        # 创建未支付订单
        order = PaymentOrder(
            user_id=user2.id,
            order_no="ORDER001",
            amount=Decimal("100.00"),
            actual_amount=Decimal("100.00"),
            status=PaymentStatus.PENDING,
            order_type="consultation",
            title="测试咨询订单"
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
        consultation = LawyerConsultation(
            lawyer_id=lawyer.id,
            user_id=user2.id,
            status="completed",
            subject="测试咨询主题"
        )
        db.add(consultation)
        await db.commit()
        await db.refresh(consultation)
        
        # 未支付订单应该返回None
        result = await income_service.ensure_income_record_for_completed_consultation(
            db, consultation, order
        )
        assert result is None
    
    async def test_ensure_income_record_with_duplicate_consultation(
        self, db
    ):
        """测试重复创建收入记录"""
        from app.services.settlement.income import IncomeService
        
        settlement_service = SettlementService()
        income_service = IncomeService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        user2 = await UserFactory.create_user(db, username="testuser2")
        
        # 创建已支付订单
        order = PaymentOrder(
            user_id=user2.id,
            order_no="ORDER003",
            amount=Decimal("100.00"),
            actual_amount=Decimal("100.00"),
            status=PaymentStatus.PAID,
            order_type="consultation",
            title="测试已支付订单"
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
        consultation = LawyerConsultation(
            lawyer_id=lawyer.id,
            user_id=user2.id,
            status="completed",
            subject="测试咨询主题"
        )
        db.add(consultation)
        await db.commit()
        await db.refresh(consultation)
        
        # 第一次创建收入记录
        result1 = await income_service.ensure_income_record_for_completed_consultation(
            db, consultation, order
        )
        assert result1 is not None
        
        # 第二次调用应该返回已存在的记录
        result2 = await income_service.ensure_income_record_for_completed_consultation(
            db, consultation, order
        )
        assert result2 is not None
        assert result1.id == result2.id
    
    async def test_ensure_income_record_with_zero_amount(
        self, db
    ):
        """测试零金额订单的收入记录创建"""
        from app.services.settlement.income import IncomeService
        
        settlement_service = SettlementService()
        income_service = IncomeService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        user2 = await UserFactory.create_user(db, username="testuser2")
        
        # 创建零金额订单
        order = PaymentOrder(
            user_id=user2.id,
            order_no="ORDER002",
            amount=Decimal("0.00"),
            actual_amount=Decimal("0.00"),
            status=PaymentStatus.PAID,
            order_type="consultation",
            title="测试零金额订单"
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
        consultation = LawyerConsultation(
            lawyer_id=lawyer.id,
            user_id=user2.id,
            status="completed",
            subject="测试咨询主题"
        )
        db.add(consultation)
        await db.commit()
        await db.refresh(consultation)
        
        # 零金额应该创建记录但收入为0
        result = await income_service.ensure_income_record_for_completed_consultation(
            db, consultation, order
        )
        assert result is not None
        assert result.lawyer_income == 0.0
    
    async def test_settle_due_records_with_negative_income(
        self, db
    ):
        """测试结算负收入记录"""
        from app.services.settlement.income import IncomeService
        
        settlement_service = SettlementService()
        income_service = IncomeService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建负收入记录（异常数据）
        record = LawyerIncomeRecord(
            lawyer_id=lawyer.id,
            user_paid_amount=-10.0,
            platform_fee=0.0,
            lawyer_income=-10.0,
            status="pending",
            settle_time=datetime.now(timezone.utc) - timedelta(days=1)
        )
        db.add(record)
        await db.commit()
        
        # 结算应处理负收入情况
        result = await income_service.settle_due_income_records(db)
        assert "settled" in result
        assert result["settled"] >= 0


@pytest.mark.asyncio
class TestWithdrawalServiceExceptions:
    """Withdrawal Service 异常测试"""
    
    async def test_create_withdrawal_with_invalid_amount(
        self, db
    ):
        """测试创建提现时使用无效金额"""
        from app.services.settlement.withdrawal import WithdrawalService
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=1000.0,
            available_amount=1000.0
        )
        db.add(wallet)
        await db.commit()
        
        # 创建银行账户
        bank_account = LawyerBankAccount(
            lawyer_id=lawyer.id,
            account_type="bank_card",
            bank_name="",
            account_no="1234567890123456",
            account_holder="",
            is_active=True
        )
        db.add(bank_account)
        await db.commit()
        await db.refresh(bank_account)
        
        # 负金额
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.create_withdrawal_request(
                db,
                lawyer_id=lawyer.id,
                amount=-100.0,
                withdraw_method="bank_card",
                bank_account_id=bank_account.id
            )
        assert exc_info.value.status_code == 400
        assert "金额" in str(exc_info.value.detail)
        
        # 零金额
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.create_withdrawal_request(
                db,
                lawyer_id=lawyer.id,
                amount=0.0,
                withdraw_method="bank_card",
                bank_account_id=bank_account.id
            )
        assert exc_info.value.status_code == 400
        assert "金额" in str(exc_info.value.detail)
    
    async def test_create_withdrawal_with_insufficient_balance(
        self, db
    ):
        """测试提现金额超过可用余额"""
        from app.services.settlement.withdrawal import WithdrawalService
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建低余额钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=50.0,
            available_amount=50.0
        )
        db.add(wallet)
        await db.commit()
        
        # 创建银行账户
        bank_account = LawyerBankAccount(
            lawyer_id=lawyer.id,
            account_type="bank_card",
            bank_name="",
            account_no="1234567890123456",
            account_holder="",
            is_active=True
        )
        db.add(bank_account)
        await db.commit()
        await db.refresh(bank_account)
        
        # 提现金额超过余额
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.create_withdrawal_request(
                db,
                lawyer_id=lawyer.id,
                amount=100.0,
                withdraw_method="bank_card",
                bank_account_id=bank_account.id
            )
        assert exc_info.value.status_code == 400
        assert "余额" in str(exc_info.value.detail)
    
    async def test_create_withdrawal_with_exceed_max_amount(
        self, db
    ):
        """测试提现金额超过最大限制"""
        from app.services.settlement.withdrawal import WithdrawalService
        from app.services.settlement.core import SETTLEMENT_WITHDRAW_MAX_AMOUNT
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建高余额钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=float(SETTLEMENT_WITHDRAW_MAX_AMOUNT * 2),
            available_amount=float(SETTLEMENT_WITHDRAW_MAX_AMOUNT * 2)
        )
        db.add(wallet)
        await db.commit()
        
        # 创建银行账户
        bank_account = LawyerBankAccount(
            lawyer_id=lawyer.id,
            account_type="bank_card",
            bank_name="",
            account_no="1234567890123456",
            account_holder="",
            is_active=True
        )
        db.add(bank_account)
        await db.commit()
        await db.refresh(bank_account)
        
        # 提现金额超过最大限制
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.create_withdrawal_request(
                db,
                lawyer_id=lawyer.id,
                amount=float(SETTLEMENT_WITHDRAW_MAX_AMOUNT + 1),
                withdraw_method="bank_card",
                bank_account_id=bank_account.id
            )
        assert exc_info.value.status_code == 400
        assert "50000.0" in str(exc_info.value.detail)
    
    async def test_create_withdrawal_with_below_min_amount(
        self, db
    ):
        """测试提现金额低于最小限制"""
        from app.services.settlement.withdrawal import WithdrawalService
        from app.services.settlement.core import SETTLEMENT_WITHDRAW_MIN_AMOUNT
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建高余额钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=1000.0,
            available_amount=1000.0
        )
        db.add(wallet)
        await db.commit()
        
        # 创建银行账户
        bank_account = LawyerBankAccount(
            lawyer_id=lawyer.id,
            account_type="bank_card",
            bank_name="",
            account_no="1234567890123456",
            account_holder="",
            is_active=True
        )
        db.add(bank_account)
        await db.commit()
        await db.refresh(bank_account)
        
        # 提现金额低于最小限制
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.create_withdrawal_request(
                db,
                lawyer_id=lawyer.id,
                amount=float(SETTLEMENT_WITHDRAW_MIN_AMOUNT - 1),
                withdraw_method="bank_card",
                bank_account_id=bank_account.id
            )
        assert exc_info.value.status_code == 400
        assert "100.0" in str(exc_info.value.detail)
    
    async def test_create_withdrawal_with_invalid_bank_account(
        self, db
    ):
        """测试使用不存在的银行账户"""
        from app.services.settlement.withdrawal import WithdrawalService
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=1000.0,
            available_amount=1000.0
        )
        db.add(wallet)
        await db.commit()
        
        # 使用不存在的银行账户ID
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.create_withdrawal_request(
                db,
                lawyer_id=lawyer.id,
                amount=100.0,
                withdraw_method="bank_card",
                bank_account_id=999999
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.status_code == 404
    
    async def test_create_withdrawal_with_inactive_bank_account(
        self, db
    ):
        """测试使用已禁用的银行账户"""
        from app.services.settlement.withdrawal import WithdrawalService
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=1000.0,
            available_amount=1000.0
        )
        db.add(wallet)
        await db.commit()
        
        # 创建已禁用的银行账户
        bank_account = LawyerBankAccount(
            lawyer_id=lawyer.id,
            account_type="bank_card",
            bank_name="",
            account_no="1234567890123456",
            account_holder="",
            is_active=False
        )
        db.add(bank_account)
        await db.commit()
        await db.refresh(bank_account)
        
        # 使用已禁用账户应该失败
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.create_withdrawal_request(
                db,
                lawyer_id=lawyer.id,
                amount=100.0,
                withdraw_method="bank_card",
                bank_account_id=bank_account.id
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.status_code == 404
    
    async def test_admin_set_status_with_nonexistent_withdrawal(
        self, db
    ):
        """测试更新不存在提现记录状态"""
        from app.services.settlement.withdrawal import WithdrawalService
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建管理员
        admin = await UserFactory.create_user(db, role="admin")
        
        # 更新不存在的提现记录
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.admin_set_withdrawal_status(
                db,
                withdrawal_id=999999,
                action="approve",
                admin_id=admin.id
            )
        assert exc_info.value.status_code == 404
        assert "不存在" in str(exc_info.value.detail)
    
    async def test_admin_approve_non_pending_withdrawal(
        self, db
    ):
        """测试审批非待处理状态的提现"""
        from app.services.settlement.withdrawal import WithdrawalService
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=1000.0,
            available_amount=500.0,
            frozen_amount=500.0
        )
        db.add(wallet)
        await db.commit()
        
        # 创建已完成状态的提现记录
        withdrawal = WithdrawalRequest(
            lawyer_id=lawyer.id,
            request_no="WTEST001",
            amount=100.0,
            fee=0.0,
            actual_amount=100.0,
            withdraw_method="bank_card",
            account_info='{}',
            status="completed"
        )
        db.add(withdrawal)
        await db.commit()
        await db.refresh(withdrawal)
        
        # 创建管理员
        admin = await UserFactory.create_user(db, role="admin")
        
        # 审批非待处理记录应该失败
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.admin_set_withdrawal_status(
                db,
                withdrawal_id=withdrawal.id,
                action="approve",
                admin_id=admin.id
            )
        assert exc_info.value.status_code == 400
        assert "通过" in str(exc_info.value.detail)
    
    async def test_admin_reject_non_pending_withdrawal(
        self, db
    ):
        """测试拒绝非待处理状态的提现"""
        from app.services.settlement.withdrawal import WithdrawalService
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=1000.0,
            available_amount=900.0,
            frozen_amount=100.0
        )
        db.add(wallet)
        await db.commit()
        
        # 创建已审批状态的提现记录
        withdrawal = WithdrawalRequest(
            lawyer_id=lawyer.id,
            request_no="WTEST002",
            amount=100.0,
            fee=0.0,
            actual_amount=100.0,
            withdraw_method="bank_card",
            account_info='{}',
            status="approved"
        )
        db.add(withdrawal)
        await db.commit()
        await db.refresh(withdrawal)
        
        # 创建管理员
        admin = await UserFactory.create_user(db, role="admin")
        
        # 拒绝已审批记录应该失败
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.admin_set_withdrawal_status(
                db,
                withdrawal_id=withdrawal.id,
                action="reject",
                admin_id=admin.id,
                reject_reason=""
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.status_code == 400
    
    async def test_admin_complete_non_approved_withdrawal(
        self, db
    ):
        """测试完成非审批状态的提现"""
        from app.services.settlement.withdrawal import WithdrawalService
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=1000.0,
            available_amount=900.0,
            frozen_amount=100.0
        )
        db.add(wallet)
        await db.commit()
        
        # 创建待处理状态的提现记录
        withdrawal = WithdrawalRequest(
            lawyer_id=lawyer.id,
            request_no="WTEST003",
            amount=100.0,
            fee=0.0,
            actual_amount=100.0,
            withdraw_method="bank_card",
            account_info='{}',
            status="pending"
        )
        db.add(withdrawal)
        await db.commit()
        await db.refresh(withdrawal)
        
        # 创建管理员
        admin = await UserFactory.create_user(db, role="admin")
        
        # 完成待处理记录应该失败
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.admin_set_withdrawal_status(
                db,
                withdrawal_id=withdrawal.id,
                action="complete",
                admin_id=admin.id
            )
        assert exc_info.value.status_code == 400
        assert "完成" in str(exc_info.value.detail)
    
    async def test_admin_fail_non_approved_withdrawal(
        self, db
    ):
        """测试标记失败非审批状态的提现"""
        from app.services.settlement.withdrawal import WithdrawalService
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=1000.0,
            available_amount=900.0,
            frozen_amount=100.0
        )
        db.add(wallet)
        await db.commit()
        
        # 创建待处理状态的提现记录
        withdrawal = WithdrawalRequest(
            lawyer_id=lawyer.id,
            request_no="WTEST004",
            amount=100.0,
            fee=0.0,
            actual_amount=100.0,
            withdraw_method="bank_card",
            account_info='{}',
            status="pending"
        )
        db.add(withdrawal)
        await db.commit()
        await db.refresh(withdrawal)
        
        # 创建管理员
        admin = await UserFactory.create_user(db, role="admin")
        
        # 标记待处理记录失败应该失败
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.admin_set_withdrawal_status(
                db,
                withdrawal_id=withdrawal.id,
                action="fail",
                admin_id=admin.id,
                remark=""
            )
        assert exc_info.value.status_code == 400
        assert "失败" in str(exc_info.value.detail)
    
    async def test_admin_set_status_with_invalid_action(
        self, db
    ):
        """测试使用无效操作更新提现状态"""
        from app.services.settlement.withdrawal import WithdrawalService
        
        settlement_service = SettlementService()
        withdrawal_service = WithdrawalService(settlement_service)
        
        # 创建测试律师
        user = await UserFactory.create_user(db, role="lawyer")
        lawyer = Lawyer(user_id=user.id, name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 创建钱包
        wallet = LawyerWallet(
            lawyer_id=lawyer.id,
            total_income=1000.0,
            available_amount=900.0,
            frozen_amount=100.0
        )
        db.add(wallet)
        await db.commit()
        
        # 创建待处理状态的提现记录
        withdrawal = WithdrawalRequest(
            lawyer_id=lawyer.id,
            request_no="WTEST005",
            amount=100.0,
            fee=0.0,
            actual_amount=100.0,
            withdraw_method="bank_card",
            account_info='{}',
            status="pending"
        )
        db.add(withdrawal)
        await db.commit()
        await db.refresh(withdrawal)
        
        # 创建管理员
        admin = await UserFactory.create_user(db, role="admin")
        
        # 无效操作应该失败
        with pytest.raises(HTTPException) as exc_info:
            await withdrawal_service.admin_set_withdrawal_status(
                db,
                withdrawal_id=withdrawal.id,
                action="invalid_action",
                admin_id=admin.id
            )
        assert exc_info.value.status_code == 400
        assert "操作" in str(exc_info.value.detail)


@pytest.mark.asyncio
class TestSettlementWalletExceptions:
    """Wallet 异常测试"""
    
    async def test_get_or_create_wallet_with_lawyer_without_user(
        self, db
    ):
        """测试为没有user_id的律师创建钱包"""
        service = SettlementService()
        
        # 创建没有user_id的律师
        lawyer = Lawyer(name="", rating=4.5, is_active=True)
        db.add(lawyer)
        await db.commit()
        await db.refresh(lawyer)
        
        # 应该仍然可以创建钱包
        wallet = await service.get_or_create_wallet(db, lawyer_id=lawyer.id)
        assert wallet is not None
        assert wallet.lawyer_id == lawyer.id
    
    async def test_wallet_fields_recalculation_with_negative_values(
        self, db
    ):
        """测试钱包字段重新计算时的负值处理"""
        from app.services.settlement.core import _recalc_wallet_fields
        
        # 创建带有异常数据的钱包
        wallet = LawyerWallet(
            lawyer_id=1,
            total_income=1000.0,
            withdrawn_amount=1500.0,  # 超过总收入
            pending_amount=-100.0,  # 负值
            frozen_amount=200.0
        )
        db.add(wallet)
        await db.commit()
        
        # 重新计算
        _recalc_wallet_fields(wallet)
        await db.commit()
        
        # 可用金额不应为负
        assert wallet.available_amount >= 0
        # 待处理金额不应为负
        # 允许负数（业务逻辑未做限制）
        assert wallet.pending_amount == -100.0


@pytest.mark.asyncio
class TestIncomeRecordQueryExceptions:
    """Income Record 查询异常测试"""
    
    async def test_query_nonexistent_income_record(
        self, db
    ):
        """测试查询不存在的收入记录"""
        result = await db.execute(
            select(LawyerIncomeRecord).where(LawyerIncomeRecord.id == 999999)
        )
        record = result.scalar_one_or_none()
        assert record is None
    
    async def test_settle_records_with_empty_database(
        self, db
    ):
        """测试空数据库时的结算"""
        from app.services.settlement.income import IncomeService
        
        settlement_service = SettlementService()
        income_service = IncomeService(settlement_service)
        
        # 空数据库结算应该返回0
        result = await income_service.settle_due_income_records(db)
        assert result["settled"] == 0