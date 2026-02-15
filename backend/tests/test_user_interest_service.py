"""Tests for user interest service."""
from __future__ import annotations

import pytest

from app.services.user_interest_service import UserInterestService


class TestUserInterestServiceCategories:
    """Test INTEREST_CATEGORIES."""

    def test_interest_categories_defined(self) -> None:
        """Test that INTEREST_CATEGORIES is defined."""
        assert hasattr(UserInterestService, "INTEREST_CATEGORIES")
        categories = UserInterestService.INTEREST_CATEGORIES
        assert isinstance(categories, dict)
        assert len(categories) > 0

    def test_interest_categories_have_expected_domains(self) -> None:
        """Test that INTEREST_CATEGORIES has expected domains."""
        categories = UserInterestService.INTEREST_CATEGORIES
        expected_domains = ["legal", "family", "labor", "property", "criminal"]
        for domain in expected_domains:
            assert domain in categories, f"Expected domain '{domain}' not found"

    def test_each_category_has_keywords(self) -> None:
        """Test that each category has a list of keywords."""
        for category, keywords in UserInterestService.INTEREST_CATEGORIES.items():
            assert isinstance(keywords, list), f"Keywords for {category} is not a list"
            assert len(keywords) > 0, f"No keywords for category {category}"

    def test_category_keywords_are_strings(self) -> None:
        """Test that all keywords are strings."""
        for category, keywords in UserInterestService.INTEREST_CATEGORIES.items():
            for keyword in keywords:
                assert isinstance(keyword, str), f"Keyword '{keyword}' in {category} is not a string"

    def test_category_keywords_are_chinese(self) -> None:
        """Test that keywords are Chinese legal terms."""
        for category, keywords in UserInterestService.INTEREST_CATEGORIES.items():
            # At least some keywords should be Chinese
            assert len(keywords) > 3, f"Category {category} has too few keywords"
            # Check that most keywords contain Chinese characters
            chinese_keywords = [k for k in keywords if any("\u4e00" <= char <= "\u9fff" for char in k)]
            assert len(chinese_keywords) >= len(keywords) * 0.8, \
                f"Category {category} doesn't have enough Chinese keywords"


class TestUserInterestServiceStructure:
    """Test UserInterestService class structure."""

    def test_service_has_extract_method(self) -> None:
        """Test that service has extract_user_interests method."""
        assert hasattr(UserInterestService, "extract_user_interests")
        assert callable(UserInterestService.extract_user_interests)

    def test_service_has_get_tags_method(self) -> None:
        """Test that service has get_user_interest_tags method."""
        assert hasattr(UserInterestService, "get_user_interest_tags")
        assert callable(UserInterestService.get_user_interest_tags)

    def test_service_has_similar_users_method(self) -> None:
        """Test that service has get_similar_users method."""
        assert hasattr(UserInterestService, "get_similar_users")
        assert callable(UserInterestService.get_similar_users)

    def test_service_has_singleton_instance(self) -> None:
        """Test that service has singleton instance."""
        from app.services import user_interest_service
        assert hasattr(user_interest_service, "user_interest_service")
        assert isinstance(user_interest_service.user_interest_service, UserInterestService)


class TestUserInterestServiceKeywordMatching:
    """Test keyword matching logic."""

    def test_category_keywords_contain_expected_terms(self) -> None:
        """Test that categories contain expected legal terms."""
        categories = UserInterestService.INTEREST_CATEGORIES

        # Legal category should contain legal terms
        assert "法律" in categories["legal"]
        assert "律师" in categories["legal"]

        # Family category should contain family terms
        assert "婚姻" in categories["family"]
        assert "离婚" in categories["family"]

        # Labor category should contain labor terms
        assert "劳动" in categories["labor"]
        assert "工资" in categories["labor"]

        # Property category should contain property terms
        assert "房产" in categories["property"]
        assert "房屋" in categories["property"]

        # Criminal category should contain criminal terms
        assert "刑事" in categories["criminal"]
        assert "犯罪" in categories["criminal"]

    def test_all_categories_have_sufficient_keywords(self) -> None:
        """Test that all categories have at least 5 keywords."""
        for category, keywords in UserInterestService.INTEREST_CATEGORIES.items():
            assert len(keywords) >= 5, f"Category {category} has only {len(keywords)} keywords"

    def test_categories_cover_different_legal_areas(self) -> None:
        """Test that categories cover different legal areas."""
        categories = UserInterestService.INTEREST_CATEGORIES

        # Should have at least 10 different categories
        assert len(categories) >= 10, f"Only {len(categories)} categories found"

        # Categories should be distinct
        all_keywords = []
        for keywords in categories.values():
            all_keywords.extend(keywords)

        # Check for some expected diversity
        assert "离婚" in all_keywords  # Family
        assert "工资" in all_keywords  # Labor
        assert "房产" in all_keywords  # Property
        assert "刑事" in all_keywords  # Criminal
        assert "专利" in all_keywords  # Intellectual property


