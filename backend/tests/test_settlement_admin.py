"""Settlement Admin Router Tests

Tests for admin withdrawal management and settlement operations.
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settlement import WithdrawalRequest, LawyerIncomeRecord, LawyerWallet
from app.models.lawfirm import Lawyer
from app.models.user import User
from app.utils.security import create_access_token, hash_password


async def _create_user(db: AsyncSession, *, username: str, email: str, role: str = "user") -> User:
    """Helper to create a test user"""
    user = User(
        username=username,
        email=email,
        nickname=username,
        hashed_password=hash_password("Test123456"),
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_lawyer(db: AsyncSession, *, user_id: int, name: str = "测试律师") -> Lawyer:
    """Helper to create a test lawyer profile"""
    lawyer = Lawyer(
        user_id=user_id,
        name=name,
        license_no=f"LICENSE-{user_id}",
        specialties="劳动法",
        experience_years=5,
        is_verified=True,
        is_active=True,
    )
    db.add(lawyer)
    await db.commit()
    await db.refresh(lawyer)
    return lawyer


async def _create_wallet(db: AsyncSession, *, lawyer_id: int, available_amount: float = 0.0) -> LawyerWallet:
    """Helper to create a test wallet"""
    wallet = LawyerWallet(
        lawyer_id=lawyer_id,
        total_income=available_amount,
        available_amount=available_amount,
        withdrawn_amount=0.0,
        pending_amount=0.0,
        frozen_amount=0.0,
    )
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


async def _create_withdrawal(
    db: AsyncSession,
    *,
    lawyer_id: int,
    request_no: str,
    amount: float = 1000.0,
    status: str = "pending",
    withdraw_method: str = "bank",
) -> WithdrawalRequest:
    """Helper to create a test withdrawal request"""
    withdrawal = WithdrawalRequest(
        lawyer_id=lawyer_id,
        request_no=request_no,
        amount=Decimal(str(amount)),
        fee=Decimal("10.00"),
        actual_amount=Decimal(str(amount - 10)),
        withdraw_method=withdraw_method,
        account_info='{"bank":"测试银行","account_no":"6222000000000000","name":"测试用户"}',
        status=status,
    )
    db.add(withdrawal)
    await db.commit()
    await db.refresh(withdrawal)
    return withdrawal


async def _create_income(
    db: AsyncSession,
    *,
    lawyer_id: int,
    amount: float = 500.0,
) -> LawyerIncomeRecord:
    """Helper to create a test income record"""
    income = LawyerIncomeRecord(
        lawyer_id=lawyer_id,
        user_paid_amount=amount,
        platform_fee=amount * 0.1,
        lawyer_income=amount * 0.9,
        status="settled",
        order_no=f"ORDER-{int(datetime.now(timezone.utc).timestamp())}",
    )
    db.add(income)
    await db.commit()
    await db.refresh(income)
    return income


@pytest.mark.asyncio
async def test_admin_list_withdrawals_empty(client: AsyncClient, db: AsyncSession):
    """Test admin withdrawal list when empty"""
    admin = await _create_user(db, username="admin_settle_test", email="admin_settle@test.com", role="admin")
    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    response = await client.get(
        "/api/admin/withdrawals",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_admin_list_withdrawals_with_filters(client: AsyncClient, db: AsyncSession):
    """Test admin withdrawal list with status and keyword filters"""
    admin = await _create_user(db, username="admin_settle2_test", email="admin_settle2@test.com", role="admin")
    user = await _create_user(db, username="lawyer_settle_test", email="lawyer_settle@test.com")
    lawyer = await _create_lawyer(db, user_id=user.id)
    await _create_wallet(db, lawyer_id=lawyer.id, available_amount=5000)

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    await _create_withdrawal(db, lawyer_id=lawyer.id, request_no="WD-001", status="pending")
    await _create_withdrawal(db, lawyer_id=lawyer.id, request_no="WD-002", status="approved")
    await _create_withdrawal(db, lawyer_id=lawyer.id, request_no="WD-003", status="pending")

    response = await client.get(
        "/api/admin/withdrawals?status=pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["status"] == "pending"

    response = await client.get(
        "/api/admin/withdrawals?keyword=WD-002",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["request_no"] == "WD-002"


@pytest.mark.asyncio
async def test_admin_get_withdrawal_detail(client: AsyncClient, db: AsyncSession):
    """Test getting withdrawal detail"""
    admin = await _create_user(db, username="admin_detail_test", email="admin_detail@test.com", role="admin")
    user = await _create_user(db, username="lawyer_detail_test", email="lawyer_detail@test.com")
    lawyer = await _create_lawyer(db, user_id=user.id)
    await _create_wallet(db, lawyer_id=lawyer.id, available_amount=5000)
    withdrawal = await _create_withdrawal(db, lawyer_id=lawyer.id, request_no="WD-DETAIL-001", amount=2000)

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    response = await client.get(
        f"/api/admin/withdrawals/{withdrawal.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["request_no"] == "WD-DETAIL-001"
    assert float(data["amount"]) == 2000.0


@pytest.mark.asyncio
async def test_admin_export_withdrawals_csv(client: AsyncClient, db: AsyncSession):
    """Test exporting withdrawals as CSV"""
    admin = await _create_user(db, username="admin_export_test", email="admin_export@test.com", role="admin")
    user = await _create_user(db, username="lawyer_export_test", email="lawyer_export@test.com")
    lawyer = await _create_lawyer(db, user_id=user.id)
    await _create_wallet(db, lawyer_id=lawyer.id, available_amount=5000)

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    await _create_withdrawal(db, lawyer_id=lawyer.id, request_no="WD-EXPORT-001", amount=1000)
    await _create_withdrawal(db, lawyer_id=lawyer.id, request_no="WD-EXPORT-002", amount=2000)

    response = await client.get(
        "/api/admin/withdrawals/export",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    
    # 验证CSV内容使用正确的UTF-8编码解码
    content = response.content.decode('utf-8-sig')
    assert "WD-EXPORT-001" in content
    assert "WD-EXPORT-002" in content
