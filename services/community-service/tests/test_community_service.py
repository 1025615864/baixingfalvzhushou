"""社区服务单元测试"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.post_service import PostService
from app.services.comment_service import CommentService
from app.services.moderation_service import ModerationService
from app.middleware.auth import AuthUser
from app.utils.scoring import calculate_hot_score, recalculate_post_hot_score


class TestHotScoreCalculation:
    def test_basic_score(self):
        score = calculate_hot_score(
            likes=10,
            comments=5,
            views=1000,
            favorites=2
        )
        assert score > 0

    def test_lawyer_bonus(self):
        regular_score = calculate_hot_score(
            likes=10,
            comments=5,
            views=1000,
            favorites=2,
            is_lawyer_post=False
        )
        lawyer_score = calculate_hot_score(
            likes=10,
            comments=5,
            views=1000,
            favorites=2,
            is_lawyer_post=True
        )
        assert lawyer_score > regular_score
        assert lawyer_score == regular_score * 1.5

    def test_time_decay(self):
        old_post_score = calculate_hot_score(
            likes=100,
            comments=50,
            views=10000,
            favorites=20,
            is_lawyer_post=False,
            created_at=datetime(2020, 1, 1)
        )
        new_post_score = calculate_hot_score(
            likes=100,
            comments=50,
            views=10000,
            favorites=20,
            is_lawyer_post=False,
            created_at=datetime.now(timezone.utc)
        )
        assert new_post_score > old_post_score


class TestModerationService:
    def setup_method(self):
        self.service = ModerationService(ai_client_instance=None)

    def test_sensitive_word_detection(self):
        result = self.service.sensitive_filter.check("这个内容包含毒品和赌博")
        assert result[0] is True
        assert len(result[1]) > 0

    def test_clean_content(self):
        result = self.service.sensitive_filter.check("这是一个正常的法律咨询帖子")
        assert result[0] is False
        assert len(result[1]) == 0

    def test_contact_info_detection(self):
        has_phone = self.service.check_contact_info("联系电话：13812345678")
        assert has_phone is True

        has_wechat = self.service.check_contact_info("微信：lawyer123")
        assert has_wechat is True

        has_email = self.service.check_contact_info("邮箱：test@example.com")
        assert has_email is True

        clean = self.service.check_contact_info("这是一个法律问题")
        assert clean is False


class TestAuthUser:
    def test_auth_user_creation(self):
        user = AuthUser(
            id=1,
            role="user",
            nickname="测试用户",
            avatar="http://example.com/avatar.png",
            is_lawyer=False
        )
        assert user.id == 1
        assert user.role == "user"
        assert user.is_lawyer is False

    def test_lawyer_user(self):
        user = AuthUser(
            id=2,
            role="lawyer",
            nickname="律师张三",
            is_lawyer=True
        )
        assert user.is_lawyer is True
        assert user.role == "lawyer"


class TestSensitiveWordFilter:
    def setup_method(self):
        from app.utils.sensitive_words import SensitiveWordFilter
        self.filter = SensitiveWordFilter()

    def test_block_sensitive_words(self):
        blocked, words = self.filter.check("这个网站有赌博和毒品内容")
        assert blocked is True
        assert len(words) > 0

    def test_filter_replacement(self):
        result = self.filter.filter("包含毒品的内容", replace_char="#")
        assert "毒品" not in result
        assert "#" in result


class TestPostModel:
    def test_hot_score_with_mock_post(self):
        mock_post = MagicMock()
        mock_post.like_count = 10
        mock_post.comment_count = 5
        mock_post.view_count = 1000
        mock_post.favorite_count = 2
        mock_post.is_lawyer = True
        mock_post.created_at = datetime.now(timezone.utc)

        score = recalculate_post_hot_score(mock_post)
        assert score > 0


class TestCommentFloorNumber:
    def test_floor_calculation_logic(self):
        existing_floors = [1, 2, 3, 5]
        next_floor = max(existing_floors) + 1
        assert next_floor == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