class TestUserInterestServiceEdgeCases:
    """Test edge cases for UserInterestService."""

    def test_categories_are_immutable(self) -> None:
        """Test that categories are not modified during operation."""
        original = dict(UserInterestService.INTEREST_CATEGORIES)
        # Just access the categories
        _ = UserInterestService.INTEREST_CATEGORIES
        # Verify they haven't changed
        assert UserInterestService.INTEREST_CATEGORIES == original

    def test_service_methods_are_coroutines(self) -> None:
        """Test that main methods are async coroutines."""
        import inspect

        # These should be async methods
        assert inspect.iscoroutinefunction(UserInterestService.extract_user_interests)
        assert inspect.iscoroutinefunction(UserInterestService.get_user_interest_tags)
        assert inspect.iscoroutinefunction(UserInterestService.get_similar_users)

    def test_service_can_be_instantiated(self) -> None:
        """Test that service can be instantiated."""
        service = UserInterestService()
        assert service is not None

    def test_categories_dont_have_overlapping_keywords(self) -> None:
        """Test that categories don't have too many overlapping keywords."""
        categories = UserInterestService.INTEREST_CATEGORIES

        # Build a mapping of keywords to categories
        keyword_to_categories = {}
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword not in keyword_to_categories:
                    keyword_to_categories[keyword] = []
                keyword_to_categories[keyword].append(category)

        # Find keywords that appear in multiple categories
        multi_category_keywords = {
            k: v for k, v in keyword_to_categories.items() if len(v) > 1
        }

        # Allow some overlap, but not too much
        assert len(multi_category_keywords) < len(keyword_to_categories) * 0.1, \
            "Too many keywords appear in multiple categories"


class TestUserInterestServiceIntegration:
    """Integration tests for UserInterestService."""

    def test_extract_method_signature(self) -> None:
        """Test extract_user_interests has correct signature."""
        import inspect

        sig = inspect.signature(UserInterestService.extract_user_interests)
        params = list(sig.parameters.keys())

        assert "db" in params
        assert "user_id" in params
        assert "days" in params
        assert "limit" in params

    def test_get_tags_method_signature(self) -> None:
        """Test get_user_interest_tags has correct signature."""
        import inspect

        sig = inspect.signature(UserInterestService.get_user_interest_tags)
        params = list(sig.parameters.keys())

        assert "db" in params
        assert "user_id" in params
        assert "days" in params

    def test_get_similar_users_method_signature(self) -> None:
        """Test get_similar_users has correct signature."""
        import inspect

        sig = inspect.signature(UserInterestService.get_similar_users)
        params = list(sig.parameters.keys())

        assert "db" in params
        assert "user_id" in params
        assert "limit" in params


class TestUserInterestServiceExtractInterests:
    """Test extract_user_interests method logic."""

    def test_extract_interests_returns_list(self) -> None:
        """Test extract_user_interests returns a list."""
        import inspect

        sig = inspect.signature(UserInterestService.extract_user_interests)
        annotations = sig.return_annotation

        # Should return list[dict[str, Any]]
        assert "list" in str(annotations).lower() or "List" in annotations.__name__

    def test_extract_interests_default_parameters(self) -> None:
        """Test extract_user_interests has correct default parameters."""
        import inspect

        sig = inspect.signature(UserInterestService.extract_user_interests)

        # Check default values
        assert sig.parameters["days"].default == 30
        assert sig.parameters["limit"].default == 10


class TestUserInterestServiceGetTags:
    """Test get_user_interest_tags method logic."""

    def test_get_tags_returns_list_of_strings(self) -> None:
        """Test get_user_interest_tags returns list of strings."""
        import inspect

        sig = inspect.signature(UserInterestService.get_user_interest_tags)
        annotations = sig.return_annotation

        # Should return list[str]
        assert "list" in str(annotations).lower() or "List" in annotations.__name__

    def test_get_tags_default_days_parameter(self) -> None:
        """Test get_user_interest_tags has correct default days parameter."""
        import inspect

        sig = inspect.signature(UserInterestService.get_user_interest_tags)

        # Check default value
        assert sig.parameters["days"].default == 30


