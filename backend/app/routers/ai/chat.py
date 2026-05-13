from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Optional, Annotated

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.ai.session import SessionManager
from app.services.ai.core import AICore
from app.services.ai.knowledge_base import LegalKnowledgeBase
from app.utils.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Chat"])

_session_manager = SessionManager(max_sessions=200, max_messages_per_session=50)
_knowledge_base: Optional[LegalKnowledgeBase] = None
_openai_client = None


def _get_settings():
    from app.config.settings import settings
    return settings


def _get_openai_client():
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    try:
        from openai import OpenAI
        _settings = _get_settings()
        api_key = getattr(_settings, "openai_api_key", "") or ""
        base_url = getattr(_settings, "openai_base_url", "") or ""
        if not api_key:
            return None
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        _openai_client = OpenAI(**kwargs)
        return _openai_client
    except Exception as e:
        logger.warning(f"OpenAI客户端初始化失败: {e}")
        return None


def _get_knowledge_base():
    global _knowledge_base
    if _knowledge_base is not None:
        return _knowledge_base
    try:
        _settings = _get_settings()
        api_key = getattr(_settings, "openai_api_key", "") or ""
        base_url = getattr(_settings, "openai_base_url", "") or ""
        _knowledge_base = LegalKnowledgeBase(api_key=api_key, base_url=base_url)
        return _knowledge_base
    except Exception:
        return None


def _build_references(kb, query: str) -> list[dict]:
    if kb is None:
        return []
    try:
        results = kb.query(query, top_k=3)
        if not results:
            return []
        refs = []
        for content, metadata, score in results:
            refs.append({
                "law_name": metadata.get("law_name", metadata.get("source", "")),
                "article": metadata.get("article", ""),
                "content": content[:500] if content else "",
                "similarity": round(float(score), 4) if score else 0,
            })
        return refs
    except Exception as e:
        logger.warning(f"知识库检索失败: {e}")
        return []


def _build_messages(session_id: str, user_message: str, kb, model: str = "deepseek-chat") -> list[dict]:
    history = _session_manager.get_history(session_id)
    normalized = _session_manager._normalize_history(history)

    is_deepseek = "deepseek" in model.lower()

    references = _build_references(kb, user_message)
    context_parts = []
    if references:
        context_parts.append("以下是与用户问题相关的法律条文参考：")
        for i, ref in enumerate(references, 1):
            context_parts.append(f"{i}. {ref['law_name']} {ref['article']}: {ref['content'][:300]}")
    context = "\n".join(context_parts) if context_parts else ""

    system_prompt = AICore.SYSTEM_PROMPT
    if context:
        system_prompt += f"\n\n{context}"

    if is_deepseek:
        system_msg = f"# System Prompt\n{system_prompt}\n\n---\n"
        history_text = ""
        for msg in normalized:
            role = "用户" if msg["role"] == "user" else "助手"
            history_text += f"{role}: {msg['content']}\n"
        user_content = f"{history_text}用户: {user_message}"
        messages = [{"role": "system", "content": system_msg + user_content}]
    else:
        messages = [{"role": "system", "content": system_prompt}]
        for msg in normalized:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

    return messages


@router.post("/chat")
async def chat(message: str = "", session_id: Optional[str] = None):
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    client = _get_openai_client()
    if client is None:
        raise HTTPException(status_code=503, detail={"message": "AI服务未配置，请设置 OPENAI_API_KEY"})

    _settings = _get_settings()
    model = getattr(_settings, "ai_model", "deepseek-chat") or "deepseek-chat"

    sid = _session_manager.get_or_create_session(session_id)
    kb = _get_knowledge_base()

    _session_manager.add_message(sid, "user", message.strip())

    messages = _build_messages(sid, message.strip(), kb, model)

    try:
        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )
        elapsed = time.time() - start

        answer = response.choices[0].message.content or ""
        usage = response.usage

        _session_manager.add_message(sid, "assistant", answer)

        references = _build_references(kb, message.strip())

        result = {
            "session_id": sid,
            "answer": answer,
            "references": references,
            "confidence": "high" if references else "medium",
            "model_used": model,
            "latency_ms": round(elapsed * 1000),
        }
        if usage:
            result["usage"] = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
        return result

    except Exception as e:
        logger.exception(f"AI对话失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(message: str = "", session_id: Optional[str] = None):
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    client = _get_openai_client()
    if client is None:
        async def _error():
            yield f"data: {json.dumps({'type': 'error', 'error': 'AI服务未配置'})}\n\n"
        return StreamingResponse(_error(), media_type="text/event-stream")

    _settings = _get_settings()
    model = getattr(_settings, "ai_model", "deepseek-chat") or "deepseek-chat"

    sid = _session_manager.get_or_create_session(session_id)
    kb = _get_knowledge_base()

    _session_manager.add_message(sid, "user", message.strip())

    messages = _build_messages(sid, message.strip(), kb, model)

    async def _generate():
        yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=True,
            )
            full_answer = ""
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_answer += delta.content
                    yield f"data: {json.dumps({'type': 'token', 'content': delta.content})}\n\n"
            _session_manager.add_message(sid, "assistant", full_answer)
            refs = _build_references(kb, message.strip())
            yield f"data: {json.dumps({'type': 'done', 'session_id': sid, 'references': refs})}\n\n"
        except Exception as e:
            logger.exception(f"流式对话失败")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/quick-replies")
async def quick_replies():
    return {"replies": ["拖欠工资怎么办", "被辞退如何维权", "工伤认定流程"]}


@router.get("/consultations")
async def list_consultations(
    q: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    if q is not None and len(q) > 200:
        raise HTTPException(status_code=400, detail="查询参数过长")
    sessions = []
    for sid, history in _session_manager.conversation_histories.items():
        title = "未命名对话"
        for msg in history:
            if msg.get("role") == "user" and msg.get("content"):
                title = str(msg["content"])[:50]
                break
        sessions.append({
            "id": hash(sid) % 100000,
            "session_id": sid,
            "title": title,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "message_count": len(history),
        })
    sessions.sort(key=lambda x: x["created_at"], reverse=True)
    return sessions[skip:skip + limit]


@router.get("/consultations/{session_id}")
async def get_consultation(session_id: str):
    if session_id not in _session_manager.conversation_histories:
        raise HTTPException(status_code=404, detail="Consultation not found")

    history = _session_manager.get_history(session_id)
    title = "未命名对话"
    for msg in history:
        if msg.get("role") == "user" and msg.get("content"):
            title = str(msg["content"])[:50]
            break

    messages = []
    for i, msg in enumerate(history):
        messages.append({
            "id": i + 1,
            "role": msg["role"],
            "content": msg["content"],
            "references": None,
            "created_at": "",
        })

    return {
        "id": hash(session_id) % 100000,
        "session_id": session_id,
        "title": title,
        "created_at": "",
        "updated_at": "",
        "messages": messages,
    }


@router.delete("/consultations/{session_id}")
async def delete_consultation(session_id: str):
    if session_id in _session_manager.conversation_histories:
        _session_manager.clear_session(session_id)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Consultation not found")