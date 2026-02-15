"""数据种子功能"""
import logging

from sqlalchemy import func, select

from .engine import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def seed_document_templates() -> None:
    """初始化内置文书模板
    
    将内置文书模板种子到数据库中。
    """
    try:
        from ..models.document_template import DocumentTemplate, DocumentTemplateVersion
        from ..services.document_templates_builtin import BUILTIN_DOCUMENT_TEMPLATES

        async with AsyncSessionLocal() as session:
            for key, meta in BUILTIN_DOCUMENT_TEMPLATES.items():
                k = str(key or "").strip()
                if not k:
                    continue

                tpl_res = await session.execute(
                    select(DocumentTemplate).where(DocumentTemplate.key == k)
                )
                tpl = tpl_res.scalar_one_or_none()
                if tpl is None:
                    tpl = DocumentTemplate(
                        key=k,
                        title=str(meta.get("title") or k).strip() or k,
                        description=str(meta.get("description") or "").strip() or None,
                        is_active=True,
                    )
                    session.add(tpl)
                    await session.flush()

                pub_res = await session.execute(
                    select(DocumentTemplateVersion)
                    .where(
                        DocumentTemplateVersion.template_id == int(tpl.id),
                        DocumentTemplateVersion.is_published.is_(True),
                    )
                    .order_by(DocumentTemplateVersion.version.desc())
                    .limit(1)
                )
                published = pub_res.scalar_one_or_none()
                if published is not None:
                    continue

                max_res = await session.execute(
                    select(func.max(DocumentTemplateVersion.version)).where(
                        DocumentTemplateVersion.template_id == int(tpl.id)
                    )
                )
                max_version = max_res.scalar_one_or_none()

                if max_version is None:
                    v = DocumentTemplateVersion(
                        template_id=int(tpl.id),
                        version=1,
                        content=str(meta.get("template") or "").strip(),
                        is_published=True,
                    )
                    if v.content:
                        session.add(v)
                    continue

                versions_res = await session.execute(
                    select(DocumentTemplateVersion).where(
                        DocumentTemplateVersion.template_id == int(tpl.id)
                    )
                )
                versions = versions_res.scalars().all()
                target = None
                for ver in versions:
                    ver.is_published = False
                    session.add(ver)
                    if int(ver.version) == int(max_version):
                        target = ver

                if target is not None:
                    target.is_published = True
                    session.add(target)

            await session.commit()
    except Exception:
        logger.exception("文书模板seed失败")


async def seed_all() -> None:
    """执行所有数据种子操作"""
    await seed_document_templates()