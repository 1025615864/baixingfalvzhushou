from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/promotion", tags=["Promotion"])

_invite_code = "INV2024A8F3"
_qrcode_url = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://baixinglaw.com/invite/INV2024A8F3"

_invite_history: list[dict] = [
    {"id": 1, "invited_user_id": 2001, "invited_user_name": "李明", "invited_user_avatar_url": None, "reward_amount": 50, "status": "claimed", "invited_at": "2025-05-01T09:00:00", "claimed_at": "2025-05-02T10:00:00"},
    {"id": 2, "invited_user_id": 2002, "invited_user_name": "王芳", "invited_user_avatar_url": None, "reward_amount": 50, "status": "claimed", "invited_at": "2025-05-03T14:00:00", "claimed_at": "2025-05-04T09:00:00"},
    {"id": 3, "invited_user_id": 2003, "invited_user_name": "赵强", "invited_user_avatar_url": None, "reward_amount": 50, "status": "pending", "invited_at": "2025-05-05T11:00:00", "claimed_at": None},
    {"id": 4, "invited_user_id": 2004, "invited_user_name": "刘洋", "invited_user_avatar_url": None, "reward_amount": 100, "status": "claimed", "invited_at": "2025-05-06T08:00:00", "claimed_at": "2025-05-07T16:00:00"},
    {"id": 5, "invited_user_id": 2005, "invited_user_name": "陈静", "invited_user_avatar_url": None, "reward_amount": 50, "status": "pending", "invited_at": "2025-05-08T15:00:00", "claimed_at": None},
    {"id": 6, "invited_user_id": 2006, "invited_user_name": "周杰", "invited_user_avatar_url": None, "reward_amount": 50, "status": "pending", "invited_at": "2025-05-09T10:00:00", "claimed_at": None},
    {"id": 7, "invited_user_id": 2007, "invited_user_name": "吴敏", "invited_user_avatar_url": None, "reward_amount": 100, "status": "claimed", "invited_at": "2025-05-10T13:00:00", "claimed_at": "2025-05-11T09:00:00"},
    {"id": 8, "invited_user_id": 2008, "invited_user_name": "孙伟", "invited_user_avatar_url": None, "reward_amount": 50, "status": "pending", "invited_at": "2025-05-12T09:00:00", "claimed_at": None},
    {"id": 9, "invited_user_id": 2009, "invited_user_name": "郑丽", "invited_user_avatar_url": None, "reward_amount": 50, "status": "claimed", "invited_at": "2025-04-28T11:00:00", "claimed_at": "2025-04-29T14:00:00"},
    {"id": 10, "invited_user_id": 2010, "invited_user_name": "冯涛", "invited_user_avatar_url": None, "reward_amount": 100, "status": "claimed", "invited_at": "2025-04-25T16:00:00", "claimed_at": "2025-04-26T10:00:00"},
]

_ranking: list[dict] = [
    {"user_id": 1001, "user_name": "张三", "avatar_url": None, "invite_count": 45},
    {"user_id": 1002, "user_name": "李四", "avatar_url": None, "invite_count": 38},
    {"user_id": 1003, "user_name": "王五", "avatar_url": None, "invite_count": 32},
    {"user_id": 1004, "user_name": "赵六", "avatar_url": None, "invite_count": 28},
    {"user_id": 1005, "user_name": "钱七", "avatar_url": None, "invite_count": 25},
    {"user_id": 1006, "user_name": "孙八", "avatar_url": None, "invite_count": 22},
    {"user_id": 1007, "user_name": "周九", "avatar_url": None, "invite_count": 19},
    {"user_id": 1008, "user_name": "吴十", "avatar_url": None, "invite_count": 17},
    {"user_id": 1009, "user_name": "郑十一", "avatar_url": None, "invite_count": 15},
    {"user_id": 1010, "user_name": "冯十二", "avatar_url": None, "invite_count": 13},
]

