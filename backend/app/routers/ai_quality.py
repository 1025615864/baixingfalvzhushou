"""AI 质量监控 API 路由"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/system/ai-quality", tags=["AI-Quality"])


class CreateQualityFeedbackBody(BaseModel):
    conversation_id: str
    model: Optional[str] = None
    query: str
    response: str
    rating: int = 5
    feedback_type: Optional[str] = None
    tags: Optional[list[str]] = None
    comment: Optional[str] = None
    is_hallucination: bool = False
    is_irrelevant: bool = False
    is_outdated: bool = False
    is_factual_error: bool = False


class UpdateQualityFeedbackBody(BaseModel):
    reviewed_by: Optional[str] = None
    review_status: Optional[str] = None
    review_notes: Optional[str] = None


_mock_quality_items: list[dict] = [
    {"id": 1, "conversation_id": "conv-001", "model": "gpt-4-turbo", "query": "劳动合同解除需要什么条件？", "response": "根据《劳动合同法》第39条...", "rating": 5, "feedback_type": "rating", "tags": ["准确", "详细"], "comment": "回答很专业", "is_hallucination": False, "is_irrelevant": False, "is_outdated": False, "is_factual_error": False, "reviewed_by": None, "review_status": "pending", "review_notes": None, "created_at": (datetime.now() - timedelta(hours=2)).isoformat()},
    {"id": 2, "conversation_id": "conv-002", "model": "deepseek-v3", "query": "酒后驾车怎么处罚？", "response": "根据《道路交通安全法》第91条...", "rating": 3, "feedback_type": "rating", "tags": ["部分准确"], "comment": "信息不够完整", "is_hallucination": False, "is_irrelevant": False, "is_outdated": True, "is_factual_error": False, "reviewed_by": "admin", "review_status": "reviewed", "review_notes": "已更新知识库", "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
    {"id": 3, "conversation_id": "conv-003", "model": "gpt-4-turbo", "query": "离婚财产怎么分割？", "response": "根据民法典第1087条...", "rating": 5, "feedback_type": "rating", "tags": ["准确", "实用"], "comment": None, "is_hallucination": False, "is_irrelevant": False, "is_outdated": False, "is_factual_error": False, "reviewed_by": None, "review_status": "pending", "review_notes": None, "created_at": (datetime.now() - timedelta(days=2)).isoformat()},
    {"id": 4, "conversation_id": "conv-004", "model": "gpt-4o", "query": "工伤认定流程", "response": "首先需要用人单位在30天内申请...", "rating": 4, "feedback_type": "rating", "tags": ["基本准确"], "comment": "流程基本正确", "is_hallucination": False, "is_irrelevant": False, "is_outdated": False, "is_factual_error": False, "reviewed_by": None, "review_status": "pending", "review_notes": None, "created_at": (datetime.now() - timedelta(days=3)).isoformat()},
    {"id": 5, "conversation_id": "conv-005", "model": "deepseek-v3", "query": "租房押金不退怎么办？", "response": "根据民法典关于租赁合同的规定...", "rating": 2, "feedback_type": "rating", "tags": ["不准确"], "comment": "引用了错误的法条", "is_hallucination": True, "is_irrelevant": False, "is_outdated": False, "is_factual_error": True, "reviewed_by": "admin", "review_status": "reviewed", "review_notes": "标注为幻觉案例，已提交模型团队", "created_at": (datetime.now() - timedelta(days=4)).isoformat()},
    {"id": 6, "conversation_id": "conv-006", "model": "gpt-4-turbo", "query": "公司裁员怎么赔偿？", "response": "经济补偿金按工作年限计算...", "rating": 5, "feedback_type": "rating", "tags": ["准确", "清晰"], "comment": None, "is_hallucination": False, "is_irrelevant": False, "is_outdated": False, "is_factual_error": False, "reviewed_by": None, "review_status": "pending", "review_notes": None, "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
    {"id": 7, "conversation_id": "conv-007", "model": "gpt-4-turbo", "query": "遗产继承顺序", "response": "第一顺序继承人为配偶、子女、父母...", "rating": 5, "feedback_type": "rating", "tags": ["准确", "权威"], "comment": "回答准确", "is_hallucination": False, "is_irrelevant": False, "is_outdated": False, "is_factual_error": False, "reviewed_by": None, "review_status": "pending", "review_notes": None, "created_at": (datetime.now() - timedelta(days=6)).isoformat()},
]

_next_id = 8


def _paginate(data: list[dict], page: int, page_size: int) -> dict:
    total = len(data)
    start = (page - 1) * page_size
    items = data[start:start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("")
async def get_quality_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rating: Optional[int] = Query(None),
    has_hallucination: Optional[bool] = Query(None),
    review_status: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
):
    data = list(_mock_quality_items)
    if rating is not None:
        data = [i for i in data if i["rating"] == rating]
    if has_hallucination is not None:
        data = [i for i in data if i["is_hallucination"] == has_hallucination]
    if review_status:
        data = [i for i in data if i["review_status"] == review_status]
    if model:
        data = [i for i in data if i.get("model") == model]
    if start_time:
        data = [i for i in data if i["created_at"] >= start_time]
    if end_time:
        data = [i for i in data if i["created_at"] <= end_time]
    return _paginate(data, page, page_size)


@router.get("/stats")
async def get_quality_stats():
    items = _mock_quality_items
    total = len(items)
    ratings = [i["rating"] for i in items]
    avg_rating = sum(ratings) / max(len(ratings), 1)
    hallucination_rate = sum(1 for i in items if i["is_hallucination"]) / max(total, 1) * 100
    return {
        "total_conversations": total,
        "average_rating": round(avg_rating, 1),
        "hallucination_rate": round(hallucination_rate, 1),
        "rating_distribution": {
            "rating_1": sum(1 for r in ratings if r == 1),
            "rating_2": sum(1 for r in ratings if r == 2),
            "rating_3": sum(1 for r in ratings if r == 3),
            "rating_4": sum(1 for r in ratings if r == 4),
            "rating_5": sum(1 for r in ratings if r == 5),
        },
        "review_status": {
            "pending": sum(1 for i in items if i["review_status"] == "pending"),
            "reviewed": sum(1 for i in items if i["review_status"] == "reviewed"),
        },
    }


@router.post("/feedback")
async def create_quality_feedback(body: CreateQualityFeedbackBody):
    global _next_id
    now = datetime.now().isoformat()
    item = {
        "id": _next_id, "conversation_id": body.conversation_id, "model": body.model,
        "query": body.query, "response": body.response, "rating": body.rating,
        "feedback_type": body.feedback_type, "tags": body.tags or [], "comment": body.comment,
        "is_hallucination": body.is_hallucination, "is_irrelevant": body.is_irrelevant,
        "is_outdated": body.is_outdated, "is_factual_error": body.is_factual_error,
        "reviewed_by": None, "review_status": "pending", "review_notes": None, "created_at": now,
    }
    _next_id += 1
    _mock_quality_items.append(item)
    return {"id": item["id"], "message": "反馈已提交"}


@router.get("/{record_id}")
async def get_quality_record(record_id: int):
    for i in _mock_quality_items:
        if i["id"] == record_id:
            return i
    return {"detail": "记录不存在"}


@router.put("/{record_id}/review")
async def review_quality_record(record_id: int, body: UpdateQualityFeedbackBody):
    for i in _mock_quality_items:
        if i["id"] == record_id:
            if body.reviewed_by: i["reviewed_by"] = body.reviewed_by
            if body.review_status: i["review_status"] = body.review_status
            if body.review_notes: i["review_notes"] = body.review_notes
            return i
    return {"detail": "记录不存在"}


@router.get("/export/csv")
async def export_quality_csv():
    header = "id,model,rating,is_hallucination,review_status,created_at"
    rows = [f"{i['id']},{i.get('model','')},{i['rating']},{i['is_hallucination']},{i['review_status']},{i['created_at']}" for i in _mock_quality_items]
    return {"content": "\n".join([header] + rows), "filename": "ai_quality_export.csv"}