"""Tests for search types."""
from __future__ import annotations

import pytest

from app.services.search.types import (
    NewsSearchItem,
    PostSearchItem,
    LawFirmSearchItem,
    LawyerSearchItem,
    KnowledgeSearchItem,
    SearchResults,
    HotKeyword,
)


class TestSearchItemTypedDicts:
    """Test search item TypedDict classes."""

    def test_news_search_item(self) -> None:
        """Test NewsSearchItem TypedDict."""
        item: NewsSearchItem = {
            "id": 1,
            "title": "Test News",
            "summary": "Test summary",
            "snippet": "Test snippet",
            "type": "news",
        }
        assert item["id"] == 1
        assert item["title"] == "Test News"
        assert item["type"] == "news"

    def test_news_search_item_optional_fields(self) -> None:
        """Test NewsSearchItem with optional fields as None."""
        item: NewsSearchItem = {
            "id": 2,
            "title": "Another News",
            "summary": None,
            "snippet": None,
            "type": "news",
        }
        assert item["summary"] is None
        assert item["snippet"] is None

    def test_post_search_item(self) -> None:
        """Test PostSearchItem TypedDict."""
        item: PostSearchItem = {
            "id": 1,
            "title": "Test Post",
            "content": "Post content here",
            "type": "post",
        }
        assert item["id"] == 1
        assert item["title"] == "Test Post"
        assert item["type"] == "post"

    def test_lawfirm_search_item(self) -> None:
        """Test LawFirmSearchItem TypedDict."""
        item: LawFirmSearchItem = {
            "id": 1,
            "name": "Test Law Firm",
            "address": "123 Test Street",
            "type": "lawfirm",
        }
        assert item["id"] == 1
        assert item["name"] == "Test Law Firm"
        assert item["address"] == "123 Test Street"

    def test_lawfirm_search_item_optional_address(self) -> None:
        """Test LawFirmSearchItem with optional address."""
        item: LawFirmSearchItem = {
            "id": 2,
            "name": "Another Law Firm",
            "address": None,
            "type": "lawfirm",
        }
        assert item["address"] is None

    def test_lawyer_search_item(self) -> None:
        """Test LawyerSearchItem TypedDict."""
        item: LawyerSearchItem = {
            "id": 1,
            "name": "John Doe",
            "specialties": "Criminal Law",
            "type": "lawyer",
        }
        assert item["id"] == 1
        assert item["name"] == "John Doe"
        assert item["specialties"] == "Criminal Law"

    def test_lawyer_search_item_optional_specialties(self) -> None:
        """Test LawyerSearchItem with optional specialties."""
        item: LawyerSearchItem = {
            "id": 2,
            "name": "Jane Doe",
            "specialties": None,
            "type": "lawyer",
        }
        assert item["specialties"] is None

    def test_knowledge_search_item(self) -> None:
        """Test KnowledgeSearchItem TypedDict."""
        item: KnowledgeSearchItem = {
            "id": 1,
            "title": "Legal Guide",
            "category": "Criminal Law",
            "type": "knowledge",
        }
        assert item["id"] == 1
        assert item["title"] == "Legal Guide"
        assert item["category"] == "Criminal Law"

    def test_knowledge_search_item_optional_category(self) -> None:
        """Test KnowledgeSearchItem with optional category."""
        item: KnowledgeSearchItem = {
            "id": 2,
            "title": "Another Guide",
            "category": None,
            "type": "knowledge",
        }
        assert item["category"] is None


class TestSearchResultsTypedDict:
    """Test SearchResults TypedDict."""

    def test_search_results(self) -> None:
        """Test SearchResults TypedDict."""
        results: SearchResults = {
            "news": [],
            "posts": [],
            "lawfirms": [],
            "lawyers": [],
            "knowledge": [],
        }
        assert results["news"] == []
        assert results["posts"] == []
        assert results["lawfirms"] == []
        assert results["lawyers"] == []
        assert results["knowledge"] == []

    def test_search_results_with_items(self) -> None:
        """Test SearchResults with items."""
        news_item: NewsSearchItem = {
            "id": 1,
            "title": "News",
            "summary": None,
            "snippet": None,
            "type": "news",
        }
        results: SearchResults = {
            "news": [news_item],
            "posts": [],
            "lawfirms": [],
            "lawyers": [],
            "knowledge": [],
        }
        assert len(results["news"]) == 1
        assert results["news"][0]["title"] == "News"

    def test_search_results_multiple_types(self) -> None:
        """Test SearchResults with multiple item types."""
        news_item: NewsSearchItem = {
            "id": 1,
            "title": "News",
            "summary": None,
            "snippet": None,
            "type": "news",
        }
        post_item: PostSearchItem = {
            "id": 1,
            "title": "Post",
            "content": "Content",
            "type": "post",
        }
        results: SearchResults = {
            "news": [news_item],
            "posts": [post_item],
            "lawfirms": [],
            "lawyers": [],
            "knowledge": [],
        }
        assert len(results["news"]) == 1
        assert len(results["posts"]) == 1
        assert len(results["lawfirms"]) == 0


class TestHotKeywordTypedDict:
    """Test HotKeyword TypedDict."""

    def test_hot_keyword(self) -> None:
        """Test HotKeyword TypedDict."""
        keyword: HotKeyword = {
            "keyword": "divorce",
            "count": 1000,
        }
        assert keyword["keyword"] == "divorce"
        assert keyword["count"] == 1000

    def test_hot_keyword_with_zero_count(self) -> None:
        """Test HotKeyword with zero count."""
        keyword: HotKeyword = {
            "keyword": "rare",
            "count": 0,
        }
        assert keyword["count"] == 0

    def test_hot_keyword_with_large_count(self) -> None:
        """Test HotKeyword with large count."""
        keyword: HotKeyword = {
            "keyword": "popular",
            "count": 999999,
        }
        assert keyword["count"] == 999999


class TestSearchTypesModule:
    """Test search types module."""

    def test_all_types_exported(self) -> None:
        """Test that all types are exported."""
        from app.services.search import types
        assert hasattr(types, 'NewsSearchItem')
        assert hasattr(types, 'PostSearchItem')
        assert hasattr(types, 'LawFirmSearchItem')
        assert hasattr(types, 'LawyerSearchItem')
        assert hasattr(types, 'KnowledgeSearchItem')
        assert hasattr(types, 'SearchResults')
        assert hasattr(types, 'HotKeyword')

    def test_type_literals(self) -> None:
        """Test that type fields have correct literals."""
        news: NewsSearchItem = {
            "id": 1,
            "title": "Test",
            "summary": None,
            "snippet": None,
            "type": "news",  # Must be "news"
        }
        assert news["type"] == "news"

        post: PostSearchItem = {
            "id": 1,
            "title": "Test",
            "content": "Test",
            "type": "post",  # Must be "post"
        }
        assert post["type"] == "post"

        lawfirm: LawFirmSearchItem = {
            "id": 1,
            "name": "Test",
            "address": None,
            "type": "lawfirm",  # Must be "lawfirm"
        }
        assert lawfirm["type"] == "lawfirm"

        lawyer: LawyerSearchItem = {
            "id": 1,
            "name": "Test",
            "specialties": None,
            "type": "lawyer",  # Must be "lawyer"
        }
        assert lawyer["type"] == "lawyer"

        knowledge: KnowledgeSearchItem = {
            "id": 1,
            "title": "Test",
            "category": None,
            "type": "knowledge",  # Must be "knowledge"
        }
        assert knowledge["type"] == "knowledge"
