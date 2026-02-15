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
