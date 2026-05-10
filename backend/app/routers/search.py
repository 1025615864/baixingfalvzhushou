from fastapi import APIRouter

router = APIRouter(prefix="/search", tags=["Search"])


class _SearchService:
    async def global_search(self, db, query, limit=10):
        raise NotImplementedError

    async def search_suggestions(self, db, query, limit=5):
        raise NotImplementedError

    async def record_search(self, db, keyword, user_id=None, ip_address=None):
        raise NotImplementedError

    @staticmethod
    def _escape_like(value: str) -> str:
        raise NotImplementedError

    @staticmethod
    def _make_snippet(text, keyword, max_len=100):
        raise NotImplementedError


search_service = _SearchService()


@router.get("")
async def global_search(q: str = ""):
    raise NotImplementedError


@router.get("/suggestions")
async def search_suggestions(q: str = "", limit: int = 5):
    raise NotImplementedError


@router.get("/hot")
async def hot_keywords(limit: int = 10):
    raise NotImplementedError


@router.get("/history")
async def search_history(limit: int = 10):
    raise NotImplementedError


@router.delete("/history")
async def clear_search_history():
    raise NotImplementedError
