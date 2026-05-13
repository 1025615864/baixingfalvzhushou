from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database.session import get_db
from ..models import FeedbackTicket

router = APIRouter(prefix="/feedback", tags=["Feedback"])


class CreateFeedbackBody(BaseModel):
    subject: str
    content: str


class UpdateFeedbackBody(BaseModel):
    status: Optional[str] = None
    admin_reply: Optional[str] = None
    admin_id: Optional[int] = None


_mock_feedback: list[dict] = [
    {"id": 1, "user_id": 1001, "subject": "AI回答不准确", "content": "在使用AI法律咨询时，关于劳动法相关问题的回答存在明显错误，建议优化算法。", "status": "open", "admin_reply": None, "admin_id": None, "created_at": "2025-05-10T09:00:00", "updated_at": "2025-05-10T09:00:00"},
    {"id": 2, "user_id": 1002, "subject": "律师预约系统建议", "content": "律师预约系统不够流畅，希望能增加更多预约时间段选项和在线支付功能。", "status": "processing", "admin_reply": "感谢您的建议，我们正在优化预约系统。", "admin_id": 1, "created_at": "2025-05-09T14:00:00", "updated_at": "2025-05-10T10:00:00"},
    {"id": 3, "user_id": 1003, "subject": "合同审查结果有误", "content": "上传了一份房屋租赁合同进行审查，但审查结果标注的风险条款与实际不符。", "status": "open", "admin_reply": None, "admin_id": None, "created_at": "2025-05-08T11:00:00", "updated_at": "2025-05-08T11:00:00"},
    {"id": 4, "user_id": 1004, "subject": "支付接口问题", "content": "在支付律师咨询费用时，微信支付接口多次提示超时，更换支付宝后成功。", "status": "closed", "admin_reply": "微信支付接口已修复，给您带来不便敬请谅解。", "admin_id": 1, "created_at": "2025-05-07T16:00:00", "updated_at": "2025-05-08T09:00:00"},
    {"id": 5, "user_id": 1005, "subject": "平台使用体验反馈", "content": "整体使用体验良好，但希望在首页增加最近浏览记录功能方便快速访问。", "status": "open", "admin_reply": None, "admin_id": None, "created_at": "2025-05-06T10:00:00", "updated_at": "2025-05-06T10:00:00"},
    {"id": 6, "user_id": 1006, "subject": "法律文书格式优化", "content": "生成的起诉状模板格式不够规范，缺少部分必要信息字段，建议按法院要求调整。", "status": "processing", "admin_reply": "已转交技术团队评估优化方案。", "admin_id": 2, "created_at": "2025-05-05T13:00:00", "updated_at": "2025-05-06T09:00:00"},
    {"id": 7, "user_id": 1007, "subject": "客服响应速度慢", "content": "通过在线客服咨询问题，等待超过30分钟才得到回复，严重影响使用体验。", "status": "closed", "admin_reply": "非常抱歉，我们已加强客服团队，响应时间已缩短至5分钟内。", "admin_id": 1, "created_at": "2025-05-04T15:00:00", "updated_at": "2025-05-05T11:00:00"},
    {"id": 8, "user_id": 1008, "subject": "登录过程不稳定", "content": "手机验证码登录时经常收不到验证码，尝试多次后才能成功登录。", "status": "processing", "admin_reply": "已联系短信服务商排查问题。", "admin_id": 2, "created_at": "2025-05-03T09:00:00", "updated_at": "2025-05-03T16:00:00"},
    {"id": 9, "user_id": 1009, "subject": "新功能建议", "content": "建议增加法律文书在线协作编辑功能，方便用户与律师共同修改文书。", "status": "open", "admin_reply": None, "admin_id": None, "created_at": "2025-05-02T14:00:00", "updated_at": "2025-05-02T14:00:00"},
    {"id": 10, "user_id": 1010, "subject": "数据更新不及时", "content": "法律法规库中关于个人信息保护法的相关解读还停留在2024年版本。", "status": "open", "admin_reply": None, "admin_id": None, "created_at": "2025-05-01T10:00:00", "updated_at": "2025-05-01T10:00:00"},
    {"id": 11, "user_id": 1011, "subject": "搜索功能不完善", "content": "搜索相关法律条文时，结果排序不合理，希望能按相关性而非时间排序。", "status": "open", "admin_reply": None, "admin_id": None, "created_at": "2025-04-30T11:00:00", "updated_at": "2025-04-30T11:00:00"},
    {"id": 12, "user_id": 1012, "subject": "手机端适配问题", "content": "在手机浏览器上访问时页面布局错乱，部分按钮无法点击。", "status": "processing", "admin_reply": "移动端适配正在进行中，预计下周完成。", "admin_id": 1, "created_at": "2025-04-29T15:00:00", "updated_at": "2025-04-30T09:00:00"},
    {"id": 13, "user_id": 1013, "subject": "积分兑换功能异常", "content": "积分商城中用积分兑换法律咨询服务时，扣了积分但未生成订单。", "status": "closed", "admin_reply": "已修复积分扣除逻辑，相关积分已退回。", "admin_id": 2, "created_at": "2025-04-28T09:00:00", "updated_at": "2025-04-28T16:00:00"},
    {"id": 14, "user_id": 1014, "subject": "通知设置不生效", "content": "在设置中关闭了邮件通知，但仍然会收到推广邮件，希望能严格遵守用户设置。", "status": "open", "admin_reply": None, "admin_id": None, "created_at": "2025-04-27T12:00:00", "updated_at": "2025-04-27T12:00:00"},
    {"id": 15, "user_id": 1015, "subject": "隐私政策不清晰", "content": "平台的隐私政策描述过于简单，希望能详细说明用户数据的使用范围和第三方共享情况。", "status": "open", "admin_reply": None, "admin_id": None, "created_at": "2025-04-26T16:00:00", "updated_at": "2025-04-26T16:00:00"},
]

