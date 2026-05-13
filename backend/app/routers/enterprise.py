from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/enterprise", tags=["Enterprise"])

_enterprise_info: dict = {
    "id": 1, "name": "百姓法律科技有限公司", "industry": "法律服务", "scale": "50-200人",
    "address": "北京市朝阳区建国路88号", "contact_person": "王经理", "contact_phone": "13800138000",
    "email": "hr@example-legal.com", "legal_representative": "张总", "business_license": "91110000MA001ABCDE",
    "verified": True, "created_at": "2024-01-15T09:00:00", "updated_at": "2025-05-01T14:30:00",
}

_team_members: list[dict] = [
    {"id": 1, "user_id": 10, "name": "王经理", "role": "admin", "email": "wang@example-legal.com", "phone": "13800138000", "joined_at": "2024-01-15T09:00:00"},
    {"id": 2, "user_id": 11, "name": "李法务", "role": "legal", "email": "li@example-legal.com", "phone": "13800138001", "joined_at": "2024-03-20T10:00:00"},
    {"id": 3, "user_id": 12, "name": "赵律师", "role": "legal", "email": "zhao@example-legal.com", "phone": "13800138002", "joined_at": "2024-06-01T09:00:00"},
    {"id": 4, "user_id": 13, "name": "陈助理", "role": "member", "email": "chen@example-legal.com", "phone": "13800138003", "joined_at": "2025-01-10T11:00:00"},
]

_member_counter = 5

_enterprise_orders: list[dict] = [
    {"id": 1, "order_no": "ENT202505010001", "order_type": "compliance_report", "title": "年度合规报告", "amount": 5000, "actual_amount": 5000, "status": "completed", "created_at": "2025-05-01T10:00:00", "paid_at": "2025-05-01T10:30:00"},
    {"id": 2, "order_no": "ENT202505080002", "order_type": "contract_review", "title": "批量合同审查(20份)", "amount": 20000, "actual_amount": 18000, "status": "paid", "created_at": "2025-05-08T14:00:00", "paid_at": "2025-05-08T14:15:00"},
    {"id": 3, "order_no": "ENT202505100003", "order_type": "legal_consultation", "title": "企业法律顾问套餐", "amount": 30000, "actual_amount": 30000, "status": "pending", "created_at": "2025-05-10T09:00:00", "paid_at": None},
]

_order_counter = 4

_COMPLIANCE_TEMPLATES = [
    {"id": 1, "name": "企业年度合规报告模板", "category": "年度报告", "description": "适用于各类企业的年度合规管理报告模板", "required_docs": ["营业执照", "年度审计报告"], "estimated_time": "5个工作日", "price": 5000},
    {"id": 2, "name": "合同合规审查模板", "category": "合同管理", "description": "企业合同合规性审查标准模板", "required_docs": ["合同文本", "交易背景说明"], "estimated_time": "2个工作日", "price": 2000},
    {"id": 3, "name": "数据合规自评报告模板", "category": "数据合规", "description": "个人信息保护与数据安全合规自评模板", "required_docs": ["数据处理活动记录", "隐私政策"], "estimated_time": "3个工作日", "price": 3000},
    {"id": 4, "name": "劳动用工合规检查清单", "category": "劳动合规", "description": "企业劳动用工合规风险排查清单", "required_docs": ["劳动合同", "社保缴纳记录"], "estimated_time": "2个工作日", "price": 1500},
]

_compliance_reports: list[dict] = [
    {"id": 1, "template_id": 1, "template_name": "企业年度合规报告模板", "status": "completed", "content": "2024年度企业合规报告已完成。主要内容包括：合规管理体系建设、重点领域合规审查、风险排查与整改等内容。", "created_at": "2025-03-15T09:00:00", "completed_at": "2025-05-01T10:00:00"},
    {"id": 2, "template_id": 4, "template_name": "劳动用工合规检查清单", "status": "generating", "content": "正在生成劳动用工合规检查报告...", "created_at": "2025-05-08T14:00:00", "completed_at": None},
]

