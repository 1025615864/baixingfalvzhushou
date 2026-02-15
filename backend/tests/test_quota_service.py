"""
配额服务单元测试

测试覆盖：
- 配额检查
- 配额更新
- 配额验证
- 配额重置
- VIP用户特殊处理
- 每日配额管理
- 配额包余额管理
"""
import pytest
from datetime import date, datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.quota_service import (
    QuotaService,
    quota_service,
    FREE_AI_CHAT_DAILY_LIMIT,
    VIP_AI_CHAT_DAILY_LIMIT,
    FREE_DOCUMENT_GENERATE_DAILY_LIMIT,
    VIP_DOCUMENT_GENERATE_DAILY_LIMIT,
    _is_vip_active,
    _is_vip_active_on_day,
)
from app.models.user import User
from app.models.user_quota import UserQuotaDaily, UserQuotaPackBalance


@pytest.mark.asyncio
async def test_get_or_create_today_new(db: AsyncSession):
    """测试创建今日配额记录（首次）"""
    service = QuotaService()
    user_id = 1

    # Act
    row = await service._get_or_create_today(db, user_id)

    # Assert
    assert row is not None
    assert row.user_id == user_id
    assert row.day == date.today()
    assert row.ai_chat_count == 0
    assert row.document_generate_count == 0


@pytest.mark.asyncio
async def test_get_or_create_today_existing(db: AsyncSession):
    """测试获取已存在的今日配额记录"""
    service = QuotaService()
    user_id = 2

    # 首次创建
    await service._get_or_create_today(db, user_id)

    # Act - 再次获取
    row = await service._get_or_create_today(db, user_id)

    # Assert
    assert row is not None
    assert row.user_id == user_id
    assert row.day == date.today()


@pytest.mark.asyncio
async def test_get_or_create_today_concurrent(db: AsyncSession):
    """测试并发创建今日配额记录"""
    import asyncio

    service = QuotaService()
    user_id = 3

    # Act - 并发创建
    results = await asyncio.gather(
        *[service._get_or_create_today(db, user_id) for _ in range(3)]
    )

    # Assert - 所有结果应该指向同一记录
    assert all(r is not None for r in results)
    # 检查数据库中只有一条记录
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count()).select_from(UserQuotaDaily).where(
            UserQuotaDaily.user_id == user_id,
            UserQuotaDaily.day == date.today()
        )
    )
    count = count_result.scalar()
    assert count == 1


@pytest.mark.asyncio
async def test_get_or_create_pack_balance_new(db: AsyncSession):
    """测试创建配额包余额（首次）"""
    service = QuotaService()
    user_id = 1

    # Act
    pack = await service._get_or_create_pack_balance(db, user_id)

    # Assert
    assert pack is not None
    assert pack.user_id == user_id
    assert pack.ai_chat_credits == 0
    assert pack.document_generate_credits == 0


@pytest.mark.asyncio
async def test_get_or_create_pack_balance_existing(db: AsyncSession):
    """测试获取已存在的配额包余额"""
    service = QuotaService()
    user_id = 2

    # 首次创建
    await service._get_or_create_pack_balance(db, user_id)

    # Act - 再次获取
    pack = await service._get_or_create_pack_balance(db, user_id)

    # Assert
    assert pack is not None
    assert pack.user_id == user_id


@pytest.mark.asyncio
async def test_ai_chat_limit_for_user_free(db: AsyncSession):
    """测试普通用户的AI聊天限额"""
    service = QuotaService()

    user = User(
        username="testuser1",
        email="test1@example.com",
        hashed_password="hash",
        vip_expires_at=None,  # 非VIP
    )
    db.add(user)
    await db.commit()

    # Act
    limit = await service._ai_chat_limit_for_user(db, user)

    # Assert
    assert limit == FREE_AI_CHAT_DAILY_LIMIT


@pytest.mark.asyncio
async def test_ai_chat_limit_for_user_vip(db: AsyncSession):
    """测试VIP用户的AI聊天限额"""
    service = QuotaService()

    user = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password="hash",
        vip_expires_at=datetime.now(timezone.utc) + timedelta(days=30),  # VIP
    )
    db.add(user)
    await db.commit()

    # Act
    limit = await service._ai_chat_limit_for_user(db, user)

    # Assert
    assert limit == VIP_AI_CHAT_DAILY_LIMIT


