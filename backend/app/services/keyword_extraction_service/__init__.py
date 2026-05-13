"""Keyword extraction service."""
from __future__ import annotations
import re
from typing import Optional


class KeywordExtractionService:
    STOP_WORDS = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}

    LEGAL_DOMAINS: dict[str, list[str]] = {
        "劳动纠纷": ["劳动合同", "工资", "加班费", "社保", "工伤", "解雇", "辞退", "劳动仲裁", "经济补偿", "赔偿金", "劳动法"],
        "婚姻家庭": ["离婚", "结婚", "抚养权", "赡养", "继承", "财产分割", "家暴", "收养", "婚姻法", "夫妻财产"],
        "合同纠纷": ["合同", "违约", "违约金", "解除合同", "履行合同", "合同法", "买卖合同", "租赁合同", "担保"],
        "交通事故": ["交通事故", "肇事", "酒驾", "违章", "赔偿", "驾照", "交通法", "理赔", "责任认定"],
        "借贷纠纷": ["借贷", "欠款", "借款", "利息", "担保", "抵押", "债务", "催收", "民间借贷"],
        "房产纠纷": ["房产", "房屋", "买卖", "租赁", "拆迁", "物业", "产权", "过户", "房产证"],
        "知识产权": ["专利", "商标", "版权", "侵权", "知识产权", "著作权", "商业秘密"],
        "刑事辩护": ["刑事", "犯罪", "辩护", "量刑", "缓刑", "取保候审", "自首", "减刑"],
        "公司法务": ["公司", "股东", "股权", "破产", "并购", "注册", "法人", "董事"],
        "消费维权": ["消费", "维权", "退货", "欺诈", "赔偿", "质量", "投诉", "三包"],
    }

    LEGAL_TERMS: list[str] = [
        "原告", "被告", "上诉", "申诉", "立案", "开庭", "判决", "裁定", "执行",
        "调解", "仲裁", "诉讼", "证据", "证人", "鉴定", "保全", "管辖", "时效",
        "抗辩", "反诉", "撤诉", "和解", "违约", "侵权", "赔偿", "免责",
    ]

    def __init__(self, max_keywords: int = 10, min_word_length: int = 2):
        self._max_keywords = max_keywords
        self._min_word_length = min_word_length
        self._keyword_to_domain: dict[str, list[str]] = {}
        for domain, keywords in self.LEGAL_DOMAINS.items():
            for kw in keywords:
                self._keyword_to_domain.setdefault(kw, []).append(domain)

    def extract_keywords(self, text: str, max_keywords: Optional[int] = None) -> list[str]:
        if not text:
            return []
        max_kw = max_keywords or self._max_keywords
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', text)
        freq: dict[str, int] = {}
        for w in words:
            if w not in self.STOP_WORDS and len(w) >= self._min_word_length:
                freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:max_kw]]

    def extract_with_scores(self, text: str, max_keywords: Optional[int] = None) -> list[dict]:
        if not text:
            return []
        max_kw = max_keywords or self._max_keywords
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', text)
        freq: dict[str, int] = {}
        for w in words:
            if w not in self.STOP_WORDS and len(w) >= self._min_word_length:
                freq[w] = freq.get(w, 0) + 1
        total = sum(freq.values()) or 1
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [{"keyword": w, "score": c / total, "count": c} for w, c in sorted_words[:max_kw]]


keyword_extraction_service = KeywordExtractionService()
