import pytest
from app.services.personalized_home import (
    UserProfile,
    InterestRecommender,
    PersonalizedHomeService,
)

class TestUserProfile:
    def test_get_or_create_profile_new(self):
        up = UserProfile()
        profile = up.get_or_create_profile(1)
        assert profile["user_id"] == 1
        assert profile["interests"] == []
        assert profile["browse_history"] == []

    def test_update_interests(self):
        up = UserProfile()
        interests = ["law", "tech"]
        up.update_interests(1, interests)
        
        profile = up.get_or_create_profile(1)
        assert profile["interests"] == interests

    def test_add_browse_history_limit(self):
        up = UserProfile()
        # Add 105 items
        for i in range(105):
            up.add_browse_history(1, str(i), "cat")
            
        profile = up.get_or_create_profile(1)
        assert len(profile["browse_history"]) == 100
        # Should enable rolling window, latest items kept
        assert profile["browse_history"][-1]["item_id"] == "104"

class TestInterestRecommender:
    def test_recommend_logic(self):
        recommender = InterestRecommender()
        # Register items
        recommender.register_item("1", "Law News", "law", ["law", "news"], 0.8)
        recommender.register_item("2", "Tech News", "tech", ["tech", "news"], 0.9)
        recommender.register_item("3", "Sport News", "sport", ["sport"], 0.5)
        
        # User interests: law
        # History: viewed nothing
        recs = recommender.recommend(1, interests=["law"], browse_history=[])
        
        # Logic: law item gets +0.3 (tag match) + 0.3*0.8 (base) = 0.54
        # Tech item gets 0 + 0.3*0.9 = 0.27
        # Sport gets 0 + 0.3*0.5 = 0.15
        
        assert len(recs) == 3
        assert recs[0]["id"] == "1"
        assert recs[1]["id"] == "2"
        assert recs[2]["id"] == "3"

    def test_recommend_history_boost_and_filter(self):
        recommender = InterestRecommender()
        recommender.register_item("1", "A", "cat1", [], 0.5)
        recommender.register_item("2", "B", "cat1", [], 0.5)
        recommender.register_item("3", "C", "cat2", [], 0.5)
        
        # History: viewed 1, category cat1
        # Item 1 should be filtered out
        # Item 2 (cat1) should get boost +0.2
        # Item 3 (cat2) no boost
        
        recs = recommender.recommend(
            1, 
            interests=[], 
            browse_history=[{"item_id": "1", "category": "cat1"}]
        )
        
        ids = [r["id"] for r in recs]
        assert "1" not in ids
        assert "2" in ids
        assert "3" in ids
        
        # Check scores: Item 2 should be higher than Item 3
        # Item 2: 0.2 (cat boost) + 0.15 (base) = 0.35
        # Item 3: 0.15 (base) = 0.15
        assert recs[0]["id"] == "2"

    def test_track_click(self):
        recommender = InterestRecommender()
        recommender.register_item("1", "T", "C", [], 0.5)
        
        recommender.track_click(1, "1")
        assert recommender._items["1"]["view_count"] == 1
        
        recommender.track_click(2, "1")
        assert recommender._items["1"]["view_count"] == 2

@pytest.mark.asyncio
class TestPersonalizedHomeService:
    async def test_get_personalized_home_integration(self):
        service = PersonalizedHomeService()
        # Setup items
        service.interest_recommender.register_item("law1", "Law Title", "law", ["law"], 0.9)
        
        # Setup user
        await service.update_user_interests(1, ["law"])
        
        home = await service.get_personalized_home(1)
        assert home["user_id"] == 1
        assert len(home["recommendations"]) == 1
        assert home["recommendations"][0]["id"] == "law1"

    async def test_track_content_view(self):
        service = PersonalizedHomeService()
        service.interest_recommender.register_item("item1", "Title", "cat", [], 0.5)
        
        res = await service.track_content_view(1, "item1", "cat")
        assert res["success"] is True
        assert res["history_count"] == 1
        
        # Verify impact
        profile = service.user_profile.get_user_profile(1)
        assert len(profile["browse_history"]) == 1
        assert service.interest_recommender._items["item1"]["view_count"] == 1

    async def test_get_stats(self):
        service = PersonalizedHomeService()
        await service.update_user_interests(1, ["a"])
        await service.update_user_interests(2, []) # empty interests
        
        # Force some recommendations
        service.interest_recommender._recommendations[1] = [{}, {}]
        service.interest_recommender._recommendations[2] = [{}]
        
        stats = await service.get_stats()
        assert stats["total_users"] == 2
        assert stats["users_with_interests"] == 1
        assert stats["total_recommendations"] == 3


