"""Tests for Withdrawal Service"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.settlement.withdrawal import WithdrawalService
from app.models.settlement import WithdrawalRequest, LawyerBankAccount, LawyerWallet
from app.models.lawfirm import Lawyer
from app.models.notification import Notification, NotificationType


class TestWithdrawalServiceCreateRequest:
    """Tests for create_withdrawal_request method."""

    @pytest.mark.asyncio
    async def test_create_withdrawal_request_invalid_amount_zero(self) -> None:
        """Test create_withdrawal_request with zero amount."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wallet = MagicMock()
        mock_wallet.available_amount = 100.0
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        service = WithdrawalService(mock_settlement)

        with pytest.raises(Exception) as exc_info:
            await service.create_withdrawal_request(
                mock_db,
                lawyer_id=1,
                amount=0,
                withdraw_method="bank_card",
                bank_account_id=1,
            )

        assert "金额不合法" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_withdrawal_request_exceeds_max(self) -> None:
        """Test create_withdrawal_request with amount exceeding max."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wallet = MagicMock()
        mock_wallet.available_amount = 100000.0
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        service = WithdrawalService(mock_settlement)

        with pytest.raises(Exception) as exc_info:
            await service.create_withdrawal_request(
                mock_db,
                lawyer_id=1,
                amount=1000000,
                withdraw_method="bank_card",
                bank_account_id=1,
            )

        assert "单次最高提现金额" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_withdrawal_request_below_min(self) -> None:
        """Test create_withdrawal_request with amount below minimum."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wallet = MagicMock()
        mock_wallet.available_amount = 100.0
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        service = WithdrawalService(mock_settlement)

        with pytest.raises(Exception) as exc_info:
            await service.create_withdrawal_request(
                mock_db,
                lawyer_id=1,
                amount=0.1,
                withdraw_method="bank_card",
                bank_account_id=1,
            )

        assert "最低提现金额" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_withdrawal_request_insufficient_balance(self) -> None:
        """Test create_withdrawal_request with insufficient balance."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wallet = MagicMock()
        mock_wallet.available_amount = 10.0
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        service = WithdrawalService(mock_settlement)

        with pytest.raises(Exception) as exc_info:
            await service.create_withdrawal_request(
                mock_db,
                lawyer_id=1,
                amount=100,
                withdraw_method="bank_card",
                bank_account_id=1,
            )

        assert "可提现余额不足" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_withdrawal_request_bank_account_not_found(self) -> None:
        """Test create_withdrawal_request with non-existent bank account."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wallet = MagicMock()
        mock_wallet.available_amount = 1000.0
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = WithdrawalService(mock_settlement)

        with patch('app.services.settlement.withdrawal._recalc_wallet_fields'):
            with pytest.raises(Exception) as exc_info:
                await service.create_withdrawal_request(
                    mock_db,
                    lawyer_id=1,
                    amount=100,
                    withdraw_method="bank_card",
                    bank_account_id=999,
                )

            assert "收款账户不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_withdrawal_request_success(self) -> None:
        """Test create_withdrawal_request success."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wallet = MagicMock()
        mock_wallet.available_amount = 1000.0
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        mock_bank = MagicMock()
        mock_bank.account_type = "bank_card"
        mock_bank.bank_name = "Test Bank"
        mock_bank.account_no = "encrypted_account"
        mock_bank.account_holder = "Test User"
        mock_bank.is_active = True

        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = mock_bank

        mock_lawyer = MagicMock()
        mock_lawyer.user_id = 1

        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = mock_lawyer

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        mock_settlement.decrypt_secret.return_value = "1234567890"
        mock_settlement.encrypt_secret.return_value = "encrypted"

        service = WithdrawalService(mock_settlement)

        with patch('app.services.settlement.withdrawal._recalc_wallet_fields'):
            wr = await service.create_withdrawal_request(
                mock_db,
                lawyer_id=1,
                amount=100,
                withdraw_method="bank_card",
                bank_account_id=1,
            )

            assert wr is not None


class TestWithdrawalServiceAdminSetStatus:
    """Tests for admin_set_withdrawal_status method."""

    @pytest.mark.asyncio
    async def test_admin_set_status_withdrawal_not_found(self) -> None:
        """Test admin_set_status with non-existent withdrawal."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = WithdrawalService(mock_settlement)

        with pytest.raises(Exception) as exc_info:
            await service.admin_set_withdrawal_status(
                mock_db,
                withdrawal_id=999,
                action="approve",
                admin_id=1,
            )

        assert "提现申请不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_admin_set_status_approve_success(self) -> None:
        """Test admin_set_status approve success."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wr = MagicMock()
        mock_wr.status = "pending"
        mock_wr.lawyer_id = 1
        mock_wr.amount = 100.0

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_wr
        mock_db.execute.return_value = mock_result

        mock_wallet = MagicMock()
        mock_wallet.available_amount = 900.0
        mock_wallet.frozen_amount = 100.0
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        service = WithdrawalService(mock_settlement)

        wr = await service.admin_set_withdrawal_status(
            mock_db,
            withdrawal_id=1,
            action="approve",
            admin_id=1,
        )

        assert wr is not None

    @pytest.mark.asyncio
    async def test_admin_set_status_approve_invalid_state(self) -> None:
        """Test admin_set_status approve with invalid state."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wr = MagicMock()
        mock_wr.status = "approved"
        mock_wr.lawyer_id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_wr
        mock_db.execute.return_value = mock_result

        mock_wallet = MagicMock()
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        service = WithdrawalService(mock_settlement)

        with pytest.raises(Exception) as exc_info:
            await service.admin_set_withdrawal_status(
                mock_db,
                withdrawal_id=1,
                action="approve",
                admin_id=1,
            )

        assert "仅待审核可通过" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_admin_set_status_reject_success(self) -> None:
        """Test admin_set_status reject success."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wr = MagicMock()
        mock_wr.status = "pending"
        mock_wr.lawyer_id = 1
        mock_wr.amount = 100.0

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_wr
        mock_db.execute.return_value = mock_result

        mock_wallet = MagicMock()
        mock_wallet.available_amount = 900.0
        mock_wallet.frozen_amount = 100.0
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        service = WithdrawalService(mock_settlement)

        wr = await service.admin_set_withdrawal_status(
            mock_db,
            withdrawal_id=1,
            action="reject",
            admin_id=1,
            reject_reason="Invalid account",
        )

        assert wr is not None

    @pytest.mark.asyncio
    async def test_admin_set_status_complete_success(self) -> None:
        """Test admin_set_status complete success."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wr = MagicMock()
        mock_wr.status = "approved"
        mock_wr.lawyer_id = 1
        mock_wr.amount = 100.0

        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = mock_wr

        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = []

        mock_lawyer = MagicMock()
        mock_lawyer.user_id = 1

        mock_result3 = MagicMock()
        mock_result3.scalar_one_or_none.return_value = mock_lawyer

        mock_db.execute.side_effect = [mock_result1, mock_result2, mock_result3]

        mock_wallet = MagicMock()
        mock_wallet.available_amount = 900.0
        mock_wallet.frozen_amount = 100.0
        mock_wallet.withdrawn_amount = 0.0
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        service = WithdrawalService(mock_settlement)

        wr = await service.admin_set_withdrawal_status(
            mock_db,
            withdrawal_id=1,
            action="complete",
            admin_id=1,
        )

        assert wr is not None

    @pytest.mark.asyncio
    async def test_admin_set_status_fail_success(self) -> None:
        """Test admin_set_status fail success."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wr = MagicMock()
        mock_wr.status = "approved"
        mock_wr.lawyer_id = 1
        mock_wr.amount = 100.0

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_wr
        mock_db.execute.return_value = mock_result

        mock_wallet = MagicMock()
        mock_wallet.available_amount = 900.0
        mock_wallet.frozen_amount = 100.0
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        service = WithdrawalService(mock_settlement)

        wr = await service.admin_set_withdrawal_status(
            mock_db,
            withdrawal_id=1,
            action="fail",
            admin_id=1,
            remark="Bank transfer failed",
        )

        assert wr is not None

    @pytest.mark.asyncio
    async def test_admin_set_status_invalid_action(self) -> None:
        """Test admin_set_status with invalid action."""
        mock_db = AsyncMock()
        mock_settlement = AsyncMock()
        mock_wr = MagicMock()
        mock_wr.status = "pending"
        mock_wr.lawyer_id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_wr
        mock_db.execute.return_value = mock_result

        mock_wallet = MagicMock()
        mock_settlement.get_or_create_wallet.return_value = mock_wallet

        service = WithdrawalService(mock_settlement)

        with pytest.raises(Exception) as exc_info:
            await service.admin_set_withdrawal_status(
                mock_db,
                withdrawal_id=1,
                action="invalid",
                admin_id=1,
            )

        assert "不支持的操作" in str(exc_info.value)