_admin_withdrawals: list[dict] = [
    {"id": 1, "request_no": "WD202505010001", "lawyer_id": 5001, "lawyer_name": "张律师", "lawyer_rating": 4.8, "lawyer_completed_count": 156, "platform_fee_rate": 0.2, "amount": 5000, "fee": 10, "actual_amount": 4990, "withdraw_method": "bank_card", "account_info_masked": "6222****1234", "status": "completed", "reject_reason": None, "admin_id": 1, "reviewed_at": "2025-05-02T14:00:00", "completed_at": "2025-05-03T09:00:00", "remark": None, "created_at": "2025-05-01T10:00:00", "updated_at": "2025-05-03T09:00:00"},
    {"id": 2, "request_no": "WD202505030001", "lawyer_id": 5002, "lawyer_name": "李律师", "lawyer_rating": 4.6, "lawyer_completed_count": 89, "platform_fee_rate": 0.2, "amount": 8000, "fee": 16, "actual_amount": 7984, "withdraw_method": "bank_card", "account_info_masked": "6217****5678", "status": "pending", "reject_reason": None, "admin_id": None, "reviewed_at": None, "completed_at": None, "remark": None, "created_at": "2025-05-03T15:00:00", "updated_at": "2025-05-03T15:00:00"},
    {"id": 3, "request_no": "WD202505050001", "lawyer_id": 5003, "lawyer_name": "王律师", "lawyer_rating": 4.5, "lawyer_completed_count": 67, "platform_fee_rate": 0.2, "amount": 3500, "fee": 7, "actual_amount": 3493, "withdraw_method": "alipay", "account_info_masked": "wan***@example.com", "status": "pending", "reject_reason": None, "admin_id": None, "reviewed_at": None, "completed_at": None, "remark": None, "created_at": "2025-05-05T09:00:00", "updated_at": "2025-05-05T09:00:00"},
    {"id": 4, "request_no": "WD202505060001", "lawyer_id": 5004, "lawyer_name": "赵律师", "lawyer_rating": 4.7, "lawyer_completed_count": 120, "platform_fee_rate": 0.2, "amount": 12000, "fee": 24, "actual_amount": 11976, "withdraw_method": "bank_card", "account_info_masked": "6228****9012", "status": "approved", "reject_reason": None, "admin_id": 1, "reviewed_at": "2025-05-06T16:00:00", "completed_at": None, "remark": "审核通过", "created_at": "2025-05-06T10:00:00", "updated_at": "2025-05-06T16:00:00"},
    {"id": 5, "request_no": "WD202505070001", "lawyer_id": 5005, "lawyer_name": "陈律师", "lawyer_rating": 4.3, "lawyer_completed_count": 45, "platform_fee_rate": 0.2, "amount": 2500, "fee": 5, "actual_amount": 2495, "withdraw_method": "bank_card", "account_info_masked": "6210****3456", "status": "rejected", "reject_reason": "银行卡信息不一致", "admin_id": 1, "reviewed_at": "2025-05-07T14:00:00", "completed_at": None, "remark": None, "created_at": "2025-05-07T09:00:00", "updated_at": "2025-05-07T14:00:00"},
    {"id": 6, "request_no": "WD202505080001", "lawyer_id": 5006, "lawyer_name": "刘律师", "lawyer_rating": 4.9, "lawyer_completed_count": 230, "platform_fee_rate": 0.15, "amount": 20000, "fee": 30, "actual_amount": 19970, "withdraw_method": "bank_card", "account_info_masked": "6215****7890", "status": "completed", "reject_reason": None, "admin_id": 1, "reviewed_at": "2025-05-08T11:00:00", "completed_at": "2025-05-09T14:00:00", "remark": None, "created_at": "2025-05-08T09:00:00", "updated_at": "2025-05-09T14:00:00"},
    {"id": 7, "request_no": "WD202505090001", "lawyer_id": 5007, "lawyer_name": "周律师", "lawyer_rating": 4.4, "lawyer_completed_count": 78, "platform_fee_rate": 0.2, "amount": 4500, "fee": 9, "actual_amount": 4491, "withdraw_method": "alipay", "account_info_masked": "zho***@example.com", "status": "pending", "reject_reason": None, "admin_id": None, "reviewed_at": None, "completed_at": None, "remark": None, "created_at": "2025-05-09T11:00:00", "updated_at": "2025-05-09T11:00:00"},
    {"id": 8, "request_no": "WD202505100001", "lawyer_id": 5008, "lawyer_name": "吴律师", "lawyer_rating": 4.2, "lawyer_completed_count": 34, "platform_fee_rate": 0.2, "amount": 1800, "fee": 4, "actual_amount": 1796, "withdraw_method": "bank_card", "account_info_masked": "6221****4321", "status": "pending", "reject_reason": None, "admin_id": None, "reviewed_at": None, "completed_at": None, "remark": None, "created_at": "2025-05-10T14:00:00", "updated_at": "2025-05-10T14:00:00"},
]


@router.get("/invite/generate")
async def get_promotion_link():
    return {
        "invite_code": _invite_code,
        "invite_url": f"https://baixinglaw.com/invite/{_invite_code}",
        "short_url": f"https://blaw.cn/i/{_invite_code}",
        "qrcode_url": _qrcode_url,
    }


@router.get("/invite/stats")
async def get_promotion_stats():
    claimed = [h for h in _invite_history if h["status"] == "claimed"]
    pending = [h for h in _invite_history if h["status"] == "pending"]
    return {
        "total_invited": len(_invite_history),
        "total_registered": len([h for h in _invite_history if h["invited_user_id"]]),
        "total_rewards": sum(h["reward_amount"] for h in claimed),
        "pending_rewards": sum(h["reward_amount"] for h in pending),
        "conversion_rate": round(len(claimed) / max(len(_invite_history), 1) * 100, 1),
    }


