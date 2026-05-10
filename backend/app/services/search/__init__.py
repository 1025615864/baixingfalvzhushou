"""Search service with sub-modules."""
from __future__ import annotations
from app.services.search.search_service import SearchService
from app.services.search.suggestions import SearchSuggestions
from app.services.search.types import SearchQuery, SearchResult, SearchFilter


search_service = SearchService()
