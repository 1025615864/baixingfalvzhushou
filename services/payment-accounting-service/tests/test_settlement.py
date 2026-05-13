import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.settlement_service import SettlementService
from app.models import LawyerWallet, Settlement


class TestSettlementService:

    @pytest.mark.asyncio
    async def test_get_or_create_wallet_new_lawyer(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = SettlementService(mock_db)
        wallet = await service.get_or_create_wallet(lawyer_id=1)

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_or_create_wallet_existing_lawyer(self):
        mock_db = AsyncMock()
        existing_wallet = LawyerWallet(lawyer_id=1, balance=500.0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_wallet
        mock_db.execute.return_value = mock_result

        service = SettlementService(mock_db)
        wallet = await service.get_or_create_wallet(lawyer_id=1)

        assert wallet.lawyer_id == 1
        assert float(wallet.balance) == 500.0
        assert not mock_db.add.called

    @pytest.mark.asyncio
    async def test_withdraw_sufficient_balance(self):
        mock_db = AsyncMock()
        existing_wallet = LawyerWallet(lawyer_id=1, balance=1000.0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_wallet
        mock_db.execute.return_value = mock_result

        service = SettlementService(mock_db)
        result = await service.withdraw(
            lawyer_id=1,
            amount=100.0,
            bank_account="6222000000001",
            real_name="张三"
        )

        assert "settlement_id" in result
        assert result["amount"] == 100.0
        assert result["status"] == "pending"
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_withdraw_insufficient_balance(self):
        mock_db = AsyncMock()
        existing_wallet = LawyerWallet(lawyer_id=1, balance=50.0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_wallet
        mock_db.execute.return_value = mock_result

        service = SettlementService(mock_db)
        with pytest.raises(ValueError, match="Insufficient balance"):
            await service.withdraw(
                lawyer_id=1,
                amount=100.0,
                bank_account="6222000000001",
                real_name="张三"
            )

    @pytest.mark.asyncio
    async def test_withdraw_platform_fee_calculation(self):
        mock_db = AsyncMock()
        existing_wallet = LawyerWallet(lawyer_id=1, balance=1000.0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_wallet
        mock_db.execute.return_value = mock_result

        service = SettlementService(mock_db)
        result = await service.withdraw(
            lawyer_id=1,
            amount=200.0,
            bank_account="6222000000001",
            real_name="张三"
        )

        assert result["fee"] == 10.0
        assert result["actual_amount"] == 190.0
