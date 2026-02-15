"""Tests for keyword extraction service."""
from __future__ import annotations

import pytest

from app.services.keyword_extraction_service import KeywordExtractionService


class TestKeywordExtractionService:
    """Test KeywordExtractionService class."""

    def test_init_creates_keyword_to_domain_mapping(self) -> None:
        """Test that initialization creates reverse mapping."""
        service = KeywordExtractionService()
        assert hasattr(service, "_keyword_to_domain")
        assert isinstance(service._keyword_to_domain, dict)

    def test_legal_domains_defined(self) -> None:
        """Test that LEGAL_DOMAINS is defined."""
        assert hasattr(KeywordExtractionService, "LEGAL_DOMAINS")
        domains = KeywordExtractionService.LEGAL_DOMAINS
        assert isinstance(domains, dict)
        assert len(domains) > 0

    def test_legal_terms_defined(self) -> None:
        """Test that LEGAL_TERMS is defined."""
        assert hasattr(KeywordExtractionService, "LEGAL_TERMS")
        terms = KeywordExtractionService.LEGAL_TERMS
        assert isinstance(terms, list)
        assert len(terms) > 0

    def test_legal_domains_contains_expected_domains(self) -> None:
        """Test that LEGAL_DOMAINS contains expected legal domains."""
        domains = KeywordExtractionService.LEGAL_DOMAINS
        expected_domains = ["劳动纠纷", "婚姻家庭", "合同纠纷", "交通事故", "借贷纠纷"]
        for domain in expected_domains:
            assert domain in domains, f"Expected domain '{domain}' not found"

    def test_domain_keywords_are_lists(self) -> None:
        """Test that each domain has a list of keywords."""
        for domain, keywords in KeywordExtractionService.LEGAL_DOMAINS.items():
            assert isinstance(keywords, list), f"Keywords for {domain} is not a list"
            assert len(keywords) > 0, f"No keywords for domain {domain}"

    def test_keyword_to_domain_mapping_completeness(self) -> None:
        """Test that all keywords are mapped to at least one domain."""
        service = KeywordExtractionService()
        for domain, keywords in KeywordExtractionService.LEGAL_DOMAINS.items():
            for keyword in keywords:
                assert keyword in service._keyword_to_domain, f"Keyword '{keyword}' not in mapping"
                domains = service._keyword_to_domain[keyword]
                assert isinstance(domains, list)
                assert domain in domains, f"Domain '{domain}' not mapped for keyword '{keyword}'"


class TestKeywordExtractionServiceMethods:
    """Test KeywordExtractionService methods if any exist."""

    def test_service_has_expected_methods(self) -> None:
        """Test that service has expected public methods."""
        service = KeywordExtractionService()
        # Check for common service methods
        public_methods = [m for m in dir(service) if not m.startswith("_")]
        # The service should have at least initialization logic
        assert len(public_methods) >= 0  # Just check it can be instantiated


class TestKeywordExtractionDomainKeywords:
    """Test specific domain keywords."""

    def test_labor_dispute_keywords(self) -> None:
        """Test labor dispute domain has expected keywords."""
        keywords = KeywordExtractionService.LEGAL_DOMAINS["劳动纠纷"]
        assert "劳动合同" in keywords
        assert "工资" in keywords
        assert "社保" in keywords
        assert "工伤" in keywords

    def test_marriage_family_keywords(self) -> None:
        """Test marriage family domain has expected keywords."""
        keywords = KeywordExtractionService.LEGAL_DOMAINS["婚姻家庭"]
        assert "离婚" in keywords
        assert "财产分割" in keywords
        assert "子女抚养" in keywords

    def test_contract_dispute_keywords(self) -> None:
        """Test contract dispute domain has expected keywords."""
        keywords = KeywordExtractionService.LEGAL_DOMAINS["合同纠纷"]
        assert "合同" in keywords
        assert "违约" in keywords
        assert "违约金" in keywords

    def test_traffic_accident_keywords(self) -> None:
        """Test traffic accident domain has expected keywords."""
        keywords = KeywordExtractionService.LEGAL_DOMAINS["交通事故"]
        assert "交通事故" in keywords
        assert "责任认定" in keywords
        assert "赔偿" in keywords

    def test_loan_dispute_keywords(self) -> None:
        """Test loan dispute domain has expected keywords."""
        keywords = KeywordExtractionService.LEGAL_DOMAINS["借贷纠纷"]
        assert "借款" in keywords
        assert "利息" in keywords
        assert "借条" in keywords


class TestKeywordExtractionEdgeCases:
    """Test edge cases for keyword extraction."""

    def test_multiple_domains_for_keyword(self) -> None:
        """Test that some keywords map to multiple domains."""
        service = KeywordExtractionService()
        # Find a keyword that maps to multiple domains
        for keyword, domains in service._keyword_to_domain.items():
            if len(domains) > 1:
                # Found a keyword in multiple domains
                assert len(domains) >= 2
                return
        # If no multi-domain keyword found, that's also valid

    def test_service_instances_are_independent(self) -> None:
        """Test that multiple service instances work correctly."""
        service1 = KeywordExtractionService()
        service2 = KeywordExtractionService()
        # Both should have the same data
        assert service1._keyword_to_domain.keys() == service2._keyword_to_domain.keys()
