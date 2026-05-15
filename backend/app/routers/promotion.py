"""推广系统 BFF 路由 - 代理优先 + Mock 降级

代理映射:
  /lawyer/links → legal-service (律师推广链接)
  admin 提现审批 → payment-accounting-service
  /user 邀请 → BFF Mock (待 referral-service 支持后迁移)
"""
from datetime import datetime
import os
import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter(prefix="/promotion", tags=["Promotion"])

PAYMENT_ACCOUNTING_URL = os.getenv("PAYMENT_ACCOUNTING_SERVICE_URL", "http://payment-accounting-service:8014")
LEGAL_SERVICE_URL = os.getenv("LEGAL_SERVICE_URL", "http://legal-service:8008")
TIMEOUT = 5.0


def _auth_headers(request: Request) -> dict:
    headers = {"content-type": "application/json"}
    if request and request.headers.get("authorization"):
        headers["authorization"] = request.headers["authorization"]
    return headers


async def _proxy_get(service_url: str, service_path: str, request: Request) -> JSONResponse:
    url = f"{service_url}/api/v1/{service_path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, headers=_auth_headers(request), params=dict(request.query_params))
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception:
        return JSONResponse(content={"items": [], "total": 0}, status_code=200)


async def _proxy_post(service_url: str, service_path: str, body: dict, request: Request) -> JSONResponse:
    url = f"{service_url}/api/v1/{service_path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, json=body, headers=_auth_headers(request))
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        raise HTTPException(status_code=503, detail="服务暂时不可用")


# ==================== 代理到 legal-service ====================

@router.get("/lawyer/links")
async def get_lawyer_promotion_links(request: Request):
    return await _proxy_get(LEGAL_SERVICE_URL, "legal/lawyers/1/promotion-links", request)


@router.post("/lawyer/links")
async def create_lawyer_promotion_link(body: dict, request: Request):
    lawyer_id = body.get("lawyer_id", 1)
    return await _proxy_post(LEGAL_SERVICE_URL, f"legal/lawyers/{lawyer_id}/promotion-links", body, request)


# ==================== 代理到 payment-accounting-service ====================

@router.get("/admin/withdrawals/pending")
async def get_pending_withdrawals(request: Request):
    return await _proxy_get(PAYMENT_ACCOUNTING_URL, "admin/withdrawals?status=pending", request)


@router.post("/admin/withdrawals/{withdrawal_id}/approve")
async def approve_withdrawal(withdrawal_id: str, body: dict, request: Request):
    return await _proxy_post(PAYMENT_ACCOUNTING_URL, f"admin/withdrawals/{withdrawal_id}/approve", body, request)


@router.post("/admin/withdrawals/{withdrawal_id}/reject")
async def reject_withdrawal(withdrawal_id: str, body: dict, request: Request):
    return await _proxy_post(PAYMENT_ACCOUNTING_URL, f"admin/withdrawals/{withdrawal_id}/reject", body, request)


# ==================== 用户邀请系统 (Mock - 待 referral-service 支持后迁移) ====================

_promotions: list[dict] = [
    {"id": 1, "user_id": 1, "user_name": "张用户", "invite_code": "INVITE001", "total_invites": 15, "total_rewards": 750, "pending_rewards": 150, "level": 3, "created_at": "2025-01-01T10:00:00", "updated_at": "2025-05-01T10:00:00"},
    {"id": 2, "user_id": 2, "user_name": "李用户", "invite_code": "INVITE002", "total_invites": 8, "total_rewards": 400, "pending_rewards": 100, "level": 2, "created_at": "2025-02-01T10:00:00", "updated_at": "2025-05-01T10:00:00"},
]
_promotion_counter = 3
_invite_history: list[dict] = []
_promotion_rules: dict = {"invite_reward": 50, "invited_reward": 30, "daily_limit": 10, "monthly_limit": 50}
_ranking: list[dict] = [
    {"rank": 1, "user_id": 1, "user_name": "张用户", "avatar_url": "/avatars/1.jpg", "invite_count": 15, "total_rewards": 750, "level": 3},
    {"rank": 2, "user_id": 2, "user_name": "李用户", "avatar_url": "/avatars/2.jpg", "invite_count": 8, "total_rewards": 400, "level": 2},
    {"rank": 3, "user_id": 3, "user_name": "王用户", "avatar_url": "/avatars/3.jpg", "invite_count": 5, "total_rewards": 250, "level": 1},
]


@router.get("/user/invite-code")
def get_invite_code(user_id: int = Query(1)):
    for p in _promotions:
        if p["user_id"] == user_id:
            return {"invite_code": p["invite_code"], "invite_url": f"https://app.example.com/invite/{p['invite_code']}", "total_invites": p["total_invites"], "total_rewards": p["total_rewards"]}
    return {"invite_code": f"INVITE{user_id}00{_promotion_counter}", "invite_url": f"https://app.example.com/invite/INVITE{user_id}00{_promotion_counter}"}


@router.post("/user/invite-code/regenerate")
def regenerate_invite_code(user_id: int = Query(1)):
    return {"invite_code": f"INVITE{user_id}0{_promotion_counter}", "invite_url": f"https://app.example.com/invite/INVITE{user_id}0{_promotion_counter}"}


@router.get("/user/invite-history")
def get_invite_history(page: int = Query(1), page_size: int = Query(20)):
    return {"items": _invite_history, "total": len(_invite_history), "page": page, "page_size": page_size}


@router.post("/user/claim-reward")
def claim_reward(body: dict):
    return {"success": True, "message": "奖励已发放", "amount": 50, "new_balance": 200}


@router.get("/rules")
def get_promotion_rules():
    return _promotion_rules


@router.put("/rules")
def update_promotion_rules(body: dict):
    _promotion_rules.update(body)
    return {"success": True, "rules": _promotion_rules}


@router.get("/stats")
def get_promotion_stats():
    total_invites = sum(p["total_invites"] for p in _promotions)
    total_rewards = sum(p["total_rewards"] for p in _promotions)
    pending_rewards = sum(p["pending_rewards"] for p in _promotions)
    return {"total_invites": total_invites, "total_rewards": total_rewards, "pending_rewards": pending_rewards, "active_promoters": len(_promotions)}


@router.get("/ranking")
def get_ranking(limit: int = Query(10)):
    return {"items": _ranking[:limit]}


@router.get("/invited-users")
def get_invited_users(page: int = Query(1), page_size: int = Query(20)):
    return {"items": [], "total": 0, "page": page, "page_size": page_size}