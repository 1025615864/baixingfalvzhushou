"""
跨模块集成测试 - 论坛完整流程

测试场景：论坛发帖 → 审核 → 评论 → 点赞 完整流程
"""

from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.main import app
from app.models.forum import Post, Comment
from app.models.user import User
from app.utils.deps import get_current_user
from app.utils.security import hash_password
from tests.helpers.test_data_factory import UserFactory, PostFactory
from tests.helpers.assertion_helpers import assert_response_success


@pytest.mark.asyncio
async def test_forum_post_flow_create_post(
    client: AsyncClient,
    test_session,
) -> None:
    """测试：创建论坛帖子"""
    # 使用UserFactory创建用户
    user = await UserFactory.create_user(
        test_session,
        username="u_forum_int",
        role="user"
    )

    async def override_user():
        return user

    app.dependency_overrides[get_current_user] = override_user
    try:
        res = await client.post(
            "/api/forum/posts",
            json={
                "title": "集成测试帖子",
                "content": "这是一个用于跨模块集成测试的帖子内容",
                "category": "general",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("title") == "集成测试帖子"
        post_id = data.get("id")
        
        return post_id
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_forum_post_flow_add_comment(
    client: AsyncClient,
    test_session,
) -> None:
    """测试：评论帖子"""
    # 使用UserFactory创建用户
    user = await UserFactory.create_user(
        test_session,
        username="u_forum_comment",
        role="user"
    )
    
    post_user = await UserFactory.create_user(
        test_session,
        username="u_forum_post",
        role="user"
    )
    
    # 使用PostFactory创建帖子
    post = await PostFactory.create_forum_post(
        test_session,
        user_id=post_user.id,
        title="测试帖子"
    )

    async def override_user():
        return user

    app.dependency_overrides[get_current_user] = override_user
    try:
        res = await client.post(
            f"/api/forum/posts/{post.id}/comments",
            json={"content": "这是一条测试评论"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("content") == "这是一条测试评论"
        comment_id = data.get("id")
        
        return int(comment_id)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_forum_post_flow_like_post(
    client: AsyncClient,
    test_session,
) -> None:
    """测试：点赞帖子"""
    # 使用UserFactory创建用户
    user = await UserFactory.create_user(
        test_session,
        username="u_forum_like",
        role="user"
    )
    
    post_user = await UserFactory.create_user(
        test_session,
        username="u_forum_like_post",
        role="user"
    )
    
    # 使用PostFactory创建帖子
    post = await PostFactory.create_forum_post(
        test_session,
        user_id=post_user.id,
        title="待点赞帖子"
    )

    async def override_user():
        return user

    app.dependency_overrides[get_current_user] = override_user
    try:
        res = await client.post(f"/api/forum/posts/{post.id}/like")
        assert res.status_code == 200
        data = res.json()
        assert data.get("liked") == True
        assert data.get("like_count") == 1
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_forum_post_flow_full_integration(
    client: AsyncClient,
    test_session,
) -> None:
    """测试：完整流程 - 发帖 → 评论 → 点赞 → 取消点赞"""
    # 使用UserFactory创建用户
    user = await UserFactory.create_user(
        test_session,
        username="u_full_flow",
        role="user"
    )

    async def override_user():
        return user

    app.dependency_overrides[get_current_user] = override_user
    try:
        # 使用PostFactory创建帖子数据
        post_data = PostFactory.create_post_data(
            user_id=user.id,
            title="完整流程测试帖子",
            content="这是用于完整流程测试的帖子内容"
        )
        
        step1_res = await client.post("/api/forum/posts", json=post_data)
        assert step1_res.status_code == 200
        post_id = step1_res.json().get("id")
        assert post_id is not None

        step2_res = await client.post(
            f"/api/forum/posts/{post_id}/comments",
            json={"content": "完整流程测试评论"},
        )
        assert step2_res.status_code == 200
        comment_id = step2_res.json().get("id")
        assert comment_id is not None

        step3_res = await client.post(f"/api/forum/posts/{post_id}/like")
        assert step3_res.status_code == 200
        assert step3_res.json().get("liked") == True

        step4_res = await client.post(f"/api/forum/posts/{post_id}/like")
        assert step4_res.status_code == 200
        assert step4_res.json().get("liked") == False

        step5_res = await client.get(f"/api/forum/posts/{post_id}")
        # 验证响应直接返回帖子数据（不是包装格式）
        assert step5_res.status_code == 200
        post_data = step5_res.json()
        assert post_data.get("title") == "完整流程测试帖子"
        assert post_data.get("like_count") == 0

    finally:
        app.dependency_overrides.pop(get_current_user, None)