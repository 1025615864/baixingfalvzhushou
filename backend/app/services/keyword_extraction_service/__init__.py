"""Keyword extraction service."""
from __future__ import annotations
import re
from typing import Optional


class KeywordExtractionService:
    STOP_WORDS = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}

    def __init__(self, max_keywords: int = 10, min_word_length: int = 2):
        self._max_keywords = max_keywords
        self._min_word_length = min_word_length

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
