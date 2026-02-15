import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from app.services.recommendation.api import (
    get_personalized_recommendations_request,
    get_onboarding_survey_request,
    complete_onboarding_request,
    check_should_onboarding_request,
    get_enhanced_recommendations_request,
    record_interaction_request,
    get_recommendation_weights_request,
    recommend_lawyers_request,
    recommend_forum_posts_request,
    recommend_news_request,
    recommend_similar_users_content_request,
)
from app.schemas.recommendation import InteractionRequest, OnboardingAnswer

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 123
    return user

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.mark.asyncio
async def test_get_personalized_recommendations_request(mock_user, mock_db):
    mock_lawyer = {
        "lawyer_id": 1,
        "lawyer_name": "Test Lawyer",
        "rating": 4.5,
        "review_count": 10,
        "consultation_count": 50,
        "is_verified": True,
        "match_score": 0.9
    }
    
    mock_post = {
        "post_id": 1,
        "title": "Test Post",
        "author_id": 2,
        "author_name": "Author",
        "view_count": 100,
        "like_count": 10,
        "comment_count": 5,
        "created_at": datetime.now(timezone.utc),
        "match_score": 0.8
    }
    
    mock_news = {
        "news_id": 1,
        "title": "Test News",
        "view_count": 50,
        "created_at": datetime.now(timezone.utc),
        "match_score": 0.7
    }

    mock_data = {
        "lawyers": [mock_lawyer],
        "posts": [mock_post],
        "news": [mock_news],
        "similar_users_content": []
    }
    with patch("app.services.recommendation.api.RecommendationService.get_personalized_recommendations", new_callable=AsyncMock) as mock_method:
        mock_method.return_value = mock_data
        
        response = await get_personalized_recommendations_request(
            current_user=mock_user,
            db=mock_db,
            lawyer_limit=5
        )
        
        # Verify structure matches PersonalizedRecommendationsResponse
        assert response.user_id == 123
        assert len(response.lawyers) == 1
        assert response.lawyers[0].lawyer_id == 1
        assert len(response.posts) == 1
        assert response.posts[0].post_id == 1
        assert len(response.news) == 1
        assert response.news[0].news_id == 1
        mock_method.assert_called_once_with(
            db=mock_db,
            user_id=123,
            lawyer_limit=5,
            post_limit=5,
            news_limit=5
        )

@pytest.mark.asyncio
async def test_get_onboarding_survey_request():
    mock_service = MagicMock()
    mock_service.get_onboarding_survey.return_value = ["question1"]
    
    with patch("app.services.recommendation.api.get_cold_start_service", return_value=mock_service):
        result = await get_onboarding_survey_request()
        assert result["survey"] == ["question1"]

@pytest.mark.asyncio
async def test_complete_onboarding_request(mock_user):
    mock_service = MagicMock()
    mock_profile = MagicMock()
    mock_profile.interest_tags = ["tag1"]
    mock_profile.interest_weights = {"tag1": 1.0}
    mock_profile.preferred_content_types = ["text"]
    mock_profile.usage_frequency = "daily"
    mock_profile.onboarding_completed = True
    
    mock_service.process_onboarding_answers.return_value = mock_profile
    
    answers = OnboardingAnswer(answers={"q1": "a1"})
    
    with patch("app.services.recommendation.api.get_cold_start_service", return_value=mock_service):
        result = await complete_onboarding_request(
            body=answers,
            current_user=mock_user
        )
        assert result["success"] is True
        assert result["profile"]["interest_tags"] == ["tag1"]
        mock_service.process_onboarding_answers.assert_called_once_with(
            user_id=123,
            answers={"q1": "a1"}
        )

@pytest.mark.asyncio
async def test_check_should_onboarding_request(mock_user):
    mock_service = MagicMock()
    mock_service.should_show_onboarding.return_value = True
    
    with patch("app.services.recommendation.api.get_cold_start_service", return_value=mock_service):
        result = await check_should_onboarding_request(current_user=mock_user)
        assert result["should_show"] is True
        mock_service.should_show_onboarding.assert_called_once_with(123)

