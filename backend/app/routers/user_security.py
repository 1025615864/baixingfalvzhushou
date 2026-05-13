"""用户安全 API 路由

提供2FA、设备管理、登录审计、密码安全、安全等级评估等面向用户的安全功能。
与 security.py（数据安全/脱敏/分级）职责分离。
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/security", tags=["User-Security"])


class CodeBody(BaseModel):
    code: str


class PasswordCheckBody(BaseModel):
    password: str


class DeviceBody(BaseModel):
    password: Optional[str] = None


# --- 2FA ---

@router.get("/2fa/status")
async def get_two_factor_status():
    return {"is_enabled": False, "is_setup": False}


@router.post("/2fa/setup/init")
async def init_two_factor_setup():
    return {
        "secret": "JBSWY3DPEHPK3PXP",
        "uri": "otpauth://totp/百姓法律助手:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=百姓法律助手",
        "backup_codes": ["A8F3-K2J9", "M5X1-P7R4", "Q9W6-Y3S8", "L2D7-H1B0", "C4N6-V8T3"],
        "qr_code_url": None,
    }


@router.post("/2fa/setup/verify")
async def verify_two_factor_setup(body: CodeBody):
    return {"message": "2FA已启用", "success": True}


@router.post("/2fa/disable")
async def disable_two_factor(body: CodeBody):
    return {"message": "2FA已禁用", "success": True}


@router.post("/2fa/verify")
async def verify_two_factor_code(body: CodeBody):
    return {"message": "验证成功", "success": True}


@router.post("/2fa/backup-codes/regenerate")
async def regenerate_backup_codes(body: CodeBody):
    return {"backup_codes": ["Z1F8-X4K2", "B3M7-D9P5", "W6Q2-Y8N3", "R1J5-S7T4", "G2L8-V6H0"]}


# --- 设备管理 ---

_devices: list[dict] = [
    {"device_id": "dev-001", "device_name": "MacBook Pro", "device_type": "desktop", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "ip_address": "192.168.1.100", "location": "北京市朝阳区", "first_login_at": "2025-01-15T09:00:00", "last_login_at": datetime.now().isoformat(), "is_current": True, "is_revoked": False},
    {"device_id": "dev-002", "device_name": "iPhone 15 Pro", "device_type": "mobile", "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0)", "ip_address": "192.168.1.101", "location": "北京市海淀区", "first_login_at": "2025-03-20T14:00:00", "last_login_at": (datetime.now() - timedelta(hours=2)).isoformat(), "is_current": False, "is_revoked": False},
    {"device_id": "dev-003", "device_name": "iPad Air", "device_type": "tablet", "user_agent": "Mozilla/5.0 (iPad; CPU OS 18_0)", "ip_address": "192.168.1.102", "location": "上海市浦东新区", "first_login_at": "2025-04-10T11:00:00", "last_login_at": (datetime.now() - timedelta(days=1)).isoformat(), "is_current": False, "is_revoked": False},
    {"device_id": "dev-004", "device_name": "Windows PC", "device_type": "desktop", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "ip_address": "10.0.0.50", "location": "广州市天河区", "first_login_at": "2025-05-01T08:00:00", "last_login_at": (datetime.now() - timedelta(days=3)).isoformat(), "is_current": False, "is_revoked": False},
    {"device_id": "dev-005", "device_name": "Android Phone", "device_type": "mobile", "user_agent": "Mozilla/5.0 (Linux; Android 14)", "ip_address": "172.16.0.30", "location": "深圳市南山区", "first_login_at": "2025-04-25T17:00:00", "last_login_at": (datetime.now() - timedelta(days=5)).isoformat(), "is_current": False, "is_revoked": True},
]


@router.get("/devices")
async def get_devices():
    active_devices = [d for d in _devices if not d["is_revoked"]]
    current = next((d for d in _devices if d["is_current"]), None)
    return {
        "devices": active_devices,
        "total": len(active_devices),
        "current_device_id": current["device_id"] if current else None,
    }


@router.delete("/devices/{device_id}")
async def revoke_device(device_id: str):
    for d in _devices:
        if d["device_id"] == device_id and not d["is_current"]:
            d["is_revoked"] = True
            return {"message": "设备已踢出", "success": True}
    return {"message": "无法踢出当前设备或不存在的设备", "success": False}


@router.delete("/devices/others")
async def revoke_other_devices():
    count = 0
    for d in _devices:
        if not d["is_current"] and not d["is_revoked"]:
            d["is_revoked"] = True
            count += 1
    return {"message": f"其他设备已全部踢出，共踢出{count}台设备", "success": True}


# --- 登录审计 ---

_login_records: list[dict] = [
    {"id": 1, "action": "login", "success": True, "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "device_id": "dev-001", "location": "北京市朝阳区", "failure_reason": None, "created_at": (datetime.now() - timedelta(hours=1)).isoformat()},
    {"id": 2, "action": "login", "success": True, "ip_address": "192.168.1.101", "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0)", "device_id": "dev-002", "location": "北京市海淀区", "failure_reason": None, "created_at": (datetime.now() - timedelta(hours=3)).isoformat()},
    {"id": 3, "action": "failed", "success": False, "ip_address": "203.0.113.50", "user_agent": "Mozilla/5.0 (Windows NT 10.0)", "device_id": None, "location": "未知", "failure_reason": "密码错误", "created_at": (datetime.now() - timedelta(hours=5)).isoformat()},
    {"id": 4, "action": "login", "success": True, "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "device_id": "dev-001", "location": "北京市朝阳区", "failure_reason": None, "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
    {"id": 5, "action": "logout", "success": True, "ip_address": "192.168.1.101", "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0)", "device_id": "dev-002", "location": "北京市海淀区", "failure_reason": None, "created_at": (datetime.now() - timedelta(days=1, hours=2)).isoformat()},
    {"id": 6, "action": "login", "success": True, "ip_address": "10.0.0.50", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "device_id": "dev-004", "location": "广州市天河区", "failure_reason": None, "created_at": (datetime.now() - timedelta(days=3)).isoformat()},
    {"id": 7, "action": "login", "success": True, "ip_address": "172.16.0.30", "user_agent": "Mozilla/5.0 (Linux; Android 14)", "device_id": "dev-005", "location": "深圳市南山区", "failure_reason": None, "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
    {"id": 8, "action": "login", "success": True, "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "device_id": "dev-001", "location": "北京市朝阳区", "failure_reason": None, "created_at": (datetime.now() - timedelta(days=7)).isoformat()},
    {"id": 9, "action": "failed", "success": False, "ip_address": "198.51.100.20", "user_agent": "Mozilla/5.0 (X11; Linux x86_64)", "device_id": None, "location": "未知", "failure_reason": "账号不存在", "created_at": (datetime.now() - timedelta(days=8)).isoformat()},
    {"id": 10, "action": "2fa_verify", "success": True, "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "device_id": "dev-001", "location": "北京市朝阳区", "failure_reason": None, "created_at": (datetime.now() - timedelta(days=9)).isoformat()},
    {"id": 11, "action": "password_change", "success": True, "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "device_id": "dev-001", "location": "北京市朝阳区", "failure_reason": None, "created_at": (datetime.now() - timedelta(days=10)).isoformat()},
    {"id": 12, "action": "login", "success": True, "ip_address": "192.168.1.102", "user_agent": "Mozilla/5.0 (iPad; CPU OS 18_0)", "device_id": "dev-003", "location": "上海市浦东新区", "failure_reason": None, "created_at": (datetime.now() - timedelta(days=12)).isoformat()},
    {"id": 13, "action": "failed", "success": False, "ip_address": "203.0.113.100", "user_agent": "Mozilla/5.0 (Windows NT 10.0)", "device_id": None, "location": "未知", "failure_reason": "验证码错误", "created_at": (datetime.now() - timedelta(days=13)).isoformat()},
    {"id": 14, "action": "login", "success": True, "ip_address": "192.168.1.101", "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0)", "device_id": "dev-002", "location": "北京市海淀区", "failure_reason": None, "created_at": (datetime.now() - timedelta(days=14)).isoformat()},
    {"id": 15, "action": "logout", "success": True, "ip_address": "10.0.0.50", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "device_id": "dev-004", "location": "广州市天河区", "failure_reason": None, "created_at": (datetime.now() - timedelta(days=14, hours=1)).isoformat()},
]


@router.get("/audit/logins")
async def get_login_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    data = list(_login_records)
    if action:
        data = [r for r in data if r["action"] == action]
    if start_date:
        data = [r for r in data if r["created_at"] >= start_date]
    if end_date:
        data = [r for r in data if r["created_at"] <= end_date]
    total = len(data)
    start = (page - 1) * page_size
    records = data[start:start + page_size]
    return {"records": records, "total": total, "page": page, "page_size": page_size}


# --- 密码安全 ---

@router.post("/password/check-strength")
async def check_password_strength(body: PasswordCheckBody):
    pwd = body.password
    score = 0
    feedback: list[str] = []
    if len(pwd) >= 8:
        score += 25
    else:
        feedback.append("密码长度至少8位")
    if any(c.isupper() for c in pwd):
        score += 20
    else:
        feedback.append("建议包含大写字母")
    if any(c.islower() for c in pwd):
        score += 15
    else:
        feedback.append("建议包含小写字母")
    if any(c.isdigit() for c in pwd):
        score += 20
    else:
        feedback.append("建议包含数字")
    if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in pwd):
        score += 20
    else:
        feedback.append("建议包含特殊字符")

    if score >= 80:
        level = "strong"
    elif score >= 50:
        level = "medium"
    else:
        level = "weak"

    return {"score": score, "level": level, "feedback": feedback, "is_acceptable": score >= 50}


# --- 安全等级 ---

@router.get("/level")
async def get_security_level():
    return {
        "score": 65,
        "level": "medium",
        "factors": {
            "password": True,
            "2fa": False,
            "recent_activity": True,
            "device_count": 4,
            "last_password_change": (datetime.now() - timedelta(days=60)).isoformat(),
        },
        "recommendations": [
            "建议启用两步验证(2FA)提升账户安全性",
            "建议定期修改密码",
            "建议定期检查登录设备列表",
        ],
    }