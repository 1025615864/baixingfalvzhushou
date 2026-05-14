from __future__ import annotations

import json
import re
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.document_template import DocumentTemplate, DocumentTemplateVersion
from ..models.document import GeneratedDocument
from ..models.contracts import ContractReviewHistory


def _template_to_dict(t: DocumentTemplate, version: DocumentTemplateVersion | None = None) -> dict:
    return {
        "id": str(t.id),
        "name": t.title,
        "category": t.key,
        "description": t.description,
        "download_count": version.usage_count if version else 0,
        "is_free": True,
        "price": 0,
        "preview_url": None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


def _template_detail_to_dict(t: DocumentTemplate, version: DocumentTemplateVersion | None = None) -> dict:
    d = _template_to_dict(t, version)
    if version:
        fields = json.loads(version.variables) if version.variables else []
        d["fields"] = fields
        d["content_preview"] = version.content
    else:
        d["fields"] = []
        d["content_preview"] = None
    return d


def _review_to_dict(r: ContractReviewHistory) -> dict:
    return {
        "id": r.id,
        "filename": r.filename,
        "contract_type": r.contract_type,
        "status": "completed" if r.report_json else "pending",
        "risk_level": r.risk_level,
        "risk_count": r.risk_count,
        "request_id": r.request_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _review_detail_to_dict(r: ContractReviewHistory) -> dict:
    d = _review_to_dict(r)
    d["text_chars"] = r.text_chars
    d["text_preview"] = r.text_preview
    d["report_json"] = r.report_json
    return d


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_latest_version(self, template_id: int) -> DocumentTemplateVersion | None:
        query = (
            select(DocumentTemplateVersion)
            .where(
                DocumentTemplateVersion.template_id == template_id,
                DocumentTemplateVersion.is_published == True,
            )
            .order_by(DocumentTemplateVersion.version.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_templates(
        self,
        page: int = 1,
        page_size: int = 10,
        category: str | None = None,
        keyword: str | None = None,
    ) -> dict:
        query = select(DocumentTemplate).where(DocumentTemplate.is_active == True)
        count_query = select(func.count()).select_from(DocumentTemplate).where(DocumentTemplate.is_active == True)

        if category:
            query = query.where(DocumentTemplate.key == category)
            count_query = count_query.where(DocumentTemplate.key == category)

        if keyword:
            pattern = f"%{keyword}%"
            kw_filter = or_(
                DocumentTemplate.title.ilike(pattern),
                DocumentTemplate.description.ilike(pattern),
            )
            query = query.where(kw_filter)
            count_query = count_query.where(kw_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(DocumentTemplate.created_at.desc())
        result = await self.db.execute(query)
        templates = result.scalars().all()

        items = []
        for t in templates:
            version = await self._get_latest_version(t.id)
            items.append(_template_to_dict(t, version))

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def get_template_detail(self, template_id: int) -> dict:
        template = await self.db.get(DocumentTemplate, template_id)
        if template is None:
            raise HTTPException(status_code=404, detail="模板不存在")
        version = await self._get_latest_version(template.id)
        return _template_detail_to_dict(template, version)

    async def generate_document(self, user_id: int, template_id: int, fields: dict) -> dict:
        template = await self.db.get(DocumentTemplate, template_id)
        if template is None:
            raise HTTPException(status_code=404, detail="模板不存在")

        version = await self._get_latest_version(template.id)
        content = version.content if version else ""

        content = re.sub(
            r"\{\{(\w+)\}\}",
            lambda m: str(fields.get(m.group(1), m.group(0))),
            content,
        )

        doc = GeneratedDocument(
            user_id=user_id,
            document_type=template.key,
            title=template.title + "（已生成）",
            content=content,
            template_key=template.key,
            template_version=version.version if version else 1,
            payload_json=json.dumps(fields, ensure_ascii=False),
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)

        return {
            "document_type": template.key,
            "title": doc.title,
            "content": content,
            "created_at": doc.created_at.isoformat() if doc.created_at else datetime.now().isoformat(),
            "template_key": template.key,
            "template_version": version.version if version else 1,
            "download_url": f"/api/documents/download/{template.key}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx",
        }

    async def get_categories(self) -> dict:
        query = select(DocumentTemplate.key).where(DocumentTemplate.is_active == True).distinct()
        result = await self.db.execute(query)
        keys = [row[0] for row in result.all()]

        categories = []
        for key in keys:
            count_result = await self.db.execute(
                select(func.count())
                .select_from(DocumentTemplate)
                .where(DocumentTemplate.is_active == True, DocumentTemplate.key == key)
            )
            count = count_result.scalar() or 0
            categories.append({"key": key, "name": key, "description": "", "count": count})

        return {"categories": categories}

    async def get_contract_reviews(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: str | None = None,
    ) -> dict:
        query = select(ContractReviewHistory).where(ContractReviewHistory.user_id == user_id)
        count_query = (
            select(func.count())
            .select_from(ContractReviewHistory)
            .where(ContractReviewHistory.user_id == user_id)
        )

        if status == "completed":
            query = query.where(ContractReviewHistory.report_json.isnot(None))
            count_query = count_query.where(ContractReviewHistory.report_json.isnot(None))
        elif status == "pending":
            query = query.where(ContractReviewHistory.report_json.is_(None))
            count_query = count_query.where(ContractReviewHistory.report_json.is_(None))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(ContractReviewHistory.created_at.desc())
        result = await self.db.execute(query)
        reviews = result.scalars().all()

        items = [_review_to_dict(r) for r in reviews]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def submit_contract_review(self, user_id: int, data: dict) -> dict:
        review = ContractReviewHistory(
            user_id=user_id,
            filename=data.get("filename", ""),
            contract_type=data.get("contract_type"),
            content_type=data.get("content_type"),
            text_chars=data.get("text_chars", 0),
            text_preview=data.get("text_preview", ""),
            risk_level="low",
            risk_count=0,
            report_json=None,
            report_markdown="",
            request_id=data.get("request_id", uuid.uuid4().hex),
            focus=data.get("focus"),
        )
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)

        return {
            "review_id": review.id,
            "request_id": review.request_id,
            "status": "pending",
            "message": "合同已提交审查，预计30秒内完成",
            "estimated_seconds": 30,
            "created_at": review.created_at.isoformat() if review.created_at else datetime.now().isoformat(),
        }

    async def get_contract_review_detail(self, user_id: int, review_id: str) -> dict:
        review = await self.db.get(ContractReviewHistory, review_id)
        if review is None:
            raise HTTPException(status_code=404, detail="审查记录不存在")
        if review.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问该审查记录")
        return _review_detail_to_dict(review)

    async def get_contract_templates(self) -> dict:
        contract_keys = ["contract", "lease", "nda", "employment", "loan", "cooperation"]
        query = select(DocumentTemplate).where(
            DocumentTemplate.is_active == True,
            DocumentTemplate.key.in_(contract_keys),
        )
        result = await self.db.execute(query)
        templates = result.scalars().all()

        items = []
        for t in templates:
            version = await self._get_latest_version(t.id)
            items.append({
                "id": str(t.id),
                "name": t.title,
                "category": t.key,
                "description": t.description,
                "download_count": version.usage_count if version else 0,
                "is_free": True,
            })

        return {"items": items, "total": len(items)}