@router.get("/invite/history")
async def get_invite_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    start = (page - 1) * page_size
    end = start + page_size
    items = _invite_history[start:end]
    return {"history": items, "total": len(_invite_history)}


@router.post("/invite/claim")
async def claim_invite_reward(invite_code: str = "all"):
    pending_items = [h for h in _invite_history if h["status"] == "pending"]
    now = datetime.now().isoformat()
    claimed_amount = 0
    claimed_count = 0
    for item in pending_items:
        item["status"] = "claimed"
        item["claimed_at"] = now
        claimed_amount += item["reward_amount"]
        claimed_count += 1
    return {"success": True, "claimed_amount": claimed_amount, "claimed_count": claimed_count, "message": "奖励领取成功"}


@router.get("/ranking/invite")
async def get_invite_ranking(limit: int = Query(10, ge=1, le=100)):
    return {"ranking": _ranking[:limit]}


@router.get("/seo/config")
async def get_seo_config():
    return {
        "config": {
            "description": "邀请好友加入百姓法律助手，双方均可获得积分奖励。好友注册成功即得50积分，好友首次消费您再得50积分！",
            "title": "百姓法律助手 - 邀请有礼",
            "keywords": "法律咨询,邀请有礼,法律服务平台",
        }
    }


@router.get("/analytics/invitation")
async def get_invitation_analytics():
    return {
        "total_visits": 2850,
        "total_signups": 156,
        "conversion_rate": 5.5,
        "rewards_claimed": 8,
        "rewards_pending": 2,
    }


@router.get("/admin/withdrawals")
async def get_admin_withdrawals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    from_time: Optional[str] = Query(None),
    to_time: Optional[str] = Query(None),
):
    data = list(_admin_withdrawals)
    if status:
        data = [w for w in data if w["status"] == status]
    if keyword:
        data = [w for w in data if keyword in (w.get("lawyer_name") or "") or keyword in (w.get("request_no") or "")]
    if from_time:
        data = [w for w in data if w["created_at"] >= from_time]
    if to_time:
        data = [w for w in data if w["created_at"] <= to_time]

    total = len(data)
    start = (page - 1) * page_size
    items = data[start:start + page_size]

    stats = {
        "total_count": len(_admin_withdrawals),
        "total_amount": sum(w["amount"] for w in _admin_withdrawals),
        "pending_count": sum(1 for w in _admin_withdrawals if w["status"] == "pending"),
        "pending_amount": sum(w["amount"] for w in _admin_withdrawals if w["status"] == "pending"),
        "approved_count": sum(1 for w in _admin_withdrawals if w["status"] == "approved"),
        "approved_amount": sum(w["amount"] for w in _admin_withdrawals if w["status"] == "approved"),
        "rejected_count": sum(1 for w in _admin_withdrawals if w["status"] == "rejected"),
        "rejected_amount": sum(w["amount"] for w in _admin_withdrawals if w["status"] == "rejected"),
        "completed_count": sum(1 for w in _admin_withdrawals if w["status"] == "completed"),
        "completed_amount": sum(w["amount"] for w in _admin_withdrawals if w["status"] == "completed"),
    }
    return {"items": items, "total": total, "page": page, "page_size": page_size, "stats": stats}


@router.get("/admin/withdrawals/{withdrawal_id}")
async def get_withdrawal_detail(withdrawal_id: int):
    for w in _admin_withdrawals:
        if w["id"] == withdrawal_id:
            result = dict(w)
            result["account_info"] = {"bank_name": "中国工商银行", "account_no": "6222021234567890123", "account_holder": w.get("lawyer_name", "")}
            return result
    return {"detail": "提现记录不存在"}


@router.post("/admin/withdrawals/{withdrawal_id}/review")
async def review_withdrawal(
    withdrawal_id: int,
    approved: bool = True,
    reject_reason: Optional[str] = None,
    remark: Optional[str] = None,
):
    for w in _admin_withdrawals:
        if w["id"] == withdrawal_id:
            w["status"] = "approved" if approved else "rejected"
            w["reviewed_at"] = datetime.now().isoformat()
            w["reject_reason"] = reject_reason if not approved else None
            w["remark"] = remark
            w["admin_id"] = 1
            return w
    return {"detail": "提现记录不存在"}


@router.get("/admin/withdrawals/export")
async def export_withdrawals(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    from_time: Optional[str] = Query(None),
    to_time: Optional[str] = Query(None),
):
    data = list(_admin_withdrawals)
    if status:
        data = [w for w in data if w["status"] == status]
    header = "请求编号,律师姓名,金额,手续费,实到金额,提现方式,状态,创建时间"
    rows = [
        f"{w['request_no']},{w['lawyer_name']},{w['amount']},{w['fee']},{w['actual_amount']},{w['withdraw_method']},{w['status']},{w['created_at']}"
        for w in data
    ]
    return {"csv_content": "\n".join([header] + rows), "filename": f"withdrawals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}