_next_id = 16


def _paginate(data: list[dict], page: int, page_size: int) -> dict:
    total = len(data)
    start = (page - 1) * page_size
    items = data[start:start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def _compute_stats() -> dict:
    return {
        "total": len(_mock_feedback),
        "open": sum(1 for f in _mock_feedback if f["status"] == "open"),
        "processing": sum(1 for f in _mock_feedback if f["status"] == "processing"),
        "closed": sum(1 for f in _mock_feedback if f["status"] == "closed"),
        "unassigned": sum(1 for f in _mock_feedback if f["status"] == "open" and f["admin_id"] is None),
    }


@router.post("")
async def create_feedback(body: CreateFeedbackBody, db: AsyncSession = Depends(get_db)):
    global _next_id
    now = datetime.now().isoformat()
    item = {
        "id": _next_id,
        "user_id": 1001,
        "subject": body.subject,
        "content": body.content,
        "status": "open",
        "admin_reply": None,
        "admin_id": None,
        "created_at": now,
        "updated_at": now,
    }
    _next_id += 1
    _mock_feedback.append(item)
    try:
        db_feedback = FeedbackTicket(
            user_id=1001, subject=body.subject, content=body.content,
            status="open",
        )
        db.add(db_feedback)
        await db.commit()
    except Exception:
        pass
    return item


@router.get("")
async def get_feedback_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return _paginate(_mock_feedback, page, page_size)


@router.get("/admin/tickets/stats")
async def get_feedback_stats():
    return _compute_stats()


@router.get("/admin/tickets")
async def get_admin_feedback_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
):
    data = list(_mock_feedback)
    if status:
        data = [f for f in data if f["status"] == status]
    if keyword:
        kw = keyword.lower()
        data = [f for f in data if kw in f["subject"].lower() or kw in f["content"].lower()]
    return _paginate(data, page, page_size)


@router.put("/admin/tickets/{ticket_id}")
async def update_feedback(ticket_id: int, body: UpdateFeedbackBody, db: AsyncSession = Depends(get_db)):
    for item in _mock_feedback:
        if item["id"] == ticket_id:
            if body.status is not None:
                item["status"] = body.status
            if body.admin_reply is not None:
                item["admin_reply"] = body.admin_reply
            if body.admin_id is not None:
                item["admin_id"] = body.admin_id
            item["updated_at"] = datetime.now().isoformat()
            try:
                db_ticket = await db.get(FeedbackTicket, ticket_id)
                if db_ticket:
                    if body.status is not None:
                        db_ticket.status = body.status
                    if body.admin_reply is not None:
                        db_ticket.admin_reply = body.admin_reply
                    if body.admin_id is not None:
                        db_ticket.admin_id = body.admin_id
                    await db.commit()
            except Exception:
                pass
            return item
    return {"detail": "反馈记录不存在"}