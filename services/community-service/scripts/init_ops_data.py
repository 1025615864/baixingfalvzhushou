"""初始化社区服务运营数据脚本

用法:
    cd services/community-service
    python -m scripts.init_ops_data

功能:
    1. 创建初始话题分类
    2. 创建示例种子帖子
    3. 创建初始运营配置
    4. 创建管理员运营角色
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.topic import Topic
from app.models.post import Post
from app.models.ops_models import OpsConfig, OpsRole
from app.utils.sensitive_words import SensitiveWordFilter


INITIAL_TOPICS = [
    {
        "name": "婚姻家庭",
        "slug": "marriage-family",
        "description": "婚姻、离婚、子女抚养、家庭纠纷等法律咨询",
        "icon": "family",
        "is_active": True,
        "sort_order": 1,
    },
    {
        "name": "劳动纠纷",
        "slug": "labor-disputes",
        "description": "劳动合同、工资福利、工伤赔偿、劳动仲裁等",
        "icon": "briefcase",
        "is_active": True,
        "sort_order": 2,
    },
    {
        "name": "房产纠纷",
        "slug": "property-disputes",
        "description": "买房卖房、租房、物业纠纷、拆迁安置等",
        "icon": "home",
        "is_active": True,
        "sort_order": 3,
    },
    {
        "name": "债务纠纷",
        "slug": "debt-disputes",
        "description": "民间借贷、债务追讨、担保纠纷等",
        "icon": "credit-card",
        "is_active": True,
        "sort_order": 4,
    },
    {
        "name": "交通事故",
        "slug": "traffic-accidents",
        "description": "交通事故责任、人身损害赔偿、保险理赔等",
        "icon": "car",
        "is_active": True,
        "sort_order": 5,
    },
    {
        "name": "刑事辩护",
        "slug": "criminal-defense",
        "description": "刑事案件咨询、辩护代理、取保候审等",
        "icon": "shield",
        "is_active": True,
        "sort_order": 6,
    },
    {
        "name": "法律常识",
        "slug": "legal-knowledge",
        "description": "普法宣传、法律知识普及、案例分析",
        "icon": "book",
        "is_active": True,
        "sort_order": 7,
    },
    {
        "name": "免费咨询",
        "slug": "free-consultation",
        "description": "公益法律援助、低收入群体法律帮扶",
        "icon": "heart",
        "is_active": True,
        "sort_order": 8,
    },
]

SAMPLE_POSTS = [
    {
        "title": "离婚时房产如何分割？",
        "content": """我结婚5年，老公在婚前付了首付买房，婚后我们一起还贷款。现在要离婚，房子该怎么分？

请问律师：
1. 首付算婚前财产吗？
2. 婚后还贷的部分怎么计算？
3. 如果房子归我，需要补偿对方多少钱？

希望有经验的律师帮忙解答，谢谢！""",
        "category": "婚姻家庭",
        "tags": ["离婚", "房产分割", "婚后财产"],
        "user_id": 1,
        "author_name": "热心网友",
        "status": "published",
    },
    {
        "title": "公司拖欠工资3个月了怎么办？",
        "content": """我在一家私企工作快2年了，从去年11月开始公司就以各种理由拖欠工资，到现在累计已经欠了3个月了。

老板总是说下个月一定发，但从来没有兑现过。我们员工应该怎么维权？

1. 申请劳动仲裁需要准备什么材料？
2. 如果公司破产了，工资还能要回来吗？
3. 能否要求公司支付经济补偿金？

请各位律师指点！""",
        "category": "劳动纠纷",
        "tags": ["拖欠工资", "劳动仲裁", "维权"],
        "user_id": 2,
        "author_name": "打工人小李",
        "status": "published",
    },
    {
        "title": "电动车被机动车撞了，对方全责，怎么索赔？",
        "content": """上周我骑电动车正常行驶，被一辆闯红灯的小轿车撞了。交警认定对方全责。

我受了轻伤，医药费花了2000多，电动车也坏了。

