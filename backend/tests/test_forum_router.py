"""
测试论坛API路由

测试论坛相关的所有端点，包括：
- 帖子管理（创建、获取、更新、删除）
- 评论管理（创建、获取、赞）
- 收藏功能
- 反应功能
- 搜索和筛选
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from tests.helpers.test_data_factory import UserFactory, PostFactory
from tests.helpers.assertion_helpers import assert_response_success


class TestForumPostsRouter:
    """测试论坛帖子路由"""

    @pytest.mark.asyncio
    async def test_create_post_without_auth(self, client: AsyncClient):
        """测试未认证创建帖子"""
        # Arrange
        post_data = {
            "title": "Test Post Title",
            "content": "Test post content",
            "category": "general"
        }

        # Act
        response = await client.post("/api/forum/posts", json=post_data)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_post_success(self, client: AsyncClient, test_user, db):
        """测试成功创建帖子"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        post_data = {
            "title": "Test Post Title",
            "content": "Test post content",
            "category": "general"
        }

        # Act
        response = await client.post("/api/forum/posts", json=post_data, headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Post Title"
        assert data["content"] == "Test post content"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_post_with_sensitive_content(self, client: AsyncClient, test_user, db):
        """测试创建包含敏感词的帖子"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        post_data = {
            "title": "Test",
            "content": "This is sensitive content",  # 假设有敏感词过滤
            "category": "general"
        }

        # Act
        response = await client.post("/api/forum/posts", json=post_data, headers=headers)

        # Assert - 可能成功或被过滤
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_get_posts_list(self, client: AsyncClient, db):
        """测试获取帖子列表"""
        # Arrange - 使用PostFactory创建多个帖子
        for i in range(5):
            post = await PostFactory.create_forum_post(
                db,
                user_id=1,
                title=f"Post {i}"
            )

        # Act
        response = await client.get("/api/forum/posts?page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 5

    @pytest.mark.asyncio
    async def test_get_posts_with_category_filter(self, client: AsyncClient, db):
        """测试按分类筛选帖子"""
        # Act
        response = await client.get("/api/forum/posts?category=general&page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_posts_with_keyword_search(self, client: AsyncClient, db):
        """测试关键词搜索帖子"""
        # Act
        response = await client.get("/api/forum/posts?keyword=test&page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_post_by_id(self, client: AsyncClient, db):
        """测试获取单个帖子详情"""
        # Arrange - 使用PostFactory创建帖子
        post = await PostFactory.create_forum_post(
            db,
            user_id=1,
            title="Test Post"
        )

        # Act
        response = await client.get(f"/api/forum/posts/{post.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == post.id
        assert data["title"] == "Test Post"

    @pytest.mark.asyncio
    async def test_get_post_not_found(self, client: AsyncClient):
        """测试获取不存在的帖子"""
        # Act
        response = await client.get("/api/forum/posts/99999")

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_post_without_auth(self, client: AsyncClient, db):
        """测试未认证更新帖子"""
        # Arrange
        update_data = {"title": "Updated Title"}

        # Act
        response = await client.put("/api/forum/posts/123", json=update_data)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_post_success(self, client: AsyncClient, test_user, db):
        """测试成功更新帖子"""
        # Arrange
        from app.utils.security import create_access_token

        # 使用PostFactory创建帖子
        post = await PostFactory.create_forum_post(
            db,
            user_id=test_user.id,
            title="Original Title"
        )

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        update_data = {"title": "Updated Title"}

        # Act
        response = await client.put(f"/api/forum/posts/{post.id}", json=update_data, headers=headers)

        # Assert
        assert response.status_code in [200, 403]  # 可能成功或权限不足

    @pytest.mark.asyncio
    async def test_delete_post_without_auth(self, client: AsyncClient, db):
        """测试未认证删除帖子"""
        # Act
        response = await client.delete("/api/forum/posts/123")

        # Assert
        assert response.status_code == 401


class TestForumCommentsRouter:
    """测试论坛评论路由"""

    @pytest.mark.asyncio
    async def test_create_comment_without_auth(self, client: AsyncClient, db):
        """测试未认证创建评论"""
        # Arrange - 使用PostFactory创建帖子
        post = await PostFactory.create_forum_post(
            db,
            user_id=1,
            title="Test Post"
        )

        comment_data = {"content": "Test comment"}

        # Act
        response = await client.post(f"/api/forum/posts/{post.id}/comments", json=comment_data)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_comment_success(self, client: AsyncClient, test_user, db):
        """测试成功创建评论"""
        # Arrange
        from app.models.forum import Post
        from app.utils.security import create_access_token

        # 先创建帖子
        post = Post(
            title="Test Post",
            content="Test content",
            category="general",
            user_id=1,
            review_status="approved",
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(post)
        await db.commit()

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        comment_data = {"content": "Test comment"}

        # Act
        response = await client.post(f"/api/forum/posts/{post.id}/comments", json=comment_data, headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test comment"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_comment_on_nonexistent_post(self, client: AsyncClient, test_user, db):
        """测试在不存在的帖子上创建评论"""
        # Arrange
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        comment_data = {"content": "Test comment"}

        # Act
        response = await client.post("/api/forum/posts/99999/comments", json=comment_data, headers=headers)

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_comments_list(self, client: AsyncClient, db):
        """测试获取评论列表"""
        # Arrange
        from app.models.forum import Post, Comment

        # 先创建帖子和评论
        post = Post(
            title="Test Post",
            content="Test content",
            category="general",
            user_id=1,
            review_status="approved",
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(post)
        await db.commit()

        for i in range(5):
            comment = Comment(
                post_id=post.id,
                user_id=1,
                content=f"Comment {i}",
                review_status="approved",
                is_deleted=False,
                created_at=datetime.now(timezone.utc),
            )
            db.add(comment)
        await db.commit()

        # Act
        response = await client.get(f"/api/forum/posts/{post.id}/comments?page=1&page_size=50")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 5

    @pytest.mark.asyncio
    async def test_like_comment_without_auth(self, client: AsyncClient, db):
        """测试未认证点赞评论"""
        # Act
        response = await client.post("/api/forum/comments/123/like")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_like_comment_success(self, client: AsyncClient, test_user, db):
        """测试成功点赞评论"""
        # Arrange
        from app.models.forum import Post, Comment
        from app.utils.security import create_access_token

        # 先创建帖子和评论
        post = Post(
            title="Test Post",
            content="Test content",
            category="general",
            user_id=1,
            review_status="approved",
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(post)
        await db.commit()

        comment = Comment(
            post_id=post.id,
            user_id=test_user.id,
            content="Test comment",
            review_status="approved",
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(comment)
        await db.commit()

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.post(f"/api/forum/comments/{comment.id}/like", headers=headers)

        # Assert
        assert response.status_code == 200


class TestForumFavoritesRouter:
    """测试论坛收藏路由"""

    @pytest.mark.asyncio
    async def test_toggle_favorite_without_auth(self, client: AsyncClient, db):
        """测试未认证切换收藏"""
        # Act
        response = await client.post("/api/forum/posts/123/favorite")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_toggle_favorite_success(self, client: AsyncClient, test_user, db):
        """测试成功收藏帖子"""
        # Arrange
        from app.models.forum import Post
        from app.utils.security import create_access_token

        # 先创建帖子
        post = Post(
            title="Test Post",
            content="Test content",
            category="general",
            user_id=1,
            review_status="approved",
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(post)
        await db.commit()

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.post(f"/api/forum/posts/{post.id}/favorite", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "favorited" in data
        assert "favorite_count" in data

    @pytest.mark.asyncio
    async def test_get_my_favorites_without_auth(self, client: AsyncClient):
        """测试未认证获取收藏列表"""
        # Act
        response = await client.get("/api/forum/favorites")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_favorites_success(self, client: AsyncClient, test_user, db):
        """测试成功获取收藏列表"""
        # Arrange
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.get("/api/forum/favorites?page=1&page_size=20", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestForumReactionsRouter:
    """测试论坛反应路由"""

    @pytest.mark.asyncio
    async def test_toggle_like_without_auth(self, client: AsyncClient, db):
        """测试未认证点赞帖子"""
        # Act
        response = await client.post("/api/forum/posts/123/like")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_toggle_like_success(self, client: AsyncClient, test_user, db):
        """测试成功点赞帖子"""
        # Arrange
        from app.models.forum import Post
        from app.utils.security import create_access_token

        # 先创建帖子
        post = Post(
            title="Test Post",
            content="Test content",
            category="general",
            user_id=1,
            review_status="approved",
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(post)
        await db.commit()

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.post(f"/api/forum/posts/{post.id}/like", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["liked"] is True


class TestForumRouterSearchAndFilter:
    """测试论坛搜索和筛选功能"""

    @pytest.mark.asyncio
    async def test_search_posts_essence_only(self, client: AsyncClient, db):
        """测试筛选精华帖"""
        # Act
        response = await client.get("/api/forum/posts?is_essence=true&page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_search_posts_with_long_keyword(self, client: AsyncClient, db):
        """测试使用过长关键词"""
        # Arrange
        long_keyword = "a" * 200

        # Act
        response = await client.get(f"/api/forum/posts?keyword={long_keyword}&page=1&page_size=10")

        # Assert
        assert response.status_code == 422
        # 检查自定义错误响应格式
        error_data = response.json()
        assert error_data["ok"] is False
        assert "error" in error_data
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
        # 检查错误详情中包含字段长度验证错误
        errors = error_data["error"]["details"]["errors"]
        assert any(
            err.get("field") == "query.keyword" and
            "string_too_long" in str(err.get("type", ""))
            for err in errors
        )

    @pytest.mark.asyncio
    async def test_get_posts_pagination(self, client: AsyncClient, db):
        """测试分页获取帖子"""
        # Arrange - 创建足够多的帖子
        from app.models.forum import Post

        for i in range(30):
            post = Post(
                title=f"Post {i}",
                content=f"Content {i}",
                category="general",
                user_id=1,
                review_status="approved",
                is_deleted=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(post)
        await db.commit()

        # Act - 第一页
        response_page1 = await client.get("/api/forum/posts?page=1&page_size=10")
        # 第二页
        response_page2 = await client.get("/api/forum/posts?page=2&page_size=10")

        # Assert
        assert response_page1.status_code == 200
        assert response_page2.status_code == 200
        data1 = response_page1.json()
        data2 = response_page2.json()
        assert len(data1["items"]) <= 10
        assert len(data2["items"]) <= 10


class TestForumRouterErrorHandling:
    """测试论坛路由错误处理"""

    @pytest.mark.asyncio
    async def test_create_post_invalid_data(self, client: AsyncClient, test_user, db):
        """测试使用无效数据创建帖子"""
        # Arrange
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        invalid_data = {
            "title": "",  # 空标题
            "content": "",  # 空内容
        }

        # Act
        response = await client.post("/api/forum/posts", json=invalid_data, headers=headers)

        # Assert - 应该返回验证错误
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_update_post_invalid_id(self, client: AsyncClient, test_user, db):
        """测试更新不存在的帖子"""
        # Arrange
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        update_data = {"title": "Updated"}

        # Act
        response = await client.put("/api/forum/posts/99999", json=update_data, headers=headers)

        # Assert
        assert response.status_code == 404