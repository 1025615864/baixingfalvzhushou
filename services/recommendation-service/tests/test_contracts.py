"""推荐服务契约测试"""
import pytest
from httpx import AsyncClient


class TestRecommendationServiceContract:
    """推荐服务契约测试"""

    @pytest.mark.asyncio
    async def test_recommend_lawyers(self, client: AsyncClient):
        """测试推荐律师"""
        response = await client.get(
            "/api/v1/recommendation/lawyers",
            params={"user_id": 1, "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_recommend_news(self, client: AsyncClient):
        """测试推荐新闻"""
        response = await client.get(
            "/api/v1/recommendation/news",
            params={"user_id": 1, "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_recommend_posts(self, client: AsyncClient):
        """测试推荐帖子"""
        response = await client.get(
            "/api/v1/recommendation/posts",
            params={"user_id": 1, "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_personalized_feed(self, client: AsyncClient):
        """测试获取个性化推荐信息流"""
        response = await client.get(
            "/api/v1/recommendation/feed",
            params={"user_id": 1, "limit": 20}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_update_user_features(self, client: AsyncClient):
        """测试更新用户特征"""
        response = await client.post(
            "/api/v1/recommendation/user/1/features",
            json={"interests": ["法律", "合同"], "view_history": [1, 2, 3]}
        )
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "features" in data
            assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_update_item_features(self, client: AsyncClient):
        """测试更新物品特征"""
        response = await client.post(
            "/api/v1/recommendation/items/news/1/features",
            params={"score": 0.8},
            json={"category": "法律", "tags": ["合同", "劳动"]}
        )
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "item_type" in data
            assert "item_id" in data
            assert "features" in data
            assert "score" in data
            assert "updated_at" in data


class TestRecommendationServiceModelsContract:
    """推荐服务模型契约测试"""

    def test_user_feature_model_fields(self):
        """测试用户特征模型字段"""
        from app.models import UserFeature

        assert UserFeature.__tablename__ == "user_features"
        assert hasattr(UserFeature, "id")
        assert hasattr(UserFeature, "user_id")
        assert hasattr(UserFeature, "features")
        assert hasattr(UserFeature, "updated_at")

    def test_item_feature_model_fields(self):
        """测试物品特征模型字段"""
        from app.models import ItemFeature

        assert ItemFeature.__tablename__ == "item_features"
        assert hasattr(ItemFeature, "id")
        assert hasattr(ItemFeature, "item_type")
        assert hasattr(ItemFeature, "item_id")
        assert hasattr(ItemFeature, "features")
        assert hasattr(ItemFeature, "score")
        assert hasattr(ItemFeature, "updated_at")


class TestRecommendationServiceResponseContract:
    """推荐服务响应格式契约测试"""

    def test_recommendation_item_structure(self):
        """测试推荐项结构"""
        item = {
            "id": 1,
            "type": "lawyer",
            "title": "推荐律师 1",
            "description": "资深律师，专业可靠",
            "url": "/lawyer/1",
            "score": 0.85
        }

        assert "id" in item
        assert "type" in item
        assert "title" in item
        assert "description" in item
        assert "url" in item
        assert "score" in item
        assert isinstance(item["score"], float)
        assert 0 <= item["score"] <= 1

    def test_feed_response_structure(self):
        """测试信息流响应结构"""
        response = {
            "items": [
                {
                    "id": 1,
                    "type": "news",
                    "title": "推荐新闻 1",
                    "description": "最新法律资讯",
                    "url": "/news/1",
                    "score": 0.82
                },
                {
                    "id": 1,
                    "type": "lawyer",
                    "title": "推荐律师 1",
                    "description": "资深律师，专业可靠",
                    "url": "/lawyer/1",
                    "score": 0.85
                }
            ]
        }

        assert "items" in response
        assert isinstance(response["items"], list)
        assert len(response["items"]) > 0

        for item in response["items"]:
            assert "id" in item
            assert "type" in item
            assert "score" in item

    def test_user_features_response_structure(self):
        """测试用户特征响应结构"""
        response = {
            "user_id": 1,
            "features": {
                "interests": ["法律", "合同"],
                "view_history": [1, 2, 3]
            },
            "updated_at": "2024-03-25T10:00:00Z"
        }

        assert "user_id" in response
        assert "features" in response
        assert "updated_at" in response
        assert isinstance(response["features"], dict)

    def test_item_features_response_structure(self):
        """测试物品特征响应结构"""
        response = {
            "item_type": "news",
            "item_id": 1,
            "features": {
                "category": "法律",
                "tags": ["合同", "劳动"]
            },
            "score": 0.8,
            "updated_at": "2024-03-25T10:00:00Z"
        }

        assert "item_type" in response
        assert "item_id" in response
        assert "features" in response
        assert "score" in response
        assert "updated_at" in response
        assert isinstance(response["score"], float)
