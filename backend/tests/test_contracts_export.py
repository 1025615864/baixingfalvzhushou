"""
合同审查报告导出功能测试

测试PDF和Word格式的导出API端点
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_export_pdf_review_not_found(client: AsyncClient):
    """测试导出PDF时审查记录不存在"""
    review_id = "non-existent-id"
    
    response = await client.get(
        f"/api/contracts/review/{review_id}/export/pdf",
        params={
            "includeDetailedRisks": True,
            "includeRecommendedEdits": True,
            "includeMissingClauses": True,
        }
    )
    
    # API返回404状态码
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_word_review_not_found(client: AsyncClient):
    """测试导出Word时审查记录不存在"""
    review_id = "non-existent-id"
    
    response = await client.get(
        f"/api/contracts/review/{review_id}/export/word",
        params={
            "includeDetailedRisks": True,
            "includeRecommendedEdits": True,
            "includeMissingClauses": True,
        }
    )
    
    # API返回404状态码
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_pdf_with_options(client: AsyncClient, test_session):
    """测试导出PDF并验证选项参数"""
    review_id = "test-review-id"
    
    # 测试所有选项为True
    response = await client.get(
        f"/api/contracts/review/{review_id}/export/pdf",
        params={
            "includeDetailedRisks": True,
            "includeRecommendedEdits": True,
            "includeMissingClauses": True,
        }
    )
    
    # 由于审查记录不存在，返回404
    assert response.status_code == 404
    
    # 测试部分选项为False
    response = await client.get(
        f"/api/contracts/review/{review_id}/export/pdf",
        params={
            "includeDetailedRisks": False,
            "includeRecommendedEdits": True,
            "includeMissingClauses": False,
        }
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_word_with_options(client: AsyncClient, test_session):
    """测试导出Word并验证选项参数"""
    review_id = "test-review-id"
    
    # 测试所有选项为True
    response = await client.get(
        f"/api/contracts/review/{review_id}/export/word",
        params={
            "includeDetailedRisks": True,
            "includeRecommendedEdits": True,
            "includeMissingClauses": True,
        }
    )
    
    # 由于审查记录不存在，返回404
    assert response.status_code == 404
    
    # 测试部分选项为False
    response = await client.get(
        f"/api/contracts/review/{review_id}/export/word",
        params={
            "includeDetailedRisks": False,
            "includeRecommendedEdits": True,
            "includeMissingClauses": False,
        }
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pdf_generator_error_handling(test_session):
    """测试PDF生成器错误处理"""
    from app.services.document_export.pdf_generator import generate_contract_pdf, PDFGenerationError
    
    # 测试不存在的review_id
    with pytest.raises(PDFGenerationError) as exc_info:
        await generate_contract_pdf(
            db=test_session,
            review_id="non-existent-id",
            options={}
        )
    
    assert "未找到审查记录" in str(exc_info.value)


@pytest.mark.asyncio
async def test_word_generator_error_handling(test_session):
    """测试Word生成器错误处理"""
    from app.services.document_export.word_generator import generate_contract_word, WordGenerationError
    
    # 测试不存在的review_id
    with pytest.raises(WordGenerationError) as exc_info:
        await generate_contract_word(
            db=test_session,
            review_id="non-existent-id",
            options={}
        )
    
    assert "未找到审查记录" in str(exc_info.value)


@pytest.mark.asyncio
async def test_export_options_validation(client: AsyncClient):
    """测试导出选项的参数验证"""
    review_id = "test-id"
    
    # 测试布尔值参数
    response = await client.get(
        f"/api/contracts/review/{review_id}/export/pdf",
        params={
            "includeDetailedRisks": "true",
            "includeRecommendedEdits": "false",
            "includeMissingClauses": "true",
        }
    )
    # 由于审查记录不存在，返回404
    assert response.status_code == 404