from __future__ import annotations


class SearchService:
    @staticmethod
    def _escape_like(value: str) -> str:
        raise NotImplementedError

    @staticmethod
    def _make_snippet(text, keyword, max_len=100):
        raise NotImplementedError

    async def global_search(self, db, query, limit=10):
        raise NotImplementedError

    async def search_suggestions(self, db, query, limit=5):
        raise NotImplementedError

    async def record_search(self, db, keyword, user_id=None, ip_address=None):
        raise NotImplementedError
