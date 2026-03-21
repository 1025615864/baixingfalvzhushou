"""Agent管理路由"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import AgentConfig
from sqlalchemy import select

router = APIRouter()


class AgentConfigResponse(BaseModel):
    id: int
    name: str
    version: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class CreateAgentConfigRequest(BaseModel):
    name: str
    version: str
    prompt_template: str
    rules: List[str] = []
    rag_config: dict = {}


class UpdateAgentConfigRequest(BaseModel):
    prompt_template: Optional[str] = None
    rules: Optional[List[str]] = None
    rag_config: Optional[dict] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_agents(
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取Agent配置列表"""
    result = await db.execute(
        select(AgentConfig).order_by(AgentConfig.created_at.desc())
    )
    agents = result.scalars().all()
    return {"items": [AgentConfigResponse.model_validate(a) for a in agents]}


@router.post("/")
async def create_agent(
    request: CreateAgentConfigRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """创建Agent配置（支持版本管理）"""
    agent = AgentConfig(
        name=request.name,
        version=request.version,
        prompt_template=request.prompt_template,
        rules=request.rules,
        rag_config=request.rag_config,
        is_active=False,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return AgentConfigResponse.model_validate(agent)


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: int,
    request: UpdateAgentConfigRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """更新Agent配置"""
    result = await db.execute(
        select(AgentConfig).where(AgentConfig.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if request.prompt_template is not None:
        agent.prompt_template = request.prompt_template
    if request.rules is not None:
        agent.rules = request.rules
    if request.rag_config is not None:
        agent.rag_config = request.rag_config
    if request.is_active is not None:
        agent.is_active = request.is_active

    await db.commit()
    await db.refresh(agent)
    return AgentConfigResponse.model_validate(agent)
