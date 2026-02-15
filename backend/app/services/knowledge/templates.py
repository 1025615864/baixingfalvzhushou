"""知识库咨询模板服务

提供咨询模板的 CRUD 操作
"""
import json
import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.knowledge import ConsultationTemplate
from ...schemas.knowledge import (
    ConsultationTemplateCreate,
    ConsultationTemplateUpdate,
    TemplateQuestionItem,
)

logger = logging.getLogger(__name__)


class KnowledgeTemplateService:
    """咨询模板服务"""

    async def create_template(
        self,
        db: AsyncSession,
        data: ConsultationTemplateCreate
    ) -> ConsultationTemplate:
        """创建咨询模板"""
        template = ConsultationTemplate(
            name=data.name,
            description=data.description,
            category=data.category,
            icon=data.icon,
            questions=json.dumps([q.model_dump()
                                 for q in data.questions], ensure_ascii=False),
            sort_order=data.sort_order,
            is_active=data.is_active,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    async def get_template(
        self,
        db: AsyncSession,
        template_id: int
    ) -> ConsultationTemplate | None:
        """获取单个咨询模板"""
        result = await db.execute(
            select(ConsultationTemplate).where(
                ConsultationTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        db: AsyncSession,
        category: str | None = None,
        is_active: bool | None = True
    ) -> List[ConsultationTemplate]:
        """获取咨询模板列表"""
        query = select(ConsultationTemplate)

        if category:
            query = query.where(ConsultationTemplate.category == category)

        if is_active is not None:
            query = query.where(ConsultationTemplate.is_active == is_active)

        query = query.order_by(
            ConsultationTemplate.sort_order,
            ConsultationTemplate.created_at)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_template(
        self,
        db: AsyncSession,
        template_id: int,
        data: ConsultationTemplateUpdate
    ) -> ConsultationTemplate | None:
        """更新咨询模板"""
        template = await self.get_template(db, template_id)
        if not template:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if "questions" in update_data and update_data["questions"]:
            update_data["questions"] = json.dumps(
                [q.model_dump() if hasattr(q, 'model_dump')
                 else q for q in update_data["questions"]],
                ensure_ascii=False
            )

        for key, value in update_data.items():
            setattr(template, key, value)

        await db.commit()
        await db.refresh(template)
        return template

    async def delete_template(
        self,
        db: AsyncSession,
        template_id: int
    ) -> bool:
        """删除咨询模板"""
        template = await self.get_template(db, template_id)
        if not template:
            return False

        await db.delete(template)
        await db.commit()
        return True

    def parse_template_questions(
            self,
            template: ConsultationTemplate) -> List[TemplateQuestionItem]:
        """解析模板问题列表"""
        try:
            questions_data = json.loads(template.questions)
            return [TemplateQuestionItem(**q) for q in questions_data]
        except Exception:
            return []


# 单例
knowledge_template_service = KnowledgeTemplateService()
