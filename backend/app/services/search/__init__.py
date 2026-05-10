"""Search service with sub-modules."""
from __future__ import annotations
from app.services.search.search_service import SearchService
from app.services.search.suggestions import SearchSuggestionService, HotKeyword
from app.services.search.types import SearchQuery, SearchResult, SearchFilter

SearchSuggestions = SearchSuggestionService

search_service = SearchService()
