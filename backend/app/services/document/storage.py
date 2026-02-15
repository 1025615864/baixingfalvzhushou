"""文书存储服务 - 文书生成 2.0"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import GeneratedDocument
from app.schemas.document import DocumentItem, DocumentListResponse

if TYPE_CHECKING:
    from app.models.user import User


class DocumentStorageService:
    """文书存储服务 - 支持版本管理"""

    async def save_document(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        document_type: str,
        title: str,
        content: str,
        template_key: str | None = None,
        template_version: int | None = None,
        payload: dict | None = None,
        parent_id: int | None = None,
        version_note: str | None = None,
    ) -> int:
        """保存生成的文书（支持版本管理）

        Args:
            db: 数据库会话
            user_id: 用户ID
            document_type: 文书类型
            title: 文书标题
            content: 文书内容
            template_key: 模板key
            template_version: 模板版本
            payload: 原始数据
            parent_id: 父版本ID（用于版本回看）
            version_note: 版本说明
        """
        if not document_type:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="document_type 不能为空")
        if not content:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="content 不能为空")

        payload_json: str | None = None
        if payload is not None:
            try:
                payload_json = json.dumps(payload, ensure_ascii=False)
            except Exception:
                payload_json = None

        # 计算版本号
        version = 1
        if parent_id:
            # 获取父文档的最大版本号
            parent_res = await db.execute(
                select(func.max(GeneratedDocument.version)).where(
                    GeneratedDocument.id == parent_id,
                    GeneratedDocument.user_id == user_id,
                )
            )
            max_version = parent_res.scalar() or 1
            version = max_version + 1

        doc = GeneratedDocument(
            user_id=user_id,
            document_type=str(document_type or "").strip(),
            title=str(title or "").strip() or "法律文书",
            content=str(content or "").strip(),
            template_key=template_key,
            template_version=template_version,
            payload_json=payload_json,
            parent_id=parent_id,
            version=version,
            version_note=version_note,
        )

        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return int(doc.id)

    async def list_user_documents(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        document_type: str | None = None,
    ) -> DocumentListResponse:
        """列出用户的文书（支持筛选）

        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            document_type: 文书类型筛选

        Returns:
            文书列表响应
        """
        page = max(1, int(page))
        page_size = max(1, min(100, int(page_size)))

        base = select(GeneratedDocument).where(
            GeneratedDocument.user_id == user_id)
        if document_type:
            base = base.where(GeneratedDocument.document_type == document_type)

        count_query = select(func.count()).select_from(base.subquery())
        total_result = await db.execute(count_query)
        total = int(total_result.scalar() or 0)

        q = base.order_by(
            GeneratedDocument.created_at.desc(),
            GeneratedDocument.id.desc())
        q = q.offset((page - 1) * page_size).limit(page_size)
        res = await db.execute(q)
        rows = res.scalars().all()

        items = [
            DocumentItem(
                id=int(x.id),
                document_type=str(x.document_type),
                title=str(x.title),
                created_at=x.created_at,
            )
            for x in rows
        ]
        return DocumentListResponse(items=items, total=total)

    async def get_document_versions(
        self,
        db: AsyncSession,
        *,
        doc_id: int,
        user_id: int,
    ) -> list[GeneratedDocument]:
        """获取文档的所有版本（用于版本回看）

        Args:
            db: 数据库会话
            doc_id: 文档ID
            user_id: 用户ID

        Returns:
            版本列表（按版本号升序）
        """
        # 获取根文档ID
        root_res = await db.execute(
            select(GeneratedDocument).where(
                GeneratedDocument.id == doc_id,
                GeneratedDocument.user_id == user_id,
            )
        )
        root_doc = root_res.scalar_one_or_none()
        if root_doc is None:
            return []

        # 查找所有相关版本
        res = await db.execute(
            select(GeneratedDocument)
            .where(
                (GeneratedDocument.id == doc_id) |
                (GeneratedDocument.parent_id == doc_id)
            )
            .where(GeneratedDocument.user_id == user_id)
            .order_by(GeneratedDocument.version.asc())
        )
        return list(res.scalars().all())

    async def create_new_version(
        self,
        db: AsyncSession,
        *,
        doc_id: int,
        user_id: int,
        content: str,
        title: str | None = None,
        version_note: str | None = None,
    ) -> int:
        """基于现有文档创建新版本（多轮收集）

        Args:
            db: 数据库会话
            doc_id: 源文档ID
            user_id: 用户ID
            content: 新版本内容
            title: 新版本标题（可选）
            version_note: 版本说明

        Returns:
            新版本的文档ID
        """
        return await self.save_document(
            db,
            user_id=user_id,
            document_type="",  # 将从源文档获取
            title=title or "",
            content=content,
            parent_id=doc_id,
            version_note=version_note,
        )

    async def get_document(
        self,
        db: AsyncSession,
        *,
        doc_id: int,
        user_id: int,
    ) -> GeneratedDocument | None:
        """获取用户文书详情

        Args:
            db: 数据库会话
            doc_id: 文书ID
            user_id: 用户ID

        Returns:
            文书对象或None
        """
        res = await db.execute(
            select(GeneratedDocument).where(
                GeneratedDocument.id == int(doc_id),
                GeneratedDocument.user_id == user_id,
            )
        )
        return res.scalar_one_or_none()

    async def get_document_for_export(
        self,
        db: AsyncSession,
        *,
        doc_id: int,
        user_id: int,
    ) -> tuple[str, str] | None:
        """获取文书用于导出

        Args:
            db: 数据库会话
            doc_id: 文书ID
            user_id: 用户ID

        Returns:
            (标题, 内容) 元组或None
        """
        res = await db.execute(
            select(GeneratedDocument).where(
                GeneratedDocument.id == int(doc_id),
                GeneratedDocument.user_id == user_id,
            )
        )
        doc = res.scalar_one_or_none()
        if doc is None:
            return None

        title = str(doc.title or "法律文书").strip() or "法律文书"
        content = str(doc.content or "")
        return (title, content)

    async def delete_document(
        self,
        db: AsyncSession,
        *,
        doc_id: int,
        user_id: int,
    ) -> bool:
        """删除文书

        Args:
            db: 数据库会话
            doc_id: 文书ID
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        res = await db.execute(
            select(GeneratedDocument).where(
                GeneratedDocument.id == int(doc_id),
                GeneratedDocument.user_id == user_id,
            )
        )
        doc = res.scalar_one_or_none()
        if doc is None:
            return False

        await db.delete(doc)
        await db.commit()
        return True


# 单例实例
document_storage_service = DocumentStorageService()
