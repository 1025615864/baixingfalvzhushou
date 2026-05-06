"""文书服务"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models import LegalDocument, DocumentTemplate


class DocumentService:
    """文书服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        consultation_id: int,
        user_id: int,
        document_type: str,
        title: str,
        lawyer_id: Optional[int] = None,
        content: Optional[str] = None,
        file_path: Optional[str] = None,
        generated_by_ai: bool = False,
        ai_prompt: Optional[str] = None,
    ) -> LegalDocument:
        """创建文书"""
        document = LegalDocument(
            consultation_id=consultation_id,
            lawyer_id=lawyer_id,
            user_id=user_id,
            document_type=document_type,
            title=title,
            content=content,
            file_path=file_path,
            status="draft",
            generated_by_ai=generated_by_ai,
            ai_prompt=ai_prompt,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def get(self, document_id: int) -> Optional[LegalDocument]:
        """获取文书"""
        result = await self.db.execute(
            select(LegalDocument).where(LegalDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_by_consultation(
        self,
        consultation_id: int,
    ) -> List[LegalDocument]:
        """获取咨询的所有文书"""
        result = await self.db.execute(
            select(LegalDocument)
            .where(LegalDocument.consultation_id == consultation_id)
            .order_by(LegalDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_lawyer(
        self,
        lawyer_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[LegalDocument], int]:
        """获取律师的文书列表"""
        query = select(LegalDocument).where(LegalDocument.lawyer_id == lawyer_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(LegalDocument.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        documents = result.scalars().all()

        return list(documents), total

    async def update_content(
        self,
        document_id: int,
        content: str,
    ) -> Optional[LegalDocument]:
        """更新文书内容"""
        document = await self.get(document_id)
        if not document:
            return None

        document.content = content
        document.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def update_status(
        self,
        document_id: int,
        new_status: str,
    ) -> Optional[LegalDocument]:
        """更新文书状态"""
        document = await self.get(document_id)
        if not document:
            return None

        document.status = new_status
        document.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete(self, document_id: int) -> bool:
        """删除文书"""
        document = await self.get(document_id)
        if not document:
            return False

        await self.db.delete(document)
        await self.db.commit()
        return True


class TemplateService:
    """模板服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_category(
        self,
        category: str,
    ) -> List[DocumentTemplate]:
        """获取分类下的模板"""
        result = await self.db.execute(
            select(DocumentTemplate)
            .where(
                DocumentTemplate.category == category,
                DocumentTemplate.is_active == True,
            )
            .order_by(DocumentTemplate.name)
        )
        return list(result.scalars().all())

    async def get(self, template_id: int) -> Optional[DocumentTemplate]:
        """获取模板"""
        result = await self.db.execute(
            select(DocumentTemplate).where(DocumentTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[DocumentTemplate]:
        """获取所有模板"""
        result = await self.db.execute(
            select(DocumentTemplate)
            .where(DocumentTemplate.is_active == True)
            .order_by(DocumentTemplate.category, DocumentTemplate.name)
        )
        return list(result.scalars().all())