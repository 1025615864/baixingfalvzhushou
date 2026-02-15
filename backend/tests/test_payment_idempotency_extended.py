import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from app.models.payment import PaymentOrder, PaymentStatus, BalanceTransaction, PaymentCallbackEvent
from app.models.user import User
from app.utils.deps import get_current_user
from sqlalchemy import select, func

class TestPaymentIdempotencyExtended:
    """Extended Payment Idempotency Tests"""

    @pytest.mark.asyncio
    async def test_sequential_duplicate_callback(self, client, test_session):
        """Test processing the same callback twice sequentially"""
        # 1. Setup User and Order
        user = User(username="idem_seq_user", email="idem_seq@example.com", nickname="idem_seq", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        order_no = "idem-seq-001"
        trade_no = "trade-seq-001"
        amount = 100.0

        order = PaymentOrder(
            order_no=order_no,
            user_id=user.id,
            order_type="recharge", # Use recharge to check balance transactions
            amount=amount,
            actual_amount=amount,
            status=PaymentStatus.PENDING,
            title="Recharge",
        )
        test_session.add(order)
        await test_session.commit()

        # 2. Mock legacy helpers to avoid real external calls if any, 
        # but here we are testing the router/service integration so we rely on the implementation.
        # We need to bypass signature verification or mock it.
        # It's easier to call the service function directly or use a mock signature.
        # However, testing `_mark_order_paid_in_tx` directly is also good.
        
        # Let's verify via `_mark_order_paid_in_tx` directly first as unit test, then full flow.
        from app.routers.payment.post_processing import _mark_order_paid_in_tx
        
        # First Call
        res1 = await _mark_order_paid_in_tx(
            test_session,
            order=order,
            payment_method="alipay",
            trade_no=trade_no,
            amount=amount
        )
        await test_session.commit()
        assert res1 is True
        
        # Reload order
        await test_session.refresh(order)
        assert order.status == PaymentStatus.PAID
        
        # Check BalanceTransaction count
        bt_res = await test_session.execute(select(func.count()).where(BalanceTransaction.order_id == order.id))
        assert bt_res.scalar() == 1

        # Second Call (Idempotent)
        res2 = await _mark_order_paid_in_tx(
            test_session,
            order=order,
            payment_method="alipay",
            trade_no=trade_no,
            amount=amount
        )
        await test_session.commit()
        assert res2 is False # Should return False as it was already paid

        # Check BalanceTransaction count (Must still be 1)
        bt_res2 = await test_session.execute(select(func.count()).where(BalanceTransaction.order_id == order.id))
        assert bt_res2.scalar() == 1

    @pytest.mark.asyncio
    async def test_concurrent_duplicate_callback(self, client, test_session):
        """Test processing the same callback concurrently"""
        # 1. Setup User and Orders
        user = User(username="idem_conc_user", email="idem_conc@example.com", nickname="idem_conc", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        order_no = "idem-conc-001"
        trade_no = "trade-conc-001"
        amount = 100.0

        order = PaymentOrder(
            order_no=order_no,
            user_id=user.id,
            order_type="recharge",
            amount=amount,
            actual_amount=amount,
            status=PaymentStatus.PENDING,
            title="Recharge",
        )
        test_session.add(order)
        await test_session.commit()

        from app.routers.payment.post_processing import _mark_order_paid_in_tx

        # Define a function to be run concurrently
        # We need separate sessions for true concurrency simulation in tests?
        # Or just simulate the race condition on the same session/row?
        # AsyncPG/SQLAlchemy async session is not thread-safe but we are in asyncio.
        # We can simulate the race by calling the function concurrently.
        
        async def mark_paid():
            # In a real race, they would check status 'PENDING' simultaneously.
            # `_mark_order_paid_in_tx` does `update ... where status='pending'`.
            # This is atomic in DB.
            return await _mark_order_paid_in_tx(
                test_session,
                order=order,
                payment_method="alipay",
                trade_no=trade_no,
                amount=amount
            )

        # Run 5 concurrent attempts
        results = await asyncio.gather(*(mark_paid() for _ in range(5)))
        
        await test_session.commit()

        # Only one should succeed (True)
        success_count = sum(1 for r in results if r is True)
        assert success_count == 1
        
        # Check BalanceTransaction count
        bt_res = await test_session.execute(select(func.count()).where(BalanceTransaction.order_id == order.id))
        assert bt_res.scalar() == 1

    @pytest.mark.asyncio
    async def test_callback_event_logging_no_constraint(self, client, test_session):
        """Test that we can log multiple events for same trade_no without IntegrityError"""
        from app.routers.payment.helpers import log_callback_event
        
        trade_no = "trade-log-001"
        provider = "alipay"
        
        # Log event 1
        await log_callback_event(
            test_session,
            provider=provider,
            order_no="order-1",
            trade_no=trade_no,
            amount=Decimal("100"),
            verified=True,
            error_message="msg1",
            raw_payload="{}"
        )

        # Log event 2 (Same trade_no)
        await log_callback_event(
            test_session,
            provider=provider,
            order_no="order-1",
            trade_no=trade_no,
            amount=Decimal("100"),
            verified=True,
            error_message="msg2",
            raw_payload="{}"
        )
        
        # Check count
        count_res = await test_session.execute(
            select(func.count()).where(PaymentCallbackEvent.trade_no == trade_no)
        )
        assert count_res.scalar() == 2
