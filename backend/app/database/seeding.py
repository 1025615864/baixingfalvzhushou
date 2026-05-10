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
    await seed_core_system_configs()
    await seed_core_knowledge_categories()


async def seed_core_system_configs() -> None:
    """初始化核心系统配置"""
    try:
        from ..models.system import SystemConfig
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            core_configs = [
                ("site_name", "百姓法律助手", "general"),
                ("site_description", "一站式法律服务平台", "general"),
                ("default_ai_model", "gpt-4o-mini", "ai"),
                ("ai_daily_free_limit", "5", "ai"),
                ("notification_enabled", "true", "notification"),
                ("forum_post_review_enabled", "true", "forum"),
                ("payment_alipay_enabled", "true", "payment"),
                ("payment_wechat_enabled", "true", "payment"),
            ]
            for key, value, category in core_configs:
                existing = (
                    await session.execute(select(SystemConfig).where(SystemConfig.key == key))
                ).scalar_one_or_none()
                if existing is None:
                    session.add(SystemConfig(key=key, value=value, category=category))
            await session.commit()
    except Exception:
        logger.exception("核心系统配置seed失败")


async def seed_core_knowledge_categories() -> None:
    """初始化核心知识分类"""
    try:
        from ..models.knowledge import KnowledgeCategory
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            categories = [
                ("民法典", "civil-code", 1),
                ("劳动法", "labor-law", 2),
                ("合同法", "contract-law", 3),
                ("婚姻家庭", "marriage-family", 4),
                ("侵权责任", "tort-liability", 5),
                ("消费者权益", "consumer-rights", 6),
                ("刑法", "criminal-law", 7),
                ("交通法规", "traffic-law", 8),
            ]
            for name, slug, sort_order in categories:
                existing = (
                    await session.execute(select(KnowledgeCategory).where(KnowledgeCategory.slug == slug))
                ).scalar_one_or_none()
                if existing is None:
                    session.add(KnowledgeCategory(name=name, slug=slug, sort_order=sort_order, is_active=True))
            await session.commit()
    except Exception:
        logger.exception("核心知识分类seed失败")