请问：
1. 除了医药费，还能索赔哪些项目？
2. 误工费怎么计算？
3. 如果对方不配合赔偿怎么办？

谢谢大家！""",
        "category": "交通事故",
        "tags": ["交通事故", "人身损害", "索赔"],
        "user_id": 3,
        "author_name": "受伤的骑士",
        "status": "published",
    },
]

INITIAL_OPS_CONFIG = {
    "community.rules": {
        "post_min_length": 20,
        "post_max_length": 50000,
        "comment_max_length": 2000,
        "posts_per_day_limit": 5,
        "comments_per_hour_limit": 20,
        "new_user_post_delay_hours": 24,
        "auto_close_days": 90,
        "require_approval_for_new_users": False,
        "allow_anonymous_view": True,
        "lawyer_badge_enabled": True,
    },
    "auto_moderation.config": {
        "ai_review_enabled": True,
        "ai_confidence_threshold": 0.7,
        "auto_reject_threshold": 0.95,
        "new_user_always_review": True,
        "reported_threshold": 3,
        "link_in_post_trigger_review": True,
    },
}

SENSITIVE_WORDS = [
    "毒品", "赌博", "诈骗", "传销", "色情",
    "暴力", "恐怖", "反动", "谣言", "造谣",
]


async def create_topics(session: AsyncSession):
    print("创建初始话题...")
    for topic_data in INITIAL_TOPICS:
        result = await session.execute(
            select(Topic).where(Topic.slug == topic_data["slug"])
        )
        existing = result.scalar_one_or_none()
        if not existing:
            topic = Topic(**topic_data)
            session.add(topic)
            print(f"  + 话题: {topic_data['name']}")
    await session.commit()
    print("话题创建完成！\n")


async def create_sample_posts(session: AsyncSession):
    print("创建示例帖子...")
    for post_data in SAMPLE_POSTS:
        post = Post(**post_data)
        session.add(post)
        print(f"  + 帖子: {post_data['title'][:30]}...")
    await session.commit()
    print("示例帖子创建完成！\n")


async def create_ops_config(session: AsyncSession):
    print("创建运营配置...")
    for key, value in INITIAL_OPS_CONFIG.items():
        result = await session.execute(
            select(OpsConfig).where(OpsConfig.key == key)
        )
        existing = result.scalar_one_or_none()
        if not existing:
            config = OpsConfig(
                key=key,
                value=json.dumps(value),
                description=f"初始化配置: {key}",
            )
            session.add(config)
            print(f"  + 配置: {key}")
    await session.commit()
    print("运营配置创建完成！\n")


async def create_admin_role(session: AsyncSession, admin_user_id: int = 1):
    print("创建管理员运营角色...")
    result = await session.execute(
        select(OpsRole).where(
            OpsRole.user_id == admin_user_id,
            OpsRole.role == "community_director"
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        role = OpsRole(
            user_id=admin_user_id,
            role="community_director",
            assigned_by=admin_user_id,
            is_active=True,
        )
        session.add(role)
        print(f"  + 用户 {admin_user_id} 已成为社区运营总监")
    await session.commit()
    print("管理员角色创建完成！\n")


def init_sensitive_words():
    print("初始化敏感词库...")
    filter_instance = SensitiveWordFilter()
    added = filter_instance.add_words(SENSITIVE_WORDS)
    print(f"  + 已添加 {added} 个敏感词")
    print("敏感词库初始化完成！\n")


async def main():
    print("=" * 50)
    print("社区服务运营数据初始化")
    print("=" * 50)
    print()

    async with AsyncSessionLocal() as session:
        await create_topics(session)
        await create_sample_posts(session)
        await create_ops_config(session)
        await create_admin_role(session)

    init_sensitive_words()

    print("=" * 50)
    print("所有初始化完成！")
    print("=" * 50)
    print()
    print("下一步:")
    print("  1. 运行数据库迁移: alembic upgrade head")
    print("  2. 启动服务: python -m uvicorn app.main:app")
    print()


if __name__ == "__main__":
    asyncio.run(main())
