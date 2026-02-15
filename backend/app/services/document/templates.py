"""文书模板服务"""
from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.models.document_template import DocumentTemplate, DocumentTemplateVersion
from app.services.document_templates_builtin import BUILTIN_DOCUMENT_TEMPLATES

if TYPE_CHECKING:
    from app.schemas.document import DocumentItem


@dataclass
class TemplateList:
    items: list[SimpleNamespace]
    total: int
    page: int
    page_size: int


@dataclass
class TemplateStats:
    total_templates: int
    total_categories: int


@dataclass
class TemplateDetail:
    id: int
    key: str
    title: str | None
    description: str | None
    template: str | None
    category: str | None


class DocumentTemplateService:
    """文书模板服务"""

    def _builtin_items(self) -> list[SimpleNamespace]:
        """获取内置模板列表"""
        items: list[SimpleNamespace] = []
        for key, data in BUILTIN_DOCUMENT_TEMPLATES.items():
            items.append(
                SimpleNamespace(
                    id=len(items) + 1,
                    key=key,
                    title=data.get("title"),
                    description=data.get("description"),
                    template=data.get("template"),
                    category=data.get("title"),
                )
            )
        return items

    async def get_categories(self, db: AsyncSession) -> list[str]:
        """获取所有模板分类"""
        return [item.category for item in self._builtin_items()
                if item.category]

    async def get_templates_by_category(
        self,
        db: AsyncSession,
        *,
        category: str,
        page: int = 1,
        page_size: int = 20,
    ) -> TemplateList:
        """按分类获取模板"""
        items = [item for item in self._builtin_items()
                 if item.category == category]
        start = (page - 1) * page_size
        end = start + page_size
        return TemplateList(items=items[start:end], total=len(
            items), page=page, page_size=page_size)

    async def get_template_detail(
        self, db: AsyncSession, *, template_id: int
    ) -> SimpleNamespace | None:
        """获取模板详情"""
        items = self._builtin_items()
        return next((item for item in items if int(
            item.id) == int(template_id)), None)

    async def get_template_by_key(
        self, db: AsyncSession, *, template_key: str
    ) -> dict | None:
        """根据key获取模板"""
        # 先查数据库
        tpl_res = await db.execute(
            select(DocumentTemplate).where(
                DocumentTemplate.key == template_key,
                DocumentTemplate.is_active.is_(True),
            )
        )
        tpl = tpl_res.scalar_one_or_none()
        if tpl:
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
            if ver:
                return {
                    "type": str(tpl.key),
                    "name": str(tpl.title),
                    "description": str(tpl.description or ""),
                    "template": str(ver.content or ""),
                }

        # 回退到内置模板
        builtin = BUILTIN_DOCUMENT_TEMPLATES.get(template_key)
        if builtin:
            return {
                "type": template_key,
                "name": str(builtin.get("title") or template_key),
                "description": str(builtin.get("description") or ""),
                "template": str(builtin.get("template") or ""),
            }
        return None

    async def get_published_template_version(
        self, db: AsyncSession, *, template_key: str
    ) -> int | None:
        """获取已发布模板版本号"""
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
        try:
            return int(ver.version)
        except Exception:
            return None

    async def search_templates(
        self,
        db: AsyncSession,
        *,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
    ) -> TemplateList:
        """搜索模板"""
        items = [
            item
            for item in self._builtin_items()
            if keyword in (item.title or "") or keyword in (item.description or "")
        ]
        start = (page - 1) * page_size
        end = start + page_size
        return TemplateList(items=items[start:end], total=len(
            items), page=page, page_size=page_size)

    async def get_popular_templates(
        self, db: AsyncSession, *, limit: int = 10
    ) -> list[SimpleNamespace]:
        """获取热门模板"""
        return self._builtin_items()[:limit]

    async def get_all_templates_paginated(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> TemplateList:
        """分页获取所有模板"""
        items = self._builtin_items()
        start = (page - 1) * page_size
        end = start + page_size
        return TemplateList(items=items[start:end], total=len(
            items), page=page, page_size=page_size)

    async def get_recommended_templates(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        limit: int = 5,
    ) -> list[SimpleNamespace]:
        """获取推荐模板"""
        return self._builtin_items()[:limit]

    async def get_document_types(self, db: AsyncSession) -> list[dict]:
        """获取支持的文书类型列表"""
        try:
            res = await db.execute(
                select(DocumentTemplate)
                .where(DocumentTemplate.is_active.is_(True))
                .order_by(DocumentTemplate.id.asc())
            )
            templates = res.scalars().all()

            out: list[dict[str, str]] = []
            for t in templates:
                ver_res = await db.execute(
                    select(DocumentTemplateVersion)
                    .where(
                        DocumentTemplateVersion.template_id == int(t.id),
                        DocumentTemplateVersion.is_published.is_(True),
                    )
                    .order_by(DocumentTemplateVersion.version.desc())
                    .limit(1)
                )
                published = ver_res.scalar_one_or_none()
                if published is None:
                    continue
                out.append(
                    {
                        "type": str(t.key),
                        "name": str(t.title),
                        "description": str(t.description or ""),
                    }
                )

            if out:
                return out
        except Exception:
            pass

        return [
            {
                "type": str(key),
                "name": str(meta.get("title") or key),
                "description": str(meta.get("description") or ""),
            }
            for key, meta in BUILTIN_DOCUMENT_TEMPLATES.items()
        ]

    async def get_stats(self, db: AsyncSession) -> TemplateStats:
        """获取模板统计信息"""
        items = self._builtin_items()
        categories = {item.category for item in items if item.category}
        return TemplateStats(total_templates=len(
            items), total_categories=len(categories))


# 单例实例
document_template_service = DocumentTemplateService()
