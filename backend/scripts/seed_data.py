"""数据库种子数据脚本"""
# pyright: ignore
import argparse
import os
import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.models.forum import Post
from app.models.news import News
from app.models.lawfirm import LawFirm, Lawyer
from app.models.payment import UserBalance
from app.models.system import SystemConfig
from app.utils.security import hash_password
from app.models.consultation import Consultation, ChatMessage
from app.models.document import GeneratedDocument
from app.models.document_template import DocumentTemplate, DocumentTemplateVersion
from app.models.calendar import CalendarReminder
from app.models.feedback import FeedbackTicket
from app.models.notification import Notification, NotificationType
from app.models.payment import BalanceTransaction, PaymentOrder
from app.models.system import SearchHistory, UserActivity
from app.models import PointsProduct


async def upsert_system_config(
    db: AsyncSession,
    *,
    key: str,
    value: str,
    description: str,
    category: str,
) -> None:
    existing = (
        await db.execute(select(SystemConfig).where(SystemConfig.key == str(key)))
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            SystemConfig(
                key=str(key),
                value=str(value),
                description=str(description),
                category=str(category),
            )
        )
    else:
        existing.value = str(value)
        if not existing.description:
            existing.description = str(description)
        if not existing.category:
            existing.category = str(category)
        db.add(existing)


async def apply_e2e_defaults(db: AsyncSession) -> None:
    if str(os.getenv("E2E_SEED", "")).strip() != "1":
        return
    await upsert_system_config(
        db,
        key="forum.review.enabled",
        value="true",
        description="论坛评论审核开关",
        category="forum",
    )
    await upsert_system_config(
        db,
        key="forum.post_review.enabled",
        value="true",
        description="论坛帖子审核开关",
        category="forum",
    )
    await upsert_system_config(
        db,
        key="forum.post_review.mode",
        value="rule",
        description="论坛帖子审核模式（all/rule）",
        category="forum",
    )
    await upsert_system_config(
        db,
        key="enable_notifications",
        value="true",
        description="通知功能开关（用于 demo/试用）",
        category="notification",
    )
    await upsert_system_config(
        db,
        key="CONSULT_REVIEW_SLA_JSON",
        value='{"pending_sla_minutes": 1440, "claimed_sla_minutes": 720, "remind_before_minutes": 60}',
        description="律师复核任务 SLA（demo 默认值）",
        category="reviews",
    )


async def create_users(db: AsyncSession):
    """创建测试用户"""
    now = datetime.now(timezone.utc)
    users = [
        User(
            username="admin",
            email="admin@baixinghelper.cn",
            nickname="管理员",
            hashed_password=hash_password("admin123"),
            role="admin",
            email_verified=True,
            email_verified_at=now,
            phone_verified=True,
            phone_verified_at=now,
            is_active=True
        ),
        User(
            username="lawyer1",
            email="lawyer1@baixinghelper.cn",
            nickname="李律师",
            hashed_password=hash_password("lawyer123"),
            role="lawyer",
            email_verified=True,
            email_verified_at=now,
            phone_verified=True,
            phone_verified_at=now,
            is_active=True
        ),
        User(
            username="user1",
            email="user1@baixinghelper.cn",
            nickname="张三",
            hashed_password=hash_password("user123"),
            role="user",
            is_active=True
        ),
    ]

    created = 0
    result_users: list[User] = []
    for user in users:
        existing = (
            await db.execute(select(User).where(User.username == user.username))
        ).scalar_one_or_none()
        if existing is None:
            db.add(user)
            result_users.append(user)
            created += 1
        else:
            existing.email = user.email
            existing.nickname = user.nickname
            existing.hashed_password = user.hashed_password
            existing.role = user.role
            if user.username in {"admin", "lawyer1"}:
                existing.email_verified = True
                existing.email_verified_at = now
                existing.phone_verified = True
                existing.phone_verified_at = now
            existing.is_active = user.is_active
            result_users.append(existing)

    await db.commit()
    for u in result_users:
        await db.refresh(u)

    print(f"✓ 创建/更新了 {len(result_users)} 个用户（新增 {created}）")
    return result_users


