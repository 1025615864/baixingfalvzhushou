"""案例推荐服务"""
import math
from typing import Optional, List, Dict, Tuple
from functools import lru_cache
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.archive import LegalCase
from app.services.archive_vector_store import search_archive, get_collection


class CaseRecommendationService:
    CAUSE_WEIGHT = 0.4
    COURT_LEVEL_WEIGHT = 0.2
    JUDGMENT_RESULT_WEIGHT = 0.2
    KEYWORD_WEIGHT = 0.2

    def __init__(self, db: Session):
        self.db = db

    def _get_case_by_id(self, case_id: int) -> Optional[LegalCase]:
        return self.db.query(LegalCase).filter(
            LegalCase.id == case_id,
            LegalCase.is_deleted == False,
            LegalCase.is_active == True
        ).first()

    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def _get_case_vector(self, case_id: int) -> Optional[List[float]]:
        collection = get_collection()
        try:
            results = collection.get(ids=[str(case_id)])
            if results and results.get("embeddings"):
                return results["embeddings"][0]
        except Exception:
            logger.exception("Failed to get case recommendations")
        return None

    def _search_vectors(self, query: str, top_k: int) -> List[Dict]:
        return search_archive(query, top_k=top_k)

    def _similarity_by_cause(self, cause1: Optional[str], cause2: Optional[str]) -> float:
        if not cause1 or not cause2:
            return 0.0
        if cause1 == cause2:
            return 1.0
        return 0.0

    def _similarity_by_court_level(self, level1: Optional[str], level2: Optional[str]) -> float:
        if not level1 or not level2:
            return 0.0
        if level1 == level2:
            return 1.0
        court_rank = {"基层": 1, "中院": 2, "高院": 3, "最高院": 4}
        rank1 = court_rank.get(level1, 0)
        rank2 = court_rank.get(level2, 0)
        if rank1 == 0 or rank2 == 0:
            return 0.0
        diff = abs(rank1 - rank2)
        return max(0.0, 1.0 - diff * 0.25)

    def _similarity_by_judgment_result(self, result1: Optional[str], result2: Optional[str]) -> float:
        if not result1 or not result2:
            return 0.0
        if result1 == result2:
            return 1.0
        result_keywords = {
            "支持": ["维持", "胜诉"],
            "驳回": ["维持", "败诉"],
            "调解": ["调解", "和解"],
            "撤销": ["撤销", "废止"]
        }
        for main_result, synonyms in result_keywords.items():
            if main_result in result1:
                for syn in synonyms:
                    if syn in result2:
                        return 0.7
        return 0.0

    def _similarity_by_keywords(self, kw1: Optional[str], kw2: Optional[str]) -> float:
        if not kw1 or not kw2:
            return 0.0
        kws1 = set(kw1.replace("，", ",").replace("、", ",").split(","))
        kws2 = set(kw2.replace("，", ",").replace("、", ",").split(","))
        kws1 = {k.strip() for k in kws1 if k.strip()}
        kws2 = {k.strip() for k in kws2 if k.strip()}
        if not kws1 or not kws2:
            return 0.0
        intersection = len(kws1 & kws2)
        union = len(kws1 | kws2)
        return intersection / union if union > 0 else 0.0

    def _calculate_comprehensive_similarity(
        self,
        case1: LegalCase,
        case2: LegalCase
    ) -> float:
        cause_sim = self._similarity_by_cause(case1.cause_of_action, case2.cause_of_action)
        court_sim = self._similarity_by_court_level(case1.court_level, case2.court_level)
        judgment_sim = self._similarity_by_judgment_result(case1.judgment_result, case2.judgment_result)
        keyword_sim = self._similarity_by_keywords(case1.keywords, case2.keywords)

        return (
            cause_sim * self.CAUSE_WEIGHT +
            court_sim * self.COURT_LEVEL_WEIGHT +
            judgment_sim * self.JUDGMENT_RESULT_WEIGHT +
            keyword_sim * self.KEYWORD_WEIGHT
        )

    def get_related_cases(
        self,
        case_id: int,
        max_results: int = 5,
        include_same_cause: bool = True,
        include_same_court: bool = True
    ) -> Tuple[List[LegalCase], Dict[int, float]]:
        source_case = self._get_case_by_id(case_id)
        if not source_case:
            return [], {}

        query_texts = []
        if source_case.title:
            query_texts.append(source_case.title)
        if source_case.facts:
            query_texts.append(source_case.facts[:500])
        if source_case.keywords:
            query_texts.append(source_case.keywords)

        query = " ".join(query_texts) if query_texts else source_case.title

        vector_results = self._search_vectors(query, top_k=max_results * 3)

        candidate_ids = set()
        for result in vector_results:
            if "case_id" in result.get("metadata", {}):
                cid = result["metadata"]["case_id"]
                if cid != case_id:
                    candidate_ids.add(cid)

        if include_same_cause and source_case.cause_of_action:
            same_cause_cases = self.db.query(LegalCase).filter(
                LegalCase.cause_of_action == source_case.cause_of_action,
                LegalCase.id != case_id,
                LegalCase.is_deleted == False,
                LegalCase.is_active == True,
                LegalCase.status == "published"
            ).limit(max_results * 2).all()
            for c in same_cause_cases:
                candidate_ids.add(c.id)

        if include_same_court and source_case.court:
            same_court_cases = self.db.query(LegalCase).filter(
                LegalCase.court == source_case.court,
                LegalCase.id != case_id,
                LegalCase.is_deleted == False,
                LegalCase.is_active == True,
                LegalCase.status == "published"
            ).limit(max_results).all()
            for c in same_court_cases:
                candidate_ids.add(c.id)

        if not candidate_ids:
            return [], {}

        candidates = self.db.query(LegalCase).filter(
            LegalCase.id.in_(candidate_ids),
            LegalCase.is_deleted == False,
            LegalCase.is_active == True
        ).all()

        similarities = {}
        for candidate in candidates:
            sim = self._calculate_comprehensive_similarity(source_case, candidate)
            similarities[candidate.id] = sim

        sorted_cases = sorted(candidates, key=lambda x: similarities.get(x.id, 0), reverse=True)
        top_cases = sorted_cases[:max_results]

        return top_cases, similarities

    def get_similar_by_case_number(self, case_id: int, max_results: int = 5) -> List[LegalCase]:
        source_case = self._get_case_by_id(case_id)
        if not source_case or not source_case.case_number:
            return []

        case_num = source_case.case_number
        similar_prefix = case_num[:6] if len(case_num) >= 6 else case_num

        similar_cases = self.db.query(LegalCase).filter(
            LegalCase.case_number.like(f"{similar_prefix}%"),
            LegalCase.id != case_id,
            LegalCase.is_deleted == False,
            LegalCase.is_active == True,
            LegalCase.status == "published"
        ).order_by(LegalCase.judge_date.desc()).limit(max_results).all()

        return similar_cases

    def get_cases_by_court(self, case_id: int, max_results: int = 5) -> List[LegalCase]:
        source_case = self._get_case_by_id(case_id)
        if not source_case or not source_case.court:
            return []

        same_court_cases = self.db.query(LegalCase).filter(
            LegalCase.court == source_case.court,
            LegalCase.id != case_id,
            LegalCase.is_deleted == False,
            LegalCase.is_active == True,
            LegalCase.status == "published"
        ).order_by(
            LegalCase.is_guiding_case.desc(),
            LegalCase.weight.desc(),
            LegalCase.judge_date.desc()
        ).limit(max_results).all()

        return same_court_cases

    def get_cases_by_cause(self, case_id: int, max_results: int = 5) -> List[LegalCase]:
        source_case = self._get_case_by_id(case_id)
        if not source_case or not source_case.cause_of_action:
            return []

        same_cause_cases = self.db.query(LegalCase).filter(
            LegalCase.cause_of_action == source_case.cause_of_action,
            LegalCase.id != case_id,
            LegalCase.is_deleted == False,
            LegalCase.is_active == True,
            LegalCase.status == "published"
        ).order_by(
            LegalCase.is_guiding_case.desc(),
            LegalCase.weight.desc(),
            LegalCase.judge_date.desc()
        ).limit(max_results).all()

        return same_cause_cases

    def get_guide_cases(
        self,
        court_level: Optional[str] = None,
        cause_of_action: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[LegalCase], int]:
        query = self.db.query(LegalCase).filter(
            LegalCase.is_guiding_case == True,
            LegalCase.is_deleted == False,
            LegalCase.is_active == True,
            LegalCase.status == "published"
        )

        if court_level:
            query = query.filter(LegalCase.court_level == court_level)
        if cause_of_action:
            query = query.filter(LegalCase.cause_of_action == cause_of_action)

        total = query.count()

        guide_cases = query.order_by(
            LegalCase.court_level.desc(),
            LegalCase.weight.desc(),
            LegalCase.judge_date.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return guide_cases, total


@lru_cache(maxsize=128)
def _get_cached_service(db_session_id: str) -> CaseRecommendationService:
    pass