@pytest.mark.asyncio
async def test_get_enhanced_recommendations_request(mock_user):
    mock_service = MagicMock()
    mock_result = MagicMock()
    mock_item = MagicMock()
    mock_item.item_id = 999
    mock_item.item_type = "news"
    mock_item.title = "Test News"
    mock_item.score = 0.95
    mock_item.reason = "relevant"
    mock_item.metadata = {}
    
    mock_result.items = [mock_item]
    mock_result.total = 1
    mock_result.source = "hybrid"
    
    mock_service.get_recommendations = AsyncMock(return_value=mock_result)
    
    with patch("app.services.recommendation.api.get_enhanced_recommendation_service", return_value=mock_service):
        result = await get_enhanced_recommendations_request(
            current_user=mock_user,
            recommendation_type="hybrid",
            limit=10
        )
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == 999
        assert result["total"] == 1
        mock_service.get_recommendations.assert_called_once_with(
            user_id=123,
            recommendation_type="hybrid",
            limit=10
        )

@pytest.mark.asyncio
async def test_record_interaction_request(mock_user):
    payload = InteractionRequest(
        content_id="1",
        content_type="article",
        tags=["tech"],
        interaction_type="click",
        weight=1.0
    )
    
    with patch("app.services.recommendation.api.record_user_interaction") as mock_record:
        result = await record_interaction_request(
            payload=payload,
            current_user=mock_user
        )
        assert result["success"] is True
        mock_record.assert_called_once_with(
            user_id=123,
            content_id="1",
            content_type="article",
            tags=["tech"],
            interaction_type="click",
            weight=1.0
        )

@pytest.mark.asyncio
async def test_get_recommendation_weights_request(mock_user):
    mock_service = MagicMock()
    mock_service.get_recommendation_weights.return_value = {"tag1": 0.5}
    
    with patch("app.services.recommendation.api.get_cold_start_service", return_value=mock_service):
        result = await get_recommendation_weights_request(current_user=mock_user)
        assert result["weights"] == {"tag1": 0.5}

@pytest.mark.asyncio
async def test_recommend_lawyers_request(mock_user, mock_db):
    with patch("app.services.recommendation.api.RecommendationService.recommend_lawyers", new_callable=AsyncMock) as mock_method:
        mock_method.return_value = [{"id": 1}]
        
        result = await recommend_lawyers_request(
            current_user=mock_user,
            db=mock_db,
            limit=10
        )
        assert result["lawyers"] == [{"id": 1}]
        mock_method.assert_called_once_with(
            db=mock_db,
            user_id=123,
            limit=10
        )

@pytest.mark.asyncio
async def test_recommend_forum_posts_request(mock_user, mock_db):
    with patch("app.services.recommendation.api.RecommendationService.recommend_forum_posts", new_callable=AsyncMock) as mock_method:
        mock_method.return_value = [{"id": 2}]
        
        result = await recommend_forum_posts_request(
            current_user=mock_user,
            db=mock_db,
            limit=10
        )
        assert result["posts"] == [{"id": 2}]

@pytest.mark.asyncio
async def test_recommend_news_request(mock_user, mock_db):
    with patch("app.services.recommendation.api.RecommendationService.recommend_news", new_callable=AsyncMock) as mock_method:
        mock_method.return_value = [{"id": 3}]
        
        result = await recommend_news_request(
            current_user=mock_user,
            db=mock_db,
            limit=10
        )
        assert result["news"] == [{"id": 3}]

@pytest.mark.asyncio
async def test_recommend_similar_users_content_request(mock_user, mock_db):
    with patch("app.services.recommendation.api.RecommendationService.recommend_similar_users_content", new_callable=AsyncMock) as mock_method:
        mock_method.return_value = [{"id": 4}]
        
        result = await recommend_similar_users_content_request(
            current_user=mock_user,
            db=mock_db,
            limit=10
        )
        assert result["content"] == [{"id": 4}]
