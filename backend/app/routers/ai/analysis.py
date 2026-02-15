"""AI analysis routes

Provides file analysis endpoints - document analysis, quick replies, message rating
"""
import asyncio
import io
import json
import logging
import os
import tempfile
import time
import uuid
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect, select

from ...config import get_settings
from ...database import get_db
from ...models.consultation import ChatMessage, Consultation
from ...models.user import User
from ...schemas.ai import FileAnalyzeResponse, QuickRepliesRequest, QuickRepliesResponse, RatingRequest, RatingResponse
from ...services.ai_metrics import ai_metrics
from ...services.critical_event_reporter import critical_event_reporter
from ...utils.deps import get_current_user, get_current_user_optional
from ...utils.helpers import _get_int_env
from ...utils.pii import sanitize_pii
from ...utils.rate_limiter import rate_limit, RateLimitConfig, get_client_ip

router = APIRouter(prefix="/ai", tags=["AI分析"])

settings = get_settings()
logger = logging.getLogger(__name__)

ERROR_AI_NOT_CONFIGURED = "AI_NOT_CONFIGURED"
ERROR_AI_UNAVAILABLE = "AI_UNAVAILABLE"
ERROR_AI_RATE_LIMITED = "AI_RATE_LIMITED"
ERROR_AI_FORBIDDEN = "AI_FORBIDDEN"
ERROR_AI_UNAUTHORIZED = "AI_UNAUTHORIZED"
ERROR_AI_BAD_REQUEST = "AI_BAD_REQUEST"
ERROR_AI_INTERNAL_ERROR = "AI_INTERNAL_ERROR"


GUEST_AI_LIMIT = _get_int_env("GUEST_AI_LIMIT", 3)
GUEST_AI_WINDOW_SECONDS = _get_int_env("GUEST_AI_WINDOW_SECONDS", 60 * 60 * 24)


def _error_code_for_http(status_code: int) -> str:
    sc = int(status_code)
    if sc == 400:
        return ERROR_AI_BAD_REQUEST
    if sc == 401:
        return ERROR_AI_UNAUTHORIZED
    if sc == 403:
        return ERROR_AI_FORBIDDEN
    if sc == 429:
        return ERROR_AI_RATE_LIMITED
    if sc == 503:
        return ERROR_AI_UNAVAILABLE
    return ERROR_AI_INTERNAL_ERROR


def _extract_message(detail: object) -> str:
    if detail is None:
        return ""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        detail_dict = cast(dict[str, object], detail)
        msg_obj = detail_dict.get("message")
        if isinstance(msg_obj, str):
            return msg_obj
        msg2_obj = detail_dict.get("detail")
        if isinstance(msg2_obj, str):
            return msg2_obj
    return str(detail)


