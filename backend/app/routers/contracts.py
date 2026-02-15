"""合同审查API路由"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from ..database import get_db
from ..models.user import User
from ..schemas.contracts import (
    ContractCompareResponse,
    ContractReviewErrorResponse,
    ContractReviewHistoryListResponse,
    ContractReviewResponse,
)
from ..services.contracts.history_service import (
    ContractCompareService,
    ContractHistoryService,
)
from ..services.contracts.review_service import review_contract_request
from ..services.document_export.pdf_generator import (
    PDFGenerationError,
    generate_contract_pdf,
)
from ..services.document_export.word_generator import (
    WordGenerationError,
    generate_contract_word,
)
from ..utils.deps import get_current_user, get_current_user_optional
from ..utils.rate_limiter import RateLimitConfig, rate_limit

router = APIRouter(prefix="/contracts", tags=["合同审查"])


@router.post("/review", response_model=ContractReviewResponse)
@rate_limit(*RateLimitConfig.AI_HEAVY, by_ip=True, by_user=False)
async def review_contract(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """审查合同"""
    return await review_contract_request(
        request=request,
        file=file,
        current_user=current_user,
        db=db,
    )


@router.get("/review/history", response_model=ContractReviewHistoryListResponse)
async def get_review_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
):
    """获取合同审查历史记录列表"""
    user_id = current_user.id if current_user else None
    return await ContractHistoryService.get_review_history(
        db=db,
        user_id=user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/review/history/{review_id}")
async def get_review_detail(
    review_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
):
    """获取审查详情

    需要用户认证才能查看审查详情，保护用户数据隐私。
    """
    review = await ContractHistoryService.get_review_detail(db=db, review_id=review_id)

    if not review:
        return ContractReviewErrorResponse(
            error_code="NOT_FOUND",
            message="未找到该审查记录",
            request_id="",
        )

    # 如果审查记录关联了用户，验证当前用户是否有权查看
    if review.user_id is not None:
        if current_user is None:
            raise HTTPException(status_code=401, detail="需要登录才能查看该审查记录")
        if current_user.id != review.user_id:
            raise HTTPException(status_code=403, detail="无权查看该审查记录")

    return ContractReviewResponse(
        filename=review.filename,
        content_type=review.content_type,
        contract_type=review.contract_type,
        text_chars=review.text_chars,
        text_preview=review.text_preview,
        risk_level=review.risk_level,
        risk_count=review.risk_count,
        report_json=review.report_json or {},
        report_markdown=review.report_markdown,
        request_id=review.request_id,
    )


@router.delete("/review/history/{review_id}")
async def delete_review(
    review_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """删除审查记录"""
    user_id = current_user.id if current_user else None
    deleted = await ContractHistoryService.delete_review(
        db=db, review_id=review_id, user_id=user_id
    )

    if not deleted:
        return {"error": "未找到该记录或无权删除"}

    return {"message": "删除成功"}


@router.post("/compare")
async def compare_contracts(
    original_file: Annotated[UploadFile, File(..., description="原版本文件")],
    new_file: Annotated[UploadFile, File(..., description="新版本文件")],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """比对两个合同文件的差异"""
    import asyncio

    # 读取原文件
    try:
        original_content = await original_file.read()
    except Exception:
        logger.exception("Failed to read original file")
        return {"error": "读取原文件失败"}

    # 读取新文件
    try:
        new_content = await new_file.read()
    except Exception:
        logger.exception("Failed to read new file")
        return {"error": "读取新文件失败"}

    # 检查文件大小
    if len(original_content) > 10 * 1024 * 1024:
        return {"error": "原文件大小不能超过10MB"}
    if len(new_content) > 10 * 1024 * 1024:
        return {"error": "新文件大小不能超过10MB"}

    # 提取文本
    try:
        from ..services.contracts.review_service import _extract_text_sync

        original_filename = original_file.filename or ""
        new_filename = new_file.filename or ""
        original_ext = (
            original_filename.rsplit(".", 1)[-1].lower()
            if "." in original_filename
            else ""
        )
        new_ext = new_filename.rsplit(".", 1)[-1].lower() if "." in new_filename else ""

        original_text = await asyncio.to_thread(
            _extract_text_sync,
            original_content,
            ext=original_ext,
            content_type=original_file.content_type,
        )
        new_text = await asyncio.to_thread(
            _extract_text_sync,
            new_content,
            ext=new_ext,
            content_type=new_file.content_type,
        )
    except Exception as e:
        return {"error": f"文件解析失败: {str(e)}"}

    # 进行比对
    try:
        result = await ContractCompareService.compare_contracts(
            original_text=original_text or "",
            new_text=new_text or "",
            original_filename=original_filename,
            new_filename=new_filename,
        )
        return result
    except Exception as e:
        return {"error": f"比对失败: {str(e)}"}


@router.get("/review/{review_id}/export/pdf")
async def export_review_pdf(
    review_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    includeDetailedRisks: bool = Query(True, description="包含详细风险分析"),
    includeRecommendedEdits: bool = Query(True, description="包含建议修改稿"),
    includeMissingClauses: bool = Query(True, description="包含缺失条款"),
):
    """
    导出合同审查报告为PDF格式

    该端点根据审查记录生成PDF格式的报告，支持选择性导出内容。
    需要用户认证才能导出关联用户的审查报告。

    Args:
        review_id: 审查记录ID
        db: 数据库会话
        current_user: 当前用户
        includeDetailedRisks: 是否包含详细风险分析
        includeRecommendedEdits: 是否包含建议修改稿
        includeMissingClauses: 是否包含缺失条款

    Returns:
        Response: PDF文件响应

    Raises:
        401: 未认证
        403: 无权访问
        404: 审查记录不存在
        500: PDF生成失败
    """
    # 先获取审查记录验证权限
    review = await ContractHistoryService.get_review_detail(db=db, review_id=review_id)

    if not review:
        raise HTTPException(status_code=404, detail="审查记录不存在")

    # 如果审查记录关联了用户，验证当前用户是否有权导出
    if review.user_id is not None:
        if current_user is None:
            raise HTTPException(status_code=401, detail="需要登录才能导出该审查记录")
        if current_user.id != review.user_id:
            raise HTTPException(status_code=403, detail="无权导出该审查记录")

    # 构建导出选项
    options = {
        "includeDetailedRisks": includeDetailedRisks,
        "includeRecommendedEdits": includeRecommendedEdits,
        "includeMissingClauses": includeMissingClauses,
    }

    # 生成PDF
    try:
        pdf_content = await generate_contract_pdf(
            db=db,
            review_id=review_id,
            options=options,
        )
    except PDFGenerationError as e:
        return {
            "error": "PDF生成失败",
            "message": str(e),
        }

    # 返回PDF文件
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=contract_review_{review_id}.pdf",
        },
    )


@router.get("/review/{review_id}/export/word")
async def export_review_word(
    review_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    includeDetailedRisks: bool = Query(True, description="包含详细风险分析"),
    includeRecommendedEdits: bool = Query(True, description="包含建议修改稿"),
    includeMissingClauses: bool = Query(True, description="包含缺失条款"),
):
    """
    导出合同审查报告为Word格式

    该端点根据审查记录生成Word格式的报告，支持选择性导出内容。
    需要用户认证才能导出关联用户的审查报告。

    Args:
        review_id: 审查记录ID
        db: 数据库会话
        current_user: 当前用户
        includeDetailedRisks: 是否包含详细风险分析
        includeRecommendedEdits: 是否包含建议修改稿
        includeMissingClauses: 是否包含缺失条款

    Returns:
        Response: Word文件响应

    Raises:
        401: 未认证
        403: 无权访问
        404: 审查记录不存在
        500: Word生成失败
    """
    # 先获取审查记录验证权限
    review = await ContractHistoryService.get_review_detail(db=db, review_id=review_id)

    if not review:
        raise HTTPException(status_code=404, detail="审查记录不存在")

    # 如果审查记录关联了用户，验证当前用户是否有权导出
    if review.user_id is not None:
        if current_user is None:
            raise HTTPException(status_code=401, detail="需要登录才能导出该审查记录")
        if current_user.id != review.user_id:
            raise HTTPException(status_code=403, detail="无权导出该审查记录")

    # 构建导出选项
    options = {
        "includeDetailedRisks": includeDetailedRisks,
        "includeRecommendedEdits": includeRecommendedEdits,
        "includeMissingClauses": includeMissingClauses,
    }

    # 生成Word文档
    try:
        word_content = await generate_contract_word(
            db=db,
            review_id=review_id,
            options=options,
        )
    except WordGenerationError as e:
        return {
            "error": "Word生成失败",
            "message": str(e),
        }

    # 返回Word文件
    return Response(
        content=word_content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=contract_review_{review_id}.docx",
        },
    )
