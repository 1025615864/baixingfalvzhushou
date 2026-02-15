"""
Settlement路由层API测试
覆盖settlement模块的所有API端点和异常分支
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from unittest import mock
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status


def _make_user(user_id: int = 1) -> MagicMock:
    """创建测试用户"""
    user = MagicMock()
    user.id = user_id
    return user


def _make_lawyer(lawyer_id: int = 1) -> MagicMock:
    """创建测试律师"""
    lawyer = MagicMock()
    lawyer.id = lawyer_id
    return lawyer


@contextmanager
def _patched_settlement_service(
    module_path: str,
    *,
    lawyer: MagicMock | None = None,
    **methods,
):
    """统一替换 settlement_service 并注入方法"""
    with patch(f"{module_path}.settlement_service") as mock_service:
        if "get_current_lawyer" not in methods:
            mock_service.get_current_lawyer = AsyncMock(return_value=lawyer)
        for name, value in methods.items():
            setattr(mock_service, name, value)
        yield mock_service


# ==================== 钱包路由测试 ====================
class TestWalletRouter:
    """钱包路由测试"""

    @pytest.mark.asyncio
    async def test_router_exists(self):
        """测试：钱包路由存在"""
        from app.routers.settlement.wallet import router
        assert router is not None
        assert len(router.routes) > 0

    @pytest.mark.asyncio
    async def test_get_wallet_success(self):
        """测试：成功获取钱包信息"""
        from app.routers.settlement.wallet import lawyer_get_wallet

        # Mock用户和lawyer
        user = _make_user()
        lawyer = _make_lawyer()
        wallet = MagicMock()
        wallet.balance = Decimal("1000.00")

        mock_db = AsyncMock()

        with _patched_settlement_service(
            "app.routers.settlement.wallet",
            lawyer=lawyer,
            get_or_create_wallet=AsyncMock(return_value=wallet),
        ):
            result = await lawyer_get_wallet(user, mock_db)

            assert result is not None

    @pytest.mark.asyncio
    async def test_get_wallet_no_lawyer(self):
        """测试：未绑定律师资料时获取钱包"""
        from app.routers.settlement.wallet import lawyer_get_wallet
        from fastapi import HTTPException

        user = _make_user(999)
        mock_db = AsyncMock()

        with _patched_settlement_service("app.routers.settlement.wallet", lawyer=None):
            with pytest.raises(HTTPException) as exc_info:
                await lawyer_get_wallet(user, mock_db)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ==================== 收入记录路由测试 ====================
class TestIncomeRouter:
    """收入记录路由测试"""

    @pytest.mark.asyncio
    async def test_router_exists(self):
        """测试：收入记录路由存在"""
        from app.routers.settlement.income import router
        assert router is not None
        assert len(router.routes) > 0

    @pytest.mark.asyncio
    async def test_list_income_records_success(self):
        """测试：成功获取收入记录列表"""
        from app.routers.settlement.income import lawyer_list_income_records

        user = _make_user()
        lawyer = _make_lawyer()

        mock_db = AsyncMock()

        # Mock查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        with _patched_settlement_service("app.routers.settlement.income", lawyer=lawyer):
            result = await lawyer_list_income_records(user, mock_db)

            assert result is not None
            assert result.total >= 0

    @pytest.mark.asyncio
    async def test_list_income_records_with_filter(self):
        """测试：带状态过滤器的收入记录列表"""
        from app.routers.settlement.income import lawyer_list_income_records

        user = _make_user()
        lawyer = _make_lawyer()

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        with _patched_settlement_service("app.routers.settlement.income", lawyer=lawyer):
            result = await lawyer_list_income_records(
                user, mock_db, status_filter="settled"
            )

            assert result.total == 0

    @pytest.mark.asyncio
    async def test_list_income_records_no_lawyer(self):
        """测试：未绑定律师资料时获取收入记录"""
        from app.routers.settlement.income import lawyer_list_income_records
        from fastapi import HTTPException

        user = _make_user(999)
        mock_db = AsyncMock()

        with _patched_settlement_service("app.routers.settlement.income", lawyer=None):
            with pytest.raises(HTTPException) as exc_info:
                await lawyer_list_income_records(user, mock_db)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_export_income_records(self):
        """测试：导出收入记录"""
        from app.routers.settlement.income import lawyer_export_income_records
        from fastapi.responses import StreamingResponse

        user = _make_user()
        lawyer = _make_lawyer()

        mock_db = AsyncMock()

        # Mock查询返回空结果
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        with _patched_settlement_service("app.routers.settlement.income", lawyer=lawyer):
            result = await lawyer_export_income_records(user, mock_db)

            assert isinstance(result, StreamingResponse)


# ==================== 提现路由测试 ====================
class TestWithdrawalRouter:
    """提现路由测试"""

    @pytest.mark.asyncio
    async def test_router_exists(self):
        """测试：提现路由存在"""
        from app.routers.settlement.withdrawal import router
        assert router is not None
        assert len(router.routes) > 0

    @pytest.mark.asyncio
    async def test_list_withdrawals_success(self):
        """测试：成功获取提现记录列表"""
        from app.routers.settlement.withdrawal import lawyer_list_withdrawals

        user = _make_user()
        lawyer = _make_lawyer()

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [mock_count_result, mock_result, MagicMock(), MagicMock()]

        with _patched_settlement_service("app.routers.settlement.withdrawal", lawyer=lawyer):
            result = await lawyer_list_withdrawals(user, mock_db)

            assert result is not None
            assert result.total >= 0

    @pytest.mark.asyncio
    async def test_list_withdrawals_no_lawyer(self):
        """测试：未绑定律师资料时获取提现记录"""
        from app.routers.settlement.withdrawal import lawyer_list_withdrawals
        from fastapi import HTTPException

        user = _make_user(999)
        mock_db = AsyncMock()

        with _patched_settlement_service("app.routers.settlement.withdrawal", lawyer=None):
            with pytest.raises(HTTPException) as exc_info:
                await lawyer_list_withdrawals(user, mock_db)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_withdrawal_detail_success(self):
        """测试：成功获取提现详情"""
        from app.routers.settlement.withdrawal import lawyer_get_withdrawal

        user = _make_user()
        lawyer = _make_lawyer()

        withdrawal_request = MagicMock()
        withdrawal_request.id = 1
        withdrawal_request.lawyer_id = 1

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = withdrawal_request

        mock_db.execute = AsyncMock(return_value=mock_result)

        with _patched_settlement_service("app.routers.settlement.withdrawal", lawyer=lawyer):
            result = await lawyer_get_withdrawal(1, user, mock_db)

            assert result is not None

    @pytest.mark.asyncio
    async def test_get_withdrawal_detail_not_found(self):
        """测试：获取不存在的提现详情"""
        from app.routers.settlement.withdrawal import lawyer_get_withdrawal
        from fastapi import HTTPException

        user = _make_user()
        lawyer = _make_lawyer()

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=mock_result)

        with _patched_settlement_service("app.routers.settlement.withdrawal", lawyer=lawyer):
            with pytest.raises(HTTPException) as exc_info:
                await lawyer_get_withdrawal(999999, user, mock_db)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_mask_account_no(self):
        """测试：账号号掩码功能"""
        from app.routers.settlement.withdrawal import _mask_account_no

        # 短账号
        result = _mask_account_no("123")
        assert result == "****"

        # 正常账号
        result = _mask_account_no("1234567890123456")
        assert result == "****3456"

        # 空账号
        result = _mask_account_no("")
        assert result == "****"

    @pytest.mark.asyncio
    async def test_mask_account_info_invalid_json(self):
        """测试：无效JSON的账户信息掩码"""
        from app.routers.settlement.withdrawal import _mask_account_info

        result = _mask_account_info("invalid json")
        assert result == "***"

    @pytest.mark.asyncio
    async def test_mask_account_info_valid_json(self):
        """测试：有效JSON的账户信息掩码"""
        from app.routers.settlement.withdrawal import _mask_account_info

        # Mock解密
        with _patched_settlement_service(
            "app.routers.settlement.withdrawal",
            decrypt_secret=MagicMock(return_value="1234567890123456"),
        ):
            result = _mask_account_info('{"account_no": "encrypted_text", "bank_name": "中国银行"}')

            # 应该包含掩码后的账号
            assert result is not None


# ==================== 银行账户路由测试 ====================
class TestBankAccountRouter:
    """银行账户路由测试"""

    @pytest.mark.asyncio
    async def test_router_exists(self):
        """测试：银行账户路由存在"""
        from app.routers.settlement.bank_account import router
        assert router is not None
        assert len(router.routes) > 0

    @pytest.mark.asyncio
    async def test_list_bank_accounts_success(self):
        """测试：成功获取银行账户列表"""
        from app.routers.settlement.bank_account import lawyer_list_bank_accounts

        user = _make_user()
        lawyer = _make_lawyer()

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(return_value=mock_result)

        with _patched_settlement_service("app.routers.settlement.bank_account", lawyer=lawyer):
            result = await lawyer_list_bank_accounts(user, mock_db)

            assert result is not None
            assert result.total >= 0

    @pytest.mark.asyncio
    async def test_list_bank_accounts_no_lawyer(self):
        """测试：未绑定律师资料时获取银行账户"""
        from app.routers.settlement.bank_account import lawyer_list_bank_accounts
        from fastapi import HTTPException

        user = _make_user(999)
        mock_db = AsyncMock()

        with _patched_settlement_service("app.routers.settlement.bank_account", lawyer=None):
            with pytest.raises(HTTPException) as exc_info:
                await lawyer_list_bank_accounts(user, mock_db)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_mask_account_no_short(self):
        """测试：短账号号掩码"""
        from app.routers.settlement.bank_account import _mask_account_no

        result = _mask_account_no("123")
        assert result == "****"

    @pytest.mark.asyncio
    async def test_mask_account_no_normal(self):
        """测试：正常账号号掩码"""
        from app.routers.settlement.bank_account import _mask_account_no

        result = _mask_account_no("1234567890123456")
        assert result == "****3456"

    @pytest.mark.asyncio
    async def test_create_bank_account(self):
        """测试：创建银行账户"""
        from app.routers.settlement.bank_account import lawyer_create_bank_account

        user = _make_user()
        lawyer = _make_lawyer()

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        async def _refresh(obj):
            now = datetime.now(timezone.utc)
            obj.id = 1
            obj.lawyer_id = lawyer.id
            obj.created_at = now
            obj.updated_at = now

        mock_db.refresh = AsyncMock(side_effect=_refresh)

        data = MagicMock()
        data.account_type = "bank_card"
        data.bank_name = "工商银行"
        data.account_no = "6222021234567890"
        data.account_holder = "测试律师"
        data.is_default = False

        with _patched_settlement_service(
            "app.routers.settlement.bank_account",
            lawyer=lawyer,
            encrypt_secret=MagicMock(return_value="encrypted"),
        ):
            result = await lawyer_create_bank_account(data, user, mock_db)

            assert result is not None


# ==================== 管理员路由测试 ====================
class TestAdminRouter:
    """管理员路由测试"""

    @pytest.mark.asyncio
    async def test_router_exists(self):
        """测试：管理员路由存在"""
        from app.routers.settlement.admin import router
        assert router is not None
        assert len(router.routes) > 0

    @pytest.mark.asyncio
    async def test_admin_list_withdrawals_success(self):
        """测试：管理员成功获取提现申请列表"""
        from app.routers.settlement.admin import admin_list_withdrawals

        admin_user = MagicMock()
        admin_user.id = 1

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [mock_count_result, mock_result, MagicMock(), MagicMock()]

        result = await admin_list_withdrawals(admin_user, mock_db)

        assert result is not None
        assert result.total >= 0

    @pytest.mark.asyncio
    async def test_admin_get_withdrawal_detail_success(self):
        """测试：管理员成功获取提现详情"""
        from app.routers.settlement.admin import admin_get_withdrawal_detail

        admin_user = MagicMock()
        admin_user.id = 1

        withdrawal_request = MagicMock()
        withdrawal_request.id = 1
        withdrawal_request.lawyer_id = 1

        lawyer = MagicMock()
        lawyer.id = 1
        lawyer.name = "测试律师"
        lawyer.rating = 4.5

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = withdrawal_request

        mock_lawyer_result = MagicMock()
        mock_lawyer_result.scalar_one_or_none.return_value = lawyer

        mock_consultation_result = MagicMock()
        mock_consultation_result.scalar.return_value = 0

        mock_db.execute.side_effect = [
            mock_result,
            mock_lawyer_result,
            mock_consultation_result
        ]

        result = await admin_get_withdrawal_detail(1, admin_user, mock_db)

        assert result is not None
        assert result.id == withdrawal_request.id

    @pytest.mark.asyncio
    async def test_admin_get_withdrawal_detail_not_found(self):
        """测试：管理员获取不存在的提现详情"""
        from app.routers.settlement.admin import admin_get_withdrawal_detail
        from fastapi import HTTPException

        admin_user = MagicMock()
        admin_user.id = 1

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await admin_get_withdrawal_detail(999999, admin_user, mock_db)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_admin_approve_withdrawal_success(self):
        """测试：管理员成功批准提现申请"""
        from app.routers.settlement.admin import admin_approve_withdrawal

        admin_user = MagicMock()
        admin_user.id = 1

        withdrawal_request = MagicMock()
        withdrawal_request.id = 1
        withdrawal_request.status = "pending"

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = withdrawal_request

        mock_db.execute = AsyncMock(return_value=mock_result)

        with _patched_settlement_service(
            "app.routers.settlement.admin",
            _build_withdrawal_item=AsyncMock(return_value=MagicMock()),
        ):
            data = MagicMock()
            data.remark = "审核通过"
            await admin_approve_withdrawal(1, data, admin_user, mock_db)

            assert withdrawal_request.status == "approved"

    @pytest.mark.asyncio
    async def test_admin_approve_withdrawal_invalid_status(self):
        """测试：管理员批准非pending状态的提现申请"""
        from app.routers.settlement.admin import admin_approve_withdrawal
        from fastapi import HTTPException

        admin_user = MagicMock()
        admin_user.id = 1

        withdrawal_request = MagicMock()
        withdrawal_request.id = 1
        withdrawal_request.status = "approved"

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = withdrawal_request

        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await admin_approve_withdrawal(1, {"remark": "test"}, admin_user, mock_db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_admin_reject_withdrawal_success(self):
        """测试：管理员成功拒绝提现申请"""
        from app.routers.settlement.admin import admin_reject_withdrawal

        admin_user = MagicMock()
        admin_user.id = 1

        withdrawal_request = MagicMock()
        withdrawal_request.id = 1
        withdrawal_request.status = "pending"

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = withdrawal_request
        mock_result.scalar.return_value = MagicMock()

        mock_db.execute.side_effect = [mock_result, mock_result]

        data = MagicMock()
        data.reject_reason = "账户信息有误"
        data.remark = "已联系律师核实"
        with patch(
            "app.routers.settlement.admin._build_withdrawal_item",
            new=AsyncMock(return_value=MagicMock()),
        ):
            result = await admin_reject_withdrawal(1, data, admin_user, mock_db)

        assert withdrawal_request.status == "rejected"

    @pytest.mark.asyncio
    async def test_admin_export_withdrawals(self):
        """测试：管理员导出提现记录"""
        from app.routers.settlement.admin import admin_export_withdrawals
        from fastapi.responses import StreamingResponse

        admin_user = MagicMock()
        admin_user.id = 1

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await admin_export_withdrawals(admin_user, mock_db)

        assert isinstance(result, StreamingResponse)

    @pytest.mark.asyncio
    async def test_admin_run_settlement_success(self):
        """测试：管理员成功执行结算"""
        from app.routers.settlement.admin import admin_run_settlement

        admin_user = MagicMock()
        admin_user.id = 1

        mock_db = AsyncMock()

        with _patched_settlement_service(
            "app.routers.settlement.admin",
            settle_due_income_records=AsyncMock(return_value={"processed": 0}),
        ):
            result = await admin_run_settlement(admin_user, mock_db)

            assert result is not None

    @pytest.mark.asyncio
    async def test_admin_export_income_records(self):
        """测试：管理员导出收入记录"""
        from app.routers.settlement.admin import admin_export_income_records
        from fastapi.responses import StreamingResponse

        admin_user = MagicMock()
        admin_user.id = 1

        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await admin_export_income_records(admin_user, mock_db)

        assert isinstance(result, StreamingResponse)


# ==================== 主路由测试 ====================
class TestMainSettlementRouter:
    """主settlement路由测试"""

    @pytest.mark.asyncio
    async def test_router_exists(self):
        """测试：主settlement路由存在"""
        from app.routers.settlement import router
        assert router is not None
        assert len(router.routes) > 0

    @pytest.mark.asyncio
    async def test_get_balance_compat(self):
        """测试：兼容路由 - 获取余额"""
        from app.routers.settlement import get_balance_compat

        user = _make_user()

        wallet = MagicMock()
        wallet.balance = Decimal("1000.00")
        wallet.frozen_balance = Decimal("100.00")
        wallet.total_withdrawn = Decimal("500.00")
        wallet.total_recharged = Decimal("1500.00")

        mock_db = AsyncMock()

        with _patched_settlement_service(
            "app.routers.settlement",
            get_or_create_wallet=AsyncMock(return_value=wallet),
        ):
            result = await get_balance_compat(user, mock_db)

            assert result is not None
            assert "balance" in result
            assert "frozen_balance" in result

    @pytest.mark.asyncio
    async def test_get_records_compat(self):
        """测试：兼容路由 - 获取交易记录"""
        from app.routers.settlement import get_records_compat

        user = _make_user()

        wallet = MagicMock()
        wallet.id = 1

        mock_db = AsyncMock()

        with _patched_settlement_service(
            "app.routers.settlement",
            get_or_create_wallet=AsyncMock(return_value=wallet),
            get_transactions=AsyncMock(return_value=[]),
        ):
            result = await get_records_compat(user, mock_db)

            assert result is not None
            assert "items" in result

    @pytest.mark.asyncio
    async def test_get_withdrawals_compat(self):
        """测试：兼容路由 - 获取提现记录"""
        from app.routers.settlement import get_withdrawals_compat

        user = _make_user()

        from sqlalchemy import select
        mock_db = AsyncMock()

        # 模拟没有lawyer的情况
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await get_withdrawals_compat(user, mock_db)
        
        assert result is not None
        assert result["items"] == []
        assert result["total"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])