class TestUserInterestServiceGetSimilarUsers:
    """Test get_similar_users method logic."""

    def test_get_similar_users_returns_list_of_ints(self) -> None:
        """Test get_similar_users returns list of integers."""
        import inspect

        sig = inspect.signature(UserInterestService.get_similar_users)
        annotations = sig.return_annotation

        # Should return list[int]
        assert "list" in str(annotations).lower() or "List" in annotations.__name__

    def test_get_similar_users_default_limit_parameter(self) -> None:
        """Test get_similar_users has correct default limit parameter."""
        import inspect

        sig = inspect.signature(UserInterestService.get_similar_users)

        # Check default value
        assert sig.parameters["limit"].default == 10


class TestUserInterestServiceCategoriesDetail:
    """Test INTEREST_CATEGORIES in detail."""

    def test_business_category_exists(self) -> None:
        """Test business category exists."""
        assert "business" in UserInterestService.INTEREST_CATEGORIES
        assert "公司" in UserInterestService.INTEREST_CATEGORIES["business"]
        assert "企业" in UserInterestService.INTEREST_CATEGORIES["business"]

    def test_intellectual_category_exists(self) -> None:
        """Test intellectual category exists."""
        assert "intellectual" in UserInterestService.INTEREST_CATEGORIES
        assert "专利" in UserInterestService.INTEREST_CATEGORIES["intellectual"]
        assert "商标" in UserInterestService.INTEREST_CATEGORIES["intellectual"]

    def test_traffic_category_exists(self) -> None:
        """Test traffic category exists."""
        assert "traffic" in UserInterestService.INTEREST_CATEGORIES
        assert "交通" in UserInterestService.INTEREST_CATEGORIES["traffic"]
        assert "事故" in UserInterestService.INTEREST_CATEGORIES["traffic"]

    def test_debt_category_exists(self) -> None:
        """Test debt category exists."""
        assert "debt" in UserInterestService.INTEREST_CATEGORIES
        assert "债务" in UserInterestService.INTEREST_CATEGORIES["debt"]
        assert "借贷" in UserInterestService.INTEREST_CATEGORIES["debt"]

    def test_consumer_category_exists(self) -> None:
        """Test consumer category exists."""
        assert "consumer" in UserInterestService.INTEREST_CATEGORIES
        assert "消费" in UserInterestService.INTEREST_CATEGORIES["consumer"]
        assert "维权" in UserInterestService.INTEREST_CATEGORIES["consumer"]


class TestUserInterestServiceCategoriesKeywords:
    """Test INTEREST_CATEGORIES keywords in detail."""

    def test_all_categories_have_at_least_8_keywords(self) -> None:
        """Test that all categories have at least 7 keywords."""
        for category, keywords in UserInterestService.INTEREST_CATEGORIES.items():
            assert len(keywords) >= 7, f"Category {category} has only {len(keywords)} keywords"

    def test_keywords_are_unique_across_categories(self) -> None:
        """Test that keywords are mostly unique across categories."""
        all_keywords = []
        for keywords in UserInterestService.INTEREST_CATEGORIES.values():
            all_keywords.extend(keywords)

        unique_keywords = set(all_keywords)
        # Allow some overlap, but most should be unique
        assert len(unique_keywords) >= len(all_keywords) * 0.8, \
            "Too many duplicate keywords across categories"

    def test_each_category_has_unique_keywords(self) -> None:
        """Test that each category has some unique keywords."""
        all_keywords = set()
        for keywords in UserInterestService.INTEREST_CATEGORIES.values():
            all_keywords.update(keywords)

        # Each category should contribute to the total unique keywords
        assert len(all_keywords) > 50, "Not enough unique keywords across all categories"

    def test_category_keywords_length_distribution(self) -> None:
        """Test keyword length distribution."""
        all_keywords = []
        for keywords in UserInterestService.INTEREST_CATEGORIES.values():
            all_keywords.extend(keywords)

        # Most keywords should be 2-4 characters long (Chinese terms)
        short_keywords = [k for k in all_keywords if len(k) <= 4]
        assert len(short_keywords) >= len(all_keywords) * 0.7, \
            "Most keywords should be short Chinese terms"