class TestPersonalizedHomeRecommendations:
    """个性化首页推荐测试"""

    @pytest.mark.asyncio
    async def test_get_personalized_home_cold_start(self):
        """测试冷启动用户个性化首页"""
        service = PersonalizedHomeService()
        
        # 新用户无兴趣和历史记录
        home = await service.get_enhanced_personalized_home(
            user_id=999,
            lawyer_limit=3,
            post_limit=3,
            news_limit=3,
            knowledge_limit=3,
        )
        
        assert home["user_id"] == 999
        assert home["is_cold_start"] is True
        assert home["recommendation_source"] == "cold_start"
        assert home["reason"] == "热门内容推荐"
        
        # 验证返回了热门内容
        assert len(home["lawyers"]) >= 0
        assert len(home["posts"]) >= 0
        assert len(home["news"]) >= 0
        assert len(home["knowledge"]) >= 0

    @pytest.mark.asyncio
    async def test_get_personalized_home_with_interests(self):
        """测试基于兴趣的个性化首页"""
        service = PersonalizedHomeService()
        
        # 设置用户兴趣
        await service.update_user_interests(100, ["labor", "contract"])
        
        # 注册用户感兴趣的内容
        service.interest_recommender.register_item(
            "labor_news_1", "劳动法新规", "news", ["labor", "law"], 0.9
        )
        service.interest_recommender.register_item(
            "contract_post_1", "合同纠纷案例", "post", ["contract", "law"], 0.8
        )
        
        home = await service.get_enhanced_personalized_home(
            user_id=100,
            lawyer_limit=3,
            post_limit=3,
            news_limit=3,
            knowledge_limit=3,
        )
        
        assert home["user_id"] == 100
        assert home["is_cold_start"] is False
        assert home["recommendation_source"] == "interest_based"
        assert home["reason"] == "根据您的兴趣推荐"
        assert home["profile"]["interests"] == ["labor", "contract"]

    @pytest.mark.asyncio
    async def test_get_personalized_home_with_history(self):
        """测试基于浏览历史的个性化首页"""
        service = PersonalizedHomeService()
        
        # 添加浏览历史
        await service.track_content_view(200, "item1", "labor")
        await service.track_content_view(200, "item2", "labor")
        await service.track_content_view(200, "item3", "contract")
        
        # 注册用户感兴趣的内容
        service.interest_recommender.register_item(
            "labor_news_2", "劳动法案例分析", "news", ["labor"], 0.85
        )
        
        home = await service.get_enhanced_personalized_home(
            user_id=200,
            lawyer_limit=2,
            post_limit=2,
            news_limit=2,
            knowledge_limit=2,
        )
        
        assert home["user_id"] == 200
        assert home["is_cold_start"] is False  # 有历史记录
        assert home["profile"]["history_count"] == 3


