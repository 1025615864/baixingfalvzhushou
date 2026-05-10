from fastapi import APIRouter
from app.config.settings import settings

router = APIRouter(tags=["AI Chat"])

def get_settings():
    return settings


@router.post("/chat")
async def chat():
    raise NotImplementedError


@router.post("/quick-replies")
async def quick_replies():
    raise NotImplementedError


@router.get("/consultations")
async def list_consultations():
    raise NotImplementedError


@router.get("/consultations/{consultation_id}")
async def get_consultation(consultation_id: int):
    raise NotImplementedError


@router.post("/consultations/{consultation_id}/share")
async def share_consultation(consultation_id: int):
    raise NotImplementedError


@router.get("/share/{share_token}")
async def get_shared_consultation(share_token: str):
    raise NotImplementedError
