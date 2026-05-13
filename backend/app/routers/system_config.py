"""系统配置 API 路由

提供配置项增删改查、分组管理、历史记录、导入导出、缓存管理等功能。
"""
from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/system/configs", tags=["System-Config"])


class UpdateConfigBody(BaseModel):
    value: object
    reason: Optional[str] = None


class BatchUpdateBody(BaseModel):
    changes: list[dict]


class ImportBody(BaseModel):
    import_data: dict
    overwrite: bool = False


class ResetBody(BaseModel):
    reason: Optional[str] = None


# --- 模拟配置数据 ---

_configs: dict[str, dict] = {
    "cfg-001": {"id": "cfg-001", "key": "system.site_name", "value": "百姓法律助手", "default_value": "百姓法律助手", "description": "网站名称", "type": "string", "options": None, "group": "system", "is_editable": True, "is_sensitive": False, "updated_at": "2025-01-01T00:00:00", "updated_by": "admin"},
    "cfg-002": {"id": "cfg-002", "key": "system.site_description", "value": "专业的法律咨询服务平台", "default_value": "百姓法律助手 - 您的随身法律顾问", "description": "网站描述", "type": "string", "options": None, "group": "system", "is_editable": True, "is_sensitive": False, "updated_at": "2025-01-01T00:00:00", "updated_by": "admin"},
    "cfg-003": {"id": "cfg-003", "key": "system.max_file_size", "value": 10, "default_value": 10, "description": "最大上传文件大小(MB)", "type": "number", "options": None, "group": "system", "is_editable": True, "is_sensitive": False, "updated_at": "2025-03-15T14:00:00", "updated_by": "admin"},
    "cfg-004": {"id": "cfg-004", "key": "system.maintenance_mode", "value": False, "default_value": False, "description": "维护模式", "type": "boolean", "options": None, "group": "system", "is_editable": True, "is_sensitive": False, "updated_at": "2025-04-01T09:00:00", "updated_by": "admin"},
    "cfg-005": {"id": "cfg-005", "key": "system.session_timeout", "value": 3600, "default_value": 1800, "description": "会话超时(秒)", "type": "number", "options": None, "group": "security", "is_editable": True, "is_sensitive": False, "updated_at": "2025-04-15T11:00:00", "updated_by": "admin"},

    "cfg-006": {"id": "cfg-006", "key": "ai.max_tokens", "value": 4096, "default_value": 2048, "description": "AI最大Token数", "type": "number", "options": None, "group": "ai", "is_editable": True, "is_sensitive": False, "updated_at": "2025-05-01T10:00:00", "updated_by": "admin"},
    "cfg-007": {"id": "cfg-007", "key": "ai.temperature", "value": 0.7, "default_value": 0.5, "description": "AI回答温度(0-1)", "type": "number", "options": None, "group": "ai", "is_editable": True, "is_sensitive": False, "updated_at": "2025-05-01T10:00:00", "updated_by": "admin"},
    "cfg-008": {"id": "cfg-008", "key": "ai.model", "value": "gpt-4-turbo", "default_value": "gpt-3.5-turbo", "description": "AI模型选择", "type": "select", "options": ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o", "deepseek-v3"], "group": "ai", "is_editable": True, "is_sensitive": False, "updated_at": "2025-05-08T16:00:00", "updated_by": "admin"},
    "cfg-009": {"id": "cfg-009", "key": "ai.prompt_template", "value": "你是一名专业律师，请根据以下问题提供法律建议...", "default_value": "你是一名法律助手，请回答用户的问题...", "description": "AI提示词模板", "type": "string", "options": None, "group": "ai", "is_editable": True, "is_sensitive": False, "updated_at": "2025-04-20T09:00:00", "updated_by": "admin"},

    "cfg-010": {"id": "cfg-010", "key": "payment.min_amount", "value": 1.0, "default_value": 1.0, "description": "最低支付金额(元)", "type": "number", "options": None, "group": "payment", "is_editable": True, "is_sensitive": False, "updated_at": "2025-03-01T00:00:00", "updated_by": "admin"},
    "cfg-011": {"id": "cfg-011", "key": "payment.platform_fee_rate", "value": 0.2, "default_value": 0.2, "description": "平台手续费比例", "type": "number", "options": None, "group": "payment", "is_editable": True, "is_sensitive": False, "updated_at": "2025-03-01T00:00:00", "updated_by": "admin"},
    "cfg-012": {"id": "cfg-012", "key": "payment.wechat_enabled", "value": True, "default_value": True, "description": "微信支付开关", "type": "boolean", "options": None, "group": "payment", "is_editable": True, "is_sensitive": False, "updated_at": "2025-04-10T12:00:00", "updated_by": "admin"},
    "cfg-013": {"id": "cfg-013", "key": "payment.alipay_enabled", "value": True, "default_value": True, "description": "支付宝支付开关", "type": "boolean", "options": None, "group": "payment", "is_editable": True, "is_sensitive": False, "updated_at": "2025-04-10T12:00:00", "updated_by": "admin"},
    "cfg-014": {"id": "cfg-014", "key": "payment.withdraw_min", "value": 100, "default_value": 100, "description": "最低提现金额(元)", "type": "number", "options": None, "group": "payment", "is_editable": True, "is_sensitive": False, "updated_at": "2025-04-10T12:00:00", "updated_by": "admin"},

    "cfg-015": {"id": "cfg-015", "key": "notification.email_enabled", "value": True, "default_value": True, "description": "邮件通知开关", "type": "boolean", "options": None, "group": "notification", "is_editable": True, "is_sensitive": False, "updated_at": "2025-02-01T00:00:00", "updated_by": "admin"},
    "cfg-016": {"id": "cfg-016", "key": "notification.sms_enabled", "value": True, "default_value": True, "description": "短信通知开关", "type": "boolean", "options": None, "group": "notification", "is_editable": True, "is_sensitive": False, "updated_at": "2025-02-01T00:00:00", "updated_by": "admin"},
    "cfg-017": {"id": "cfg-017", "key": "notification.push_enabled", "value": False, "default_value": False, "description": "App推送通知开关", "type": "boolean", "options": None, "group": "notification", "is_editable": True, "is_sensitive": False, "updated_at": "2025-02-01T00:00:00", "updated_by": "admin"},

    "cfg-018": {"id": "cfg-018", "key": "security.max_login_attempts", "value": 5, "default_value": 5, "description": "最大登录尝试次数", "type": "number", "options": None, "group": "security", "is_editable": True, "is_sensitive": False, "updated_at": "2025-04-15T11:00:00", "updated_by": "admin"},
    "cfg-019": {"id": "cfg-019", "key": "security.lockout_duration", "value": 1800, "default_value": 900, "description": "账户锁定时间(秒)", "type": "number", "options": None, "group": "security", "is_editable": True, "is_sensitive": False, "updated_at": "2025-04-15T11:00:00", "updated_by": "admin"},
    "cfg-020": {"id": "cfg-020", "key": "security.api_key", "value": "sk-proj-xxxx-xxxx-xxxx", "default_value": None, "description": "第三方API密钥", "type": "string", "options": None, "group": "security", "is_editable": True, "is_sensitive": True, "updated_at": "2025-05-01T08:00:00", "updated_by": "admin"},
}

_groups: list[dict] = [
    {"id": "grp-001", "name": "系统设置", "description": "网站基本配置", "icon": "settings", "order": 1, "config_count": 4},
    {"id": "grp-002", "name": "AI配置", "description": "人工智能相关参数", "icon": "robot", "order": 2, "config_count": 4},
    {"id": "grp-003", "name": "支付配置", "description": "支付与手续费设置", "icon": "wallet", "order": 3, "config_count": 5},
    {"id": "grp-004", "name": "通知配置", "description": "邮件、短信、推送通知设置", "icon": "bell", "order": 4, "config_count": 3},
    {"id": "grp-005", "name": "安全配置", "description": "账户安全与API设置", "icon": "shield", "order": 5, "config_count": 4},
]

_history: list[dict] = [
    {"id": "hist-001", "config_id": "cfg-006", "config_key": "ai.max_tokens", "old_value": 2048, "new_value": 4096, "updated_by": "admin", "updated_by_name": "管理员", "updated_at": "2025-05-01T10:00:00", "change_reason": "升级模型上下文窗口"},
    {"id": "hist-002", "config_id": "cfg-008", "config_key": "ai.model", "old_value": "gpt-3.5-turbo", "new_value": "gpt-4-turbo", "updated_by": "admin", "updated_by_name": "管理员", "updated_at": "2025-05-08T16:00:00", "change_reason": "提升回答质量"},
    {"id": "hist-003", "config_id": "cfg-005", "config_key": "system.session_timeout", "old_value": 1800, "new_value": 3600, "updated_by": "admin", "updated_by_name": "管理员", "updated_at": "2025-04-15T11:00:00", "change_reason": "延长用户会话时间"},
    {"id": "hist-004", "config_id": "cfg-007", "config_key": "ai.temperature", "old_value": 0.5, "new_value": 0.7, "updated_by": "admin", "updated_by_name": "管理员", "updated_at": "2025-05-01T10:00:00", "change_reason": "增加回答多样性"},
    {"id": "hist-005", "config_id": "cfg-012", "config_key": "payment.wechat_enabled", "old_value": False, "new_value": True, "updated_by": "admin", "updated_by_name": "管理员", "updated_at": "2025-04-10T12:00:00", "change_reason": "开通微信支付"},
    {"id": "hist-006", "config_id": "cfg-019", "config_key": "security.lockout_duration", "old_value": 900, "new_value": 1800, "updated_by": "admin", "updated_by_name": "管理员", "updated_at": "2025-04-15T11:00:00", "change_reason": "加强安全策略"},
    {"id": "hist-007", "config_id": "cfg-003", "config_key": "system.max_file_size", "old_value": 5, "new_value": 10, "updated_by": "admin", "updated_by_name": "管理员", "updated_at": "2025-03-15T14:00:00", "change_reason": "用户反馈文件大小限制过小"},
    {"id": "hist-008", "config_id": "cfg-009", "config_key": "ai.prompt_template", "old_value": "你是一名法律助手，请回答用户的问题...", "new_value": "你是一名专业律师，请根据以下问题提供法律建议...", "updated_by": "admin", "updated_by_name": "管理员", "updated_at": "2025-04-20T09:00:00", "change_reason": "优化AI回答专业性"},
]


# ===== 注意：静态路由必须在参数化路由之前定义 =====

@router.get("/groups")
async def get_config_groups():
    updated_groups = []
    for g in _groups:
        count = sum(1 for c in _configs.values() if c["group"] == g["id"].replace("grp-", ""))
        updated_groups.append({**g, "config_count": count})
    return {"groups": updated_groups}


@router.get("/history")
async def get_config_history(
    config_id: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    data = list(_history)
    if config_id:
        data = [h for h in data if h["config_id"] == config_id]
    if group:
        data = [h for h in data if _configs.get(h["config_id"], {}).get("group") == group]
    if start_date:
        data = [h for h in data if h["updated_at"] >= start_date]
    if end_date:
        data = [h for h in data if h["updated_at"] <= end_date]
    total = len(data)
    items = data[offset:offset + limit]
    return {"histories": items, "total": total}


@router.get("/export")
async def export_config():
    return {"export_data": {"configs": list(_configs.values()), "groups": _groups}, "exported_at": datetime.now().isoformat()}


@router.get("/cache")
async def get_config_cache():
    return {"cached_keys": len(_configs), "cache_size": 1024, "last_refreshed": datetime.now().isoformat(), "status": "active"}


@router.post("/cache/refresh")
async def refresh_config_cache():
    return {"cached_keys": len(_configs), "last_refreshed": datetime.now().isoformat(), "status": "refreshed"}


@router.put("/batch")
async def batch_update_config(body: BatchUpdateBody):
    updated: list[dict] = []
    histories: list[dict] = []
    now = datetime.now().isoformat()
    for change in body.changes:
        cfg_id = change.get("config_id", "")
        if cfg_id in _configs:
            old_val = _configs[cfg_id]["value"]
            _configs[cfg_id]["value"] = change.get("value", old_val)
            _configs[cfg_id]["updated_at"] = now
            updated.append(dict(_configs[cfg_id]))
            histories.append({
                "id": f"hist-{len(_history) + 1}",
                "config_id": cfg_id,
                "config_key": _configs[cfg_id]["key"],
                "old_value": old_val,
                "new_value": change.get("value"),
                "updated_by": "admin",
                "updated_at": now,
            })
    return {"updated": updated, "histories": histories}


@router.post("/import")
async def import_config(body: ImportBody):
    now = datetime.now().isoformat()
    imported = 0
    updated = 0
    errors: list[str] = []
    import_data = body.import_data
    if isinstance(import_data, dict):
        for key, value in import_data.items():
            for cfg_id, cfg in _configs.items():
                if cfg["key"] == key:
                    if body.overwrite:
                        cfg["value"] = value
                        cfg["updated_at"] = now
                        updated += 1
                    else:
                        imported += 1
                    break
    return {"imported_count": imported, "updated_count": updated, "errors": errors, "imported_at": now}


# ===== 参数化路由（必须在静态路由之后） =====

@router.get("")
async def get_config_list(
    group: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    editable: Optional[bool] = Query(None),
):
    configs = list(_configs.values())
    if group:
        configs = [c for c in configs if c["group"] == group]
    if search:
        kw = search.lower()
        configs = [c for c in configs if kw in c["key"].lower() or kw in c["description"].lower()]
    if editable is not None:
        configs = [c for c in configs if c["is_editable"] == editable]
    return {"configs": configs, "groups": _groups}


@router.get("/{config_id}")
async def get_config_detail(config_id: str):
    if config_id in _configs:
        return {"config": _configs[config_id]}
    return {"config": None}


@router.put("/{config_id}")
async def update_config(config_id: str, body: UpdateConfigBody):
    if config_id not in _configs:
        return {"detail": "配置不存在"}
    now = datetime.now().isoformat()
    old_val = _configs[config_id]["value"]
    _configs[config_id]["value"] = body.value
    _configs[config_id]["updated_at"] = now
    history_entry = {
        "id": f"hist-{len(_history) + 1}",
        "config_id": config_id,
        "config_key": _configs[config_id]["key"],
        "old_value": old_val,
        "new_value": body.value,
        "updated_by": "admin",
        "updated_by_name": "管理员",
        "updated_at": now,
        "change_reason": body.reason,
    }
    _history.append(history_entry)
    return {"config": _configs[config_id], "history": history_entry}


@router.post("/{config_id}/reset")
async def reset_config(config_id: str, body: ResetBody = ResetBody()):
    if config_id not in _configs:
        return {"detail": "配置不存在"}
    now = datetime.now().isoformat()
    old_val = _configs[config_id]["value"]
    _configs[config_id]["value"] = _configs[config_id]["default_value"]
    _configs[config_id]["updated_at"] = now
    history_entry = {
        "id": f"hist-{len(_history) + 1}",
        "config_id": config_id,
        "config_key": _configs[config_id]["key"],
        "old_value": old_val,
        "new_value": _configs[config_id]["default_value"],
        "updated_by": "admin",
        "updated_at": now,
    }
    _history.append(history_entry)
    return {"config": _configs[config_id], "history": history_entry}