"""Cross-Domain 域名管理 Schema"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DomainBase(BaseModel):
    """域名基础 Schema"""
    domain: str = Field(..., min_length=1, max_length=255, description="域名")

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """验证域名格式"""
        v = v.strip().lower()
        if not v:
            raise ValueError("域名不能为空")
        # 移除 http:// 或 https:// 前缀
        if v.startswith("http://"):
            v = v[7:]
        elif v.startswith("https://"):
            v = v[8:]
        # 移除尾部斜杠
        v = v.rstrip("/")
        return v


class DomainCreate(DomainBase):
    """创建域名 Schema"""
    pass


class DomainUpdate(BaseModel):
    """更新域名 Schema"""
    domain: str | None = Field(None, min_length=1, max_length=255, description="域名")


class DomainVerify(BaseModel):
    """域名验证 Schema"""
    verification_code: str = Field(..., min_length=1, max_length=64, description="验证代码")


class DomainResponse(DomainBase):
    """域名响应 Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="域名ID")
    status: Literal["pending", "verified", "failed"] = Field(..., description="验证状态")
    user_id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class DomainDetailResponse(DomainResponse):
    """域名详情响应 Schema"""
    verification_code: str = Field(..., description="验证代码")


class DomainListResponse(BaseModel):
    """域名列表响应 Schema"""
    items: list[DomainResponse] = Field(default_factory=list, description="域名列表")
    total: int = Field(..., description="总数")


class DomainVerifyResult(BaseModel):
    """域名验证结果 Schema"""
    success: bool = Field(..., description="验证是否成功")
    message: str = Field(..., description="验证结果消息")
    status: Literal["pending", "verified", "failed"] = Field(..., description="当前状态")