def _make_error_response(
    *,
    status_code: int,
    error_code: str,
    message: str,
    request_id: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    out_headers: dict[str, str] = {
        "X-Request-Id": str(request_id),
        "X-Error-Code": str(error_code),
    }
    if headers:
        for k, v in headers.items():
            out_headers[str(k)] = str(v)

    return JSONResponse(
        status_code=int(status_code),
        content={
            "error_code": str(error_code),
            "message": str(message),
            "detail": str(message),
            "request_id": str(request_id),
        },
        headers=out_headers,
    )


def _audit_event(event: str, payload: dict[str, object]) -> None:
    try:
        logger.info(
            "ai_audit event=%s payload=%s",
            str(event),
            json.dumps(
                payload,
                ensure_ascii=False))
    except Exception:
        logger.exception("ai_audit event logging failed: %s", str(event))


async def _enforce_guest_ai_quota(request: Request) -> None:
    from ...utils.rate_limiter import rate_limiter
    key = f"ai:guest:{get_client_ip(request)}"
    allowed, remaining, wait_time = await rate_limiter.check(key, GUEST_AI_LIMIT, GUEST_AI_WINDOW_SECONDS)
    if allowed:
        return
    raise HTTPException(
        status_code=429,
        detail=f"游客模式 24 小时内仅可试用 {int(GUEST_AI_LIMIT)} 次，请登录后继续",
        headers={
            "X-RateLimit-Limit": str(GUEST_AI_LIMIT),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(int(time.time() + wait_time)),
            "Retry-After": str(int(wait_time)),
        },
    )


@router.post("/files/analyze", response_model=FileAnalyzeResponse)
@rate_limit(*RateLimitConfig.AI_CHAT, by_ip=True, by_user=False)
async def analyze_file(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User | None, Depends(
        get_current_user_optional)] = None,
):
    started_at = float(time.time())
    request_id = str(getattr(request.state, "request_id", "")
                     or "").strip() or uuid.uuid4().hex
    ai_metrics.record_request("file_analyze")
    client_ip = get_client_ip(request)

    current_user_id: int | None = None
    if current_user is not None:
        try:
            identity = inspect(current_user).identity
            if identity:
                current_user_id = cast(int | None, identity[0])
        except Exception:
            logger.exception("Failed to get current_user_id from identity")
            current_user_id = None

    user_id_str = str(
        current_user_id) if current_user_id is not None else "guest"

    e2e_mock_enabled = bool(settings.debug) and str(
        request.headers.get("X-E2E-Mock-AI") or "").strip() == "1"
    if e2e_mock_enabled:
        try:
            _ = await file.read()
        except Exception:
            logger.exception("E2E mock file read failed")
        _ = response.headers.setdefault("X-Request-Id", request_id)
        return FileAnalyzeResponse(
            filename=str(file.filename or "attachment"),
            content_type=str(file.content_type or "") or None,
            text_chars=12,
            text_preview="这是一个E2E mock 的文件内容",
            summary="这是一个E2E mock 的文件分析结果",
        )

    if not settings.openai_api_key:
        error_code = ERROR_AI_NOT_CONFIGURED
        message = "AI服务未配置：请设置 OPENAI_API_KEY 后重试"
        ai_metrics.record_error(
            endpoint="file_analyze",
            request_id=request_id,
            error_code=error_code,
            status_code=503,
            message=message,
        )
        critical_event_reporter.fire_and_forget(
            event="ai_not_configured",
            severity="warning",
            request_id=request_id,
            title="AI服务未配置",
            message=message,
            data={
                "endpoint": "file_analyze",
                "user_id": user_id_str,
                "ip": client_ip,
            },
            dedup_key="ai_not_configured",
        )
        _audit_event(
            "file_analyze_error",
            {
                "request_id": request_id,
                "endpoint": "file_analyze",
                "user_id": user_id_str,
                "ip": client_ip,
                "status_code": 503,
                "error_code": error_code,
                "duration_ms": int((time.time() - started_at) * 1000),
            },
        )
        return _make_error_response(
            status_code=503,
            error_code=error_code,
            message=message,
            request_id=request_id,
        )

    if current_user is None:
        await _enforce_guest_ai_quota(request)

    try:
        content = await file.read()
    except Exception:
        logger.exception("File read failed during analysis")
        return _make_error_response(
            status_code=400,
            error_code=ERROR_AI_BAD_REQUEST,
            message="读取文件失败",
            request_id=request_id,
        )

    if not content:
        return _make_error_response(
            status_code=400,
            error_code=ERROR_AI_BAD_REQUEST,
            message="文件为空",
            request_id=request_id,
        )

    if len(content) > 10 * 1024 * 1024:
        return _make_error_response(
            status_code=400,
            error_code=ERROR_AI_BAD_REQUEST,
            message="文件大小不能超过 10MB",
            request_id=request_id,
        )

    filename = str(file.filename or "attachment").strip() or "attachment"
    content_type = str(file.content_type or "").strip() or None
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    def _extract_text_sync() -> str:
        if ext == "pdf" or (content_type or "").lower() == "application/pdf":
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            parts: list[str] = []
            for page in reader.pages:
                t = page.extract_text() or ""
                if t:
                    parts.append(t)
            return "\n".join(parts)

        if ext == "docx" or (content_type or "").lower(
        ) == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            import os
            import docx2txt

            tmp_path: str | None = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                return str(docx2txt.process(tmp_path) or "")
            finally:
                if tmp_path:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

        if ext in {"txt", "md", "csv", "json"} or (
                content_type or "").startswith("text/"):
            try:
                return content.decode("utf-8", errors="replace")
            except Exception:
                return str(content.decode(errors="replace"))

        raise ValueError("unsupported")

    try:
        extracted = await asyncio.to_thread(_extract_text_sync)
    except ValueError:
        return _make_error_response(
            status_code=400,
            error_code=ERROR_AI_BAD_REQUEST,
            message="不支持的文件类型",
            request_id=request_id,
        )
    except Exception:
        return _make_error_response(
            status_code=500,
            error_code=ERROR_AI_INTERNAL_ERROR,
            message="文件解析失败",
            request_id=request_id,
        )

    extracted_norm = str(extracted or "").strip()
    if not extracted_norm:
        return _make_error_response(
            status_code=400,
            error_code=ERROR_AI_BAD_REQUEST,
            message="无法从文件中提取文本",
            request_id=request_id,
        )

    max_chars = 200_000
    if len(extracted_norm) > max_chars:
        extracted_norm = extracted_norm[:max_chars]

    preview = extracted_norm[:4000]

    extracted_for_ai = sanitize_pii(extracted_norm)

    def _summarize_sync() -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url)
        res = client.chat.completions.create(
            model=str(
                settings.ai_model or "").strip() or "gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "你是法律文书/材料分析助手。请用简洁中文输出：1) 摘要 2) 关键信息要点 3) 风险与建议。",
                },
                {
                    "role": "user",
                    "content": f"请分析以下文件内容：\n\n{extracted_for_ai}",
                },
            ],
            temperature=0.2,
            max_tokens=800,
        )
        choices = getattr(res, "choices", None)
        if not choices:
            return ""
        msg = getattr(choices[0], "message", None)
        return str(getattr(msg, "content", "") or "")

    try:
        summary = await asyncio.to_thread(_summarize_sync)
    except Exception:
        ai_metrics.record_error(
            endpoint="file_analyze",
            request_id=request_id,
            error_code=ERROR_AI_INTERNAL_ERROR,
            status_code=500,
            message="summarize_failed",
        )
        critical_event_reporter.fire_and_forget(
            event="ai_file_analyze_failed",
            severity="error",
            request_id=request_id,
            title="文件分析失败",
            message="summarize_failed",
            data={
                "endpoint": "file_analyze",
            },
            dedup_key="ai_file_analyze_failed",
        )
        return _make_error_response(
            status_code=500,
            error_code=ERROR_AI_INTERNAL_ERROR,
            message="文件分析失败",
            request_id=request_id,
        )

    summary_norm = str(summary or "").strip()
    if not summary_norm:
        return _make_error_response(
            status_code=500,
            error_code=ERROR_AI_INTERNAL_ERROR,
            message="文件分析失败",
            request_id=request_id,
        )

    _audit_event(
        "file_analyze_ok",
        {
            "request_id": request_id,
            "endpoint": "file_analyze",
            "user_id": user_id_str,
            "ip": client_ip,
            "duration_ms": int((time.time() - started_at) * 1000),
            "text_len": len(extracted_norm),
        },
    )

    response.headers["X-Request-Id"] = request_id
    return FileAnalyzeResponse(
        filename=filename,
        content_type=content_type,
        text_chars=len(extracted_norm),
        text_preview=preview,
        summary=summary_norm,
    )