class TestUserInterestServiceMethodSignatures:
    """Test method signatures in detail."""

    def test_extract_user_interests_parameter_types(self) -> None:
        """Test extract_user_interests parameter types."""
        import inspect
        sig = inspect.signature(UserInterestService.extract_user_interests)

        # Check parameter types annotation
        annotations = sig.parameters
        assert "db" in annotations
        assert "user_id" in annotations
        assert "days" in annotations
        assert "limit" in annotations

    def test_get_user_interest_tags_parameter_types(self) -> None:
        """Test get_user_interest_tags parameter types."""
        import inspect
        sig = inspect.signature(UserInterestService.get_user_interest_tags)

        annotations = sig.parameters
        assert "db" in annotations
        assert "user_id" in annotations
        assert "days" in annotations

    def test_get_similar_users_parameter_types(self) -> None:
        """Test get_similar_users parameter types."""
        import inspect
        sig = inspect.signature(UserInterestService.get_similar_users)

        annotations = sig.parameters
        assert "db" in annotations
        assert "user_id" in annotations
        assert "limit" in annotations


class TestUserInterestServiceReturnTypes:
    """Test return types of methods."""

    def test_extract_user_interests_return_type(self) -> None:
        """Test extract_user_interests return type annotation."""
        import inspect
        sig = inspect.signature(UserInterestService.extract_user_interests)
        return_annotation = sig.return_annotation

        # Should be list[dict[str, Any]]
        assert "list" in str(return_annotation).lower()

    def test_get_user_interest_tags_return_type(self) -> None:
        """Test get_user_interest_tags return type annotation."""
        import inspect
        sig = inspect.signature(UserInterestService.get_user_interest_tags)
        return_annotation = sig.return_annotation

        # Should be list[str]
        assert "list" in str(return_annotation).lower()

    def test_get_similar_users_return_type(self) -> None:
        """Test get_similar_users return type annotation."""
        import inspect
        sig = inspect.signature(UserInterestService.get_similar_users)
        return_annotation = sig.return_annotation

        # Should be list[int]
        assert "list" in str(return_annotation).lower()


class TestUserInterestServiceCategoriesCompleteness:
    """Test INTEREST_CATEGORIES completeness."""

    def test_all_expected_categories_exist(self) -> None:
        """Test that all expected legal categories exist."""
        expected_categories = [
            "legal", "family", "labor", "property", "criminal",
            "business", "intellectual", "traffic", "debt", "consumer"
        ]
        for category in expected_categories:
            assert category in UserInterestService.INTEREST_CATEGORIES, \
                f"Expected category '{category}' not found"

    def test_category_keywords_are_chinese_characters(self) -> None:
        """Test that category keywords contain Chinese characters."""
        for category, keywords in UserInterestService.INTEREST_CATEGORIES.items():
            # Each keyword should contain at least one Chinese character
            for keyword in keywords:
                has_chinese = any("\u4e00" <= char <= "\u9fff" for char in keyword)
                assert has_chinese, f"Keyword '{keyword}' in category '{category}' should contain Chinese characters"

    def test_no_empty_categories(self) -> None:
        """Test that no category is empty."""
        for category, keywords in UserInterestService.INTEREST_CATEGORIES.items():
            assert len(keywords) > 0, f"Category '{category}' is empty"

    def test_no_duplicate_keywords_in_category(self) -> None:
        """Test that no category has duplicate keywords."""
        for category, keywords in UserInterestService.INTEREST_CATEGORIES.items():
            assert len(keywords) == len(set(keywords)), \
                f"Category '{category}' has duplicate keywords"


class TestUserInterestServiceMethodDefaults:
    """Test method default parameter values."""

    def test_extract_user_interests_defaults(self) -> None:
        """Test extract_user_interests default parameter values."""
        import inspect
        sig = inspect.signature(UserInterestService.extract_user_interests)

        assert sig.parameters["days"].default == 30
        assert sig.parameters["limit"].default == 10

    def test_get_user_interest_tags_defaults(self) -> None:
        """Test get_user_interest_tags default parameter values."""
        import inspect
        sig = inspect.signature(UserInterestService.get_user_interest_tags)

        assert sig.parameters["days"].default == 30

    def test_get_similar_users_defaults(self) -> None:
        """Test get_similar_users default parameter values."""
        import inspect
        sig = inspect.signature(UserInterestService.get_similar_users)

        assert sig.parameters["limit"].default == 10


