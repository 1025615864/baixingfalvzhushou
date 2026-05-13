"""律师与律所管理 API 路由"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database.session import get_db
from ..models import (
    LawFirm, Lawyer, LawyerReview, LawyerSchedule, LawyerConsultation,
    LawyerHomepage, LawyerPromotionLink, LawyerReplyTemplate,
)

router = APIRouter(prefix="/lawyers", tags=["Lawyer"])

# --- 模拟律师数据 ---

_mock_lawyers: list[dict] = [
    {"id": 1, "user_id": 101, "firm_id": 1, "name": "张律师", "avatar": None, "title": "高级合伙人", "license_no": "LW202301001", "phone": "13800001001", "email": "zhang@lawfirm.com", "introduction": "专注民商事诉讼20年，擅长合同纠纷、公司治理、劳动争议等领域。", "specialties": "合同纠纷,公司法,劳动争议", "experience_years": 20, "case_count": 350, "rating": 4.8, "review_count": 128, "consultation_fee": 500, "is_verified": True, "is_active": True, "created_at": "2024-01-01T00:00:00", "firm_name": "京华律师事务所"},
    {"id": 2, "user_id": 102, "firm_id": 1, "name": "李律师", "avatar": None, "title": "合伙人", "license_no": "LW202301002", "phone": "13800001002", "email": "li@lawfirm.com", "introduction": "刑事辩护专家，曾办理多起重特大刑事案件。", "specialties": "刑事辩护,取保候审,二审辩护", "experience_years": 15, "case_count": 200, "rating": 4.6, "review_count": 89, "consultation_fee": 400, "is_verified": True, "is_active": True, "created_at": "2024-02-01T00:00:00", "firm_name": "京华律师事务所"},
    {"id": 3, "user_id": 103, "firm_id": 2, "name": "王律师", "avatar": None, "title": "专职律师", "license_no": "LW202301003", "phone": "13800001003", "email": "wang@lawfirm.com", "introduction": "知识产权领域专业律师，代理过多起商标侵权案。", "specialties": "知识产权,商标权,专利维权,著作权", "experience_years": 10, "case_count": 120, "rating": 4.7, "review_count": 72, "consultation_fee": 350, "is_verified": True, "is_active": True, "created_at": "2024-03-01T00:00:00", "firm_name": "天元律师事务所"},
    {"id": 4, "user_id": 104, "firm_id": 2, "name": "赵律师", "avatar": None, "title": "副主任", "license_no": "LW202301004", "phone": "13800001004", "email": "zhao@lawfirm.com", "introduction": "投资并购与资本市场法律专家。", "specialties": "投资并购,资本市场,尽职调查", "experience_years": 12, "case_count": 85, "rating": 4.9, "review_count": 56, "consultation_fee": 800, "is_verified": True, "is_active": True, "created_at": "2024-04-01T00:00:00", "firm_name": "天元律师事务所"},
    {"id": 5, "user_id": 105, "firm_id": 3, "name": "陈律师", "avatar": None, "title": "专职律师", "license_no": "LW202301005", "phone": "13800001005", "email": "chen@lawfirm.com", "introduction": "劳动争议与工伤赔偿领域的资深律师。", "specialties": "劳动争议,工伤赔偿,经济补偿", "experience_years": 8, "case_count": 180, "rating": 4.3, "review_count": 95, "consultation_fee": 200, "is_verified": True, "is_active": True, "created_at": "2024-05-01T00:00:00", "firm_name": "正法律师事务所"},
    {"id": 6, "user_id": 106, "firm_id": 3, "name": "刘律师", "avatar": None, "title": "主任", "license_no": "LW202301006", "phone": "13800001006", "email": "liu@lawfirm.com", "introduction": "婚姻家事、遗产继承领域权威律师。", "specialties": "离婚纠纷,财产分割,子女抚养,遗产继承", "experience_years": 18, "case_count": 400, "rating": 4.9, "review_count": 230, "consultation_fee": 600, "is_verified": True, "is_active": True, "created_at": "2024-06-01T00:00:00", "firm_name": "正法律师事务所"},
]

_mock_reviews: list[dict] = [
    {"id": 1, "lawyer_id": 1, "user_id": 201, "consultation_id": 301, "rating": 5, "content": "张律师非常专业，帮我把合同纠纷处理得很完美。", "is_anonymous": False, "professionalism": 5, "responsiveness": 5, "attitude": 5, "tags": ["专业", "负责", "高效"], "created_at": "2025-04-15T14:00:00", "username": "用户A"},
    {"id": 2, "lawyer_id": 1, "user_id": 202, "consultation_id": 302, "rating": 4, "content": "整体不错，回复有时稍慢。", "is_anonymous": False, "professionalism": 4, "responsiveness": 3, "attitude": 5, "tags": ["专业", "耐心"], "created_at": "2025-04-20T10:00:00", "username": "用户B"},
    {"id": 3, "lawyer_id": 2, "user_id": 203, "consultation_id": 303, "rating": 5, "content": "李律师刑事辩护经验丰富，庭审表现非常出色。", "is_anonymous": True, "professionalism": 5, "responsiveness": 4, "attitude": 5, "tags": ["经验丰富", "专业"], "created_at": "2025-04-18T09:00:00", "username": "匿名用户"},
    {"id": 4, "lawyer_id": 3, "user_id": 204, "consultation_id": 304, "rating": 4, "content": "商标侵权案件处理得当，收费合理。", "is_anonymous": False, "professionalism": 4, "responsiveness": 4, "attitude": 4, "tags": ["专业", "收费合理"], "created_at": "2025-05-01T11:00:00", "username": "用户C"},
]

_mock_schedules: list[dict] = [
    {"id": 1, "lawyer_id": 1, "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), "start_time": "09:00", "end_time": "10:00", "is_available": True, "consultation_id": None, "note": None, "created_at": "2025-05-01T00:00:00", "updated_at": "2025-05-01T00:00:00"},
    {"id": 2, "lawyer_id": 1, "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), "start_time": "14:00", "end_time": "15:00", "is_available": True, "consultation_id": None, "note": None, "created_at": "2025-05-01T00:00:00", "updated_at": "2025-05-01T00:00:00"},
    {"id": 3, "lawyer_id": 1, "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"), "start_time": "10:00", "end_time": "11:00", "is_available": False, "consultation_id": 301, "note": None, "created_at": "2025-05-02T00:00:00", "updated_at": "2025-05-02T00:00:00"},
]

_mock_consultations: list[dict] = [
    {"id": 1, "user_id": 201, "lawyer_id": 1, "subject": "合同纠纷法律咨询", "description": "与供应商产生合同纠纷，需要律师协助", "category": "合同纠纷", "contact_phone": "13900000001", "preferred_time": "工作日", "status": "completed", "admin_note": None, "created_at": "2025-05-01T09:00:00", "updated_at": "2025-05-01T10:00:00", "lawyer_name": "张律师", "payment_order_no": f"ORD{datetime.now().strftime('%Y%m%d')}001", "payment_status": "paid", "payment_amount": 500, "review_id": 1, "can_review": True},
    {"id": 2, "user_id": 202, "lawyer_id": 1, "subject": "劳动纠纷咨询", "description": "被公司无故辞退，需要法律帮助", "category": "劳动争议", "contact_phone": "13900000002", "preferred_time": "周末", "status": "confirmed", "admin_note": "已安排", "created_at": "2025-05-02T14:00:00", "updated_at": "2025-05-02T15:00:00", "lawyer_name": "张律师", "payment_order_no": f"ORD{datetime.now().strftime('%Y%m%d')}002", "payment_status": "paid", "payment_amount": 500, "review_id": None, "can_review": False},
    {"id": 3, "user_id": 203, "lawyer_id": 2, "subject": "刑事案件咨询", "description": "被刑事拘留，需要律师辩护", "category": "刑事辩护", "contact_phone": "13900000003", "preferred_time": "尽快", "status": "pending", "admin_note": None, "created_at": "2025-05-03T11:00:00", "updated_at": "2025-05-03T11:00:00", "lawyer_name": "李律师", "payment_order_no": None, "payment_status": "unpaid", "payment_amount": 400, "review_id": None, "can_review": False},
]

_mock_homepages: dict[str, dict] = {
    "1": {"id": 1, "lawyer_id": 1, "banner_image": None, "profile_image": None, "slogan": "正义也许会迟到，但永远不会缺席", "bio": "专注民商事诉讼二十年，致力于为每一位委托人提供专业的法律服务。", "specialties_display": ["合同纠纷", "公司治理", "劳动争议"], "achievements": ["北京市优秀律师", "全国十佳民商事律师"], "education": "北京大学法学院硕士", "service_areas": ["合同审查", "诉讼代理", "法律顾问"], "service_hours": "周一至周五 9:00-18:00", "response_time": "2小时内", "contact_phone": "138-0000-1001", "contact_email": "zhang@lawfirm.com", "wechat_qrcode": None, "weibo_url": None, "linkedin_url": None, "zhihu_url": None, "case_studies": [{"title": "某公司股权纠纷案", "description": "成功为公司挽回损失500万元", "achievement": "胜诉"}], "video_url": None, "video_cover": None, "seo_title": "张律师 - 京华律师事务所", "seo_description": "民商事诉讼专家", "seo_keywords": "律师,民事诉讼,合同纠纷", "theme_color": "#1a56db", "background_color": "#f8fafc", "is_published": True, "view_count": 2580, "created_at": "2024-01-15T00:00:00", "updated_at": "2025-01-01T00:00:00"},
}

_promotion_links: list[dict] = [
    {"id": 1, "lawyer_id": 1, "platform": "微信", "url": "https://mp.weixin.qq.com/s/xxxx", "title": "合同纠纷处理指南", "clicks": 320, "created_at": "2025-04-01T00:00:00", "updated_at": "2025-04-01T00:00:00"},
    {"id": 2, "lawyer_id": 1, "platform": "知乎", "url": "https://zhuanlan.zhihu.com/xxxx", "title": "律师教你如何应对劳动争议", "clicks": 580, "created_at": "2025-03-15T00:00:00", "updated_at": "2025-03-15T00:00:00"},
]

_reply_templates: list[dict] = [
    {"id": 1, "lawyer_id": 1, "category": "问候", "title": "首次回复", "content": "您好，感谢您的咨询。我是张律师，很高兴为您服务。请您详细描述一下您遇到的问题，我会尽快给您专业的建议。", "usage_count": 128, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
    {"id": 2, "lawyer_id": 1, "category": "定价", "title": "费用说明", "content": "我的咨询服务费为500元/次，包括初步法律分析和建议。如需代理诉讼，费用另行协商。", "usage_count": 56, "created_at": "2024-02-01T00:00:00", "updated_at": "2024-02-01T00:00:00"},
]

_law_firms: list[dict] = [
    {"id": 1, "name": "京华律师事务所", "logo": None, "introduction": "成立于2000年，拥有100+执业律师，在多个法律领域具有丰富经验。", "address": "北京市朝阳区建国路88号", "phone": "010-88880001", "email": "info@jinghua-law.com", "website": "https://www.jinghua-law.com", "lawyer_count": 45, "rating": 4.7, "review_count": 320, "is_active": True, "created_at": "2024-01-01T00:00:00"},
    {"id": 2, "name": "天元律师事务所", "logo": None, "introduction": "综合性律师事务所，擅长商事、知识产权等领域。", "address": "上海市浦东新区世纪大道100号", "phone": "021-88880002", "email": "info@tianyuan-law.com", "website": "https://www.tianyuan-law.com", "lawyer_count": 30, "rating": 4.8, "review_count": 180, "is_active": True, "created_at": "2024-02-01T00:00:00"},
    {"id": 3, "name": "正法律师事务所", "logo": None, "introduction": "以婚姻家事、劳动法为特色专业的中型律师事务所。", "address": "广州市天河区珠江新城15号", "phone": "020-88880003", "email": "info@zhengfa-law.com", "website": None, "lawyer_count": 20, "rating": 4.5, "review_count": 210, "is_active": True, "created_at": "2024-03-01T00:00:00"},
]

_next_schedule_id = 4
_next_consultation_id = 4
_next_review_id = 5
_next_promotion_id = 3
_next_template_id = 3
_next_firm_id = 4


def _paginate(data: list[dict], page: int, page_size: int) -> dict:
    total = len(data)
    start = (page - 1) * page_size
    items = data[start:start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# --- 律师 CRUD ---

@router.get("")
async def get_lawyers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    firm_id: Optional[int] = Query(None),
    is_verified: Optional[bool] = Query(None),
    min_rating: Optional[float] = Query(None),
):
    data = list(_mock_lawyers)
    if search:
        kw = search.lower()
        data = [l for l in data if kw in l["name"].lower() or kw in (l.get("specialties") or "").lower()]
    if specialty:
        data = [l for l in data if specialty in (l.get("specialties") or "")]
    if firm_id:
        data = [l for l in data if l.get("firm_id") == firm_id]
    if is_verified is not None:
        data = [l for l in data if l["is_verified"] == is_verified]
    if min_rating:
        data = [l for l in data if l["rating"] >= min_rating]
    return _paginate(data, page, page_size)


@router.get("/{lawyer_id}")
async def get_lawyer_detail(lawyer_id: int):
    for l in _mock_lawyers:
        if l["id"] == lawyer_id:
            return l
    return {"detail": "律师不存在"}


@router.get("/ranking")
async def get_lawyer_ranking(limit: int = Query(10, ge=1)):
    sorted_lawyers = sorted(_mock_lawyers, key=lambda l: l["rating"], reverse=True)
    ranking = [
        {"user_id": l["id"], "user_name": l["name"], "avatar_url": l.get("avatar"), "rating": l["rating"], "review_count": l["review_count"], "rank": i + 1, "firm_name": l.get("firm_name")}
        for i, l in enumerate(sorted_lawyers[:limit])
    ]
    return {"ranking": ranking}


# --- 评价 ---

@router.get("/{lawyer_id}/reviews")
async def get_lawyer_reviews(
    lawyer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    reviews = [r for r in _mock_reviews if r["lawyer_id"] == lawyer_id]
    return _paginate(reviews, page, page_size)


@router.get("/{lawyer_id}/reviews/summary")
async def get_review_summary(lawyer_id: int):
    reviews = [r for r in _mock_reviews if r["lawyer_id"] == lawyer_id]
    if not reviews:
        return {"detail": "暂无评价"}
    avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
    rating_dist = {f"rating_{i}_count": sum(1 for r in reviews if r["rating"] == i) for i in range(1, 6)}
    lawyer = next((l for l in _mock_lawyers if l["id"] == lawyer_id), None)
    return {
        "lawyer_id": lawyer_id,
        "lawyer_name": lawyer["name"] if lawyer else "",
        "total_reviews": len(reviews),
        "average_rating": round(avg_rating, 1),
        "dimension_stats": {
            "professionalism_avg": round(sum(r["professionalism"] for r in reviews) / len(reviews), 1),
            "responsiveness_avg": round(sum(r["responsiveness"] for r in reviews) / len(reviews), 1),
            "attitude_avg": round(sum(r["attitude"] for r in reviews) / len(reviews), 1),
        },
        "rating_distribution": rating_dist,
        "tag_stats": {},
        "popular_tags": ["专业", "负责"],
    }


@router.post("/{lawyer_id}/reviews")
async def create_review(
    lawyer_id: int, rating: int = 5, content: str = "",
    consultation_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    global _next_review_id
    now = datetime.now().isoformat()
    review = {
        "id": _next_review_id, "lawyer_id": lawyer_id, "user_id": 999, "consultation_id": consultation_id,
        "rating": rating, "content": content, "is_anonymous": False,
        "professionalism": rating, "responsiveness": rating, "attitude": rating,
        "tags": [], "created_at": now, "username": "当前用户",
    }
    _next_review_id += 1
    _mock_reviews.append(review)
    try:
        db_review = LawyerReview(
            lawyer_id=lawyer_id, user_id=999, consultation_id=consultation_id,
            rating=rating, content=content, is_anonymous=False,
            professionalism=rating, responsiveness=rating, attitude=rating,
            tags="[]",
        )
        db.add(db_review)
        await db.commit()
    except Exception:
        pass
    return review


# --- 日程 ---

@router.get("/{lawyer_id}/schedules")
async def get_lawyer_schedules(lawyer_id: int):
    schedules = [s for s in _mock_schedules if s["lawyer_id"] == lawyer_id]
    return {"schedules": schedules}


@router.post("/{lawyer_id}/schedules/available-slots")
async def get_available_slots(lawyer_id: int, date: str):
    available = [s for s in _mock_schedules if s["lawyer_id"] == lawyer_id and s["date"] == date and s["is_available"]]
    slots = [{"date": s["date"], "start_time": s["start_time"], "end_time": s["end_time"]} for s in available]
    return {"available_slots": slots}


# -- 咨询预约 ---

@router.get("/consultations/mine")
async def get_my_consultations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
):
    data = list(_mock_consultations)
    if status:
        data = [c for c in data if c["status"] == status]
    return _paginate(data, page, page_size)


@router.post("/consultations/book")
async def book_consultation(
    lawyer_id: int,
    subject: str = "",
    description: str = "",
    category: str = "",
    contact_phone: str = "",
    preferred_time: str = "",
    date: str = "",
    start_time: str = "",
    db: AsyncSession = Depends(get_db),
):
    global _next_consultation_id
    now = datetime.now().isoformat()
    lawyer = next((l for l in _mock_lawyers if l["id"] == lawyer_id), None)
    consultation = {
        "id": _next_consultation_id, "user_id": 999, "lawyer_id": lawyer_id,
        "subject": subject, "description": description, "category": category,
        "contact_phone": contact_phone, "preferred_time": preferred_time,
        "status": "confirmed", "admin_note": None,
        "created_at": now, "updated_at": now,
        "lawyer_name": lawyer["name"] if lawyer else "",
        "payment_order_no": f"ORD{datetime.now().strftime('%Y%m%d')}{_next_consultation_id}",
        "payment_status": "paid", "payment_amount": lawyer["consultation_fee"] if lawyer else 0,
        "review_id": None, "can_review": False,
    }
    _next_consultation_id += 1
    _mock_consultations.append(consultation)
    try:
        db_consultation = LawyerConsultation(
            user_id=999, lawyer_id=lawyer_id, subject=subject,
            description=description, category=category,
            contact_phone=contact_phone, status="confirmed",
        )
        db.add(db_consultation)
        await db.commit()
    except Exception:
        pass
    return {"booking": consultation, "message": "预约成功"}


@router.post("/consultations/{consultation_id}/cancel")
async def cancel_consultation(consultation_id: int, db: AsyncSession = Depends(get_db)):
    for c in _mock_consultations:
        if c["id"] == consultation_id:
            c["status"] = "cancelled"
            c["updated_at"] = datetime.now().isoformat()
            try:
                db_consultation = await db.get(LawyerConsultation, consultation_id)
                if db_consultation:
                    db_consultation.status = "cancelled"
                    await db.commit()
            except Exception:
                pass
            return {"message": "已取消", "consultation": c}
    return {"detail": "咨询不存在"}


# --- 律师主页 ---

class HomepageBody(BaseModel):
    slogan: Optional[str] = None
    bio: Optional[str] = None
    specialties_display: Optional[list[str]] = None
    achievements: Optional[list[str]] = None
    education: Optional[str] = None
    service_areas: Optional[list[str]] = None
    service_hours: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_published: Optional[bool] = None
    theme_color: Optional[str] = None


@router.get("/{lawyer_id}/homepage")
async def get_lawyer_homepage(lawyer_id: int):
    h = _mock_homepages.get(str(lawyer_id))
    if h:
        return h
    return {"detail": "未创建主页"}


@router.put("/{lawyer_id}/homepage")
async def update_lawyer_homepage(lawyer_id: int, body: HomepageBody):
    key = str(lawyer_id)
    if key not in _mock_homepages:
        _mock_homepages[key] = {"id": int(datetime.now().timestamp()), "lawyer_id": lawyer_id, "created_at": datetime.now().isoformat(), "view_count": 0, "is_published": False}
    h = _mock_homepages[key]
    for field, value in body.model_dump(exclude_none=True).items():
        h[field] = value
    h["updated_at"] = datetime.now().isoformat()
    return h


# --- 推广链接 ---

@router.get("/{lawyer_id}/promotion-links")
async def get_promotion_links(lawyer_id: int):
    links = [l for l in _promotion_links if l["lawyer_id"] == lawyer_id]
    stats = {"total_clicks": sum(l["clicks"] for l in links), "platform_count": len(set(l["platform"] for l in links))}
    return {"items": links, "total": len(links), "stats": stats}


@router.post("/{lawyer_id}/promotion-links")
async def create_promotion_link(lawyer_id: int, platform: str = "", url: str = "", title: str = ""):
    global _next_promotion_id
    now = datetime.now().isoformat()
    link = {"id": _next_promotion_id, "lawyer_id": lawyer_id, "platform": platform, "url": url, "title": title, "clicks": 0, "created_at": now, "updated_at": now}
    _next_promotion_id += 1
    _promotion_links.append(link)
    return link


@router.put("/{lawyer_id}/promotion-links/{link_id}")
async def update_promotion_link(lawyer_id: int, link_id: int, platform: Optional[str] = None, url: Optional[str] = None, title: Optional[str] = None):
    for l in _promotion_links:
        if l["id"] == link_id and l["lawyer_id"] == lawyer_id:
            if platform: l["platform"] = platform
            if url: l["url"] = url
            if title: l["title"] = title
            l["updated_at"] = datetime.now().isoformat()
            return l
    return {"detail": "推广链接不存在"}


# --- 快捷回复模板 ---

@router.get("/{lawyer_id}/reply-templates")
async def get_reply_templates(lawyer_id: int):
    templates = [t for t in _reply_templates if t["lawyer_id"] == lawyer_id]
    return {"items": templates, "total": len(templates), "categories": list(set(t["category"] for t in templates))}


@router.post("/{lawyer_id}/reply-templates")
async def create_reply_template(lawyer_id: int, category: str = "", title: str = "", content: str = ""):
    global _next_template_id
    now = datetime.now().isoformat()
    template = {"id": _next_template_id, "lawyer_id": lawyer_id, "category": category, "title": title, "content": content, "usage_count": 0, "created_at": now, "updated_at": now}
    _next_template_id += 1
    _reply_templates.append(template)
    return template


@router.delete("/{lawyer_id}/reply-templates/{template_id}")
async def delete_reply_template(lawyer_id: int, template_id: int):
    global _reply_templates
    _reply_templates = [t for t in _reply_templates if not (t["id"] == template_id and t["lawyer_id"] == lawyer_id)]
    return {"message": "已删除"}


# ==========================================
# 律所管理（独立路由 prefix=/lawfirm）
# ==========================================

lawfirm_router = APIRouter(prefix="/lawfirm", tags=["LawFirm"])


@lawfirm_router.get("/firms")
async def get_law_firms():
    return {"items": _law_firms, "total": len(_law_firms)}


@lawfirm_router.get("/firms/{firm_id}")
async def get_law_firm_detail(firm_id: int):
    for f in _law_firms:
        if f["id"] == firm_id:
            lawyers = [l for l in _mock_lawyers if l.get("firm_id") == firm_id]
            f["lawyers"] = lawyers
            return f
    return {"detail": "律所不存在"}


@lawfirm_router.post("/firms")
async def create_law_firm(
    name: str = "", introduction: str = "", address: str = "", phone: str = "",
    db: AsyncSession = Depends(get_db),
):
    global _next_firm_id
    now = datetime.now().isoformat()
    firm = {"id": _next_firm_id, "name": name, "logo": None, "introduction": introduction, "address": address, "phone": phone, "email": "", "website": None, "lawyer_count": 0, "rating": 0, "review_count": 0, "is_active": True, "created_at": now}
    _next_firm_id += 1
    _law_firms.append(firm)
    try:
        db_firm = LawFirm(name=name, description=introduction, address=address, phone=phone)
        db.add(db_firm)
        await db.commit()
    except Exception:
        pass
    return firm


# ==========================================
# 律师认证
# ==========================================

verification_router = APIRouter(prefix="/verification", tags=["Verification"])


@verification_router.get("/status")
async def get_verification_status():
    return {
        "has_verification": True,
        "verification_status": "approved",
        "verification_id": 1,
        "submitted_at": "2024-01-15T00:00:00",
        "reviewed_at": "2024-01-20T00:00:00",
        "reject_reason": None,
        "is_verified_lawyer": True,
    }


@verification_router.post("/submit")
async def submit_verification(
    real_name: str = "",
    id_card_no: str = "",
    license_no: str = "",
    firm_name: str = "",
    specialties: str = "",
    introduction: str = "",
    experience_years: int = 0,
):
    now = datetime.now().isoformat()
    return {
        "id": 1, "user_id": 999, "real_name": real_name, "id_card_no": id_card_no,
        "license_no": license_no, "firm_name": firm_name, "specialties": specialties,
        "introduction": introduction, "experience_years": experience_years,
        "id_card_front": None, "id_card_back": None, "license_photo": None,
        "status": "pending", "reject_reason": None, "created_at": now, "reviewed_at": None,
        "message": "认证申请已提交",
    }