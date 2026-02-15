"""用户相关的Pydantic模式"""
from datetime import datetime
from typing import Any, ClassVar
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from ..utils.validators import (
    validate_password_strength,
    validate_username,
    validate_phone,
    validate_email_detail,
)


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=2, max_length=20, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    nickname: str | None = Field(None, max_length=50, description="昵称")
    _allow_reserved_usernames: ClassVar[bool] = True

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        is_valid, msg = validate_username(
            v,
            allow_reserved=bool(getattr(cls, "_allow_reserved_usernames", False)),
        )
        if not is_valid:
            raise ValueError(msg)
        return v

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        is_valid, msg = validate_email_detail(v)
        if not is_valid:
            raise ValueError(msg)
        return v


class UserCreate(UserBase):
    """用户注册模式"""
    _allow_reserved_usernames: ClassVar[bool] = False
    password: str = Field(..., min_length=8, max_length=50, description="密码")
    agree_terms: bool = Field(..., description="同意用户协议")
    agree_privacy: bool = Field(..., description="同意隐私政策")
    agree_ai_disclaimer: bool = Field(..., description="同意AI咨询免责声明")

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v


class UserLogin(BaseModel):
    """用户登录模式"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """用户更新模式"""
    nickname: str | None = Field(None, max_length=50)
    avatar: str | None = None
    phone: str | None = Field(None, max_length=20)

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not validate_phone(v):
            raise ValueError("手机号格式不正确")
        return v


class UserResponse(UserBase):
    """用户响应模式"""
    id: int
    avatar: str | None = None
    phone: str | None = None
    email_verified: bool = False
    email_verified_at: datetime | None = None
    phone_verified: bool = False
    phone_verified_at: datetime | None = None
    role: str = "user"
    is_active: bool = True
    vip_expires_at: datetime | None = None
    created_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    _allow_reserved_usernames: ClassVar[bool] = True


class Token(BaseModel):
    """Token响应模式"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15分钟


class TokenRefreshRequest(BaseModel):
    """Token刷新请求"""
    refresh_token: str | None = None  # 可选，如果不提供则从Cookie读取


class TokenRefreshResponse(BaseModel):
    """Token刷新响应"""
    access_token: str
    refresh_token: str | None = None  # 新的refresh_token（轮换时返回）
    token_type: str = "bearer"
    expires_in: int = 900  # 15分钟
    rotated: bool = False  # 是否发生轮换
    message: str = "Token刷新成功"


class TokenRevokeRequest(BaseModel):
    """Token撤销请求"""
    token: str | None = None  # 要撤销的token，不提供则撤销当前用户的所有token


class ActiveTokenInfo(BaseModel):
    """活跃Token信息"""
    jti: str
    family: str
    issued_at: str
    expires_at: str
    rotation_count: int
    device_info: str | None = None
    ip_address: str | None = None