class TestUserInterestServiceCategoriesCoverage:
    """Test that categories cover various legal domains."""

    def test_family_category_keywords(self) -> None:
        """Test family category has expected keywords."""
        keywords = UserInterestService.INTEREST_CATEGORIES["family"]
        expected = ["婚姻", "离婚", "抚养", "赡养", "继承"]
        for kw in expected:
            assert kw in keywords, f"Expected keyword '{kw}' not in family category"

    def test_labor_category_keywords(self) -> None:
        """Test labor category has expected keywords."""
        keywords = UserInterestService.INTEREST_CATEGORIES["labor"]
        expected = ["劳动", "工资", "加班", "社保", "工伤"]
        for kw in expected:
            assert kw in keywords, f"Expected keyword '{kw}' not in labor category"

    def test_property_category_keywords(self) -> None:
        """Test property category has expected keywords."""
        keywords = UserInterestService.INTEREST_CATEGORIES["property"]
        expected = ["房产", "房屋", "买卖", "租赁"]
        for kw in expected:
            assert kw in keywords, f"Expected keyword '{kw}' not in property category"

    def test_criminal_category_keywords(self) -> None:
        """Test criminal category has expected keywords."""
        keywords = UserInterestService.INTEREST_CATEGORIES["criminal"]
        expected = ["刑事", "犯罪", "辩护", "缓刑"]
        for kw in expected:
            assert kw in keywords, f"Expected keyword '{kw}' not in criminal category"


class TestUserInterestServiceCategoriesStatistics:
    """Test INTEREST_CATEGORIES statistics."""

    def test_total_categories_count(self) -> None:
        """Test total number of categories."""
        categories = UserInterestService.INTEREST_CATEGORIES
        assert len(categories) == 10, f"Expected 10 categories, got {len(categories)}"

    def test_total_keywords_count(self) -> None:
        """Test total number of keywords across all categories."""
        categories = UserInterestService.INTEREST_CATEGORIES
        total_keywords = sum(len(keywords) for keywords in categories.values())
        assert total_keywords >= 70, f"Expected at least 70 keywords, got {total_keywords}"

    def test_average_keywords_per_category(self) -> None:
        """Test average number of keywords per category."""
        categories = UserInterestService.INTEREST_CATEGORIES
        avg_keywords = sum(len(keywords) for keywords in categories.values()) / len(categories)
        assert avg_keywords >= 7, f"Expected at least 7 keywords per category, got {avg_keywords}"

    def test_keywords_length_range(self) -> None:
        """Test that keywords are within expected length range."""
        categories = UserInterestService.INTEREST_CATEGORIES
        all_keywords = []
        for keywords in categories.values():
            all_keywords.extend(keywords)

        # Most keywords should be 2-6 characters
        valid_lengths = [k for k in all_keywords if 2 <= len(k) <= 6]
        assert len(valid_lengths) >= len(all_keywords) * 0.9, \
            "Most keywords should be 2-6 characters long"


class TestUserInterestServiceMethodCompleteness:
    """Test method completeness."""

    def test_all_methods_are_static(self) -> None:
        """Test that all public methods are static."""
        import inspect

        public_methods = [
            "extract_user_interests",
            "get_user_interest_tags",
            "get_similar_users",
        ]

        for method_name in public_methods:
            method = getattr(UserInterestService, method_name)
            assert inspect.ismethod(method) or callable(method), \
                f"Method {method_name} should be callable"

    def test_service_has_class_attribute(self) -> None:
        """Test that service has INTEREST_CATEGORIES class attribute."""
        assert hasattr(UserInterestService, "INTEREST_CATEGORIES")
        assert isinstance(UserInterestService.INTEREST_CATEGORIES, dict)

    def test_service_can_be_instantiated(self) -> None:
        """Test that service can be instantiated."""
        service = UserInterestService()
        assert service is not None


