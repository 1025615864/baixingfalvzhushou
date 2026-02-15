"""Word生成器测试"""

import uuid

import pytest

from app.services.document_export.word_generator import (
    WordGenerationError,
    generate_contract_word,
    _get_risk_level_map,
)


@pytest.mark.asyncio
async def test_generate_word_review_not_found(mock_db):
    """测试生成Word - 审查记录不存在"""
    fake_id = str(uuid.uuid4())
    
    with pytest.raises(WordGenerationError) as exc_info:
        await generate_contract_word(db=mock_db, review_id=fake_id, options={})
    
    assert "未找到审查记录" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_word_without_docx(mock_db):
    """测试生成Word - 缺少python-docx依赖"""
    from app.services.document_export import word_generator
    from app.models.contracts import ContractReviewHistory
    from datetime import datetime

    # 先创建一个有效的审查记录
    review_id = str(uuid.uuid4())
    history = ContractReviewHistory(
        id=review_id,
        user_id=None,
        filename="test.pdf",
        contract_type="劳动合同",
        content_type="application/pdf",
        text_chars=100,
        text_preview="test preview",
        risk_level="medium",
        risk_count=1,
        report_json={"contract_type": "劳动合同", "risk_level": "medium"},
        report_markdown="# test",
        request_id=str(uuid.uuid4()),
        created_at=datetime.now(),
    )
    mock_db.add(history)
    await mock_db.commit()

    # 临时禁用docx
    original_available = word_generator.DOCX_AVAILABLE
    word_generator.DOCX_AVAILABLE = False

    try:
        with pytest.raises(WordGenerationError) as exc_info:
            await generate_contract_word(db=mock_db, review_id=review_id, options={})

        assert "python-docx" in str(exc_info.value)
    finally:
        word_generator.DOCX_AVAILABLE = original_available


@pytest.mark.asyncio
async def test_generate_word_success(mock_db):
    """测试生成Word成功"""
    from app.models.contracts import ContractReviewHistory
    from datetime import datetime

    review_id = str(uuid.uuid4())
    history = ContractReviewHistory(
        id=review_id,
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
    mock_db.add(history)
    await mock_db.commit()

    # 包含所有部分
    options1 = {
        "includeDetailedRisks": True,
        "includeRecommendedEdits": True,
        "includeMissingClauses": True,
    }
    word1 = await generate_contract_word(db=mock_db, review_id=review_id, options=options1)
    assert len(word1) > 0


@pytest.mark.asyncio
async def test_generate_word_with_options(mock_db):
    """测试生成Word - 带选项控制"""
    from app.models.contracts import ContractReviewHistory
    from datetime import datetime

    review_id = str(uuid.uuid4())
    history = ContractReviewHistory(
        id=review_id,
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
            "risk_level": "medium",
            "risk_count": 1,
            "risk_items": [{"title": "测试风险", "type": "测试", "severity": "low"}],
            "recommended_edits": [{"location": "第1条", "original": "原文", "suggested": "修改后"}],
            "missing_clauses": [{"type": "测试条款", "description": "测试描述"}],
        },
        report_markdown="# test",
        request_id=str(uuid.uuid4()),
        created_at=datetime.now(),
    )
    mock_db.add(history)
    await mock_db.commit()

    # 只包含风险分析
    options2 = {
        "includeDetailedRisks": True,
        "includeRecommendedEdits": False,
        "includeMissingClauses": False,
    }
    word2 = await generate_contract_word(db=mock_db, review_id=review_id, options=options2)
    assert len(word2) > 0


def test_get_word_risk_level_map():
    """测试获取Word风险等级映射"""
    level_map = _get_risk_level_map()

    assert "low" in level_map
    assert "medium" in level_map
    assert "high" in level_map
    assert level_map["low"] == "低风险"
    assert level_map["medium"] == "中风险"
    assert level_map["high"] == "高风险"