@pytest.mark.asyncio
async def test_ai_chat_limit_for_user_admin(db: AsyncSession):
    """测试管理员的AI聊天限额"""
    service = QuotaService()

    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password="hash",
        role="admin",
    )
    db.add(user)
    await db.commit()

    # Act
    limit = await service._ai_chat_limit_for_user(db, user)

    # Assert
    assert limit == 10**9  # 无限制


@pytest.mark.asyncio
async def test_ai_chat_limit_for_user_super_admin(db: AsyncSession):
    """测试超级管理员的AI聊天限额"""
    service = QuotaService()

    user = User(
        username="superadmin",
        email="superadmin@example.com",
        hashed_password="hash",
        role="super_admin",
    )
    db.add(user)
    await db.commit()

    # Act
    limit = await service._ai_chat_limit_for_user(db, user)

    # Assert
    assert limit == 10**9  # 无限制


@pytest.mark.asyncio
async def test_ai_chat_limit_for_user_vip_expired(db: AsyncSession):
    """测试VIP已过期的用户"""
    service = QuotaService()

    user = User(
        username="testuser3",
        email="test3@example.com",
        hashed_password="hash",
        vip_expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # VIP已过期
    )
    db.add(user)
    await db.commit()

    # Act
    limit = await service._ai_chat_limit_for_user(db, user)

    # Assert
    assert limit == FREE_AI_CHAT_DAILY_LIMIT