async def create_balances(db: AsyncSession, users: list[User]):
    """为测试用户创建/更新余额账户（便于本地联调余额支付）"""
    # 仅为普通用户预置余额，避免影响管理员/律师账号的演示
    default_balance_by_username: dict[str, float] = {
        "user1": 200.0,
    }

    touched = 0
    for u in users:
        amount = float(default_balance_by_username.get(u.username, 0.0))
        res = await db.execute(select(UserBalance).where(UserBalance.user_id == int(u.id)))
        bal = res.scalar_one_or_none()

        amount_cents = int(round(amount * 100))
        if bal is None:
            bal = UserBalance(
                user_id=int(u.id),
                balance=amount,
                frozen=0.0,
                total_recharged=amount,
                total_consumed=0.0,
                balance_cents=amount_cents,
                frozen_cents=0,
                total_recharged_cents=amount_cents,
                total_consumed_cents=0,
            )
            db.add(bal)
            touched += 1
        else:
            # 以脚本配置为准（可重复执行）
            bal.balance = amount
            bal.frozen = 0.0
            bal.total_recharged = max(float(getattr(bal, "total_recharged", 0.0) or 0.0), amount)
            bal.total_consumed = float(getattr(bal, "total_consumed", 0.0) or 0.0)

            bal.balance_cents = amount_cents
            bal.frozen_cents = 0
            bal.total_recharged_cents = max(int(getattr(bal, "total_recharged_cents", 0) or 0), amount_cents)
            bal.total_consumed_cents = int(getattr(bal, "total_consumed_cents", 0) or 0)
            db.add(bal)

    await db.commit()
    print(f"✓ 创建/更新了余额账户（新增 {touched}）")


async def create_news(db: AsyncSession):
    """创建测试新闻"""
    news_items = [
        News(
            title="民法典实施三周年：成效显著",
            summary="自2021年1月1日民法典正式实施以来，我国民事法律制度更加完善...",
            content="民法典作为新中国成立以来第一部以法典命名的法律...",
            category="法律动态",
            is_published=True,
            is_top=True,
            view_count=3420
        ),
        News(
            title="劳动合同法修订草案公开征求意见",
            summary="为进一步保障劳动者权益，劳动合同法修订草案现向社会公开征求意见...",
            content="根据经济社会发展需要，劳动合同法修订草案对现行法律进行了多处修改...",
            category="政策解读",
            is_published=True,
            view_count=2890
        ),
        News(
            title="最高法发布消费者权益保护典型案例",
            summary="最高人民法院发布10个消费者权益保护典型案例，涉及网购、预付卡等领域...",
            content="为充分发挥典型案例的示范引领作用，最高人民法院选取了10个典型案例...",
            category="案例分析",
            is_published=True,
            view_count=2156
        ),
    ]
    created = 0
    updated = 0
    for item in news_items:
        if getattr(item, "is_top", None) is None:
            item.is_top = False
        if getattr(item, "is_published", None) is None:
            item.is_published = True

        title = str(getattr(item, "title", "") or "").strip()
        if not title:
            continue
        existing = (
            await db.execute(select(News).where(News.title == title).order_by(News.id.asc()).limit(1))
        ).scalar_one_or_none()
        if existing is None:
            db.add(item)
            created += 1
        else:
            existing.summary = item.summary
            existing.content = item.content
            existing.category = item.category
            existing.is_published = bool(item.is_published) if item.is_published is not None else True
            existing.is_top = bool(item.is_top) if item.is_top is not None else False
            existing.view_count = int(getattr(item, "view_count", 0) or 0)
            db.add(existing)
            updated += 1
    await db.commit()
    print(f"✓ 创建/更新新闻：新增 {created}，更新 {updated}")


async def create_law_firms(db: AsyncSession):
    """创建测试律所"""
    firms = [
        LawFirm(
            name="北京正义律师事务所",
            description="专注于民商事诉讼、刑事辩护、知识产权保护等领域",
            address="北京市朝阳区建国路88号",
            city="北京",
            province="北京",
            phone="010-12345678",
            email="contact@zhengyilaw.com",
            rating=4.8,
            review_count=156,
            is_verified=True,
            is_active=True,
            specialties="民商事诉讼,刑事辩护,知识产权"
        ),
        LawFirm(
            name="上海明理律师事务所",
            description="为企业和个人提供全方位法律服务",
            address="上海市浦东新区陆家嘴环路1000号",
            city="上海",
            province="上海",
            phone="021-87654321",
            email="info@minglilaw.com",
            rating=4.6,
            review_count=98,
            is_verified=True,
            is_active=True,
            specialties="公司法务,合同纠纷,劳动争议"
        ),
    ]

    created = 0
    for firm in firms:
        existing = (
            await db.execute(select(LawFirm).where(LawFirm.name == firm.name))
        ).scalar_one_or_none()
        if existing is None:
            db.add(firm)
            created += 1
        else:
            existing.description = firm.description
            existing.address = firm.address
            existing.city = firm.city
            existing.province = firm.province
            existing.phone = firm.phone
            existing.email = firm.email
            existing.rating = firm.rating
            existing.review_count = firm.review_count
            existing.is_verified = firm.is_verified
            existing.is_active = firm.is_active
            existing.specialties = firm.specialties

    await db.commit()
    print(f"✓ 创建/更新了 {len(firms)} 个律所（新增 {created}）")