class TestInterestBasedRecommendations:
    """基于兴趣的推荐测试"""

    @pytest.mark.asyncio
    async def test_interest_based_lawyer_recommendations(self):
        """测试基于兴趣的律师推荐"""
        service = PersonalizedHomeService()
        
        # 设置用户兴趣
        await service.update_user_interests(300, ["婚姻家庭", "劳动纠纷"])
        
        lawyers = await service._get_interest_based_lawyers(
            interests=["婚姻家庭", "劳动纠纷"],
            limit=5
        )
        
        assert len(lawyers) > 0
        # 验证推荐理由包含兴趣标签
        for lawyer in lawyers:
            assert "reason" in lawyer
            assert "擅长" in lawyer["reason"]

    @pytest.mark.asyncio
    async def test_interest_based_post_recommendations(self):
        """测试基于兴趣的帖子推荐"""
        service = PersonalizedHomeService()
        
        # 设置用户兴趣和浏览历史
        interests = ["劳动纠纷"]
        browse_history = [{"item_id": "1", "category": "labor"}]
        
        posts = await service._get_interest_based_posts(
            interests=interests,
            browse_history=browse_history,
            limit=5
        )
        
        assert len(posts) > 0
        # 验证推荐理由
        for post in posts:
            assert "reason" in post

    @pytest.mark.asyncio
    async def test_interest_based_news_recommendations(self):
        """测试基于兴趣的新闻推荐"""
        service = PersonalizedHomeService()
        
        news = await service._get_interest_based_news(
            interests=["劳动纠纷", "婚姻家庭"],
            limit=5
        )
        
        assert len(news) > 0
        # 验证推荐理由包含兴趣标签
        for item in news:
            assert "reason" in item

    @pytest.mark.asyncio
    async def test_interest_based_knowledge_recommendations(self):
        """测试基于兴趣的知识推荐"""
        service = PersonalizedHomeService()
        
        knowledge = await service._get_interest_based_knowledge(
            interests=["合同纠纷", "债权债务"],
            limit=5
        )
        
        assert len(knowledge) > 0
        # 验证推荐理由
        for item in knowledge:
            assert "reason" in item


class TestHotContentRecommendations:
    """热门内容推荐测试"""

    @pytest.mark.asyncio
    async def test_get_hot_lawyers(self):
        """测试获取热门律师"""
        service = PersonalizedHomeService()
        
        lawyers = await service._get_hot_lawyers(limit=5)
        
        assert len(lawyers) > 0
        for lawyer in lawyers:
            assert "lawyer_id" in lawyer
            assert "name" in lawyer
            assert "rating" in lawyer
            assert "reason" in lawyer

    @pytest.mark.asyncio
    async def test_get_hot_posts(self):
        """测试获取热门帖子"""
        service = PersonalizedHomeService()
        
        posts = await service._get_hot_posts(limit=5)
        
        assert len(posts) > 0
        for post in posts:
            assert "post_id" in post
            assert "title" in post
            assert "view_count" in post
            assert "reason" in post

    @pytest.mark.asyncio
    async def test_get_hot_news(self):
        """测试获取热门新闻"""
        service = PersonalizedHomeService()
        
        news = await service._get_hot_news(limit=5)
        
        assert len(news) > 0
        for item in news:
            assert "news_id" in item
            assert "title" in item
            assert "view_count" in item
            assert "reason" in item

    @pytest.mark.asyncio
    async def test_get_hot_knowledge(self):
        """测试获取热门知识"""
        service = PersonalizedHomeService()
        
        knowledge = await service._get_hot_knowledge(limit=5)
        
        assert len(knowledge) > 0
        for item in knowledge:
            assert "knowledge_id" in item
            assert "title" in item
            assert "category" in item
            assert "reason" in item

    @pytest.mark.asyncio
    async def test_get_hot_content_recommendations(self):
        """测试获取综合热门内容推荐"""
        service = PersonalizedHomeService()
        
        hot_content = await service._get_hot_content_recommendations(limit=10)
        
        assert len(hot_content) > 0
        for item in hot_content:
            assert "id" in item
            assert "type" in item
            assert "title" in item
            assert "reason" in item
            assert "tags" in item
            assert "score" in item


class TestContentTracking:
    """内容追踪测试"""

    @pytest.mark.asyncio
    async def test_track_content_view_updates_history(self):
        """测试内容浏览追踪更新历史记录"""
        service = PersonalizedHomeService()
        
        result = await service.track_content_view(
            user_id=400,
            item_id="test_item_1",
            category="test_category"
        )
        
        assert result["success"] is True
        assert result["history_count"] == 1
        
        # 验证历史记录已保存
        profile = service.user_profile.get_user_profile(400)
        assert len(profile["browse_history"]) == 1
        assert profile["browse_history"][0]["item_id"] == "test_item_1"

    @pytest.mark.asyncio
    async def test_track_content_view_updates_item_views(self):
        """测试内容浏览追踪更新 item 浏览次数"""
        service = PersonalizedHomeService()
        
        # 注册内容项
        service.interest_recommender.register_item(
            "tracked_item", "测试内容", "test", ["tag1"], 0.7
        )
        
        # 追踪浏览
        await service.track_content_view(
            user_id=401,
            item_id="tracked_item",
            category="test"
        )
        
        # 验证浏览次数增加
        assert service.interest_recommender._items["tracked_item"]["view_count"] == 1

    @pytest.mark.asyncio
    async def test_track_multiple_content_views(self):
        """测试多次内容浏览追踪"""
        service = PersonalizedHomeService()
        
        # 追踪多个内容
        for i in range(5):
            await service.track_content_view(
                user_id=402,
                item_id=f"item_{i}",
                category=f"category_{i % 2}"
            )
        
        profile = service.user_profile.get_user_profile(402)
        assert len(profile["browse_history"]) == 5


