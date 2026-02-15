"""企业合规SaaS API 路由

提供企业账号管理、合同审查、合规模板库等功能。
"""
from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..services.enterprise_compliance import EnterpriseAccountManager, ContractReviewService, ComplianceTemplateService
from ..utils.deps import get_current_user_optional, get_current_user

router = APIRouter(prefix="/enterprise", tags=["企业合规SaaS"])

account_manager = EnterpriseAccountManager()
contract_review_service = ContractReviewService()
template_service = ComplianceTemplateService()


@router.post("/account/create")
async def create_enterprise_account(
    company_name: str,
    admin_email: str,
    current_user: Annotated[User, Depends(get_current_user)],
    industry: str = Query(default="general", description="行业"),
    scale: str = Query(default="smb", description="规模: smb/mid/enterprise"),
) -> dict:
    """创建企业账号"""
    result = await account_manager.create_enterprise_account(
        company_name=company_name,
        admin_email=admin_email,
        industry=industry,
        scale=scale,
    )
    return result


@router.get("/account/{account_id}")
async def get_enterprise_account(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """获取企业账号信息"""
    account = await account_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="企业账号不存在")
    return account


@router.post("/account/{account_id}/update")
async def update_enterprise_account(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    company_name: str | None = None,
    industry: str | None = None,
    scale: str | None = None,
    subscription_plan: str | None = None,
) -> dict:
    """更新企业账号"""
    update_data = {}
    if company_name:
        update_data["company_name"] = company_name
    if industry:
        update_data["industry"] = industry
    if scale:
        update_data["scale"] = scale
    if subscription_plan:
        update_data["subscription_plan"] = subscription_plan

    result = await account_manager.update_account(account_id, **update_data)
    return result


@router.post("/account/{account_id}/user/add")
async def add_enterprise_user(
    account_id: int,
    email: str,
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    role: str = Query(default="member", description="角色: member/admin/viewer"),
) -> dict:
    """添加企业用户"""
    result = await account_manager.add_user(
        account_id=account_id,
        email=email,
        name=name,
        role=role,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/account/{account_id}/users")
async def list_enterprise_users(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """获取企业用户列表"""
    users = await account_manager.list_users(account_id)
    return {
        "users": users,
        "total": len(users),
    }


@router.post("/contract/submit")
async def submit_contract_review(
    account_id: int,
    user_id: int,
    title: str,
    content: str,
    current_user: Annotated[User, Depends(get_current_user)],
    contract_type: str = Query(default="general", description="合同类型"),
) -> dict:
    """提交合同审查"""
    result = await contract_review_service.submit_contract(
        account_id=account_id,
        user_id=user_id,
        title=title,
        content=content,
        contract_type=contract_type,
    )
    return result


@router.get("/contract/{contract_id}")
async def get_contract_review(
    contract_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """获取合同审查结果"""
    result = await contract_review_service.get_review_result(contract_id)
    if not result:
        raise HTTPException(status_code=404, detail="合同不存在")
    return result


@router.get("/templates")
async def list_compliance_templates(
    current_user: Annotated[User, Depends(get_current_user)],
    category: str | None = Query(None, description="模板分类"),
) -> dict:
    """获取合规模板列表"""
    templates = await template_service.list_templates(category)
    return {
        "templates": templates,
        "total": len(templates),
    }


@router.get("/templates/{template_id}")
async def get_compliance_template(
    template_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """获取合规模板详情"""
    template = await template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("/templates/{template_id}/generate")
async def generate_contract_from_template(
    template_id: int,
    values: dict,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """根据模板生成合同"""
    result = await template_service.generate_contract(template_id, values)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/stats")
async def get_enterprise_stats(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """获取企业合规统计"""
    return await contract_review_service.get_stats(account_id)