async def create_lawyers(db: AsyncSession, users: list[User]):
    lawyer_user = next((u for u in users if u.username == "lawyer1"), None)
    if lawyer_user is None:
        return

    firm = (
        await db.execute(select(LawFirm).order_by(LawFirm.id.asc()).limit(1))
    ).scalar_one_or_none()
    firm_id = int(firm.id) if firm else None

    existing = (
        await db.execute(select(Lawyer).where(Lawyer.user_id == int(lawyer_user.id)))
    ).scalar_one_or_none()

    if existing is None:
        db.add(
            Lawyer(
                user_id=int(lawyer_user.id),
                firm_id=firm_id,
                name=str(lawyer_user.nickname or lawyer_user.username or "律师"),
                consultation_fee=10.0,
                is_verified=True,
                is_active=True,
            )
        )
    else:
        existing.firm_id = firm_id
        existing.name = str(lawyer_user.nickname or lawyer_user.username or existing.name)
        existing.consultation_fee = float(getattr(existing, "consultation_fee", 10.0) or 10.0)
        existing.is_verified = True
        existing.is_active = True
        db.add(existing)

    await db.commit()
    print("✓ 创建/更新了 1 个律师资料（绑定 lawyer1）")


async def create_posts(db: AsyncSession, users: list):
    """创建测试帖子"""
    posts = [
        Post(
            title="劳动合同试用期被无故辞退怎么办？",
            content="我在一家公司工作了2个月，还在试用期内，昨天突然被通知辞退，没有任何理由...",
            category="劳动纠纷",
            user_id=users[2].id if len(users) > 2 else 1
        ),
        Post(
            title="离婚时房产如何分割？求助",
            content="我和丈夫结婚5年，现在准备离婚，婚后共同购买了一套房产，请问如何分割？",
            category="婚姻家庭",
            user_id=users[2].id if len(users) > 2 else 1
        ),
    ]
    created = 0
    updated = 0
    for post in posts:
        title = str(getattr(post, "title", "") or "").strip()
        user_id = int(getattr(post, "user_id", 0) or 0)
        if not title or user_id <= 0:
            continue
        existing = (
            await db.execute(
                select(Post)
                .where(Post.title == title, Post.user_id == user_id)
                .order_by(Post.id.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(post)
            created += 1
        else:
            existing.content = post.content
            existing.category = post.category
            existing.is_deleted = False
            db.add(existing)
            updated += 1
    await db.commit()
    print(f"✓ 创建/更新帖子：新增 {created}，更新 {updated}")


async def reset_demo_tables(db: AsyncSession) -> None:
    await db.execute(delete(BalanceTransaction))
    await db.execute(delete(PaymentOrder))
    await db.execute(delete(Notification))
    await db.execute(delete(ChatMessage))
    await db.execute(delete(Consultation))
    await db.execute(delete(GeneratedDocument))
    await db.execute(delete(DocumentTemplateVersion))
    await db.execute(delete(DocumentTemplate))
    await db.execute(delete(CalendarReminder))
    await db.execute(delete(FeedbackTicket))
    await db.execute(delete(SearchHistory))
    await db.execute(delete(UserActivity))
    await db.commit()
    print("✓ 已清理 demo 相关数据表")


async def seed_demo_data(db: AsyncSession, users: list[User]) -> None:
    user1 = next((u for u in users if getattr(u, "username", None) == "user1"), None)
    admin = next((u for u in users if getattr(u, "username", None) == "admin"), None)
    if user1 is None:
        return

    # 文书模板与版本（幂等）
    templates: list[dict[str, object]] = [
        {
            "key": "labor_contract_termination_notice",
            "title": "解除劳动合同通知书",
            "description": "用于解除劳动合同的通知书模板（demo）",
            "version": 1,
            "content": """解除劳动合同通知书\n\n致：{{employee_name}}\n\n您于 {{start_date}} 入职，岗位为 {{position}}。鉴于 {{reason}}，现依据《劳动合同法》及劳动合同约定，自 {{termination_date}} 起解除劳动合同。\n\n请于 {{handover_date}} 前完成工作交接。\n\n单位：{{company_name}}\n日期：{{today}}\n""",
        },
        {
            "key": "civil_complaint_basic",
            "title": "民事起诉状（通用）",
            "description": "民事起诉状通用模板（demo）",
            "version": 1,
            "content": """民事起诉状\n\n原告：{{plaintiff_name}}\n被告：{{defendant_name}}\n\n诉讼请求：\n1. {{claim_1}}\n2. {{claim_2}}\n\n事实与理由：\n{{facts}}\n\n此致\n{{court_name}}\n\n具状人：{{plaintiff_name}}\n日期：{{today}}\n""",
        },
    ]

    for t in templates:
        key = str(t.get("key") or "").strip()
        tpl = (
            await db.execute(select(DocumentTemplate).where(DocumentTemplate.key == key))
        ).scalar_one_or_none()
        if tpl is None:
            tpl = DocumentTemplate(
                key=key,
                title=str(t.get("title") or key),
                description=str(t.get("description") or "") or None,
                is_active=True,
            )
            db.add(tpl)
            await db.commit()
            await db.refresh(tpl)
        else:
            tpl.title = str(t.get("title") or tpl.title)
            tpl.description = str(t.get("description") or tpl.description or "") or None
            tpl.is_active = True
            db.add(tpl)
            await db.commit()

        ver_raw = t.get("version")
        ver = 1
        if isinstance(ver_raw, int):
            ver = ver_raw
        elif isinstance(ver_raw, str) and ver_raw.strip():
            ver = int(ver_raw.strip())
        content = str(t.get("content") or "")
        v = (
            await db.execute(
                select(DocumentTemplateVersion).where(
                    DocumentTemplateVersion.template_id == int(tpl.id),
                    DocumentTemplateVersion.version == ver,
                )
            )
        ).scalar_one_or_none()
        if v is None:
            db.add(
                DocumentTemplateVersion(
                    template_id=int(tpl.id),
                    version=ver,
                    content=content,
                    is_published=True,
                )
            )
        else:
            v.content = content
            v.is_published = True
            db.add(v)
        await db.commit()

    # 生成文书（幂等：按 user_id+title）
    docs: list[GeneratedDocument] = [
        GeneratedDocument(
            user_id=int(user1.id),
            document_type="template",
            title="解除劳动合同通知书（示例）",
            content="（示例）已根据模板生成：解除劳动合同通知书...",
            template_key="labor_contract_termination_notice",
            template_version=1,
            payload_json='{"employee_name": "张三", "company_name": "北京正义律师事务所"}',
        ),
        GeneratedDocument(
            user_id=int(user1.id),
            document_type="template",
            title="民事起诉状（示例）",
            content="（示例）民事起诉状正文...",
            template_key="civil_complaint_basic",
            template_version=1,
            payload_json='{"plaintiff_name": "张三", "defendant_name": "李四"}',
        ),
    ]
    for d in docs:
        existing = (
            await db.execute(
                select(GeneratedDocument)
                .where(
                    GeneratedDocument.user_id == int(d.user_id),
                    GeneratedDocument.title == str(d.title),
                )
                .order_by(GeneratedDocument.id.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(d)
        else:
            existing.document_type = d.document_type
            existing.content = d.content
            existing.template_key = d.template_key
            existing.template_version = d.template_version
            existing.payload_json = d.payload_json
            db.add(existing)
        await db.commit()

    # 日历提醒（幂等：按 user_id+title）
    now = datetime.now(timezone.utc).replace(microsecond=0)
    due_at = now + timedelta(days=7)
    remind_at = now + timedelta(days=6)
    cal_title = "合同到期提醒（demo）"
    cal = (
        await db.execute(
            select(CalendarReminder)
            .where(CalendarReminder.user_id == int(user1.id), CalendarReminder.title == cal_title)
            .order_by(CalendarReminder.id.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if cal is None:
        db.add(
            CalendarReminder(
                user_id=int(user1.id),
                title=cal_title,
                note="合同将于 7 天后到期，建议提前续签或办理解除手续。",
                due_at=due_at,
                remind_at=remind_at,
                is_done=False,
            )
        )
    else:
        cal.note = "合同将于 7 天后到期，建议提前续签或办理解除手续。"
        cal.due_at = due_at
        cal.remind_at = remind_at
        cal.is_done = False
        cal.done_at = None
        db.add(cal)
    await db.commit()

    # 反馈工单（幂等：按 user_id+subject）
    tickets: list[FeedbackTicket] = [
        FeedbackTicket(
            user_id=int(user1.id),
            subject="登录验证码收不到（demo）",
            content="我尝试登录，但邮箱验证码没有收到，是否可以帮忙排查？",
            status="open",
            admin_reply=None,
            admin_id=None,
        ),
        FeedbackTicket(
            user_id=int(user1.id),
            subject="建议：增加常用合同模板（demo）",
            content="希望增加：借款合同、劳动合同、租赁合同等常用模板。",
            status="closed",
            admin_reply="已收到建议，我们会在后续版本中逐步补充。",
            admin_id=int(admin.id) if admin is not None else None,
        ),
    ]
    for t in tickets:
        existing = (
            await db.execute(
                select(FeedbackTicket)
                .where(FeedbackTicket.user_id == int(t.user_id), FeedbackTicket.subject == str(t.subject))
                .order_by(FeedbackTicket.id.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(t)
        else:
            existing.content = t.content
            existing.status = t.status
            existing.admin_reply = t.admin_reply
            existing.admin_id = t.admin_id
            db.add(existing)
        await db.commit()

    # 咨询会话（幂等：按 session_id；消息每次重建）
    session_id = "demo_user1_session"
    consult = (
        await db.execute(select(Consultation).where(Consultation.session_id == session_id))
    ).scalar_one_or_none()
    if consult is None:
        consult = Consultation(
            user_id=int(user1.id),
            session_id=session_id,
            title="劳动合同解除咨询（demo）",
        )
        db.add(consult)
        await db.commit()
        await db.refresh(consult)
    else:
        consult.user_id = int(user1.id)  # type: ignore[assignment]
        consult.title = "劳动合同解除咨询（demo）"  # type: ignore[assignment]
        db.add(consult)
        await db.commit()
        await db.refresh(consult)

    await db.execute(delete(ChatMessage).where(ChatMessage.consultation_id == int(consult.id)))  # type: ignore[arg-type]
    await db.commit()
    db.add(
        ChatMessage(
            consultation_id=int(consult.id),  # type: ignore[arg-type]
            role="user",
            content="我在试用期被无故辞退，公司不赔偿合法么？",
            references=None,
        )
    )
    db.add(
        ChatMessage(
            consultation_id=int(consult.id),  # type: ignore[arg-type]
            role="assistant",
            content="一般需要结合是否符合法定解除条件、是否提前通知等因素。建议先确认解除理由及证据。",
            references='[{"law":"劳动合同法","article":"第三十九条"}]',
        )
    )
    await db.commit()

    # 通知（幂等：按 user_id+type+dedupe_key）
    dedupe_key = "demo:welcome"
    notice = (
        await db.execute(
            select(Notification)
            .where(
                Notification.user_id == int(user1.id),  # type: ignore[arg-type]
                Notification.type == NotificationType.SYSTEM,
                Notification.dedupe_key == dedupe_key,
            )
            .order_by(Notification.id.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if notice is None:
        db.add(
            Notification(
                user_id=int(user1.id),  # type: ignore[arg-type]
                type=NotificationType.SYSTEM,
                title="欢迎使用百姓法律助手（demo）",
                content="已为你准备了示例数据：论坛帖子、新闻、模板、咨询对话等。",
                link="/",
                dedupe_key=dedupe_key,
                is_read=False,
                related_user_id=int(admin.id) if admin is not None else None,  # type: ignore[arg-type]
            )
        )
    else:
        notice.title = "欢迎使用百姓法律助手（demo）"
        notice.content = "已为你准备了示例数据：论坛帖子、新闻、模板、咨询对话等。"
        notice.link = "/"
        notice.is_read = False
        notice.related_user_id = int(admin.id) if admin is not None else None
        db.add(notice)
    await db.commit()

    # 支付订单 + 余额流水（幂等：按 order_no；流水按 order_id 每次重建）
    order_no = "DEMO-RECHARGE-USER1"
    order = (
        await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == order_no))
    ).scalar_one_or_none()
    if order is None:
        order = PaymentOrder(
            order_no=order_no,
            user_id=int(user1.id),
            order_type="recharge",
            amount=200.0,
            actual_amount=200.0,
            status="paid",
            payment_method="balance",
            trade_no="DEMO-TRADE-0001",
            paid_at=datetime.now(timezone.utc),
            title="余额充值（demo）",
            description="用于演示余额与订单列表",
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
    else:
        order.status = "paid"
        order.payment_method = "balance"
        order.amount = 200.0
        order.actual_amount = 200.0
        order.title = "余额充值（demo）"
        order.description = "用于演示余额与订单列表"
        db.add(order)
        await db.commit()
        await db.refresh(order)

    await db.execute(delete(BalanceTransaction).where(BalanceTransaction.order_id == int(order.id)))
    await db.commit()
    bal = (
        await db.execute(select(UserBalance).where(UserBalance.user_id == int(user1.id)))
    ).scalar_one_or_none()
    if bal is not None:
        bal.balance = 200.0
        bal.frozen = 0.0
        bal.balance_cents = 20000
        bal.frozen_cents = 0
        bal.total_recharged = max(float(getattr(bal, "total_recharged", 0.0) or 0.0), 200.0)
        bal.total_recharged_cents = max(int(getattr(bal, "total_recharged_cents", 0) or 0), 20000)
        db.add(bal)
        await db.commit()
        db.add(
            BalanceTransaction(
                user_id=int(user1.id),
                order_id=int(order.id),
                type="recharge",
                amount=200.0,
                balance_before=0.0,
                balance_after=200.0,
                amount_cents=20000,
                balance_before_cents=0,
                balance_after_cents=20000,
                description="demo 充值流水",
            )
        )
        await db.commit()

    # 搜索历史 + 行为数据（幂等：按 keyword / 按 user_id+action）
    for kw in ["劳动合同解除", "离婚财产分割", "工伤赔偿标准"]:
        existing = (
            await db.execute(
                select(SearchHistory)
                .where(SearchHistory.user_id == int(user1.id), SearchHistory.keyword == str(kw))
                .order_by(SearchHistory.id.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(SearchHistory(keyword=str(kw), user_id=int(user1.id), ip_address="127.0.0.1"))
            await db.commit()

    act = (
        await db.execute(
            select(UserActivity)
            .where(UserActivity.user_id == int(user1.id), UserActivity.action == "page_view")
            .order_by(UserActivity.id.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if act is None:
        db.add(
            UserActivity(
                user_id=int(user1.id),
                session_id="demo_session",
                action="page_view",
                page="/forum",
                target=None,
                target_id=None,
                referrer="/",
                user_agent="demo",
                ip_address="127.0.0.1",
                device_type="desktop",
                extra_data=None,
                duration=12,
            )
        )
        await db.commit()

    print("✓ demo 数据已初始化")


async def seed_points_products(db: AsyncSession) -> None:
    """创建积分商城商品"""
    products = [
        # 优惠券类型
        {
            "id": "coupon_10",
            "name": "10元优惠券",
            "description": "可用于支付咨询费用、文档生成等",
            "points_required": 100,
            "product_type": "voucher",
            "stock": 1000,
            "extra_data": {"face_value": 10, "valid_days": 30},
        },
        {
            "id": "coupon_30",
            "name": "30元优惠券",
            "description": "大额优惠券，适合多次咨询使用",
            "points_required": 280,
            "product_type": "voucher",
            "stock": 500,
            "extra_data": {"face_value": 30, "valid_days": 30},
        },
        {
            "id": "coupon_50",
            "name": "50元优惠券",
            "description": "大额优惠券，超值优惠",
            "points_required": 450,
            "product_type": "voucher",
            "stock": 200,
            "extra_data": {"face_value": 50, "valid_days": 30},
        },
        # VIP 类型
        {
            "id": "vip_week",
            "name": "VIP周卡",
            "description": "7天VIP会员权益，包括AI无限次咨询、优先回复等",
            "points_required": 500,
            "product_type": "vip",
            "stock": 100,
            "extra_data": {"vip_days": 7},
        },
        {
            "id": "vip_month",
            "name": "VIP月卡",
            "description": "30天VIP会员权益，解锁全部高级功能",
            "points_required": 1800,
            "product_type": "vip",
            "stock": 50,
            "extra_data": {"vip_days": 30},
        },
        {
            "id": "vip_quarter",
            "name": "VIP季卡",
            "description": "90天VIP会员，超值之选",
            "points_required": 5000,
            "product_type": "vip",
            "stock": 20,
            "extra_data": {"vip_days": 90},
        },
        # 套餐类型
        {
            "id": "ai_chat_10",
            "name": "AI咨询10次包",
            "description": "10次AI法律咨询次数，有效期30天",
            "points_required": 200,
            "product_type": "package",
            "stock": 200,
            "extra_data": {"ai_chat_count": 10, "valid_days": 30},
        },
        {
            "id": "ai_chat_50",
            "name": "AI咨询50次包",
            "description": "50次AI法律咨询次数，适合高频用户",
            "points_required": 800,
            "product_type": "package",
            "stock": 100,
            "extra_data": {"ai_chat_count": 50, "valid_days": 60},
        },
        {
            "id": "doc_gen_5",
            "name": "文档生成5次包",
            "description": "5次法律文档生成次数",
            "points_required": 300,
            "product_type": "package",
            "stock": 150,
            "extra_data": {"doc_gen_count": 5, "valid_days": 30},
        },
    ]

    for product_data in products:
        existing = (await db.execute(select(PointsProduct).where(PointsProduct.id == product_data["id"]))).scalar_one_or_none()
        if existing is None:
            product = PointsProduct(
                id=product_data["id"],
                name=product_data["name"],
                description=product_data.get("description"),
                points_required=product_data["points_required"],
                product_type=product_data["product_type"],
                stock=product_data["stock"],
                status="active",
                extra_data=product_data.get("extra_data"),
            )
            db.add(product)

    await db.commit()
    print(f"✓ 已创建 {len(products)} 个积分商品")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--reset-news", action="store_true")
    parser.add_argument("--reset-posts", action="store_true")
    parser.add_argument("--reset-demo", action="store_true")
    parser.add_argument("--reset-all", action="store_true")
    parser.add_argument("--apply-default-config", action="store_true")
    parser.add_argument("--seed-legal-knowledge", action="store_true")
    parser.add_argument("--reset-legal-knowledge", action="store_true")
    parser.add_argument("--seed-points-products", action="store_true")
    args = parser.parse_args()

    print("开始初始化种子数据...")
    await init_db()
     
    async with AsyncSessionLocal() as db:
        if bool(getattr(args, "demo", False)):
            args.apply_default_config = True
            args.seed_legal_knowledge = True
        if args.apply_default_config:
            os.environ["E2E_SEED"] = "1"
        await apply_e2e_defaults(db)
        await db.commit()

        if args.reset_all or bool(getattr(args, "reset_demo", False)):
            await reset_demo_tables(db)

        if args.seed_legal_knowledge:
            from scripts.seed_legal_knowledge import seed_law_knowledge

            reset = bool(args.reset_legal_knowledge or args.reset_all)
            res = await seed_law_knowledge(db, reset=reset)
            print(
                f"✓ 法律知识库：新增 {res['created']}，更新 {res['updated']}，当前总数 {res['total']}"
            )

        users = await create_users(db)
        await create_balances(db, users)
        if args.reset_all or args.reset_news:
            await db.execute(delete(News))
            await db.commit()
        await create_news(db)
        await create_law_firms(db)
        await create_lawyers(db, users)
        if args.reset_all or args.reset_posts:
            await db.execute(delete(Post))
            await db.commit()
        await create_posts(db, users)

        if bool(getattr(args, "demo", False)):
            await seed_demo_data(db, users)

        if args.seed_points_products or bool(getattr(args, "demo", False)):
            await seed_points_products(db)
      
    print("\n✓ 种子数据初始化完成!")
    print("\n测试账号:")
    print("  管理员: admin / admin123")
    print("  律师: lawyer1 / lawyer123")
    print("  用户: user1 / user123")


if __name__ == "__main__":
    asyncio.run(main())
