import pytest
from unittest.mock import MagicMock
from app.services.news_quality_service import NewsQualityService, LegalProfessionalResult, ContentQualityResult

class TestNewsQualityService:
    @pytest.fixture
    def service(self):
        return NewsQualityService()

    @pytest.fixture
    def mock_news(self):
        news = MagicMock()
        news.title = "Test News"
        news.content = "Test Content"
        news.source = "Test Source"
        news.source_site = "Test Site"
        news.cover_image = None
        news.published_at = None
        return news

    def test_analyze_legal_professional_high_score(self, service):
        news = MagicMock()
        news.title = "最高法院发布最新刑事判决书"
        news.content = """
        最高人民法院发布了关于刑法的最新司法解释。
        根据《中华人民共和国刑法》第一百二十条规定，...
        本案属于重大刑事案件。
        涉及北京市第一中级人民法院。
        判决如下：被告人有期徒刑十年。
        """
        news.source = "最高法"
        
        result = service.analyze_legal_professional(news)
        
        assert result.legal_score > 60
        assert "刑法" in result.legal_categories
        assert "刑事案件" in result.case_types
        assert result.has_citation is True
        assert result.is_verdict is True
        assert "《中华人民共和国刑法》" in result.law_references

    def test_analyze_legal_professional_low_score(self, service, mock_news):
        # 普通新闻，无相关法律内容
        mock_news.title = "今天天气不错"
        mock_news.content = "大家一起去公园散步。"
        
        result = service.analyze_legal_professional(mock_news)
        
        assert result.legal_score < 30
        assert not result.legal_categories
        assert not result.case_types
        assert not result.has_citation
        assert not result.is_verdict

    def test_analyze_content_quality_high_authority(self, service):
        news = MagicMock()
        news.title = "权威发布"
        news.content = "内容 " * 200  # 足够长
        news.source = "新华网"  # 权威来源
        news.source_site = "xinhuanet.com"
        
        result = service.analyze_content_quality(news)
        
        assert result.authority_score >= 40
        assert result.source_credibility in ["high", "medium"]

    def test_analyze_content_quality_readability(self, service):
        news = MagicMock()
        news.title = "Test Readability"
        # Construct content with mixed sentence lengths
        short_sentences = "Short sentence. " * 10
        long_sentence = "Very long sentence " * 30 + "."
        news.content = short_sentences + long_sentence
        
        result = service.analyze_content_quality(news)
        
        # Just verifying it runs and calculates scores, exact score depends on logic
        assert 0 <= result.readability_score <= 100
        assert result.word_count > 0
        assert result.sentence_count > 0

    def test_analyze_content_quality_information(self, service):
        news = MagicMock()
        news.title = "Info Rich News"
        news.content = """
        根据第十条规定，增长率为50%。
        涉及金额1000万元。
        """
        
        result = service.analyze_content_quality(news)
        
        # Contains numbers and potential citations
        assert result.information_score > 0
        
    def test_get_quality_summary(self, service, mock_news):
        summary = service.get_quality_summary(mock_news)
        
        assert "legal_professional" in summary
        assert "content_quality" in summary
        assert "summary" in summary
        assert "is_high_quality" in summary["summary"]
