"""微信相关 API 路由"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.wechat_service import wechat_auth_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wechat", tags=["WeChat"])


class QrCodeResponse(BaseModel):
    qrcode_id: str
    qrcode_base64: str
    expire_seconds: int
    status: str


class ScanStatusResponse(BaseModel):
    status: str
    qrcode_id: Optional[str] = None
    token: Optional[str] = None
    user: Optional[dict] = None


class WechatLoginRequest(BaseModel):
    code: str
    state: Optional[str] = ""


@router.get("/qrcode", response_model=QrCodeResponse)
async def get_login_qrcode():
    """获取微信扫码登录二维码"""
    try:
        result = wechat_auth_service.generate_login_qrcode()
        return result
    except Exception as e:
        logger.exception("生成二维码失败")
        raise HTTPException(status_code=500, detail="二维码生成失败")


@router.get("/qrcode/status/{qrcode_id}", response_model=ScanStatusResponse)
async def check_qrcode_status(qrcode_id: str):
    """轮询二维码扫码状态"""
    result = wechat_auth_service.check_scan_status(qrcode_id)
    return result


@router.post("/qrcode/confirm/{qrcode_id}")
async def confirm_qrcode_scan(qrcode_id: str):
    """确认扫码登录（模拟微信回调）"""
    result = wechat_auth_service.confirm_scan(qrcode_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/callback")
async def wechat_callback(code: str = "", state: str = ""):
    """微信 OAuth 回调"""
    result = await wechat_auth_service.handle_callback(code, state)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result