class ActiveTokensResponse(BaseModel):
    """活跃Token列表响应"""
    tokens: list[ActiveTokenInfo]
    total: int
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token数据模式"""
    user_id: int | None = None
    username: str | None = None


class LoginResponse(BaseModel):
    """登录响应模式"""
    user: UserResponse
    token: Token | None = None
    message: str = "登录成功"


class RegisterResponse(BaseModel):
    """注册响应模式"""
    user: UserResponse
    message: str = "注册成功"


class PasswordChange(BaseModel):
    """密码修改模式"""
    old_password: str = Field(..., min_length=1, description="当前密码")
    new_password: str = Field(..., min_length=8,
                              max_length=50, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_new_password_complexity(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True


class EmailVerificationRequestResponse(MessageResponse):
    token: str | None = None
    verify_url: str | None = None


class SmsSendRequest(BaseModel):
    phone: str = Field(..., min_length=5, max_length=20, description="手机号")
    scene: str = Field("bind_phone", description="验证码使用场景")


class SmsVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=5, max_length=20, description="手机号")
    scene: str = Field("bind_phone", description="验证码使用场景")
    code: str = Field(..., min_length=4, max_length=10, description="验证码")


class SmsSendResponse(MessageResponse):
    code: str | None = None


class PasswordResetRequest(BaseModel):
    """密码重置请求"""
    email: EmailStr = Field(..., description="注册邮箱")


class PasswordResetConfirm(BaseModel):
    """密码重置确认"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8,
                              max_length=50, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_new_password_complexity(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v


class PasswordResetDebugRequest(BaseModel):
    email: EmailStr = Field(..., description="注册邮箱")


class PasswordResetDebugResponse(MessageResponse):
    token: str
    reset_url: str


# ==================== 安全中心相关 Schema ====================

class TwoFAStatusResponse(BaseModel):
    """2FA状态响应"""
    is_enabled: bool = Field(..., description="2FA是否已启用")
    is_setup: bool = Field(..., description="是否已设置（有密钥但未启用）")


class TwoFASetupRequest(BaseModel):
    """2FA设置请求"""
    # 初始化设置不需要参数，由后端生成


class TwoFASetupResponse(BaseModel):
    """2FA设置响应"""
    secret: str = Field(..., description="TOTP密钥（base32编码）")
    uri: str = Field(..., description="二维码URI（符合Google Authenticator标准）")
    backup_codes: list[str] = Field(..., description="备用验证码列表")
    qr_code_url: str | None = Field(None, description="二维码图片URL（可选）")


class TwoFAVerifyRequest(BaseModel):
    """2FA验证请求"""
    code: str = Field(..., min_length=6, max_length=10, description="验证码（6位数字或备用码）")


class TwoFADisableRequest(BaseModel):
    """禁用2FA请求"""
    code: str = Field(..., min_length=6, max_length=10, description="验证码（6位数字或备用码）")


class DeviceInfo(BaseModel):
    """设备信息"""
    device_id: str = Field(..., description="设备唯一标识")
    device_name: str | None = Field(None, description="设备名称")
    device_type: str = Field(..., description="设备类型（desktop, mobile, tablet等）")
    user_agent: str | None = Field(None, description="用户代理")
    ip_address: str | None = Field(None, description="IP地址")
    location: str | None = Field(None, description="地理位置")
    first_login_at: datetime | None = Field(None, description="首次登录时间")
    last_login_at: datetime | None = Field(None, description="最后登录时间")
    is_current: bool = Field(False, description="是否为当前设备")
    is_revoked: bool = Field(False, description="是否已撤销")


class DeviceListResponse(BaseModel):
    """设备列表响应"""
    devices: list[DeviceInfo] = Field(..., description="设备列表")
    total: int = Field(..., description="设备总数")
    current_device_id: str | None = Field(None, description="当前设备ID")


class DeviceRevokeRequest(BaseModel):
    """撤销设备请求"""
    device_id: str = Field(..., description="要撤销的设备ID")


class LoginRecord(BaseModel):
    """登录记录"""
    id: int = Field(..., description="记录ID")
    action: str = Field(..., description="操作类型（login, logout, 2fa_verify, failed等）")
    success: bool = Field(..., description="是否成功")
    ip_address: str | None = Field(None, description="IP地址")
    user_agent: str | None = Field(None, description="用户代理")
    device_id: str | None = Field(None, description="设备ID")
    location: str | None = Field(None, description="地理位置")
    failure_reason: str | None = Field(None, description="失败原因")
    created_at: datetime = Field(..., description="记录时间")


class LoginHistoryResponse(BaseModel):
    """登录历史响应"""
    records: list[LoginRecord] = Field(..., description="登录记录列表")
    total: int = Field(..., description="记录总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class LoginHistoryRequest(BaseModel):
    """登录历史查询请求"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    start_date: datetime | None = Field(None, description="开始日期")
    end_date: datetime | None = Field(None, description="结束日期")


class PasswordChangeRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=1, description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=50, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_new_password_complexity(cls, v: str) -> str:
        from ..utils.validators import validate_password_strength
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v


class PasswordStrengthRequest(BaseModel):
    """密码强度检查请求"""
    password: str = Field(..., min_length=1, description="要检查的密码")


class PasswordStrengthResponse(BaseModel):
    """密码强度响应"""
    score: int = Field(..., ge=0, le=100, description="强度分数（0-100）")
    level: str = Field(..., description="强度等级（weak, medium, strong）")
    feedback: list[str] = Field(..., description="改进建议")
    is_acceptable: bool = Field(..., description="是否可接受")


class SecurityLevelResponse(BaseModel):
    """安全等级响应"""
    score: int = Field(..., ge=0, le=100, description="安全分数（0-100）")
    level: str = Field(..., description="安全等级（low, medium, high）")
    factors: dict[str, Any] = Field(..., description="安全因素详情")
    recommendations: list[str] = Field(..., description="安全建议")


class BackupCodesRegenerateRequest(BaseModel):
    """重新生成备用码请求"""
    code: str = Field(..., min_length=6, max_length=10, description="当前2FA验证码")


class BackupCodesRegenerateResponse(BaseModel):
    """重新生成备用码响应"""
    backup_codes: list[str] = Field(..., description="新的备用验证码列表")


class SecurityOverviewResponse(BaseModel):
    """安全概览响应"""
    two_fa: dict[str, Any] = Field(..., description="2FA状态信息")
    security_level: dict[str, Any] = Field(..., description="安全等级信息")
    active_devices: list[dict[str, Any]] = Field(..., description="活跃设备列表")
    recent_logins: list[dict[str, Any]] = Field(..., description="最近登录记录")
    recommendations: list[str] = Field(..., description="安全建议")