_report_counter = 3

_PERMISSIONS = [
    {"id": 1, "name": "企业信息管理", "key": "enterprise_info", "description": "查看和编辑企业基本信息"},
    {"id": 2, "name": "团队成员管理", "key": "team_member", "description": "添加、编辑、移除团队成员"},
    {"id": 3, "name": "订单管理", "key": "order_mgmt", "description": "查看和管理企业订单"},
    {"id": 4, "name": "合同审查", "key": "contract_review", "description": "发起和管理合同审查"},
    {"id": 5, "name": "合规报告", "key": "compliance_report", "description": "生成和查看合规报告"},
    {"id": 6, "name": "文档管理", "key": "document_mgmt", "description": "上传和管理企业文档"},
]

_ROLE_PERMISSIONS = {
    "admin": ["enterprise_info", "team_member", "order_mgmt", "contract_review", "compliance_report", "document_mgmt"],
    "legal": ["enterprise_info", "contract_review", "compliance_report", "document_mgmt"],
    "member": ["enterprise_info", "contract_review", "document_mgmt"],
}

_documents: list[dict] = [
    {"id": 1, "name": "营业执照.pdf", "category": "证照", "size": 1024000, "file_type": "pdf", "version": 1, "uploaded_by": "王经理", "created_at": "2024-01-15T09:00:00"},
    {"id": 2, "name": "年度审计报告2024.pdf", "category": "财务", "size": 2048000, "file_type": "pdf", "version": 1, "uploaded_by": "李法务", "created_at": "2025-03-20T10:00:00"},
    {"id": 3, "name": "劳动合同模板.docx", "category": "合同", "size": 512000, "file_type": "docx", "version": 2, "uploaded_by": "赵律师", "created_at": "2025-04-01T14:00:00"},
]

_doc_counter = 4
_doc_versions: dict[int, list[dict]] = {}

_contract_reviews: list[dict] = []


@router.get("/info")
def get_enterprise_info():
    return _enterprise_info


@router.post("/info")
def update_enterprise_info(body: dict):
    for k, v in body.items():
        if k in _enterprise_info:
            _enterprise_info[k] = v
    _enterprise_info["updated_at"] = datetime.now().isoformat()
    return {"success": True, "data": _enterprise_info}


@router.get("/members")
def get_team_members(user_id: Optional[int] = Query(None)):
    return {"members": _team_members, "total": len(_team_members)}


@router.post("/members")
def add_team_member(body: dict):
    global _member_counter
    member = {
        "id": _member_counter,
        "user_id": body.get("user_id", _member_counter),
        "name": body.get("name", ""),
        "role": body.get("role", "member"),
        "email": body.get("email", ""),
        "phone": body.get("phone", ""),
        "joined_at": datetime.now().isoformat(),
    }
    _team_members.append(member)
    _member_counter += 1
    return {"success": True, "member": member}


@router.delete("/members/{member_id}")
def remove_team_member(member_id: int):
    global _team_members
    _team_members = [m for m in _team_members if m["id"] != member_id]
    return {"success": True}


@router.put("/members/{member_id}/role")
def update_member_role(member_id: int, body: dict):
    for m in _team_members:
        if m["id"] == member_id:
            m["role"] = body.get("role", m["role"])
            return {"success": True, "member": m}
    raise HTTPException(status_code=404, detail="成员不存在")


@router.get("/orders")
def get_enterprise_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
):
    items = list(_enterprise_orders)
    if status:
        items = [o for o in items if o["status"] == status]
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "total": total, "page": page, "page_size": page_size}


@router.post("/contract-review")
def submit_contract_review(body: dict):
    review = {
        "id": len(_contract_reviews) + 1,
        "title": body.get("title", ""),
        "content": body.get("content", ""),
        "status": "submitted",
        "created_at": datetime.now().isoformat(),
    }
    _contract_reviews.append(review)
    return {"success": True, "review": review}


