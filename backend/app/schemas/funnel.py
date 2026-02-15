from typing import Any
from pydantic import BaseModel, Field

class FunnelStep(BaseModel):
    step_id: str = Field(..., description="步骤ID")
    name: str = Field(..., description="步骤名称")
    event_type: str = Field(..., description="事件类型")
    conditions: list[dict[str, Any]] | None = Field(default=None, description="过滤条件")

class FunnelCreateRequest(BaseModel):
    funnel_id: str = Field(..., description="漏斗ID")
    name: str = Field(..., description="漏斗名称")
    steps: list[FunnelStep] = Field(..., description="步骤列表")

class FunnelTrackRequest(BaseModel):
    funnel_id: str = Field(..., description="漏斗ID")
    step_id: str = Field(..., description="步骤ID")
    properties: dict[str, Any] | None = Field(default=None, description="事件属性")
