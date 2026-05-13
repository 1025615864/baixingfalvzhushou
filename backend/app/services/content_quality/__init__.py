"""Content quality scoring service."""
from __future__ import annotations
from typing import Optional


class UserVotingSystem:
    def __init__(self):
        self._votes: dict[str, dict[int, str]] = {}
        self._stats: dict[str, dict] = {}

    def vote(self, content_id: str, user_id: int, vote_type: str) -> dict:
        if content_id not in self._votes:
            self._votes[content_id] = {}
        self._votes[content_id][user_id] = vote_type
        return self._compute_stats(content_id)

    def _compute_stats(self, content_id: str) -> dict:
        votes = self._votes.get(content_id, {})
        up = sum(1 for v in votes.values() if v == "up")
        down = sum(1 for v in votes.values() if v == "down")
        return {"content_id": content_id, "vote_type": votes.get(list(votes.keys())[-1] if votes else None, ""), "total_up": up, "total_down": down, "score": up - down}

    def get_vote_stats(self, content_id: str) -> dict:
        if content_id not in self._votes:
            return {"up": 0, "down": 0, "score": 0}
        votes = self._votes[content_id]
        up = sum(1 for v in votes.values() if v == "up")
        down = sum(1 for v in votes.values() if v == "down")
        return {"up": up, "down": down, "score": up - down}


class AIQualityEvaluator:
    def __init__(self):
        self._evaluations: dict[str, dict] = {}

    def evaluate_content(self, content_id: str, content_text: str, category: str = "general") -> dict:
        length = len(content_text)
        if length < 50:
            score, level = 50, "poor"
        elif length < 200:
            score, level = 60, "average"
        elif length < 1000:
            score, level = 75, "good"
        else:
            score, level = 95, "excellent"
        result = {"content_id": content_id, "total_score": score, "quality_level": level}
        self._evaluations[content_id] = result
        return result

    def get_evaluation(self, content_id: str) -> dict:
        if content_id in self._evaluations:
            return self._evaluations[content_id]
        return {"content_id": content_id, "total_score": 0, "quality_level": "unknown"}


class ContentQualityScoringService:
    def __init__(self):
        self._voting = UserVotingSystem()
        self._evaluator = AIQualityEvaluator()
        self._scores: dict[str, dict] = {}

    async def rate_content(self, content_id: str, user_id: int, content_text: str, category: str = "general", vote_type: Optional[str] = None) -> dict:
        ai_result = self._evaluator.evaluate_content(content_id, content_text, category)
        if vote_type:
            vote_stats = self._voting.vote(content_id, user_id, vote_type)
        else:
            vote_stats = self._voting.get_vote_stats(content_id)
        combined = (ai_result["total_score"] + vote_stats["score"]) / 2
        result = {
            "content_id": content_id, "ai_score": ai_result["total_score"],
            "ai_level": ai_result["quality_level"], "vote_stats": vote_stats,
            "combined_score": combined,
        }
        self._scores[content_id] = result
        return result

    async def get_quality_score(self, content_id: str) -> dict:
        if content_id in self._scores:
            s = self._scores[content_id]
            return {"content_id": content_id, "vote_score": s["vote_stats"]["score"], "ai_score": s["ai_score"], "quality_level": s["ai_level"]}
        return {"content_id": content_id, "vote_score": 0, "ai_score": 0, "quality_level": "unknown"}

    async def get_top_rated_content(self, limit: int = 10) -> list[dict]:
        items = sorted(self._scores.values(), key=lambda x: x["combined_score"], reverse=True)
        return items[:limit]

    async def get_stats(self) -> dict:
        total = len(self._scores)
        dist = {}
        for s in self._scores.values():
            lvl = s["ai_level"]
            dist[lvl] = dist.get(lvl, 0) + 1
        total_votes = 0
        for s in self._scores.values():
            vs = s["vote_stats"]
            up = vs.get("up", vs.get("total_up", 0) or 0)
            down = vs.get("down", vs.get("total_down", 0) or 0)
            total_votes += int(up) + int(down)
        return {"total_content": total, "quality_distribution": dist, "total_votes": total_votes}


content_quality_service = ContentQualityScoringService()


async def rate_content(content_id: str, user_id: int, content_text: str, category: str = "general", vote_type: Optional[str] = None) -> dict:
    return await content_quality_service.rate_content(content_id, user_id, content_text, category, vote_type)


async def get_quality_score(content_id: str) -> dict:
    return await content_quality_service.get_quality_score(content_id)