@router.post("/quick-replies", response_model=QuickRepliesResponse)
@rate_limit(*RateLimitConfig.AI_CHAT, by_ip=True, by_user=False)
async def quick_replies(
    payload: QuickRepliesRequest,
    request: Request,
):
    _ = request
    user_text = str(payload.user_message or "")
    answer_text = str(payload.assistant_answer or "")
    haystack = (user_text + "\n" + answer_text).lower()

    replies: list[str] = []

    refs = payload.references or []
    if refs:
        ref0 = refs[0]
        law_name = str(getattr(ref0, "law_name", "") or "").strip()
        article = str(getattr(ref0, "article", "") or "").strip()
        if law_name and article:
            replies.append(f"《{law_name}》{article}的适用范围是什么？")

    if "离婚" in haystack or "婚姻" in haystack:
        replies.extend([
            "双方是否有子女？抚养权/抚养费怎么安排？",
            "有哪些共同财产与共同债务？请列一下金额与证据。",
            "是否有家暴/出轨/分居等情形？对应证据有哪些？",
        ])
    elif "劳动" in haystack or "工资" in haystack or "社保" in haystack:
        replies.extend([
            "是否签订劳动合同？入职时间、岗位、工资是多少？",
            "有没有考勤、聊天记录、工资条或转账记录？",
            "你希望的诉求是补发工资、赔偿还是恢复劳动关系？",
        ])
    elif "合同" in haystack or "违约" in haystack or "定金" in haystack:
        replies.extend([
            "合同是否书面？关键条款（金额/期限/违约责任）是什么？",
            "对方的违约行为具体是什么？造成了哪些损失？",
            "你现在掌握的证据有哪些（合同、付款凭证、聊天记录）？",
        ])
    elif "借" in haystack or "借款" in haystack or "欠" in haystack:
        replies.extend([
            "是否有借条/转账记录/聊天记录能证明借款关系？",
            "约定的还款期限与利息是多少？是否逾期？",
            "对方目前是否有可执行财产线索？",
        ])
    else:
        replies.extend([
            "需要准备哪些证据？",
            "请给出可操作的处理步骤（先协商/调解/仲裁/起诉）。",
            "这个问题的诉讼/仲裁时效一般是多久？",
        ])

    seen: set[str] = set()
    out: list[str] = []
    for r in replies:
        s = str(r).strip()
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= 6:
            break

    return QuickRepliesResponse(replies=out)


