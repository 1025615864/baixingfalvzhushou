"""PDF生成器测试"""

import uuid

import pytest

from app.services.document_export.pdf_generator import (
    PDFGenerationError,
    generate_contract_pdf,
    _build_markdown_report,
    _get_risk_level_map,
)


@pytest.mark.asyncio
async def test_generate_pdf_review_not_found(mock_db):
    """测试生成PDF - 审查记录不存在"""
    fake_id = str(uuid.uuid4())
    
    with pytest.raises(PDFGenerationError) as exc_info:
        await generate_contract_pdf(db=mock_db, review_id=fake_id, options={})
    
    assert "未找到审查记录" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_pdf_without_weasyprint(mock_db):
    """测试生成PDF - 缺少weasyprint依赖"""
    from app.services.document_export import pdf_generator
    
    # 临时禁用weasyprint
    original_available = pdf_generator.WEASYPRINT_AVAILABLE
    pdf_generator.WEASYPRINT_AVAILABLE = False
    
    try:
        fake_id = str(uuid.uuid4())
        with pytest.raises(PDFGenerationError) as exc_info:
            await generate_contract_pdf(db=mock_db, review_id=fake_id, options={})
        
        assert "weasyprint" in str(exc_info.value)
    finally:
        pdf_generator.WEASYPRINT_AVAILABLE = original_available


@pytest.mark.asyncio
async def test_build_markdown_report_all_sections(mock_db):
    """测试构建Markdown报告 - 包含所有部分"""
    from app.models.contracts import ContractReviewHistory
    from datetime import datetime

    review = ContractReviewHistory(
        id=str(uuid.uuid4()),
        user_id=None,
        filename="test.pdf",
        contract_type="劳动合同",
        content_type="application/pdf",
        text_chars=100,
        text_preview="test preview",
        risk_level="medium",
        risk_count=1,
        report_json={
            "contract_type": "劳动合同",
            "summary": "测试总结",
            "overall_risk_level": "medium",
            "risk_level": "medium",
            "risk_count": 1,
            "risk_items": [
                {
                    "title": "违约责任",
                    "type": "条款问题",
                    "severity": "high",
                    "location": "第3条",
                    "description": "违约责任条款不明确",
                    "legal_basis": "《民法典》第五百八十五条",
                    "suggestion": "建议明确违约金计算方式和支付期限"
                }
            ],
            "recommended_edits": [
                {
                    "location": "第5条",
                    "original": "甲方应在收到发票后付款",
                    "suggested": "甲方应在收到发票后15个工作日内付款"
                }
            ],
            "missing_clauses": [
                {
                    "type": "争议解决条款",
                    "description": "合同未明确约定争议解决方式",
                    "suggested_text": "双方因本合同发生争议，应协商解决；协商不成的，提交XX仲裁委员会仲裁。"
                }
            ]
        },
        report_markdown="# 合同风险体检报告\n\n测试内容",
        request_id=str(uuid.uuid4()),
        created_at=datetime.now(),
    )

    options = {
        "includeDetailedRisks": True,
        "includeRecommendedEdits": True,
        "includeMissingClauses": True,
    }
    
    content = _build_markdown_report(review=review, options=options)
    
    assert "# 合同审查报告" in content
    assert "# 基本信息" in content
    assert "test.pdf" in content
    assert "劳动合同" in content
    assert "## 风险评级" in content
    assert "中风险" in content
    assert "风险点数量: 1" in content
    assert "## 风险分析" in content
    assert "违约责任" in content
    assert "## 建议修改稿" in content
    assert "第5条" in content
    assert "## 缺失条款建议" in content
    assert "争议解决条款" in content
    assert "## 免责声明" in content


@pytest.mark.asyncio
async def test_build_markdown_report_only_risks():
    """测试构建Markdown报告 - 仅包含风险分析"""
    from app.models.contracts import ContractReviewHistory
    from datetime import datetime

    review = ContractReviewHistory(
        id=str(uuid.uuid4()),
        user_id=None,
        filename="test.pdf",
        contract_type="劳动合同",
        content_type="application/pdf",
        text_chars=100,
        text_preview="test",
        risk_level="low",
        risk_count=1,
        report_json={
            "contract_type": "劳动合同",
            "risk_level": "low",
            "risk_count": 1,
            "risk_items": [{"title": "测试风险", "type": "测试", "severity": "low", "location": "第1条"}],
            "recommended_edits": [{"location": "第1条"}],
            "missing_clauses": [{"type": "测试条款"}],
        },
        report_markdown="# test",
        request_id=str(uuid.uuid4()),
        created_at=datetime.now(),
    )
    
    options = {
        "includeDetailedRisks": True,
        "includeRecommendedEdits": False,
        "includeMissingClauses": False,
    }
    
    content = _build_markdown_report(review=review, options=options)
    
    assert "测试风险" in content
    assert "## 建议修改稿" not in content
    assert "## 缺失条款建议" not in content


def test_get_risk_level_map():
    """测试获取风险等级映射"""
    level_map = _get_risk_level_map()

    assert "low" in level_map
    assert "medium" in level_map
    assert "high" in level_map
    assert level_map["low"] == "低风险"
    assert level_map["medium"] == "中风险"
    assert level_map["high"] == "高风险"