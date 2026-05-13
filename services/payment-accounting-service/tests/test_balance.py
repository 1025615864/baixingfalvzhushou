import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.balance_service import BalanceService
from app.models import UserBalance, BalanceTransaction


class TestBalanceService:

    @pytest.mark.asyncio
    async def test_get_or_create_balance_new_user(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = BalanceService(mock_db)
        balance = await service.get_or_create_balance(user_id=1)

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_or_create_balance_existing_user(self):
        mock_db = AsyncMock()
        existing_balance = UserBalance(user_id=1, balance=100.0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_balance
        mock_db.execute.return_value = mock_result

        service = BalanceService(mock_db)
        balance = await service.get_or_create_balance(user_id=1)

        assert balance.user_id == 1
        assert float(balance.balance) == 100.0
        assert not mock_db.add.called

    @pytest.mark.asyncio
    async def test_recharge(self):
        mock_db = AsyncMock()
        existing_balance = UserBalance(user_id=1, balance=100.0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_balance
        mock_db.execute.return_value = mock_result

        service = BalanceService(mock_db)
        balance = await service.recharge(user_id=1, amount=50.0, order_id=1)

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_consume_sufficient_balance(self):
        mock_db = AsyncMock()
        existing_balance = UserBalance(user_id=1, balance=100.0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_balance
        mock_db.execute.return_value = mock_result

        service = BalanceService(mock_db)
        balance = await service.consume(user_id=1, amount=30.0, order_id=1)

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_consume_insufficient_balance(self):
        mock_db = AsyncMock()
        existing_balance = UserBalance(user_id=1, balance=10.0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_balance
        mock_db.execute.return_value = mock_result

        service = BalanceService(mock_db)
        with pytest.raises(ValueError, match="Insufficient balance"):
            await service.consume(user_id=1, amount=50.0, order_id=1)

    @pytest.mark.asyncio
    async def test_get_transactions(self):
        mock_db = AsyncMock()
        mock_total_result = MagicMock()
        mock_total_result.scalars.return_value.all.return_value = [1, 2, 3]
        mock_tx_result = MagicMock()
        mock_tx_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_total_result, mock_tx_result]

        service = BalanceService(mock_db)
        transactions, total = await service.get_transactions(user_id=1, page=1, page_size=20)

        assert total == 3
