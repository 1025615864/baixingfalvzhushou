"""
用户服务单元测试

测试覆盖：
- 用户查询（按ID、用户名、邮箱）
- 用户创建
- 用户更新
- 用户认证
- 状态检查
- 用户列表查询
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.services.user_service import UserService, user_service
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password


@pytest.mark.asyncio
async def test_get_user_by_id_success(db: AsyncSession):
    """测试根据ID成功获取用户"""
    # Arrange
    user = User(
        username="testuser1",
        email="test1@example.com",
        nickname="测试用户1",
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Act
    found_user = await UserService.get_by_id(db, user.id)

    # Assert
    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.username == "testuser1"
    assert found_user.email == "test1@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db: AsyncSession):
    """测试根据ID获取不存在的用户"""
    # Act
    found_user = await UserService.get_by_id(db, 99999)

    # Assert
    assert found_user is None


@pytest.mark.asyncio
async def test_get_user_by_username_success(db: AsyncSession):
    """测试根据用户名成功获取用户"""
    # Arrange
    user = User(
        username="testuser2",
        email="test2@example.com",
        nickname="测试用户2",
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()

    # Act
    found_user = await UserService.get_by_username(db, "testuser2")

    # Assert
    assert found_user is not None
    assert found_user.username == "testuser2"
    assert found_user.email == "test2@example.com"


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(db: AsyncSession):
    """测试根据用户名获取不存在的用户"""
    # Act
    found_user = await UserService.get_by_username(db, "nonexistent")

    # Assert
    assert found_user is None


@pytest.mark.asyncio
async def test_get_user_by_email_success(db: AsyncSession):
    """测试根据邮箱成功获取用户"""
    # Arrange
    user = User(
        username="testuser3",
        email="test3@example.com",
        nickname="测试用户3",
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()

    # Act
    found_user = await UserService.get_by_email(db, "test3@example.com")

    # Assert
    assert found_user is not None
    assert found_user.email == "test3@example.com"
    assert found_user.username == "testuser3"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db: AsyncSession):
    """测试根据邮箱获取不存在的用户"""
    # Act
    found_user = await UserService.get_by_email(db, "nonexistent@example.com")

    # Assert
    assert found_user is None


@pytest.mark.asyncio
async def test_get_user_by_username_or_email_with_username(db: AsyncSession):
    """测试根据用户名或邮箱获取用户（使用用户名）"""
    # Arrange
    user = User(
        username="testuser4",
        email="test4@example.com",
        nickname="测试用户4",
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()

    # Act
    found_user = await UserService.get_by_username_or_email(db, "testuser4")

    # Assert
    assert found_user is not None
    assert found_user.username == "testuser4"


@pytest.mark.asyncio
async def test_get_user_by_username_or_email_with_email(db: AsyncSession):
    """测试根据用户名或邮箱获取用户（使用邮箱）"""
    # Arrange
    user = User(
        username="testuser5",
        email="test5@example.com",
        nickname="测试用户5",
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()

    # Act
    found_user = await UserService.get_by_username_or_email(db, "test5@example.com")

    # Assert
    assert found_user is not None
    assert found_user.email == "test5@example.com"


@pytest.mark.asyncio
async def test_create_user_success(db: AsyncSession):
    """测试成功创建用户"""
    # Arrange
    user_data = UserCreate(
        username="newuser",
        email="newuser@example.com",
        nickname="新用户",
        password="SecurePass123",
        agree_terms=True,
        agree_privacy=True,
        agree_ai_disclaimer=True
    )

    # Act
    user = await UserService.create(db, user_data)

    # Assert
    assert user is not None
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert user.nickname == "新用户"
    assert user.hashed_password is not None
    assert user.hashed_password != "SecurePass123"  # 密码应该被哈希
    assert verify_password("SecurePass123", user.hashed_password)  # 验证密码可以正确验证


@pytest.mark.asyncio
async def test_create_user_with_default_nickname(db: AsyncSession):
    """测试创建用户时使用用户名作为默认昵称"""
    # Arrange
    user_data = UserCreate(
        username="newuser2",
        email="newuser2@example.com",
        nickname=None,  # 不提供昵称
        password="SecurePass123",
        agree_terms=True,
        agree_privacy=True,
        agree_ai_disclaimer=True
    )

    # Act
    user = await UserService.create(db, user_data)

    # Assert
    assert user is not None
    assert user.nickname == "newuser2"  # 应该使用用户名作为默认昵称


@pytest.mark.asyncio
async def test_create_user_duplicate_username(db: AsyncSession):
    """测试创建用户时用户名重复"""
    # Arrange
    # 先创建一个用户
    existing_user = User(
        username="existinguser",
        email="existing@example.com",
        hashed_password=hash_password("password123")
    )
    db.add(existing_user)
    await db.commit()

    # 尝试创建相同用户名的用户
    user_data = UserCreate(
        username="existinguser",
        email="different@example.com",
        password="SecurePass123",
        agree_terms=True,
        agree_privacy=True,
        agree_ai_disclaimer=True
    )

    # Act & Assert
    with pytest.raises(ValueError, match="用户名或邮箱已被使用"):
        await UserService.create(db, user_data)


@pytest.mark.asyncio
async def test_create_user_duplicate_email(db: AsyncSession):
    """测试创建用户时邮箱重复"""
    # Arrange
    # 先创建一个用户
    existing_user = User(
        username="uniqueuser",
        email="duplicate@example.com",
        hashed_password=hash_password("password123")
    )
    db.add(existing_user)
    await db.commit()

    # 尝试创建相同邮箱的用户
    user_data = UserCreate(
        username="newuniqueuser",
        email="duplicate@example.com",
        password="SecurePass123",
        agree_terms=True,
        agree_privacy=True,
        agree_ai_disclaimer=True
    )

    # Act & Assert
    with pytest.raises(ValueError, match="用户名或邮箱已被使用"):
        await UserService.create(db, user_data)


@pytest.mark.asyncio
async def test_update_user_success(db: AsyncSession):
    """测试成功更新用户信息"""
    # Arrange
    user = User(
        username="testuser6",
        email="test6@example.com",
        nickname="旧昵称",
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()

    update_data = UserUpdate(
        nickname="新昵称",
        avatar="https://example.com/avatar.jpg"
    )

    # Act
    updated_user = await UserService.update(db, user, update_data)

    # Assert
    assert updated_user.nickname == "新昵称"
    assert updated_user.avatar == "https://example.com/avatar.jpg"
    assert updated_user.username == "testuser6"  # 用户名不应该改变
    assert updated_user.email == "test6@example.com"  # 邮箱不应该改变


@pytest.mark.asyncio
async def test_update_user_phone_number_change(db: AsyncSession):
    """测试更新用户手机号时重置验证状态"""
    # Arrange
    user = User(
        username="testuser7",
        email="test7@example.com",
        phone="13800138000",
        phone_verified=True,
        phone_verified_at=datetime.now(timezone.utc),
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()

    update_data = UserUpdate(
        phone="13800138001"
    )

    # Act
    updated_user = await UserService.update(db, user, update_data)

    # Assert
    assert updated_user.phone == "13800138001"
    assert updated_user.phone_verified is False  # 手机号改变时验证状态应该被重置
    assert updated_user.phone_verified_at is None


@pytest.mark.asyncio
async def test_update_user_partial(db: AsyncSession):
    """测试部分更新用户信息"""
    # Arrange
    user = User(
        username="testuser8",
        email="test8@example.com",
        nickname="原始昵称",
        phone="13800138000",
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()

    # 只更新昵称，不更新手机号
    update_data = UserUpdate(
        nickname="更新后的昵称"
    )

    # Act
    updated_user = await UserService.update(db, user, update_data)

    # Assert
    assert updated_user.nickname == "更新后的昵称"
    assert updated_user.phone == "13800138000"  # 手机号不应该改变


@pytest.mark.asyncio
async def test_update_user_remove_phone(db: AsyncSession):
    """测试移除用户手机号"""
    # Arrange
    user = User(
        username="testuser9",
        email="test9@example.com",
        phone="13800138000",
        phone_verified=True,
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()

    update_data = UserUpdate(
        phone=None
    )

    # Act
    updated_user = await UserService.update(db, user, update_data)

    # Assert
    assert updated_user.phone is None
    assert updated_user.phone_verified is False
    assert updated_user.phone_verified_at is None


@pytest.mark.asyncio
async def test_authenticate_success(db: AsyncSession):
    """测试成功认证用户"""
    # Arrange
    user = User(
        username="authuser",
        email="auth@example.com",
        hashed_password=hash_password("CorrectPassword123")
    )
    db.add(user)
    await db.commit()

    # Act
    authenticated_user = await UserService.authenticate(db, "authuser", "CorrectPassword123")

    # Assert
    assert authenticated_user is not None
    assert authenticated_user.username == "authuser"
    assert authenticated_user.email == "auth@example.com"


@pytest.mark.asyncio
async def test_authenticate_with_email(db: AsyncSession):
    """测试使用邮箱认证用户"""
    # Arrange
    user = User(
        username="emailuser",
        email="email@example.com",
        hashed_password=hash_password("CorrectPassword123")
    )
    db.add(user)
    await db.commit()

    # Act - 使用邮箱而不是用户名
    authenticated_user = await UserService.authenticate(db, "email@example.com", "CorrectPassword123")

    # Assert
    assert authenticated_user is not None
    assert authenticated_user.email == "email@example.com"


@pytest.mark.asyncio
async def test_authenticate_user_not_found(db: AsyncSession):
    """测试认证不存在的用户"""
    # Act
    authenticated_user = await UserService.authenticate(db, "nonexistent", "password123")

    # Assert
    assert authenticated_user is None


@pytest.mark.asyncio
async def test_authenticate_wrong_password(db: AsyncSession):
    """测试使用错误密码认证"""
    # Arrange
    user = User(
        username="wrongpass",
        email="wrongpass@example.com",
        hashed_password=hash_password("CorrectPassword123")
    )
    db.add(user)
    await db.commit()

    # Act
    authenticated_user = await UserService.authenticate(db, "wrongpass", "WrongPassword123")

    # Assert
    assert authenticated_user is None


@pytest.mark.asyncio
async def test_is_username_taken_true(db: AsyncSession):
    """测试检查用户名是否已被使用（已被使用）"""
    # Arrange
    user = User(
        username="takenuser",
        email="taken@example.com",
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()

    # Act
    is_taken = await UserService.is_username_taken(db, "takenuser")

    # Assert
    assert is_taken is True


@pytest.mark.asyncio
async def test_is_username_taken_false(db: AsyncSession):
    """测试检查用户名是否已被使用（未被使用）"""
    # Act
    is_taken = await UserService.is_username_taken(db, "freetouser")

    # Assert
    assert is_taken is False


@pytest.mark.asyncio
async def test_is_email_taken_true(db: AsyncSession):
    """测试检查邮箱是否已被使用（已被使用）"""
    # Arrange
    user = User(
        username="emailtaken",
        email="takenemail@example.com",
        hashed_password=hash_password("password123")
    )
    db.add(user)
    await db.commit()

    # Act
    is_taken = await UserService.is_email_taken(db, "takenemail@example.com")

    # Assert
    assert is_taken is True


@pytest.mark.asyncio
async def test_is_email_taken_false(db: AsyncSession):
    """测试检查邮箱是否已被使用（未被使用）"""
    # Act
    is_taken = await UserService.is_email_taken(db, "freeemail@example.com")

    # Assert
    assert is_taken is False


@pytest.mark.asyncio
async def test_get_user_list_without_keyword(db: AsyncSession):
    """测试获取用户列表（无关键词）"""
    # Arrange
    users = [
        User(username=f"user{i}", email=f"user{i}@example.com", hashed_password=hash_password("pass"))
        for i in range(5)
    ]
    for user in users:
        db.add(user)
    await db.commit()

    # Act
    user_list, total = await UserService.get_user_list(db, page=1, page_size=10)

    # Assert
    assert len(user_list) == 5
    assert total == 5


@pytest.mark.asyncio
async def test_get_user_list_with_keyword(db: AsyncSession):
    """测试获取用户列表（带关键词）"""
    # Arrange
    users = [
        User(username="testuser1", email="test1@example.com", nickname="测试用户1", hashed_password=hash_password("pass")),
        User(username="testuser2", email="test2@example.com", nickname="测试用户2", hashed_password=hash_password("pass")),
        User(username="otheruser", email="other@example.com", nickname="其他用户", hashed_password=hash_password("pass")),
    ]
    for user in users:
        db.add(user)
    await db.commit()

    # Act - 搜索关键词"test"
    user_list, total = await UserService.get_user_list(db, page=1, page_size=10, keyword="test")

    # Assert
    assert len(user_list) == 2  # 应该找到2个匹配的用户
    assert total == 2

    # Act - 搜索关键词"测试"
    user_list2, total2 = await UserService.get_user_list(db, page=1, page_size=10, keyword="测试")

    # Assert
    assert len(user_list2) == 2
    assert total2 == 2


@pytest.mark.asyncio
async def test_get_user_list_pagination(db: AsyncSession):
    """测试用户列表分页"""
    # Arrange
    users = [
        User(username=f"user{i}", email=f"user{i}@example.com", hashed_password=hash_password("pass"))
        for i in range(15)
    ]
    for user in users:
        db.add(user)
    await db.commit()

    # Act - 第一页
    page1, total1 = await UserService.get_user_list(db, page=1, page_size=10)
    assert len(page1) == 10
    assert total1 == 15

    # Act - 第二页
    page2, total2 = await UserService.get_user_list(db, page=2, page_size=10)
    assert len(page2) == 5
    assert total2 == 15

    # 验证分页正确性
    page1_ids = [u.id for u in page1]
    page2_ids = [u.id for u in page2]
    assert len(set(page1_ids) & set(page2_ids)) == 0  # 两页不应该有重叠


@pytest.mark.asyncio
async def test_get_user_list_ordering(db: AsyncSession):
    """测试用户列表排序（应该按ID降序）"""
    # Arrange
    users = [
        User(username=f"user{i}", email=f"user{i}@example.com", hashed_password=hash_password("pass"))
        for i in range(3)
    ]
    for user in users:
        db.add(user)
    await db.commit()

    # Act
    user_list, total = await UserService.get_user_list(db, page=1, page_size=10)

    # Assert - 应该按ID降序排列
    assert user_list[0].id > user_list[1].id
    assert user_list[1].id > user_list[2].id
    assert total == 3


@pytest.mark.asyncio
async def test_user_service_singleton():
    """测试用户服务单例"""
    # Act & Assert
    assert user_service is not None
    assert isinstance(user_service, UserService)