@router.post("/messages/rate", response_model=RatingResponse)
async def rate_message(
    request: RatingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    评价AI回复

    - **message_id**: 消息ID（必须是assistant角色的消息）
    - **rating**: 评分 1=差评, 2=一般, 3=好评
    - **feedback**: 反馈内容（可选）
    """
    result = await db.execute(
        select(ChatMessage, Consultation.user_id)
        .join(Consultation, ChatMessage.consultation_id == Consultation.id)
        .where(ChatMessage.id == request.message_id)
    )
    row = cast(tuple[ChatMessage, int | None] | None, result.first())
    if row is None:
        message = None
        owner_user_id = None
    else:
        message, owner_user_id = row

    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")

    if owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限评价该消息")

    message_role = cast(str, cast(object, getattr(message, "role", "")))
    if message_role != "assistant":
        raise HTTPException(status_code=400, detail="只能评价AI回复")

    setattr(message, "rating", request.rating)
    setattr(message, "feedback", request.feedback)

    # 记录AI质量监控评分
    try:
        from ...middleware.ai_quality_middleware import get_ai_logger
        ai_logger = get_ai_logger()
        if ai_logger is not None:
            # 从消息的references中获取request_id
            refs_json = cast(str | None, getattr(message, "references", None))
            request_id = ""
            if refs_json:
                try:
                    refs_data = json.loads(refs_json)
                    request_id = str(
                        refs_data.get(
                            "meta", {}).get(
                            "request_id", ""))
                except (json.JSONDecodeError, AttributeError):
                    pass

            is_positive = request.rating >= 2  # 2-3分为正面评价
            ai_logger.log_feedback(
                request_id=request_id,
                is_positive=is_positive,
                feedback_text=request.feedback,
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"AI质量评分日志记录失败: {e}")

    await db.commit()

    rating_text = {1: "差评", 2: "一般", 3: "好评"}.get(request.rating, "")
    return RatingResponse(message=f"感谢您的{rating_text}反馈！")


@router.get("/integration/stats")
async def get_integration_stats(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    获取用户的模块联动统计

    返回各类联动功能的使用情况：
    - pending_workflows: 待完成的工作流数量
    - lawyer_referrals: 律师推荐次数
    - document_lawyer_referrals: 文书→律师推荐次数
    - forum_ai_referrals: 论坛→AI推荐次数
    - completed_documents: 已完成的文书数量
    """
    from ...services.integration.module_integration import get_integration_service

    integration_service = get_integration_service()
    stats = integration_service.get_integration_stats(int(current_user.id))

    return stats