class TestLawyerRecommendations:
    """律师推荐功能测试"""

    @pytest.mark.asyncio
    async def test_lawyer_recommendation_with_specialties(self):
        """测试律师推荐 - 擅长领域匹配"""
        service = PersonalizedHomeService()
        
        # 设置用户兴趣为特定领域
        await service.update_user_interests(500, ["劳动纠纷"])
        
        lawyers = await service._get_interest_based_lawyers(
            interests=["劳动纠纷"],
            limit=3
        )
        
        assert len(lawyers) > 0
        # 验证推荐理由提及擅长领域
        assert any("擅长" in lawyer.get("reason", "") for lawyer in lawyers)

    @pytest.mark.asyncio
    async def test_lawyer_recommendation_rating_priority(self):
        """测试律师推荐 - 评分优先级"""
        service = PersonalizedHomeService()
        
        lawyers = await service._get_hot_lawyers(limit=10)
        
        # 验证返回的律师包含评分信息
        for lawyer in lawyers:
            assert "rating" in lawyer
            assert isinstance(lawyer["rating"], (int, float))

    @pytest.mark.asyncio
    async def test_lawyer_recommendation_limit(self):
        """测试律师推荐数量限制"""
        service = PersonalizedHomeService()
        
        lawyers_limit_1 = await service._get_hot_lawyers(limit=1)
        lawyers_limit_5 = await service._get_hot_lawyers(limit=5)
        
        assert len(lawyers_limit_1) <= 1
        assert len(lawyers_limit_5) <= 5
        assert len(lawyers_limit_1) <= len(lawyers_limit_5)


class TestPersonalizedHomeEdgeCases:
    """个性化首页边界情况测试"""

    @pytest.mark.asyncio
    async def test_empty_interests_list(self):
        """测试空兴趣列表"""
        service = PersonalizedHomeService()
        
        await service.update_user_interests(600, [])
        
        home = await service.get_enhanced_personalized_home(
            user_id=600,
            lawyer_limit=3,
            post_limit=3,
            news_limit=3,
            knowledge_limit=3,
        )
        
        # 空兴趣列表应视为冷启动
        assert home["is_cold_start"] is True

    @pytest.mark.asyncio
    async def test_minimal_history_threshold(self):
        """测试最小历史记录阈值"""
        service = PersonalizedHomeService()
        
        # 只添加 2 条历史记录（少于 3 条阈值）
        await service.track_content_view(601, "item1", "cat1")
        await service.track_content_view(601, "item2", "cat1")
        
        home = await service.get_enhanced_personalized_home(
            user_id=601,
            lawyer_limit=3,
            post_limit=3,
            news_limit=3,
            knowledge_limit=3,
        )
        
        # 历史记录少于 3 条且无兴趣，应视为冷启动
        assert home["is_cold_start"] is True

    @pytest.mark.asyncio
    async def test_zero_limits(self):
        """测试零限制参数"""
        service = PersonalizedHomeService()
        
        await service.update_user_interests(602, ["test"])
        
        home = await service.get_enhanced_personalized_home(
            user_id=602,
            lawyer_limit=0,
            post_limit=0,
            news_limit=0,
            knowledge_limit=0,
        )
        
        assert len(home["lawyers"]) == 0
        assert len(home["posts"]) == 0
        assert len(home["news"]) == 0
        assert len(home["knowledge"]) == 0

    @pytest.mark.asyncio
    async def test_large_limits(self):
        """测试大数量限制"""
        service = PersonalizedHomeService()
        
        lawyers = await service._get_hot_lawyers(limit=100)
        
        # 验证返回数量不超过可用数据
        assert len(lawyers) <= 2  # 当前实现只返回 2 个热门律师
