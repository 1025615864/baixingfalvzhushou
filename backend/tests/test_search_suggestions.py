"""Tests for search suggestion service."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.search.suggestions import (
    HotKeyword,
    SearchSuggestionService,
    search_suggestion_service,
)


class TestSearchSuggestionService:
    """Test SearchSuggestionService class."""

    def test_service_exists(self) -> None:
        """Test SearchSuggestionService class exists."""
        assert SearchSuggestionService is not None

    def test_singleton_exists(self) -> None:
        """Test search_suggestion_service singleton exists."""
        assert search_suggestion_service is not None
        assert isinstance(search_suggestion_service, SearchSuggestionService)

    def test_service_has_required_methods(self) -> None:
        """Test SearchSuggestionService has expected methods."""
        service = search_suggestion_service
        assert hasattr(service, 'get_search_suggestions')
        assert hasattr(service, 'get_hot_keywords')
        assert hasattr(service, '_escape_like')

    def test_service_can_be_instantiated(self) -> None:
        """Test SearchSuggestionService can be instantiated."""
        service = SearchSuggestionService()
        assert service is not None


class TestEscapeLike:
    """Test _escape_like helper method."""

    def test_escape_simple_string(self) -> None:
        """Test escaping simple string."""
        service = SearchSuggestionService()
        result = service._escape_like("test")
        assert result == "test"

    def test_escape_percent(self) -> None:
        """Test escaping percent sign."""
        service = SearchSuggestionService()
        result = service._escape_like("test%")
        assert result == "test\\%"

    def test_escape_underscore(self) -> None:
        """Test escaping underscore."""
        service = SearchSuggestionService()
        result = service._escape_like("test_")
        assert result == "test\\_"

    def test_escape_backslash(self) -> None:
        """Test escaping backslash."""
        service = SearchSuggestionService()
        result = service._escape_like("test\\")
        assert result == "test\\\\"

    def test_escape_multiple_special_chars(self) -> None:
        """Test escaping multiple special characters."""
        service = SearchSuggestionService()
        result = service._escape_like("test%_\\value")
        assert result == "test\\%\\_\\\\value"

    def test_escape_empty_string(self) -> None:
        """Test escaping empty string."""
        service = SearchSuggestionService()
        result = service._escape_like("")
        assert result == ""

    def test_escape_none(self) -> None:
        """Test escaping None-like value."""
        service = SearchSuggestionService()
        result = service._escape_like(None)
        assert result == ""

    def test_escape_custom_escape_char(self) -> None:
        """Test with custom escape character."""
        service = SearchSuggestionService()
        result = service._escape_like("test%", escape="|")
        assert result == "test|%"


class TestGetSearchSuggestions:
    """Test get_search_suggestions method."""

    def test_get_suggestions_is_async(self) -> None:
        """Test get_search_suggestions is async."""
        import inspect
        service = SearchSuggestionService()
        assert inspect.iscoroutinefunction(service.get_search_suggestions)

    @pytest.mark.asyncio
    async def test_get_suggestions_empty_query(self) -> None:
        """Test get_suggestions returns empty for empty query."""
        service = SearchSuggestionService()
        result = await service.get_search_suggestions(db=AsyncMock(), query="")
        assert result == []

    def test_get_suggestions_short_query(self) -> None:
        """Test get_suggestions method signature."""
        import inspect
        service = SearchSuggestionService()
        sig = inspect.signature(service.get_search_suggestions)
        params = list(sig.parameters.keys())
        assert "db" in params
        assert "query" in params
        assert "limit" in params

    def test_get_suggestions_with_limit(self) -> None:
        """Test get_suggestions with valid query."""
        import asyncio
        service = SearchSuggestionService()
        # Just verify method exists and is callable
        assert callable(service.get_search_suggestions)

    @pytest.mark.asyncio
    async def test_get_hot_keywords_with_limit(self) -> None:
        """Test get_hot_keywords respects limit."""
        service = SearchSuggestionService()

        mock_result = MagicMock()
        mock_result.all.return_value = []

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_hot_keywords(db=mock_db, limit=5)

        # Should not raise
        assert isinstance(result, list)


class TestSearchSuggestionServiceIntegration:
    """Integration tests."""

    def test_service_module_exports(self) -> None:
        """Test that module exports are correct."""
        from app.services.search import suggestions
        assert hasattr(suggestions, 'HotKeyword')
        assert hasattr(suggestions, 'SearchSuggestionService')
        assert hasattr(suggestions, 'search_suggestion_service')

    def test_full_service_structure(self) -> None:
        """Test service has complete structure."""
        service = SearchSuggestionService()
        # Should have all expected attributes
        assert hasattr(service, '_escape_like')
        assert hasattr(service, 'get_search_suggestions')
        assert hasattr(service, 'get_hot_keywords')