@router.get("/contract-review")
def get_contract_reviews(page: int = Query(1), page_size: int = Query(20)):
    items = _contract_reviews
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "total": total}


@router.get("/compliance/templates")
def get_compliance_templates():
    return {"templates": _COMPLIANCE_TEMPLATES}


@router.get("/compliance/reports")
def get_compliance_reports(page: int = Query(1), page_size: int = Query(20)):
    total = len(_compliance_reports)
    start = (page - 1) * page_size
    return {"items": _compliance_reports[start:start + page_size], "total": total}


@router.get("/compliance/reports/{report_id}")
def get_compliance_report(report_id: int):
    for r in _compliance_reports:
        if r["id"] == report_id:
            return r
    raise HTTPException(status_code=404, detail="报告不存在")


@router.post("/compliance/reports")
def generate_compliance_report(body: dict):
    global _report_counter
    report = {
        "id": _report_counter,
        "template_id": body.get("template_id"),
        "template_name": body.get("template_name", "自定义报告"),
        "status": "generating",
        "content": "正在生成合规报告...",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    _compliance_reports.append(report)
    _report_counter += 1
    return {"success": True, "report": report}


@router.delete("/compliance/reports/{report_id}")
def delete_compliance_report(report_id: int):
    global _compliance_reports
    _compliance_reports = [r for r in _compliance_reports if r["id"] != report_id]
    return {"success": True}


@router.get("/compliance/reports/{report_id}/export")
def export_compliance_report(report_id: int):
    return {"download_url": f"/api/enterprise/compliance/reports/{report_id}/download", "format": "pdf"}


@router.get("/permissions")
def get_permissions():
    return {"permissions": _PERMISSIONS}


@router.get("/permissions/roles/{role_key}")
def get_role_permissions(role_key: str):
    permissions = _ROLE_PERMISSIONS.get(role_key, [])
    return {"role": role_key, "permissions": permissions}


@router.put("/permissions/roles/{role_key}")
def update_role_permissions(role_key: str, body: dict):
    _ROLE_PERMISSIONS[role_key] = body.get("permissions", [])
    return {"success": True, "role": role_key, "permissions": _ROLE_PERMISSIONS[role_key]}


@router.get("/documents")
def get_enterprise_documents(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items = list(_documents)
    if category:
        items = [d for d in items if d["category"] == category]
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "total": total}


@router.get("/documents/{doc_id}")
def get_enterprise_document(doc_id: int):
    for d in _documents:
        if d["id"] == doc_id:
            return d
    raise HTTPException(status_code=404, detail="文档不存在")


@router.post("/documents")
def upload_enterprise_document(body: dict):
    global _doc_counter
    doc = {
        "id": _doc_counter,
        "name": body.get("name", "未命名文档"),
        "category": body.get("category", "其他"),
        "size": body.get("size", 0),
        "file_type": body.get("file_type", "pdf"),
        "version": 1,
        "uploaded_by": body.get("uploaded_by", "系统"),
        "created_at": datetime.now().isoformat(),
    }
    _documents.append(doc)
    _doc_counter += 1
    return {"success": True, "document": doc}


@router.put("/documents/{doc_id}")
def update_enterprise_document(doc_id: int, body: dict):
    for d in _documents:
        if d["id"] == doc_id:
            d["version"] = d.get("version", 1) + 1
            for k, v in body.items():
                if k in d:
                    d[k] = v
            return {"success": True, "document": d}
    raise HTTPException(status_code=404, detail="文档不存在")


@router.delete("/documents/{doc_id}")
def delete_enterprise_document(doc_id: int):
    global _documents
    _documents = [d for d in _documents if d["id"] != doc_id]
    return {"success": True}


@router.get("/documents/{doc_id}/versions")
def get_document_versions(doc_id: int):
    versions = _doc_versions.get(doc_id, [])
    return {"doc_id": doc_id, "versions": versions}