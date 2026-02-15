from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContractReviewResponse(BaseModel):
    filename: str = Field(..., description="文件名")
    content_type: str | None = Field(None, description="文件类型")
    contract_type: str | None = Field(None, description="合同类型")
    text_chars: int = Field(..., description="提取文本长度")
    text_preview: str = Field(..., description="提取文本预览")
    risk_level: str = Field("low", description="风险等级：low/medium/high")
    risk_count: int = Field(0, description="风险点数量")
    report_json: dict[str, Any] = Field(
        default_factory=dict, description="结构化风险体检报告")
    report_markdown: str = Field("", description="可渲染的 Markdown 报告")
    request_id: str = Field("", description="请求ID")


class ContractReviewErrorResponse(BaseModel):
    error_code: str
    message: str
    request_id: str


class ContractReviewHistoryItem(BaseModel):
    """合同审查历史记录项"""
    id: str = Field(..., description="记录ID")
    filename: str = Field(..., description="文件名")
    contract_type: str | None = Field(None, description="合同类型")
    risk_level: str = Field(..., description="风险等级：low/medium/high")
    risk_count: int = Field(default=0, description="风险点数量")
    request_id: str = Field(..., description="请求ID")
    created_at: datetime = Field(..., description="审查时间")


class ContractReviewHistoryListResponse(BaseModel):
    """审查历史列表响应"""
    items: list[ContractReviewHistoryItem] = Field(default_factory=list, description="历史记录列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=10, description="每页数量")


class ContractDiffItem(BaseModel):
    """合同比对差异项"""
    type: str = Field(..., description="差异类型：add/remove/modify")
    content: str = Field(..., description="差异内容")
    position: dict[str, int] = Field(..., description="位置信息：page, line")


class ContractCompareResponse(BaseModel):
    """合同比对响应"""
    original_filename: str = Field(..., description="原版本文件名")
    new_filename: str = Field(..., description="新版本文件名")
    differences: list[ContractDiffItem] = Field(default_factory=list, description="差异列表")
    summary: dict[str, int] = Field(..., description="差异统计：added, removed, modified")
    request_id: str = Field(..., description="请求ID")
