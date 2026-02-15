"""语音管理路由"""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...utils.deps import require_admin

router = APIRouter(prefix="/voice", tags=["语音管理"])


@router.get("/providers")
async def get_voice_providers(
    _current_user: Annotated[User, Depends(require_admin)],
):
    """获取语音提供商列表"""
    return {
        "providers": [
            {"id": "azure", "name": "Azure TTS"},
            {"id": "aliyun", "name": "阿里云语音"},
            {"id": "baidu", "name": "百度语音"},
        ]
    }


@router.get("/config")
async def get_voice_config(
    _current_user: Annotated[User, Depends(require_admin)],
):
    """获取语音配置"""
    return {
        "enabled": False,
        "default_provider": None,
    }


@router.put("/config")
async def update_voice_config(
    _current_user: Annotated[User, Depends(require_admin)],
    enabled: bool = False,
    provider: str | None = None,
):
    """更新语音配置"""
    return {"message": "配置已更新", "enabled": enabled, "provider": provider}
