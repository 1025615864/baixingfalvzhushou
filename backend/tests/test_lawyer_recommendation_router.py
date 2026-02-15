"""Tests for lawyer_recommendation router"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.routers.lawyer_recommendation import router


class TestRecommendLawyers:
    """Test recommend_lawyers endpoint"""

    @pytest.mark.asyncio
    async def test_recommend_lawyers_success(self):
        """Test successful lawyer recommendation"""
        db = AsyncMock()
        current_user = MagicMock()
        current_user.id = 1

        mock_results = [
            MagicMock(
                lawyer_id=1,
                lawyer_name="张律师",
                specialties=["劳动纠纷", "合同纠纷"],
                rating=4.5,
                completed_count=100,
                match_score=0.9,
                overall_score=85,
                match_reasons=["专长匹配", "评分高"],
            )
        ]

        with patch('app.routers.lawyer_recommendation.get_lawyer_matching_service') as mock_get_service, \
             patch('app.routers.lawyer_recommendation.get_db', return_value=db):
            mock_service = AsyncMock()
            mock_service.recommend_lawyers.return_value = mock_results
            mock_get_service.return_value = mock_service

            response = await router.routes[0].endpoint(db, current_user, "劳动纠纷", limit=10)

            assert response["query"] == "劳动纠纷"
            assert response["count"] == 1
            assert response["lawyers"][0]["lawyer_id"] == 1
            assert response["lawyers"][0]["lawyer_name"] == "张律师"

    @pytest.mark.asyncio
    async def test_recommend_lawyers_db_none(self):
        """Test lawyer recommendation with None database"""
        db = None
        current_user = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await router.routes[0].endpoint(db, current_user, "劳动纠纷")

        assert exc_info.value.status_code == 500
        assert "数据库连接失败" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_recommend_lawyers_exception(self):
        """Test lawyer recommendation with exception"""
        db = AsyncMock()
        current_user = MagicMock()

        with patch('app.routers.lawyer_recommendation.get_lawyer_matching_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.recommend_lawyers.side_effect = Exception("Service error")
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await router.routes[0].endpoint(db, current_user, "劳动纠纷")

            assert exc_info.value.status_code == 500
            assert "律师推荐失败" in exc_info.value.detail


class TestRecommendLawyersByKeywords:
    """Test recommend_lawyers_by_keywords endpoint"""

    @pytest.mark.asyncio
    async def test_recommend_by_keywords_success(self):
        """Test successful lawyer recommendation by keywords"""
        db = AsyncMock()
        current_user = MagicMock()
        current_user.id = 1

        mock_results = [
            MagicMock(
                lawyer_id=1,
                lawyer_name="李律师",
                specialties=["婚姻家庭"],
                rating=4.8,
                completed_count=150,
                match_score=0.95,
                overall_score=90,
                match_reasons=["专长匹配", "完成单数高"],
            )
        ]

        with patch('app.routers.lawyer_recommendation.get_lawyer_matching_service') as mock_get_service, \
             patch('app.routers.lawyer_recommendation.get_db', return_value=db):
            mock_service = AsyncMock()
            mock_service.match_lawyers_by_keywords.return_value = mock_results
            mock_get_service.return_value = mock_service

            response = await router.routes[1].endpoint(
                db, current_user, keywords=["劳动纠纷"], domains=[], limit=10
            )

            assert response["keywords"] == ["劳动纠纷"]
            assert response["domains"] == []
            assert response["count"] == 1
            assert response["lawyers"][0]["lawyer_id"] == 1
            assert response["lawyers"][0]["lawyer_name"] == "李律师"

    @pytest.mark.asyncio
    async def test_recommend_by_keywords_empty_keywords_and_domains(self):
        """Test lawyer recommendation with empty keywords and domains"""
        db = AsyncMock()
        current_user = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await router.routes[1].endpoint(
                db, current_user, keywords=[], domains=[], limit=10
            )

        assert exc_info.value.status_code == 400
        assert "关键词和领域不能同时为空" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_recommend_by_keywords_db_none(self):
        """Test lawyer recommendation by keywords with None database"""
        db = None
        current_user = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await router.routes[1].endpoint(
                db, current_user, keywords=["劳动纠纷"], domains=[], limit=10
            )

        assert exc_info.value.status_code == 500
        assert "数据库连接失败" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_recommend_by_keywords_exception(self):
        """Test lawyer recommendation by keywords with exception"""
        db = AsyncMock()
        current_user = MagicMock()

        with patch('app.routers.lawyer_recommendation.get_lawyer_matching_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.match_lawyers_by_keywords.side_effect = Exception("Service error")
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await router.routes[1].endpoint(
                    db, current_user, keywords=["劳动纠纷"], domains=[], limit=10
                )

            assert exc_info.value.status_code == 500
            assert "律师推荐失败" in exc_info.value.detail