@pytest.mark.asyncio
async def test_enforce_ai_chat_quota_within_limit(db: AsyncSession):
    """测试AI聊天配额检查（未超限）"""
    service = QuotaService()

    user = User(
        username="testuser4",
        email="test4@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.commit()

    # Act - 不应该抛出异常
    await service.enforce_ai_chat_quota(db, user)


@pytest.mark.asyncio
async def test_enforce_ai_chat_quota_over_limit(db: AsyncSession):
    """测试AI聊天配额检查（已超限）"""
    service = QuotaService()

    user = User(
        username="testuser5",
        email="test5@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()

    # 创建今日配额记录并设置已使用次数
    daily = UserQuotaDaily(
        user_id=user.id,
        day=date.today(),
        ai_chat_count=100,  # 超过FREE_AI_CHAT_DAILY_LIMIT
        document_generate_count=0,
    )
    db.add(daily)
    await db.commit()

    # Act & Assert - 应该抛出HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await service.enforce_ai_chat_quota(db, user)

    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "今日 AI 咨询次数已用尽" in exc_info.value.detail


@pytest.mark.asyncio
async def test_enforce_ai_chat_quota_with_pack_credits(db: AsyncSession):
    """测试AI聊天配额检查（有配额包余额）"""
    service = QuotaService()

    user = User(
        username="testuser6",
        email="test6@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()

    # 创建今日配额记录并设置已使用次数
    daily = UserQuotaDaily(
        user_id=user.id,
        day=date.today(),
        ai_chat_count=100,
        document_generate_count=0,
    )
    db.add(daily)

    # 创建配额包余额
    pack = UserQuotaPackBalance(
        user_id=user.id,
        ai_chat_credits=10,  # 有配额包余额
        document_generate_credits=0,
    )
    db.add(pack)
    await db.commit()

    # Act - 不应该抛出异常（因为配额包有余额）
    await service.enforce_ai_chat_quota(db, user)


@pytest.mark.asyncio
async def test_record_ai_chat_usage_within_limit(db: AsyncSession):
    """测试记录AI聊天使用（未超限）"""
    service = QuotaService()

    user = User(
        username="testuser7",
        email="test7@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.commit()

    # Act
    await service.record_ai_chat_usage(db, user)

    # Assert
    daily = await service._get_or_create_today(db, user.id)
    assert daily.ai_chat_count == 1


@pytest.mark.asyncio
async def test_record_ai_chat_usage_multiple_times(db: AsyncSession):
    """测试多次记录AI聊天使用"""
    service = QuotaService()

    user = User(
        username="testuser8",
        email="test8@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.commit()

    # Act - 记录3次
    await service.record_ai_chat_usage(db, user)
    await service.record_ai_chat_usage(db, user)
    await service.record_ai_chat_usage(db, user)

    # Assert
    daily = await service._get_or_create_today(db, user.id)
    assert daily.ai_chat_count == 3


@pytest.mark.asyncio
async def test_record_ai_chat_usage_from_pack(db: AsyncSession):
    """测试从配额包记录AI聊天使用"""
    service = QuotaService()

    user = User(
        username="testuser9",
        email="test9@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()

    # 创建今日配额记录并设置已使用次数
    daily = UserQuotaDaily(
        user_id=user.id,
        day=date.today(),
        ai_chat_count=100,
        document_generate_count=0,
    )
    db.add(daily)

    # 创建配额包余额
    pack = UserQuotaPackBalance(
        user_id=user.id,
        ai_chat_credits=10,
        document_generate_credits=0,
    )
    db.add(pack)
    await db.commit()

    # Act
    await service.record_ai_chat_usage(db, user)

    # Assert - 配额包余额应该减少
    pack_result = await db.execute(
        select(UserQuotaPackBalance).where(UserQuotaPackBalance.user_id == user.id)
    )
    updated_pack = pack_result.scalar_one()
    assert updated_pack.ai_chat_credits == 9


@pytest.mark.asyncio
async def test_record_ai_chat_usage_over_limit_no_pack(db: AsyncSession):
    """测试记录AI聊天使用（超限且无配额包）"""
    service = QuotaService()

    user = User(
        username="testuser10",
        email="test10@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()

    # 创建今日配额记录并设置已使用次数
    daily = UserQuotaDaily(
        user_id=user.id,
        day=date.today(),
        ai_chat_count=100,
        document_generate_count=0,
    )
    db.add(daily)
    await db.commit()

    # Act & Assert - 应该抛出异常
    with pytest.raises(HTTPException) as exc_info:
        await service.record_ai_chat_usage(db, user)

    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.asyncio
async def test_consume_ai_chat_within_limit(db: AsyncSession):
    """测试消费AI聊天配额（未超限）"""
    service = QuotaService()

    user = User(
        username="testuser11",
        email="test11@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.commit()

    # Act - 不应该抛出异常
    await service.consume_ai_chat(db, user)

    # Assert - 使用次数应该增加
    daily = await service._get_or_create_today(db, user.id)
    assert daily.ai_chat_count == 1


@pytest.mark.asyncio
async def test_enforce_document_generate_quota_within_limit(db: AsyncSession):
    """测试文档生成配额检查（未超限）"""
    service = QuotaService()

    user = User(
        username="testuser12",
        email="test12@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.commit()

    # Act - 不应该抛出异常
    await service.enforce_document_generate_quota(db, user)


@pytest.mark.asyncio
async def test_enforce_document_generate_quota_over_limit(db: AsyncSession):
    """测试文档生成配额检查（已超限）"""
    service = QuotaService()

    user = User(
        username="testuser13",
        email="test13@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()

    # 创建今日配额记录并设置已使用次数
    daily = UserQuotaDaily(
        user_id=user.id,
        day=date.today(),
        ai_chat_count=0,
        document_generate_count=100,  # 超过FREE_DOCUMENT_GENERATE_DAILY_LIMIT
    )
    db.add(daily)
    await db.commit()

    # Act & Assert - 应该抛出HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await service.enforce_document_generate_quota(db, user)

    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "今日文书生成次数已用尽" in exc_info.value.detail


@pytest.mark.asyncio
async def test_record_document_generate_usage_within_limit(db: AsyncSession):
    """测试记录文档生成使用（未超限）"""
    service = QuotaService()

    user = User(
        username="testuser14",
        email="test14@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.commit()

    # Act
    await service.record_document_generate_usage(db, user)

    # Assert
    daily = await service._get_or_create_today(db, user.id)
    assert daily.document_generate_count == 1


@pytest.mark.asyncio
async def test_record_document_generate_usage_multiple_times(db: AsyncSession):
    """测试多次记录文档生成使用"""
    service = QuotaService()

    user = User(
        username="testuser15",
        email="test15@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.commit()

    # Act - 记录3次
    await service.record_document_generate_usage(db, user)
    await service.record_document_generate_usage(db, user)
    await service.record_document_generate_usage(db, user)

    # Assert
    daily = await service._get_or_create_today(db, user.id)
    assert daily.document_generate_count == 3


@pytest.mark.asyncio
async def test_document_generate_limit_for_user_free(db: AsyncSession):
    """测试普通用户的文档生成限额"""
    service = QuotaService()

    user = User(
        username="testuser16",
        email="test16@example.com",
        hashed_password="hash",
        vip_expires_at=None,
    )
    db.add(user)
    await db.commit()

    # Act
    limit = await service._doc_limit_for_user(db, user)

    # Assert
    assert limit == FREE_DOCUMENT_GENERATE_DAILY_LIMIT


@pytest.mark.asyncio
async def test_document_generate_limit_for_user_vip(db: AsyncSession):
    """测试VIP用户的文档生成限额"""
    service = QuotaService()

    user = User(
        username="testuser17",
        email="test17@example.com",
        hashed_password="hash",
        vip_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(user)
    await db.commit()

    # Act
    limit = await service._doc_limit_for_user(db, user)

    # Assert
    assert limit == VIP_DOCUMENT_GENERATE_DAILY_LIMIT


@pytest.mark.asyncio
async def test_consume_document_generate_within_limit(db: AsyncSession):
    """测试消费文档生成配额（未超限）"""
    service = QuotaService()

    user = User(
        username="testuser18",
        email="test18@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.commit()

    # Act - 不应该抛出异常
    await service.consume_document_generate(db, user)

    # Assert - 使用次数应该增加
    daily = await service._get_or_create_today(db, user.id)
    assert daily.document_generate_count == 1


@pytest.mark.asyncio
async def test_get_today_quota_info(db: AsyncSession):
    """测试获取今日配额信息"""
    service = QuotaService()

    user = User(
        username="testuser19",
        email="test19@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()

    # 创建配额记录
    daily = UserQuotaDaily(
        user_id=user.id,
        day=date.today(),
        ai_chat_count=3,
        document_generate_count=5,
    )
    db.add(daily)
    await db.commit()

    # Act
    quota_info = await service.get_today_quota(db, user)

    # Assert
    assert quota_info["day"] == date.today()
    assert "ai_chat_limit" in quota_info
    assert "ai_chat_used" in quota_info
    assert "ai_chat_remaining" in quota_info
    assert "document_generate_limit" in quota_info
    assert "document_generate_used" in quota_info
    assert "document_generate_remaining" in quota_info
    assert quota_info["ai_chat_used"] == 3
    assert quota_info["document_generate_used"] == 5
    assert "is_vip_active" in quota_info


@pytest.mark.asyncio
async def test_get_today_quota_with_pack_balance(db: AsyncSession):
    """测试获取今日配额信息（包含配额包）"""
    service = QuotaService()

    user = User(
        username="testuser20",
        email="test20@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()

    # 创建配额包余额
    pack = UserQuotaPackBalance(
        user_id=user.id,
        ai_chat_credits=20,
        document_generate_credits=10,
    )
    db.add(pack)
    await db.commit()

    # Act
    quota_info = await service.get_today_quota(db, user)

    # Assert
    assert quota_info["ai_chat_pack_remaining"] == 20
    assert quota_info["document_generate_pack_remaining"] == 10


@pytest.mark.asyncio
async def test_is_vip_active_none_user():
    """测试VIP状态检查（用户为None）"""
    # Act & Assert
    assert _is_vip_active(None) is False


@pytest.mark.asyncio
async def test_is_vip_active_no_expires_at():
    """测试VIP状态检查（无过期时间）"""
    user = User(
        username="testuser21",
        email="test21@example.com",
        hashed_password="hash",
        vip_expires_at=None,
    )

    # Act & Assert
    assert _is_vip_active(user) is False


@pytest.mark.asyncio
async def test_is_vip_active_future():
    """测试VIP状态检查（未来过期）"""
    user = User(
        username="testuser22",
        email="test22@example.com",
        hashed_password="hash",
        vip_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    # Act & Assert
    assert _is_vip_active(user) is True


@pytest.mark.asyncio
async def test_is_vip_active_past():
    """测试VIP状态检查（过去过期）"""
    user = User(
        username="testuser23",
        email="test23@example.com",
        hashed_password="hash",
        vip_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )

    # Act & Assert
    assert _is_vip_active(user) is False


@pytest.mark.asyncio
async def test_is_vip_active_on_day_specific_date(db: AsyncSession):
    """测试特定日期的VIP状态"""
    service = QuotaService()

    user = User(
        username="testuser24",
        email="test24@example.com",
        hashed_password="hash",
        vip_expires_at=datetime.now(timezone.utc) + timedelta(days=10),
    )
    db.add(user)
    await db.commit()

    # Act - 检查今天和10天后的状态
    today = date.today()
    future_date = today + timedelta(days=5)

    limit_today = await service._ai_chat_limit_for_user_on_day(db, user, today)
    limit_future = await service._ai_chat_limit_for_user_on_day(db, user, future_date)

    # Assert - 两日期应该都是VIP限额
    assert limit_today == VIP_AI_CHAT_DAILY_LIMIT
    assert limit_future == VIP_AI_CHAT_DAILY_LIMIT


@pytest.mark.asyncio
async def test_quota_service_singleton():
    """测试配额服务单例"""
    # Act & Assert
    assert quota_service is not None
    assert isinstance(quota_service, QuotaService)
