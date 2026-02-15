from __future__ import annotations

from app.services.ai_response_strategy import ResponseStrategy
from app.services.content_safety import RiskLevel
from app.services.disclaimer import DisclaimerManager


def test_disclaimer_general_when_no_risk_and_not_redirect() -> None:
    mgr = DisclaimerManager()
    out = mgr.get_disclaimer(risk_level=RiskLevel.SAFE, strategy=ResponseStrategy.GENERAL_LEGAL)
    assert out == mgr.GENERAL_DISCLAIMER


def test_disclaimer_high_risk() -> None:
    mgr = DisclaimerManager()
    out = mgr.get_disclaimer(risk_level=RiskLevel.HIGH, strategy=ResponseStrategy.GENERAL_LEGAL)
    assert "高风险提示" in out
    assert "正式法律意见" not in out


def test_disclaimer_medium_risk_and_redirect() -> None:
    mgr = DisclaimerManager()
    out = mgr.get_disclaimer(risk_level=RiskLevel.MEDIUM, strategy=ResponseStrategy.REDIRECT)
    assert "风险提示" in out
    assert "预约专业律师咨询" in out
    assert "重要提示" not in out


def test_disclaimer_redirect_without_risk_uses_redirect_text_only() -> None:
    mgr = DisclaimerManager()
    out = mgr.get_disclaimer(risk_level=RiskLevel.SAFE, strategy=ResponseStrategy.REDIRECT)
    assert "预约专业律师咨询" in out
    assert "重要提示" not in out


class TestDisclaimerEdgeCases:
    """测试免责声明边缘情况"""

    def test_disclaimer_empty_risk(self):
        """测试空风险等级"""
        mgr = DisclaimerManager()
        out = mgr.get_disclaimer(risk_level=None, strategy=ResponseStrategy.GENERAL_LEGAL)
        assert out == mgr.GENERAL_DISCLAIMER

    def test_disclaimer_empty_strategy(self):
        """测试空策略"""
        mgr = DisclaimerManager()
        out = mgr.get_disclaimer(risk_level=RiskLevel.SAFE, strategy=None)
        assert out == mgr.GENERAL_DISCLAIMER

    def test_disclaimer_warning_risk(self):
        """测试低风险等级"""
        mgr = DisclaimerManager()
        out = mgr.get_disclaimer(risk_level=RiskLevel.LOW, strategy=ResponseStrategy.GENERAL_LEGAL)
        assert "风险提示" in out or "重要提示" in out

    def test_disclaimer_general_legal_safe(self):
        """测试通用法律策略安全风险"""
        mgr = DisclaimerManager()
        out = mgr.get_disclaimer(risk_level=RiskLevel.SAFE, strategy=ResponseStrategy.GENERAL_LEGAL)
        assert "重要提示" in out

    def test_disclaimer_general_legal_high_risk(self):
        """测试通用法律策略高风险"""
        mgr = DisclaimerManager()
        out = mgr.get_disclaimer(risk_level=RiskLevel.HIGH, strategy=ResponseStrategy.GENERAL_LEGAL)
        assert "高风险提示" in out

    def test_disclaimer_all_strategies(self):
        """测试所有策略类型"""
        mgr = DisclaimerManager()
        strategies = [
            ResponseStrategy.GENERAL_LEGAL,
            ResponseStrategy.REDIRECT,
        ]
        for strategy in strategies:
            out = mgr.get_disclaimer(risk_level=RiskLevel.SAFE, strategy=strategy)
            assert isinstance(out, str)
            assert len(out) > 0

    def test_disclaimer_all_risk_levels(self):
        """测试所有风险等级"""
        mgr = DisclaimerManager()
        risk_levels = [
            RiskLevel.SAFE,
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.BLOCKED,
        ]
        for risk_level in risk_levels:
            out = mgr.get_disclaimer(risk_level=risk_level, strategy=ResponseStrategy.GENERAL_LEGAL)
            assert isinstance(out, str)
            assert len(out) > 0
