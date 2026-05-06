"""并发竞态测试"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.post_service import PostService
from app.models.post import Post, PostLike
from app.database import AsyncSessionLocal


class TestConcurrentLike:
    @pytest.fixture
    def mock_db(self):
        mock = AsyncMock(spec=AsyncSessionLocal)
        return mock

    @pytest.fixture
    def mock_cache(self):
        mock = MagicMock()
        mock.incr_like_count = AsyncMock(return_value=1)
        mock.decr_like_count = AsyncMock(return_value=0)
        return mock

    @pytest.mark.asyncio
    async def test_concurrent_like_same_post(self, mock_db, mock_cache):
        post_id = 1
        user_ids = [1, 2, 3, 4, 5]

        async def mock_execute(query):
            result = MagicMock()
            result.scalar_one_or_none = MagicMock(return_value=None)
            return result

        mock_db.execute = mock_execute
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.delete = AsyncMock()

        service = PostService(
            db=mock_db,
            user_client=None,
            event_bus=None,
            cache=mock_cache
        )

        tasks = [service.like_post(post_id, user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        liked_count = sum(1 for r in results if r.get("action") == "liked")
        assert liked_count == 5

    @pytest.mark.asyncio
    async def test_like_unlike_race_condition(self, mock_db, mock_cache):
        post_id = 1
        user_id = 1

        post_mock = MagicMock()
        post_mock.id = post_id
        post_mock.like_count = 0
        post_mock.user_id = 999

        existing_like = MagicMock()
        existing_like.scalar_one_or_none = MagicMock(return_value=None)

        call_count = [0]

        async def mock_execute(query):
            result = MagicMock()
            if call_count[0] == 0:
                result.scalar_one_or_none = MagicMock(return_value=post_mock)
            else:
                result.scalar_one_or_none = MagicMock(return_value=None)
            call_count[0] += 1
            return result

        mock_db.execute = mock_execute
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.delete = AsyncMock()

        service = PostService(
            db=mock_db,
            user_client=None,
            event_bus=None,
            cache=mock_cache
        )

        result1 = await service.like_post(post_id, user_id)
        result2 = await service.like_post(post_id, user_id)

        assert result1.get("action") == "liked"
        assert result2.get("action") == "unliked"


class TestFloorNumberConcurrency:
    def test_concurrent_floor_assignment(self):
        existing_floors = []
        lock = asyncio.Lock()

        async def assign_floor(floor_num):
            async with lock:
                existing_floors.append(floor_num)

        async def get_next_floor():
            async with lock:
                return max(existing_floors) + 1 if existing_floors else 1

        async def simulate_floor_assignment():
            tasks = []
            for i in range(10):
                tasks.append(assign_floor(i + 1))

            await asyncio.gather(*tasks)

            next_floor = await get_next_floor()
            return next_floor

        next_floor = asyncio.get_event_loop().run_until_complete(
            simulate_floor_assignment()
        )
        assert next_floor == 11
        assert len(existing_floors) == 10


class TestHotScoreConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_hot_score_update(self):
        post_mock = MagicMock()
        post_mock.like_count = 0
        post_mock.comment_count = 0
        post_mock.view_count = 0
        post_mock.favorite_count = 0
        post_mock.is_lawyer = False
        post_mock.created_at = datetime.now(timezone.utc)

        update_count = [0]

        async def mock_commit():
            update_count[0] += 1

        mock_db = AsyncMock()
        mock_db.commit = mock_commit

        from app.utils.scoring import calculate_hot_score

        async def update_score():
            post_mock.like_count += 1
            post_mock.hot_score = calculate_hot_score(
                likes=post_mock.like_count,
                comments=post_mock.comment_count,
                views=post_mock.view_count,
                favorites=post_mock.favorite_count,
                is_lawyer_post=post_mock.is_lawyer,
                created_at=post_mock.created_at
            )

        tasks = [update_score() for _ in range(10)]
        await asyncio.gather(*tasks)

        assert post_mock.like_count == 10
        assert update_count[0] == 10


class TestCommentTreeConcurrency:
    def test_nested_comment_race(self):
        comments = {}

        async def add_comment(comment_id, parent_id):
            await asyncio.sleep(0.001)
            comments[comment_id] = {"id": comment_id, "parent_id": parent_id}

        async def simulate():
            tasks = [
                add_comment(1, None),
                add_comment(2, 1),
                add_comment(3, 1),
                add_comment(4, 2),
                add_comment(5, 3),
            ]
            await asyncio.gather(*tasks)
            return comments

        result = asyncio.get_event_loop().run_until_complete(simulate())

        assert len(result) == 5
        assert result[2]["parent_id"] == 1
        assert result[4]["parent_id"] == 3


class TestSearchVectorConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_post_creation(self):
        posts = []

        async def create_post(post_id):
            post = MagicMock()
            post.id = post_id
            post.title = f"Post {post_id}"
            post.content = f"Content {post_id}"
            post.search_vector = f"post {post_id} content {post_id}"
            posts.append(post)
            return post

        async def simulate():
            tasks = [create_post(i) for i in range(100)]
            return await asyncio.gather(*tasks)

        results = asyncio.get_event_loop().run_until_complete(simulate())

        assert len(results) == 100
        assert len(posts) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
