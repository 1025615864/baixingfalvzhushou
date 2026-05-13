import asyncio
import json
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.settings import settings
from app.utils.deps import get_db, get_current_user

router = APIRouter(tags=["AI Analysis"])


def get_settings():
    return settings


async def _enforce_guest_ai_quota():
    pass


class QuickRepliesRequest(BaseModel):
    user_message: str = ""
    assistant_answer: str = ""
    references: list = []


class RateMessageRequest(BaseModel):
    message_id: Optional[int] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None


QUICK_REPLY_MAP = {
    "离婚": ["子女抚养权怎么判？", "财产如何分割？", "需要准备什么材料？", "诉讼离婚还是协议离婚？"],
    "劳动": ["劳动合同怎么处理？", "如何申请劳动仲裁？", "加班费怎么计算？", "经济补偿金怎么算？"],
    "违约": ["损失如何赔偿？", "违约金怎么计算？", "合同还能继续履行吗？", "如何解除合同？"],
}

ALLOWED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".pdf", ".docx", ".doc"}
ALLOWED_MIMES = {"text/", "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def _extract_text_sync(content: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("exe", "bin"):
        raise ValueError("不支持的文件类型")
    if ext in ("txt", "md", "csv", "json"):
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return str(content)
    if ext in ("pdf",):
        return content.decode("utf-8", errors="replace")
    if ext in ("docx", "doc"):
        return content.decode("utf-8", errors="replace")
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return str(content)


def _summarize_sync(text: str) -> str:
    return text[:200] if text else "无法提取文本内容"


def _generate_quick_replies(user_message: str, assistant_answer: str, references: list) -> list[str]:
    replies = []
    for keyword, reply_list in QUICK_REPLY_MAP.items():
        if keyword in user_message or keyword in assistant_answer:
            replies.extend(reply_list)
    if not replies:
        replies = ["还有其他问题吗？", "需要更详细的法律分析吗？", "是否需要咨询专业律师？"]
    return replies[:4]


@router.post("/files/analyze")
async def analyze_file(file: UploadFile = File(...)):
    _settings = get_settings()
    api_key = getattr(_settings, 'openai_api_key', '')
    if not api_key:
        raise HTTPException(status_code=503, detail={"message": "AI服务未配置", "error_code": "AI_NOT_CONFIGURED"})

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail={"message": "文件为空", "error_code": "AI_BAD_REQUEST"})

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail={"message": "文件过大", "error_code": "AI_BAD_REQUEST"})

    filename = file.filename or "unknown.txt"
    try:
        extracted_text = await asyncio.to_thread(_extract_text_sync, content, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"message": str(e), "error_code": "AI_BAD_REQUEST"})

    summary = await asyncio.to_thread(_summarize_sync, extracted_text)

    return {"filename": filename, "summary": summary}


@router.post("/quick-replies")
async def quick_replies(request: QuickRepliesRequest):
    replies = _generate_quick_replies(request.user_message, request.assistant_answer, request.references)
    return {"replies": replies}


@router.post("/messages/rate")
async def rate_message(
    request: RateMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from sqlalchemy import select
    from app.models.consultation import ChatMessage, Consultation

    if request.message_id is None:
        raise HTTPException(status_code=404, detail="Message not found")

    stmt = select(ChatMessage).where(ChatMessage.id == request.message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    stmt2 = select(Consultation).where(Consultation.id == message.consultation_id)
    result2 = await db.execute(stmt2)
    consultation = result2.scalar_one_or_none()

    if consultation is not None and current_user is not None:
        if consultation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    if request.rating is not None:
        message.rating = request.rating
    if request.feedback is not None:
        message.feedback = request.feedback

    await db.commit()
    await db.refresh(message)

    return {"status": "ok", "message_id": message.id}


@router.get("/integration/stats")
async def integration_stats():
    try:
        from app.services.integration.module_integration import get_integration_service
        service = get_integration_service()
        return await service.get_integration_stats()
    except Exception:
        return {"pending_workflows": 0, "lawyer_referrals": 0}
