from __future__ import annotations

import re
from pydantic import BaseModel
from typing import Optional


class LegalProfessionalResult(BaseModel):
    is_legal_professional: bool = False
    specialty: Optional[str] = None
    confidence: float = 0.0
    legal_score: float = 0.0
    legal_categories: list[str] = []
    case_types: list[str] = []
    has_citation: bool = False
    is_verdict: bool = False
    law_references: list[str] = []


class ContentQualityResult(BaseModel):
    quality_score: float = 0.0
    issues: list[str] = []
    suggestions: list[str] = []
    authority_score: float = 0.0
    source_credibility: str = "low"
    readability_score: float = 0.0
    word_count: int = 0
    sentence_count: int = 0
    information_score: float = 0.0


LEGAL_KEYWORDS = {
    "刑法": "刑事",
    "民法": "民事",
    "合同法": "合同",
    "公司法": "公司",
    "劳动法": "劳动",
    "行政法": "行政",
    "知识产权": "知识产权",
    "婚姻法": "婚姻",
    "侵权": "侵权",
    "宪法": "宪法",
}

CASE_TYPE_KEYWORDS = {
    "刑事案件": "刑事",
    "民事案件": "民事",
    "行政案件": "行政",
    "经济纠纷": "经济",
    "劳动争议": "劳动",
    "合同纠纷": "合同",
}

AUTHORITATIVE_SOURCES = {
    "新华网", "人民日报", "央视", "中国法院网", "最高法", "最高检",
    "xinhuanet.com", "people.com.cn", "cctv.com", "chinacourt.org",
}

VERDICT_KEYWORDS = ["判决如下", "判决书", "裁定书", "裁决书", "被告人", "原告人", "上诉人", "被上诉人"]


class NewsQualityService:
    def analyze_legal_professional(self, news) -> LegalProfessionalResult:
        title = getattr(news, "title", "") or ""
        content = getattr(news, "content", "") or ""
        source = getattr(news, "source", "") or ""
        full_text = f"{title} {content}"

        legal_score = 0.0
        legal_categories = []
        case_types = []
        law_references = []
        has_citation = False
        is_verdict = False

        for keyword, category in LEGAL_KEYWORDS.items():
            if keyword in full_text:
                legal_score += 15
                if category not in legal_categories:
                    legal_categories.append(category)

        for keyword, case_type in CASE_TYPE_KEYWORDS.items():
            if keyword in full_text:
                legal_score += 10
                if case_type not in case_types:
                    case_types.append(case_type)

        citation_pattern = re.compile(r"《[^》]+》")
        citations = citation_pattern.findall(full_text)
        if citations:
            has_citation = True
            legal_score += 15
            law_references = list(dict.fromkeys(citations))

        law_article_pattern = re.compile(r"第[一二三四五六七八九十百千\d]+条")
        if law_article_pattern.search(full_text):
            legal_score += 10

        court_keywords = ["法院", "法庭", "审判", "检察院", "公安"]
        for kw in court_keywords:
            if kw in full_text:
                legal_score += 5

        for kw in VERDICT_KEYWORDS:
            if kw in full_text:
                is_verdict = True
                legal_score += 10
                break

        if source in AUTHORITATIVE_SOURCES:
            legal_score += 5

        legal_score = min(legal_score, 100.0)

        return LegalProfessionalResult(
            is_legal_professional=legal_score > 50,
            legal_score=legal_score,
            legal_categories=legal_categories,
            case_types=case_types,
            has_citation=has_citation,
            is_verdict=is_verdict,
            law_references=law_references,
            confidence=legal_score / 100.0,
        )

    def analyze_content_quality(self, news) -> ContentQualityResult:
        title = getattr(news, "title", "") or ""
        content = getattr(news, "content", "") or ""
        source = getattr(news, "source", "") or ""
        source_site = getattr(news, "source_site", "") or ""
        full_text = f"{title} {content}"

        authority_score = 0.0
        source_credibility = "low"

        if source in AUTHORITATIVE_SOURCES or source_site in AUTHORITATIVE_SOURCES:
            authority_score = 50.0
            source_credibility = "high"
        elif source or source_site:
            authority_score = 25.0
            source_credibility = "medium"

        word_count = len(full_text.replace(" ", ""))
        sentences = re.split(r"[。！？.!?]", content)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)

        readability_score = 50.0
        if sentence_count > 0:
            avg_len = word_count / sentence_count
            if 10 <= avg_len <= 40:
                readability_score = 80.0
            elif 5 <= avg_len <= 60:
                readability_score = 60.0
            else:
                readability_score = 30.0

        information_score = 0.0
        number_pattern = re.compile(r"\d+\.?\d*%?")
        numbers = number_pattern.findall(content)
        information_score += min(len(numbers) * 5, 30)

        citation_pattern = re.compile(r"第[一二三四五六七八九十百千\d]+条")
        if citation_pattern.search(content):
            information_score += 20

        amount_pattern = re.compile(r"\d+万?元")
        if amount_pattern.search(content):
            information_score += 15

        information_score = min(information_score, 100.0)

        quality_score = (authority_score * 0.3 + readability_score * 0.3 + information_score * 0.4)

        issues = []
        suggestions = []
        if word_count < 100:
            issues.append("内容过短")
            suggestions.append("建议增加内容长度")
        if authority_score < 20:
            issues.append("来源权威性不足")
            suggestions.append("建议引用权威来源")

        return ContentQualityResult(
            quality_score=quality_score,
            issues=issues,
            suggestions=suggestions,
            authority_score=authority_score,
            source_credibility=source_credibility,
            readability_score=readability_score,
            word_count=word_count,
            sentence_count=sentence_count,
            information_score=information_score,
        )

    def get_quality_summary(self, news) -> dict:
        legal_result = self.analyze_legal_professional(news)
        quality_result = self.analyze_content_quality(news)

        is_high_quality = (
            legal_result.legal_score > 50
            and quality_result.quality_score > 60
        )

        return {
            "legal_professional": legal_result.model_dump(),
            "content_quality": quality_result.model_dump(),
            "summary": {
                "is_high_quality": is_high_quality,
                "overall_score": (legal_result.legal_score + quality_result.quality_score) / 2,
            },
        }


news_quality_service = NewsQualityService()
