"""微信生态 API 路由

提供微信登录、消息推送、小程序码等功能。
"""
from __future__ import annotations

import logging
from typing import Annotated, Any
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db
from ..models.user import User
from ..services.wechat_service import (
    wechat_auth_service,
    wechat_message_service,
    wechat_mini_service,
    wechat_public_service,
)
from ..utils.deps import get_current_user_optional, get_current_user

router = APIRouter(prefix="/wechat", tags=["微信生态"])
logger = logging.getLogger(__name__)

# ==================== 微信登录 ====================


def _validate_redirect_uri(redirect_uri: str) -> bool:
    """
    验证回调地址是否在白名单中，防止 SSRF 和开放重定向攻击
    
    Args:
        redirect_uri: 待验证的回调地址
        
    Returns:
        bool: 是否在白名单中
    """
    if not redirect_uri:
        return False
    
    try:
        parsed = urlparse(redirect_uri)
        
        # 禁止非 http/https 协议
        if parsed.scheme not in ("http", "https"):
            logger.warning(f"Redirect URI rejected: invalid scheme {parsed.scheme}")
            return False
        
        # 获取配置的 CORS 白名单作为重定向白名单
        settings = get_settings()
        allowed_hosts = settings.cors_allow_origins or []
        
        # 如果没有配置白名单，只允许 localhost（开发环境）
        if not allowed_hosts:
            allowed_hosts = ["localhost", "127.0.0.1"]
        
        # 提取主机名（去除端口）
        host = parsed.hostname or ""
        
        # 检查是否在白名单中
        for allowed in allowed_hosts:
            allowed_parsed = urlparse(allowed)
            allowed_host = allowed_parsed.hostname or allowed
            
            # 精确匹配或子域名匹配
            if host == allowed_host or host.endswith(f".{allowed_host}"):
                return True
        
        logger.warning(f"Redirect URI rejected: host {host} not in whitelist")
        return False
        
    except Exception as e:
        logger.warning(f"Redirect URI validation failed: {e}")
        return False


@router.get("/auth/qrcode")
async def get_wechat_login_qrcode(
    redirect_uri: str = Query(..., description="回调地址"),
) -> dict:
    """获取微信登录二维码"""
    # 验证回调地址白名单，防止 SSRF 攻击
    if not _validate_redirect_uri(redirect_uri):
        raise HTTPException(
            status_code=400,
            detail="无效的回调地址，请在 CORS 白名单中配置该域名"
        )
    
    result = await wechat_auth_service.get_login_qrcode(redirect_uri)
    return result


@router.post("/auth/callback")
async def handle_wechat_callback(
    code: str = Query(..., description="授权码"),
    state: str = Query(..., description="状态"),
) -> dict:
    """处理微信登录回调"""
    result = await wechat_auth_service.handle_callback(code, state)
    return result


@router.get("/auth/userinfo")
async def get_wechat_user_info(
    openid: str,
) -> dict:
    """获取微信用户信息"""
    user_info = await wechat_auth_service.get_user_info(openid)
    if not user_info:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user_info


# 兼容前端路由：/user/wechat/login（换取 token）
@router.post("/user/login")
async def wechat_user_login(
    code: str = Query(..., description="微信授权码"),
    state: str = Query(..., description="状态参数"),
) -> dict:
    """微信登录换取 token（兼容前端 /user/wechat/login 接口）"""
    result = await wechat_auth_service.handle_callback(code, state)
    return result


# ==================== 消息推送 ====================

@router.post("/message/send")
async def send_template_message(
    request: dict = Body(..., description="模板消息请求体"),
) -> dict:
    """发送模板消息（兼容前端 body 传参）"""
    openid = request.get("openid")
    template_id = request.get("templateId")
    data = request.get("data")
    page = request.get("page")
    
    if not openid or not template_id:
        raise HTTPException(
            status_code=400,
            detail="缺少必要参数：openid 和 templateId"
        )
    
    result = await wechat_message_service.send_template_message(
        openid=openid,
        template_id=template_id,
        data=data or {},
        page=page,
    )
    return result


@router.get("/message/history")
async def get_message_history(
    openid: str,
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    """获取消息历史"""
    messages = await wechat_message_service.get_message_history(openid, limit)
    return {
        "messages": messages,
        "total": len(messages),
    }


@router.post("/message/template/register")
async def register_message_template(
    template_id: str = Query(..., description="模板ID"),
    name: str = Query(..., description="模板名称"),
    content: str = Query(..., description="模板内容"),
) -> dict:
    """注册模板"""
    result = wechat_message_service.register_template(
        template_id, name, content)
    return result


# ==================== 小程序 ====================

@router.get("/mini/qrcode")
async def get_mini_program_qrcode(
    path: str = Query(..., description="页面路径"),
    width: int = Query(default=430, ge=100, le=1280),
) -> dict:
    """获取小程序码"""
    result = await wechat_mini_service.get_wxacode(path, width)
    return result


@router.get("/mini/scene")
async def analyze_scene(
    scene: str = Query(..., description="场景值"),
) -> dict:
    """解析场景值"""
    result = await wechat_mini_service.analyze_scene(scene)
    return result


# ==================== 公众号 ====================

@router.post("/mp/article/publish")
async def publish_mp_article(
    title: str = Query(..., description="标题"),
    content: str = Query(..., description="内容"),
    thumb_url: str | None = Query(None, description="封面图"),
) -> dict:
    """发布公众号文章"""
    result = await wechat_public_service.publish_article(title, content, thumb_url)
    return result


@router.get("/mp/articles")
async def get_mp_articles(
    limit: int = Query(default=10, ge=1, le=50),
) -> dict:
    """获取公众号文章列表"""
    articles = await wechat_public_service.get_article_list(limit)
    return {
        "articles": articles,
        "total": len(articles),
    }
