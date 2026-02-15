"""新闻质量评估服务

提供法律专业性识别、内容质量评分、权威性评估等功能
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.news import News


# 法律领域分类
LEGAL_CATEGORIES = {
    "民法典": ["民法典", "民事", "合同", "侵权", "物权", "人格权", "婚姻家庭", "继承"],
    "刑法": ["刑法", "刑事", "犯罪", "判刑", "有期徒刑", "无期徒刑", "死刑", "公诉", "逮捕"],
    "行政法": ["行政", "行政处罚", "行政复议", "行政诉讼", "国家机关", "公务员"],
    "经济法": ["公司法", "证券法", "反垄断法", "消费者权益", "产品质量", "税务", "金融"],
    "劳动法": ["劳动", "劳动合同", "工资", "社保", "工伤", "仲裁", "裁员"],
    "房地产": ["房产", "房价", "限购", "房贷", "租赁", "物业", "拆迁"],
    "知识产权": ["专利", "商标", "著作权", "版权", "侵权", "山寨"],
    "国际法": ["国际", "外交", "条约", "世贸", "跨境", "海外"],
}

# 案件类型关键词
CASE_TYPE_KEYWORDS = {
    "民事案件": ["民事", "民事诉讼", "民事判决", "民事调解", "民事纠纷"],
    "刑事案件": ["刑事", "刑事案件", "刑事判决", "刑事附带民事", "刑事诉讼"],
    "行政案件": ["行政诉讼", "行政判决", "行政行为", "行政纠纷"],
    "仲裁案件": ["仲裁", "仲裁委员会", "仲裁裁决", "商事仲裁", "劳动仲裁"],
    "执行案件": ["执行", "强制执行", "执行局", "执行标的", "执行和解"],
}

# 法律条文引用模式
LEGAL_CITATION_PATTERN = re.compile(
    r"(?:第[一二三四五六七八九十百千0-9]+条?|第[0-9]+条)"  # 第x条
    r"(?:\s*(?:之[一二三四五六七八九十百千0-9]+)?款)?"    # 第x款
    r"(?:\s*(?:第[一二三四五六七八九十百千0-9]+)?项)?",   # 第x项
    re.IGNORECASE
)

# 法典/法规名称模式
LAW_NAME_PATTERN = re.compile(
    r"(?:《([^》]+)》|(?:中华人民共和国)?([^(《)》]+?)法)",
    re.IGNORECASE
)

# 法院/机构名称
COURT_KEYWORDS = ["法院", "检察院", "公安局", "司法局", "仲裁委员会", "人大", "人大常委会"]


@dataclass
class LegalProfessionalResult:
    """法律专业性分析结果"""
    legal_category: str | None           # 主要法律分类
    legal_categories: list[str]          # 涉及的所有法律分类
    case_type: str | None               # 案件类型
    case_types: list[str]               # 涉及的所有案件类型
    law_references: list[str]           # 引用的法律条文
    court_name: str | None              # 涉及的法院/机构
    is_verdict: bool                    # 是否为判决书
    has_citation: bool                  # 是否有法律引用
    legal_score: int                    # 法律专业性评分 (0-100)


@dataclass
class ContentQualityResult:
    """内容质量评估结果"""
    readability_score: int              # 可读性评分 (0-100)
    authority_score: int                # 权威性评分 (0-100)
    information_score: int              # 信息量评分 (0-100)
    freshness_score: int                # 时效性评分 (0-100)
    overall_score: int                  # 综合评分 (0-100)
    word_count: int                     # 字数
    sentence_count: int                 # 句子数
    avg_sentence_length: float          # 平均句子长度
    has_images: bool                    # 是否有图片
    has_source_citation: bool           # 是否有来源引用
    source_credibility: str             # 来源可信度 (high/medium/low)


class NewsQualityService:
    """新闻质量评估服务"""

    def __init__(self) -> None:
        pass

    def analyze_legal_professional(
            self, news: "News") -> LegalProfessionalResult:
        """分析新闻的法律专业性"""
        title = str(getattr(news, "title", "") or "").strip()
        content = str(getattr(news, "content", "") or "").strip()
        source = str(getattr(news, "source", "") or "").strip()
        source_site = str(getattr(news, "source_site", "") or "").strip()

        text = f"{title}\n{content}"

        # 1. 法律分类识别
        legal_categories: list[str] = []
        for category, keywords in LEGAL_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    if category not in legal_categories:
                        legal_categories.append(category)
                    break

        # 2. 案件类型识别
        case_types: list[str] = []
        for case_type, keywords in CASE_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    if case_type not in case_types:
                        case_types.append(case_type)
                    break

        # 3. 法律条文引用识别
        law_references: list[str] = []

        # 提取法条引用
        citations = LEGAL_CITATION_PATTERN.findall(text)
        for citation in citations:
            if isinstance(citation, tuple):
                citation = "".join(c for c in citation if c)
            if citation and citation not in law_references:
                law_references.append(citation[:50])

        # 提取法规名称
        law_names = LAW_NAME_PATTERN.findall(text)
        for name_tuple in law_names:
            name = name_tuple[0] or name_tuple[1]
            if name and len(name) >= 2:
                full_ref = f"《{name}》"
                if full_ref not in law_references:
                    law_references.append(full_ref)

        # 4. 法院/机构识别
        court_name: str | None = None
        for keyword in COURT_KEYWORDS:
            if keyword in text:
                # 尝试提取完整机构名
                idx = text.find(keyword)
                surrounding = text[max(0, idx - 20):idx + 20]
                court_name = f"...{surrounding}..."
                break

        # 5. 是否为判决书
        is_verdict = any(word in text.lower() for word in [
            "判决书", "判决如下", "裁定如下", "执行通知书",
            "民事判决", "刑事判决", "行政判决"
        ])

        # 6. 是否有法律引用
        has_citation = bool(law_references) or bool(law_names)

        # 7. 法律专业性评分 (0-100)
        legal_score = 0

        # 基础分：标题包含法律关键词
        if any(word in title.lower() for word in ["法律", "法规", "条例", "规定"]):
            legal_score += 10

        # 加分：有法律分类
        legal_score += min(len(legal_categories) * 15, 30)

        # 加分：有案件类型
        legal_score += min(len(case_types) * 10, 20)

        # 加分：有法律条文引用
        if law_references:
            legal_score += min(len(law_references) * 5, 20)

        # 加分：涉及法院/机构
        if court_name:
            legal_score += 10

        # 加分：判决书类型
        if is_verdict:
            legal_score += 10

        legal_score = min(legal_score, 100)

        return LegalProfessionalResult(
            legal_category=legal_categories[0] if legal_categories else None,
            legal_categories=legal_categories,
            case_type=case_types[0] if case_types else None,
            case_types=case_types,
            law_references=law_references[:10],  # 最多保留10条
            court_name=court_name,
            is_verdict=is_verdict,
            has_citation=has_citation,
            legal_score=legal_score,
        )

    def analyze_content_quality(self, news: "News") -> ContentQualityResult:
        """分析新闻内容质量"""
        title = str(getattr(news, "title", "") or "").strip()
        content = str(getattr(news, "content", "") or "").strip()
        cover_image = getattr(news, "cover_image", None)
        source = str(getattr(news, "source", "") or "").strip()
        source_site = str(getattr(news, "source_site", "") or "").strip()
        published_at = getattr(news, "published_at", None)

        text = f"{title}\n{content}"

        # 1. 文本统计
        word_count = len(text)
        # 按句号、问号、感叹号分句
        sentences = re.split(r"[。！？.!?]+", text)
        sentence_count = len([s for s in sentences if s.strip()])
        avg_sentence_length = word_count / max(1, sentence_count)

        # 2. 可读性评分 (0-100)
        readability_score = 100
        # 句子太长扣分
        if avg_sentence_length > 50:
            readability_score -= 20
        elif avg_sentence_length > 30:
            readability_score -= 10
        # 字数太少扣分
        if word_count < 100:
            readability_score -= 30
        elif word_count < 300:
            readability_score -= 15
        # 字数适中加分
        if 500 <= word_count <= 5000:
            readability_score += 10
        readability_score = max(0, min(100, readability_score))

        # 3. 权威性评分 (0-100)
        authority_score = 0

        # 来源可信度评估
        credible_sources = [
            "新华网", "人民网", "央视", "中国法院网", "最高法",
            "司法部", "公安部", "检察院", "政府网", "gov.cn",
            "新浪", "网易", "搜狐", "腾讯", "凤凰网"
        ]

        source_combined = f"{source} {source_site}".lower()
        for credible in credible_sources:
            if credible.lower() in source_combined:
                authority_score += 40
                break
        else:
            # 未知来源
            authority_score += 10

        # 有来源引用加分
        if source or source_site:
            authority_score += 20

        # 有官方机构提到
        official_keywords = ["法院", "检察院", "公安部", "司法部", "人大", "国务院"]
        if any(kw in text for kw in official_keywords):
            authority_score += 20

        # 内容长度适中
        if 300 <= word_count <= 5000:
            authority_score += 20

        authority_score = min(authority_score, 100)

        # 4. 信息量评分 (0-100)
        information_score = 0

        # 基于字数
        if word_count >= 500:
            information_score += 40
        elif word_count >= 200:
            information_score += 25
        elif word_count >= 100:
            information_score += 15

        # 基于句子数
        if sentence_count >= 10:
            information_score += 30
        elif sentence_count >= 5:
            information_score += 20
        elif sentence_count >= 3:
            information_score += 10

        # 有法律条文引用
        if LEGAL_CITATION_PATTERN.search(text):
            information_score += 20

        # 有数据/数字
        if re.search(r"[0-9]+", text):
            information_score += 10

        information_score = min(information_score, 100)

        # 5. 时效性评分 (0-100)
        freshness_score = 100
        # 简单处理：如果发布时间较近，加分
        # 这里可以结合当前时间计算
        if published_at is None:
            freshness_score = 70  # 无发布时间信息

        # 6. 是否有图片
        has_images = bool(cover_image)

        # 7. 是否有来源引用
        has_source_citation = bool(source or source_site)

        # 8. 来源可信度
        source_credibility: str
        if authority_score >= 70:
            source_credibility = "high"
        elif authority_score >= 40:
            source_credibility = "medium"
        else:
            source_credibility = "low"

        # 9. 综合评分
        overall_score = int(
            readability_score * 0.2 +
            authority_score * 0.3 +
            information_score * 0.3 +
            freshness_score * 0.2
        )

        return ContentQualityResult(
            readability_score=readability_score,
            authority_score=authority_score,
            information_score=information_score,
            freshness_score=freshness_score,
            overall_score=overall_score,
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=round(avg_sentence_length, 1),
            has_images=has_images,
            has_source_citation=has_source_citation,
            source_credibility=source_credibility,
        )

    def get_quality_summary(self, news: "News") -> dict:
        """获取质量评估综合摘要"""
        legal_result = self.analyze_legal_professional(news)
        quality_result = self.analyze_content_quality(news)

        return {
            "legal_professional": {
                "category": legal_result.legal_category,
                "categories": legal_result.legal_categories,
                "case_type": legal_result.case_type,
                "case_types": legal_result.case_types,
                "law_references": legal_result.law_references,
                "court_name": legal_result.court_name,
                "is_verdict": legal_result.is_verdict,
                "has_citation": legal_result.has_citation,
                "legal_score": legal_result.legal_score,
            },
            "content_quality": {
                "readability_score": quality_result.readability_score,
                "authority_score": quality_result.authority_score,
                "information_score": quality_result.information_score,
                "freshness_score": quality_result.freshness_score,
                "overall_score": quality_result.overall_score,
                "source_credibility": quality_result.source_credibility,
            },
            "summary": {
                "is_high_quality": quality_result.overall_score >= 70,
                "is_professional": legal_result.legal_score >= 50,
                "is_verdict": legal_result.is_verdict,
                "needs_review": legal_result.legal_score < 30 or quality_result.overall_score < 40,
            }}


news_quality_service = NewsQualityService()
