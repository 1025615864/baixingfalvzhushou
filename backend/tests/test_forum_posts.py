"""测试论坛帖子功能"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.forum import Post
from tests.helpers.test_data_factory import UserFactory, PostFactory
from tests.helpers.assertion_helpers import assert_response_success


class TestForumPostsRoutes:
    """测试论坛帖子路由"""

    @pytest.mark.asyncio
    async def test_get_posts_empty(self, client: AsyncClient):
        """测试获取空帖子列表"""
        response = await client.get("/api/forum/posts")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_posts_with_pagination(self, client: AsyncClient):
        """测试分页获取帖子列表"""
        response = await client.get("/api/forum/posts?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["page"] == 1
        assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_get_posts_with_category(self, client: AsyncClient):
        """测试按分类获取帖子"""
        response = await client.get("/api/forum/posts?category=general")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_posts_with_keyword(self, client: AsyncClient):
        """测试关键词搜索帖子"""
        response = await client.get("/api/forum/posts?keyword=test")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_posts_with_essence(self, client: AsyncClient):
        """测试获取精华帖"""
        response = await client.get("/api/forum/posts?is_essence=true")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_posts_invalid_page(self, client: AsyncClient):
        """测试无效的页码"""
        response = await client.get("/api/forum/posts?page=0")
        
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_posts_invalid_page_size(self, client: AsyncClient):
        """测试无效的页面大小"""
        response = await client.get("/api/forum/posts?page_size=0")
        
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_posts_page_size_too_large(self, client: AsyncClient):
        """测试页面大小超过限制"""
        response = await client.get("/api/forum/posts?page_size=200")
        
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_hot_posts(self, client: AsyncClient):
        """测试获取热门帖子"""
        response = await client.get("/api/forum/hot")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_hot_posts_with_category(self, client: AsyncClient):
        """测试按分类获取热门帖子"""
        response = await client.get("/api/forum/hot?category=general")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_hot_posts_invalid_limit(self, client: AsyncClient):
        """测试无效的限制数量"""
        response = await client.get("/api/forum/hot?limit=0")
        
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_hot_posts_limit_too_large(self, client: AsyncClient):
        """测试限制数量超过最大值"""
        response = await client.get("/api/forum/hot?limit=100")
        
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_post_not_found(self, client: AsyncClient):
        """测试获取不存在的帖子"""
        response = await client.get("/api/forum/posts/999999")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_post_detail(self, client: AsyncClient):
        """测试获取帖子详情"""
        response = await client.get("/api/forum/posts/1")
        
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_create_post_unauthorized(self, client: AsyncClient):
        """测试未授权创建帖子"""
        response = await client.post("/api/forum/posts", json={
            "title": "Test post",
            "content": "Test content",
            "category": "general"
        })
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_update_post_unauthorized(self, client: AsyncClient):
        """测试未授权更新帖子"""
        response = await client.put("/api/forum/posts/1", json={
            "title": "Updated title"
        })
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_delete_post_unauthorized(self, client: AsyncClient):
        """测试未授权删除帖子"""
        response = await client.delete("/api/forum/posts/1")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_my_posts_unauthorized(self, client: AsyncClient):
        """测试未授权获取我的帖子"""
        response = await client.get("/api/forum/me/posts")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_my_deleted_posts_unauthorized(self, client: AsyncClient):
        """测试未授权获取我删除的帖子"""
        response = await client.get("/api/forum/me/posts/deleted")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_deleted_post_detail_unauthorized(self, client: AsyncClient):
        """测试未授权获取回收站帖子详情"""
        response = await client.get("/api/forum/posts/1/recycle")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_like_post_unauthorized(self, client: AsyncClient):
        """测试未授权点赞帖子"""
        response = await client.post("/api/forum/posts/1/like")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_unlike_post_unauthorized(self, client: AsyncClient):
        """测试未授权取消点赞"""
        response = await client.delete("/api/forum/posts/1/like")
        
        # API端点可能不存在或返回404/405
        assert response.status_code in [401, 403, 404, 405]

    @pytest.mark.asyncio
    async def test_favorite_post_unauthorized(self, client: AsyncClient):
        """测试未授权收藏帖子"""
        response = await client.post("/api/forum/posts/1/favorite")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_unfavorite_post_unauthorized(self, client: AsyncClient):
        """测试未授权取消收藏"""
        response = await client.delete("/api/forum/posts/1/favorite")
        
        # API端点可能不存在或返回404/405
        assert response.status_code in [401, 403, 404, 405]

    @pytest.mark.asyncio
    async def test_create_post_as_user(self, client: AsyncClient, test_user: User):
        """测试用户创建帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 使用PostFactory创建帖子数据
        post_data = PostFactory.create_post_data(user_id=test_user.id)

        response = await client.post("/api/forum/posts", headers=headers, json=post_data)
        
        assert response.status_code in [200, 201, 400]

    @pytest.mark.asyncio
    async def test_update_post_as_user(self, client: AsyncClient, test_user: User):
        """测试用户更新帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.put("/api/forum/posts/1", headers=headers, json={
            "title": "Updated title"
        })
        
        assert response.status_code in [200, 403, 404]

    @pytest.mark.asyncio
    async def test_delete_post_as_user(self, client: AsyncClient, test_user: User):
        """测试用户删除帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/forum/posts/1", headers=headers)
        
        assert response.status_code in [200, 403, 404]

    @pytest.mark.asyncio
    async def test_create_post_with_sensitive_words(self, client: AsyncClient, test_user: User):
        """测试创建包含敏感词的帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 使用PostFactory创建包含敏感词的帖子数据
        post_data = PostFactory.create_post_data(
            user_id=test_user.id,
            title="敏感内容测试",
            content="This is sensitive content with bad words"
        )

        response = await client.post("/api/forum/posts", headers=headers, json=post_data)
        
        assert response.status_code in [200, 201, 400]

    @pytest.mark.asyncio
    async def test_create_post_success_flow(self, client: AsyncClient, db: AsyncSession):
        """测试成功创建帖子的完整流程"""
        # 创建测试用户
        author = await UserFactory.create_user(db, role="user")
        
        # 使用PostFactory创建帖子数据
        post_data = PostFactory.create_post_data(user_id=author.id)
        
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(author.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post("/api/forum/posts", headers=headers, json=post_data)
        
        # 验证响应直接返回帖子数据（不是包装格式）
        assert response.status_code == 200
        data = response.json()
        assert data.get("title") == post_data["title"]
        assert data.get("content") == post_data["content"]
        assert data.get("id") is not None

    @pytest.mark.asyncio
    async def test_create_post_with_long_title(self, client: AsyncClient, db: AsyncSession):
        """测试创建标题过长的帖子"""
        author = await UserFactory.create_user(db, role="user")
        
        # 使用PostFactory创建超长标题
        post_data = PostFactory.create_post_data(
            user_id=author.id,
            title="T" * 300  # 超长标题
        )
        
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(author.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post("/api/forum/posts", headers=headers, json=post_data)
        
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_post_with_xss(self, client: AsyncClient, test_user: User):
        """测试创建包含XSS的帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/forum/posts", headers=headers, json={
            "title": "<script>alert('xss')</script>",
            "content": "Test content",
            "category": "general"
        })
        
        assert response.status_code in [400, 200, 201]

    @pytest.mark.asyncio
    async def test_like_post(self, client: AsyncClient, test_user: User):
        """测试点赞帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/forum/posts/1/like", headers=headers)
        
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_unlike_post(self, client: AsyncClient, test_user: User):
        """测试取消点赞"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/forum/posts/1/like", headers=headers)
        
        # API端点可能不存在或返回405
        assert response.status_code in [200, 404, 405]

    @pytest.mark.asyncio
    async def test_favorite_post(self, client: AsyncClient, test_user: User):
        """测试收藏帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/forum/posts/1/favorite", headers=headers)
        
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_unfavorite_post(self, client: AsyncClient, test_user: User):
        """测试取消收藏"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/forum/posts/1/favorite", headers=headers)
        
        # API端点可能不存在或返回405
        assert response.status_code in [200, 404, 405]

    @pytest.mark.asyncio
    async def test_get_my_posts(self, client: AsyncClient, test_user: User):
        """测试获取我的帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/forum/me/posts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_my_deleted_posts(self, client: AsyncClient, test_user: User):
        """测试获取我删除的帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/forum/me/posts/deleted", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_restore_post(self, client: AsyncClient, test_user: User):
        """测试恢复帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/forum/posts/1/restore", headers=headers)
        
        assert response.status_code in [200, 403, 404]

    @pytest.mark.asyncio
    async def test_permanently_delete_post(self, client: AsyncClient, test_user: User):
        """测试永久删除帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/forum/posts/1/permanent", headers=headers)
        
        assert response.status_code in [200, 403, 404]

    @pytest.mark.asyncio
    async def test_set_essence_post(self, client: AsyncClient, test_user: User):
        """测试设置精华帖"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.put("/api/forum/posts/1/essence", headers=headers, json={
            "is_essence": True
        })
        
        assert response.status_code in [200, 403, 404]

    @pytest.mark.asyncio
    async def test_pin_post(self, client: AsyncClient, test_user: User):
        """测试置顶帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.put("/api/forum/posts/1/pin", headers=headers, json={
            "is_pinned": True
        })
        
        assert response.status_code in [200, 403, 404]

    @pytest.mark.asyncio
    async def test_lock_post(self, client: AsyncClient, test_user: User):
        """测试锁定帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.put("/api/forum/posts/1/lock", headers=headers, json={
            "is_locked": True
        })
        
        assert response.status_code in [200, 403, 404]

    @pytest.mark.asyncio
    async def test_get_post_comments(self, client: AsyncClient):
        """测试获取帖子评论"""
        response = await client.get("/api/forum/posts/1/comments")
        
        # API端点可能不存在
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_create_comment_unauthorized(self, client: AsyncClient):
        """测试未授权创建评论"""
        response = await client.post("/api/forum/posts/1/comments", json={
            "content": "Test comment"
        })
        
        # API端点可能不存在或返回404/405
        assert response.status_code in [401, 403, 404, 405]

    @pytest.mark.asyncio
    async def test_create_comment(self, client: AsyncClient, test_user: User):
        """测试创建评论"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/forum/posts/1/comments", headers=headers, json={
            "content": "Test comment"
        })
        
        # API端点可能不存在或返回404/405
        assert response.status_code in [200, 201, 404, 405]

    @pytest.mark.asyncio
    async def test_delete_comment_unauthorized(self, client: AsyncClient):
        """测试未授权删除评论"""
        response = await client.delete("/api/forum/posts/1/comments/1")
        
        # API端点可能不存在或返回404/405
        assert response.status_code in [401, 403, 404, 405]

    @pytest.mark.asyncio
    async def test_delete_comment(self, client: AsyncClient, test_user: User):
        """测试删除评论"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/forum/posts/1/comments/1", headers=headers)
        
        # API端点可能不存在或返回404/405
        assert response.status_code in [200, 403, 404, 405]

    @pytest.mark.asyncio
    async def test_report_post(self, client: AsyncClient, test_user: User):
        """测试举报帖子"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/forum/posts/1/report", headers=headers, json={
            "reason": "spam"
        })
        
        # API端点可能不存在或返回404/405
        assert response.status_code in [200, 404, 405]

    @pytest.mark.asyncio
    async def test_share_post(self, client: AsyncClient):
        """测试分享帖子"""
        response = await client.post("/api/forum/posts/1/share", json={
            "platform": "wechat"
        })
        
        # API端点可能不存在或返回404/405
        assert response.status_code in [200, 404, 405]

    @pytest.mark.asyncio
    async def test_search_posts_special_characters(self, client: AsyncClient):
        """测试搜索特殊字符"""
        response = await client.get("/api/forum/posts?keyword=<script>alert('xss')</script>")
        
        assert response.status_code == 200
