"""文书核心服务 - 业务逻辑层"""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_templates_builtin import BUILTIN_DOCUMENT_TEMPLATES
from app.models.document_template import DocumentTemplate, DocumentTemplateVersion
from app.utils.rate_limiter import rate_limiter, get_client_ip

if TYPE_CHECKING:
    from fastapi import Request


# Guest quota configuration
def _get_int_env(key: str, default: int) -> int:
    raw = os.getenv(key, "").strip()
    if not raw:
        return int(default)
    try:
        return int(raw)
    except Exception:
        return int(default)


GUEST_DOCUMENT_GENERATE_LIMIT = _get_int_env(
    "GUEST_DOCUMENT_GENERATE_LIMIT", 0)
GUEST_DOCUMENT_GENERATE_WINDOW_SECONDS = _get_int_env(
    "GUEST_DOCUMENT_GENERATE_WINDOW_SECONDS", 60 * 60 * 24
)


class DocumentGenerationService:
    """文书生成服务"""

    async def _get_published_document_template(
        self, db: AsyncSession, *, template_key: str
    ) -> tuple[str, str | None, str, int] | None:
        """获取已发布的文书模板"""
        key = str(template_key or "").strip()
        if not key:
            return None

        tpl_res = await db.execute(
            select(DocumentTemplate).where(
                DocumentTemplate.key == key,
                DocumentTemplate.is_active.is_(True),
            )
        )
        tpl = tpl_res.scalar_one_or_none()
        if tpl is None:
            return None

        ver_res = await db.execute(
            select(DocumentTemplateVersion)
            .where(
                DocumentTemplateVersion.template_id == int(tpl.id),
                DocumentTemplateVersion.is_published.is_(True),
            )
            .order_by(DocumentTemplateVersion.version.desc())
            .limit(1)
        )
        ver = ver_res.scalar_one_or_none()
        if ver is None:
            return None

        content = str(ver.content or "").strip()
        if not content:
            return None

        return (str(tpl.title), tpl.description, content, int(ver.version))

    async def _enforce_guest_document_quota(
        self,
        request: Request,
        *,
        limit: int | None = None,
        window_seconds: int | None = None,
    ) -> None:
        """强制执行游客文书生成配额"""
        limit_value = int(limit) if limit is not None else int(
            GUEST_DOCUMENT_GENERATE_LIMIT)
        window_value = (
            int(window_seconds)
            if window_seconds is not None
            else int(GUEST_DOCUMENT_GENERATE_WINDOW_SECONDS)
        )
        if limit_value <= 0:
            return

        key = f"doc:guest:{get_client_ip(request)}"
        allowed, remaining, wait_time = await rate_limiter.check(
            key,
            limit_value,
            window_value,
        )
        if allowed:
            return
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="游客模式文书生成次数已用尽，请登录后继续",
            headers={
                "X-RateLimit-Limit": str(limit_value),
                "X-RateLimit-Remaining": str(max(0, remaining)),
                "X-RateLimit-Reset": str(int(time.time() + wait_time)),
                "Retry-After": str(int(wait_time)),
            },
        )

    async def generate_document_content(
        self,
        db: AsyncSession,
        *,
        document_type: str,
        plaintiff_name: str,
        defendant_name: str,
        case_type: str,
        facts: str,
        claims: str,
        evidence: str | None = None,
    ) -> dict:
        """生成文书内容"""
        template_key = str(document_type or "").strip()
        if not template_key:
            raise HTTPException(status_code=400, detail="document_type 不能为空")

        if len(facts) > 8000 or len(claims) > 4000 or (
                evidence and len(evidence) > 4000):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="输入内容过长，请缩短事实/诉求/证据描述"
            )

        template_title: str | None = None
        template_content: str | None = None
        template_version: int | None = None

        db_template = await self._get_published_document_template(db, template_key=template_key)
        if db_template is not None:
            template_title, _desc, template_content, template_version = db_template
        else:
            builtin = BUILTIN_DOCUMENT_TEMPLATES.get(template_key)
            if builtin is not None:
                template_title = str(builtin.get("title") or template_key)
                template_content = str(
                    builtin.get("template") or "").strip() or None

        if template_content is None or template_title is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文书类型: {template_key}",
            )

        # 准备证据部分
        evidence_section = ""
        evidence_count = 0
        if evidence:
            evidence_section = f"证据及证据说明：\n{evidence}"
            evidence_count = len(evidence.split('\n'))

        # 根据案件类型确定法院名称
        court_name = "人民法院"

        # 格式化日期
        date_str = datetime.now().strftime("%Y年%m月%d日")

        # 填充模板
        content = template_content.format(
            plaintiff_name=plaintiff_name,
            defendant_name=defendant_name,
            case_type=case_type,
            facts=facts,
            claims=claims,
            evidence_section=evidence_section,
            evidence_count=evidence_count if evidence_count > 0 else "若干",
            court_name=court_name,
            date=date_str,
        )

        return {
            "document_type": template_key,
            "title": template_title,
            "content": content,
            "created_at": datetime.now(),
            "template_key": template_key,
            "template_version": template_version,
        }


# 单例实例
document_generation_service = DocumentGenerationService()