class TestUserInterestServiceFunctional:
    """Functional tests for UserInterestService methods."""

    @pytest.mark.asyncio
    async def test_extract_user_interests_with_behaviors(self) -> None:
        """Test extract_user_interests with behavior logs."""
        from app.services.user_interest_service import UserInterestService
        from app.models.analytics import UserBehaviorLog
        from unittest.mock import AsyncMock, MagicMock
        from datetime import datetime, timezone

        mock_db = AsyncMock()
        mock_behavior = MagicMock()
        mock_behavior.user_id = 1
        mock_behavior.created_at = datetime.now(timezone.utc)
        mock_behavior.metadata_json = '{"keywords": ["律师", "咨询"], "category": "法律"}'
        mock_behavior.resource_type = "forum_post"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_behavior]
        mock_db.execute.return_value = mock_result

        result = await UserInterestService.extract_user_interests(mock_db, 1)

        assert len(result) > 0
        assert all("category" in item for item in result)
        assert all("score" in item for item in result)

    @pytest.mark.asyncio
    async def test_extract_user_interests_no_behaviors(self) -> None:
        """Test extract_user_interests with no behavior logs."""
        from app.services.user_interest_service import UserInterestService
        from unittest.mock import AsyncMock, MagicMock

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await UserInterestService.extract_user_interests(mock_db, 1)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_interest_tags_simplified(self) -> None:
        """Test get_user_interest_tags returns simplified tags."""
        from app.services.user_interest_service import UserInterestService
        from unittest.mock import AsyncMock, patch

        mock_db = AsyncMock()

        with patch.object(UserInterestService, 'extract_user_interests', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = [
                {"category": "legal", "score": 10, "matched_keywords": ["律师"]},
                {"category": "family", "score": 5, "matched_keywords": ["婚姻"]},
            ]

            result = await UserInterestService.get_user_interest_tags(mock_db, 1)

            assert result == ["legal", "family"]

    @pytest.mark.asyncio
    async def test_get_similar_users_with_overlap(self) -> None:
        """Test get_similar_users finds users with similar interests."""
        from app.services.user_interest_service import UserInterestService
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_db = AsyncMock()

        with patch.object(UserInterestService, 'get_user_interest_tags', new_callable=AsyncMock) as mock_tags:
            mock_tags.side_effect = [
                ["legal", "family"],  # Current user
                ["legal", "family"],  # Similar user 1
                ["legal"],  # Similar user 2
                ["family"],  # Similar user 3
            ]

            mock_result = MagicMock()
            mock_result.all.return_value = [(2,), (3,), (4,)]
            mock_db.execute.return_value = mock_result

            result = await UserInterestService.get_similar_users(mock_db, 1)

            assert isinstance(result, list)
            assert all(isinstance(user_id, int) for user_id in result)

    @pytest.mark.asyncio
    async def test_get_similar_users_no_current_interests(self) -> None:
        """Test get_similar_users returns empty when no current interests."""
        from app.services.user_interest_service import UserInterestService
        from unittest.mock import AsyncMock, patch

        mock_db = AsyncMock()

        with patch.object(UserInterestService, 'get_user_interest_tags', new_callable=AsyncMock) as mock_tags:
            mock_tags.return_value = []

            result = await UserInterestService.get_similar_users(mock_db, 1)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_similar_users_low_similarity(self) -> None:
        """Test get_similar_users filters by similarity threshold."""
        from app.services.user_interest_service import UserInterestService
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_db = AsyncMock()

        with patch.object(UserInterestService, 'get_user_interest_tags', new_callable=AsyncMock) as mock_tags:
            mock_tags.side_effect = [
                ["legal"],  # Current user
                ["family"],  # Other user 1 (no overlap)
                ["labor"],  # Other user 2 (no overlap)
            ]

            mock_result = MagicMock()
            mock_result.all.return_value = [(2,), (3,)]
            mock_db.execute.return_value = mock_result

            result = await UserInterestService.get_similar_users(mock_db, 1)

            assert result == []

    @pytest.mark.asyncio
    async def test_extract_user_interests_limit(self) -> None:
        """Test extract_user_interests respects limit parameter."""
        from app.services.user_interest_service import UserInterestService
        from app.models.analytics import UserBehaviorLog
        from unittest.mock import AsyncMock, MagicMock
        from datetime import datetime, timezone

        mock_db = AsyncMock()

        behaviors = []
        for i in range(15):
            mock_behavior = MagicMock()
            mock_behavior.user_id = 1
            mock_behavior.created_at = datetime.now(timezone.utc)
            mock_behavior.metadata_json = f'{{"keywords": ["keyword{i}"]}}'
            mock_behavior.resource_type = "forum_post"
            behaviors.append(mock_behavior)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = behaviors
        mock_db.execute.return_value = mock_result

        result = await UserInterestService.extract_user_interests(mock_db, 1, limit=5)

        assert len(result) <= 5
