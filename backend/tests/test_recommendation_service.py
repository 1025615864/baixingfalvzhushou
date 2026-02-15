"""推荐服务测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.recommendation_service import (
    RecommendationService,
    recommendation_service,
    _generate_lawyer_reason,
    _generate_post_reason,
    _generate_news_reason,
)


class TestRecommendationHelpers:
    """推荐服务辅助函数测试类"""

    def test_generate_lawyer_reason_high_rating(self):
        """测试生成律师推荐理由（高评分）"""
        mock_lawyer = MagicMock()
        mock_lawyer.rating = 4.8
        mock_lawyer.experience_years = 12
        mock_lawyer.review_count = 100
        mock_lawyer.specialties = "婚姻家庭,劳动纠纷"

        reason = _generate_lawyer_reason(mock_lawyer, ["婚姻家庭"], 0.9)

        assert "评分高" in reason or "资深律师" in reason

    def test_generate_lawyer_reason_experience(self):
        """测试生成律师推荐理由（经验丰富）"""
        mock_lawyer = MagicMock()
        mock_lawyer.rating = 4.2
        mock_lawyer.experience_years = 7
        mock_lawyer.review_count = 30
        mock_lawyer.specialties = "劳动纠纷,交通事故"

        reason = _generate_lawyer_reason(mock_lawyer, ["劳动纠纷"], 0.8)

        assert "经验丰富" in reason or "擅长" in reason

    def test_generate_lawyer_reason_interest_match(self):
        """测试生成律师推荐理由（兴趣匹配）"""
        mock_lawyer = MagicMock()
        mock_lawyer.rating = 4.5
        mock_lawyer.experience_years = 5
        mock_lawyer.review_count = 20
        mock_lawyer.specialties = "婚姻家庭,离婚财产分割"

        reason = _generate_lawyer_reason(mock_lawyer, ["婚姻家庭"], 0.85)

        assert "擅长" in reason

    def test_generate_lawyer_reason_default(self):
        """测试生成律师推荐理由（默认）"""
        mock_lawyer = MagicMock()
        mock_lawyer.rating = 3.8
        mock_lawyer.experience_years = 2
        mock_lawyer.review_count = 5
        mock_lawyer.specialties = "法律咨询"

        reason = _generate_lawyer_reason(mock_lawyer, [], 0.5)

        assert reason == "为您推荐"

    def test_generate_post_reason_hot(self):
        """测试生成帖子推荐理由（热门）"""
        mock_post = MagicMock()
        mock_post.title = "法律知识分享"
        mock_post.content = "详细的法律知识讲解"
        mock_post.view_count = 2000
        mock_post.like_count = 100

        reason = _generate_post_reason(mock_post, ["法律"], 0.9)

        assert "热门帖子" in reason or "高赞内容" in reason

    def test_generate_post_reason_interest(self):
        """测试生成帖子推荐理由（兴趣匹配）"""
        mock_post = MagicMock()
        mock_post.title = "劳动合同法解读"
        mock_post.content = "详细解读劳动合同法"
        mock_post.view_count = 300
        mock_post.like_count = 20

        reason = _generate_post_reason(mock_post, ["劳动"], 0.7)

        assert "涉及" in reason or "热门帖子" in reason

    def test_generate_news_reason_popular(self):
        """测试生成新闻推荐理由（热门）"""
        mock_news = MagicMock()
        mock_news.title = "最新法律法规"
        mock_news.content = "法律法规新变化"
        mock_news.view_count = 1500

        reason = _generate_news_reason(mock_news, ["法律"], 0.85)

        assert "热门新闻" in reason or "阅读量高" in reason

    def test_generate_news_reason_interest(self):
        """测试生成新闻推荐理由（兴趣匹配）"""
        mock_news = MagicMock()
        mock_news.title = "劳动合同法修订"
        mock_news.content = "劳动合同法相关修订内容"
        mock_news.view_count = 400

        reason = _generate_news_reason(mock_news, ["劳动"], 0.75)

        assert "关于" in reason or "热门新闻" in reason

    def test_generate_news_reason_default(self):
        """测试生成新闻推荐理由（默认）"""
        mock_news = MagicMock()
        mock_news.title = "一般新闻"
        mock_news.content = "新闻内容"
        mock_news.view_count = 50

        reason = _generate_news_reason(mock_news, [], 0.5)

        assert reason == "最新资讯"


class TestRecommendationService:
    """推荐服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.mark.asyncio
    async def test_recommend_lawyers_no_interests(self, mock_db):
        """测试推荐律师（无兴趣标签）"""
        mock_lawyer = MagicMock()
        mock_lawyer.id = 1
        mock_lawyer.rating = 4.5
        mock_lawyer.review_count = 50
        mock_lawyer.experience_years = 10
        mock_lawyer.specialties = "婚姻家庭"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_lawyer]
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.recommendation_service.user_interest_service') as mock_interest_service:
            mock_interest_service.get_user_interest_tags = AsyncMock(return_value=[])

            result = await RecommendationService.recommend_lawyers(mock_db, user_id=1, limit=10)

            assert len(result) > 0
            assert "reason" in result[0]

    @pytest.mark.asyncio
    async def test_recommend_lawyers_with_interests(self, mock_db):
        """测试推荐律师（有兴趣标签）"""
        mock_lawyer = MagicMock()
        mock_lawyer.id = 1
        mock_lawyer.rating = 4.5
        mock_lawyer.review_count = 50
        mock_lawyer.experience_years = 10
        mock_lawyer.specialties = "婚姻家庭,劳动纠纷"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_lawyer]
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.recommendation_service.user_interest_service') as mock_interest_service:
            mock_interest_service.get_user_interest_tags = AsyncMock(return_value=["婚姻家庭"])

            result = await RecommendationService.recommend_lawyers(mock_db, user_id=1, limit=10)

            assert len(result) > 0
            assert "reason" in result[0]

    @pytest.mark.asyncio
    async def test_recommend_posts(self, mock_db):
        """测试推荐帖子"""
        mock_post = MagicMock()
        mock_post.id = 1
        mock_post.title = "法律知识分享"
        mock_post.view_count = 500
        mock_post.like_count = 30

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_post]
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.recommendation_service.user_interest_service') as mock_interest_service:
            mock_interest_service.get_user_interest_tags = AsyncMock(return_value=["法律"])

            result = await RecommendationService.recommend_posts(mock_db, user_id=1, limit=10)

            assert len(result) > 0
            assert "reason" in result[0]

    @pytest.mark.asyncio
    async def test_recommend_news(self, mock_db):
        """测试推荐新闻"""
        mock_news = MagicMock()
        mock_news.id = 1
        mock_news.title = "最新法律法规"
        mock_news.view_count = 600

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_news]
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.recommendation_service.user_interest_service') as mock_interest_service:
            mock_interest_service.get_user_interest_tags = AsyncMock(return_value=["法律"])

            result = await RecommendationService.recommend_news(mock_db, user_id=1, limit=10)

            assert len(result) > 0
            assert "reason" in result[0]

    @pytest.mark.asyncio
    async def test_recommend_lawyers_empty(self, mock_db):
        """测试推荐律师（空结果）"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.recommendation_service.user_interest_service') as mock_interest_service:
            mock_interest_service.get_user_interest_tags = AsyncMock(return_value=[])

            result = await RecommendationService.recommend_lawyers(mock_db, user_id=1, limit=10)

            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_recommend_lawyers_limit(self, mock_db):
        """测试推荐律师（限制数量）"""
        mock_lawyers = [MagicMock(id=i, rating=4.5, review_count=50, 
                                experience_years=10, specialties="婚姻家庭") 
                       for i in range(10)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_lawyers
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.recommendation_service.user_interest_service') as mock_interest_service:
            mock_interest_service.get_user_interest_tags = AsyncMock(return_value=[])

            result = await RecommendationService.recommend_lawyers(mock_db, user_id=1, limit=5)

            assert len(result) == 5


class TestRecommendationServiceSingleton:
    """推荐服务单例测试类"""

    def test_singleton(self):
        """测试服务单例"""
        service1 = recommendation_service
        service2 = recommendation_service
        assert service1 is service2
