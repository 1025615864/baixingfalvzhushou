"""Script to create all missing service module stubs."""
import os

BASE = r"d:\Git\baixingfalvzhushou\backend\app\services"

def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if os.path.exists(full):
        print(f"SKIP (exists): {path}")
        return
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"CREATED: {path}")

# ============================================================
# app.services.ai sub-modules
# ============================================================
write("ai/__init__.py", "")

write("ai/session.py", '''"""AI session management."""
import time
import uuid
from typing import Optional


class SessionManager:
    def __init__(self, max_sessions: int = 100, max_messages_per_session: int = 50):
        self._max_sessions = max_sessions
        self._max_messages_per_session = max_messages_per_session
        self.conversation_histories: dict[str, list[dict]] = {}
        self._last_seen: dict[str, float] = {}

    def get_or_create_session(self, session_id: Optional[str] = None, initial_history: Optional[list[dict]] = None) -> str:
        if session_id is None:
            session_id = uuid.uuid4().hex
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = list(initial_history) if initial_history else []
            self._last_seen[session_id] = time.time()
            self._evict_if_needed()
        else:
            self._last_seen[session_id] = time.time()
        return session_id

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = []
            self._last_seen[session_id] = time.time()
        self.conversation_histories[session_id].append({"role": role, "content": content})
        if len(self.conversation_histories[session_id]) > self._max_messages_per_session:
            self.conversation_histories[session_id] = self.conversation_histories[session_id][-self._max_messages_per_session:]

    def get_history(self, session_id: str) -> list[dict]:
        return self.conversation_histories.get(session_id, [])

    def get_recent_history(self, session_id: str, limit: int = 10) -> list[dict]:
        history = self.conversation_histories.get(session_id, [])
        return history[-limit:]

    def clear_session(self, session_id: str) -> None:
        self.conversation_histories.pop(session_id, None)
        self._last_seen.pop(session_id, None)

    def _evict_if_needed(self) -> None:
        if len(self.conversation_histories) <= self._max_sessions:
            return
        oldest = sorted(self._last_seen.items(), key=lambda x: x[1])
        to_remove = len(self.conversation_histories) - self._max_sessions
        for sid, _ in oldest[:to_remove]:
            self.clear_session(sid)

    def _normalize_history(self, history: list[dict]) -> list[dict]:
        valid_roles = {"user", "assistant"}
        result = []
        for msg in history:
            role = msg.get("role", "").strip().lower()
            content = msg.get("content", "")
            if role in valid_roles and content and content.strip():
                result.append({"role": role, "content": content.strip() if isinstance(content, str) else content})
        if len(result) > self._max_messages_per_session:
            result = result[-self._max_messages_per_session:]
        return result
''')

write("ai/core.py", '''"""AI core utilities."""
from __future__ import annotations
from typing import Optional


class AICore:
    SYSTEM_PROMPT = "你是\\"百姓法律助手\\"的AI法律咨询员，请根据中国法律为用户提供专业的法律咨询意见。"
    SYSTEM_PROMPT_V2 = (
        "你是\\"百姓法律助手\\"的AI法律咨询员。\\n"
        "输出优先级：结论摘要 > 法律依据 > 详细分析。\\n"
        "请在回答中包含结论摘要和法律依据。"
    )

    @classmethod
    def _system_prompt_for_version(cls, version: Optional[str]) -> str:
        if version is None:
            return cls.SYSTEM_PROMPT
        v = str(version).strip().lower()
        if v in ("v2", "2", "beta"):
            return cls.SYSTEM_PROMPT_V2
        return cls.SYSTEM_PROMPT

    @classmethod
    def _encoding_for_model(cls, model: Optional[str]):
        try:
            import tiktoken
            try:
                return tiktoken.encoding_for_model(model)
            except KeyError:
                return tiktoken.get_encoding("cl100k_base")
        except ImportError:
            return None

    @classmethod
    def _count_tokens(cls, text: Optional[str], model: str = "gpt-4") -> int:
        if not text:
            return 0
        enc = cls._encoding_for_model(model)
        if enc is None:
            return len(str(text)) // 4
        return len(enc.encode(str(text)))

    @classmethod
    def _estimate_cost_usd(cls, model: Optional[str], prompt_tokens: int, completion_tokens: int) -> Optional[float]:
        if not model:
            return None
        m = model.lower()
        pricing = {
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (5.00, 15.00),
            "gpt-3.5-turbo": (0.50, 1.50),
        }
        matched = None
        for key in pricing:
            if m.startswith(key):
                matched = key
                break
        if matched is None:
            return None
        p_in, p_out = pricing[matched]
        return (prompt_tokens / 1_000_000) * p_in + (completion_tokens / 1_000_000) * p_out
''')

write("ai/knowledge_base.py", '''"""AI knowledge base service."""
from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class QualityResult:
    total_candidates: int = 0
    qualified_count: int = 0
    avg_similarity: float = 0.0
    confidence: str = "low"


class LegalKnowledgeBase:
    RELEVANCE_THRESHOLD: float = 0.5
    MIN_REFERENCES: int = 1
    MAX_REFERENCES: int = 5

    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self._initialized = False
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    def initialize(self) -> None:
        if self._initialized:
            return
        try:
            from app.core.config import settings
            if settings.openai_api_key:
                try:
                    from langchain_openai import OpenAIEmbeddings
                    from langchain_community.vectorstores import Chroma
                    self.embeddings = OpenAIEmbeddings(
                        openai_api_key=settings.openai_api_key,
                        openai_api_base=getattr(settings, 'openai_base_url', None),
                    )
                    self.vector_store = Chroma(
                        persist_directory=getattr(settings, 'chroma_persist_dir', './chroma_db'),
                        embedding_function=self.embeddings,
                    )
                except Exception:
                    self.embeddings = None
                    self.vector_store = None
        except Exception:
            pass
        self._initialized = True

    def search(self, query: str, k: int = 5) -> list[tuple[str, dict, float]]:
        if not self._initialized:
            self.initialize()
        if self.vector_store is None:
            return []
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return [(doc.page_content, doc.metadata, self._score_to_similarity(score)) for doc, score in results]
        except Exception:
            return []

    def search_with_quality_control(self, query: str, k: int = 5, threshold: float = 0.5) -> tuple[list[tuple[str, dict, float]], QualityResult]:
        results = self.search(query, k=k)
        qualified = [r for r in results if r[2] >= threshold]
        qualified = qualified[:self.MAX_REFERENCES]
        avg_sim = sum(r[2] for r in qualified) / len(qualified) if qualified else 0.0
        confidence = self._calculate_confidence(qualified)
        quality = QualityResult(
            total_candidates=len(results),
            qualified_count=len(qualified),
            avg_similarity=avg_sim,
            confidence=confidence,
        )
        return qualified, quality

    def add_law_documents(self, documents: list[dict]) -> None:
        if not self._initialized:
            self.initialize()
        if not documents or self.vector_store is None:
            return
        texts = []
        metadatas = []
        for doc in documents:
            law_name = doc.get("law_name", "") or ""
            article = doc.get("article", "") or ""
            content = doc.get("content", "") or ""
            text = f"【{law_name}】{article}\\n{content}"
            metadata = {
                "law_name": str(law_name),
                "article": str(article),
                "source": str(doc.get("source", "")),
                "source_url": str(doc.get("source_url", "")),
                "source_version": str(doc.get("source_version", "")),
                "source_hash": str(doc.get("source_hash", "")),
                "ingest_batch_id": str(doc.get("ingest_batch_id", "")),
                "knowledge_id": str(doc.get("knowledge_id", "")),
            }
            texts.append(text)
            metadatas.append(metadata)
        self.vector_store.add_texts(texts=texts, metadatas=metadatas)

    def _score_to_similarity(self, score: float) -> float:
        if score <= 0:
            return 1.0
        if score <= 1.0:
            return 1.0 - score
        return 1.0 / (1.0 + score)

    def _calculate_confidence(self, results: list[tuple]) -> str:
        if not results:
            return "low"
        avg = sum(r[2] for r in results) / len(results)
        if avg >= 0.85 and len(results) >= 2:
            return "high"
        if avg >= 0.7:
            return "medium"
        return "low"
''')

write("ai/models.py", '''"""AI model configuration."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AIModelConfig:
    model_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    weight: int = 1
''')

write("ai/cache_optimizer.py", '''"""AI cache optimizer service."""
from __future__ import annotations
import asyncio
import enum
import time
from typing import Optional, Any
from dataclasses import dataclass, field


class CachePriority(enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CacheInvalidationReason(enum.Enum):
    TTL_EXPIRED = "ttl_expired"
    MANUAL_INVALIDATE = "manual_invalidate"
    KNOWLEDGE_BASE_UPDATE = "knowledge_base_update"
    USER_FEEDBACK = "user_feedback"


class RetryStrategy(enum.Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


@dataclass
class RetryConfig:
    strategy: RetryStrategy = RetryStrategy.FIXED
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0

    def get_delay(self, attempt: int) -> float:
        if self.strategy == RetryStrategy.FIXED:
            return self.base_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** attempt)
            return min(delay, self.max_delay)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
            return min(delay, self.max_delay)
        return self.base_delay


@dataclass
class VectorSearchCacheEntry:
    query: str
    k: int
    results: list
    timestamp: float


class VectorSearchCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self._cache: dict[str, VectorSearchCacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def _key(self, query: str, k: int) -> str:
        return f"{query}::{k}"

    def get_sync(self, query: str, k: int = 5) -> Optional[list]:
        key = self._key(query, k)
        entry = self._cache.get(key)
        if entry and (time.time() - entry.timestamp) < self._default_ttl:
            self._hits += 1
            return entry.results
        self._misses += 1
        return None

    def set_sync(self, query: str, results: list, k: int = 5) -> None:
        key = self._key(query, k)
        self._cache[key] = VectorSearchCacheEntry(query=query, k=k, results=results, timestamp=time.time())
        if len(self._cache) > self._max_size:
            oldest = min(self._cache.items(), key=lambda x: x[1].timestamp)
            del self._cache[oldest[0]]

    async def get(self, query: str, k: int = 5) -> Optional[list]:
        return self.get_sync(query, k)

    async def set(self, query: str, results: list, k: int = 5) -> None:
        self.set_sync(query, results, k)

    def get_stats(self) -> dict:
        return {"hits": self._hits, "misses": self._misses, "size": len(self._cache)}


@dataclass
class AIResponseCacheEntry:
    question: str
    answer: str
    references: list
    model_used: str
    confidence: str
    priority: CachePriority = CachePriority.MEDIUM
    timestamp: float = 0.0
    feedback: list = field(default_factory=list)


class AIResponseCache:
    def __init__(self, high_priority_ttl: int = 7200, default_ttl: int = 3600, low_priority_ttl: int = 1800):
        self._cache: dict[str, AIResponseCacheEntry] = {}
        self._high_priority_ttl = high_priority_ttl
        self._default_ttl = default_ttl
        self._low_priority_ttl = low_priority_ttl
        self._feedback_threshold = 3

    def _get_ttl(self, priority: CachePriority) -> int:
        if priority == CachePriority.HIGH:
            return self._high_priority_ttl
        elif priority == CachePriority.LOW:
            return self._low_priority_ttl
        return self._default_ttl

    async def get(self, question: str) -> Optional[AIResponseCacheEntry]:
        entry = self._cache.get(question)
        if entry is None:
            return None
        ttl = self._get_ttl(entry.priority)
        if time.time() - entry.timestamp > ttl:
            del self._cache[question]
            return None
        if len(entry.feedback) >= self._feedback_threshold:
            del self._cache[question]
            return None
        return entry

    async def set(self, question: str, answer: str, references: list, model_used: str, confidence: str, priority: CachePriority = CachePriority.MEDIUM) -> str:
        key = question
        self._cache[key] = AIResponseCacheEntry(
            question=question, answer=answer, references=references,
            model_used=model_used, confidence=confidence, priority=priority,
            timestamp=time.time(),
        )
        return key

    async def add_feedback(self, cache_key: str, feedback_type: str) -> None:
        entry = self._cache.get(cache_key)
        if entry:
            entry.feedback.append(feedback_type)

    def get_stats(self) -> dict:
        dist = {"high": 0, "medium": 0, "low": 0}
        for e in self._cache.values():
            dist[e.priority.value] = dist.get(e.priority.value, 0) + 1
        return {"priority_distribution": dist, "size": len(self._cache)}


class ResultDeduplicator:
    def deduplicate(self, results: list[tuple[str, dict, float]]) -> list[tuple[str, dict, float]]:
        seen_ids = set()
        seen_hashes = set()
        deduped = []
        for content, metadata, score in results:
            kid = metadata.get("knowledge_id")
            content_hash = hash(content)
            if kid and kid in seen_ids:
                continue
            if not kid and content_hash in seen_hashes:
                continue
            if kid:
                seen_ids.add(kid)
            seen_hashes.add(content_hash)
            deduped.append((content, metadata, score))
        return deduped

    def merge_and_deduplicate(self, result_sets: list[list[tuple]], max_results: int = 10) -> list[tuple]:
        merged = []
        for rs in result_sets:
            merged.extend(rs)
        deduped = self.deduplicate(merged)
        deduped.sort(key=lambda x: x[2], reverse=True)
        return deduped[:max_results]


class BatchRetrievalOptimizer:
    def __init__(self, batch_window_ms: int = 50):
        self._batch_window_ms = batch_window_ms

    async def execute_with_batching(self, query: str, k: int, search_func) -> list:
        return await search_func(query, k)


class RequestQueueManager:
    def __init__(self, max_concurrent: int = 10, queue_size: int = 100):
        self._max_concurrent = max_concurrent
        self._queue_size = queue_size
        self._completed = 0

    async def submit(self, request_func, priority: int = 5) -> Any:
        result = await request_func()
        self._completed += 1
        return result

    def get_stats(self) -> dict:
        return {"requests_completed": self._completed}


class AIRequestExecutor:
    def __init__(self, default_timeout: float = 30.0):
        self._default_timeout = default_timeout
        self._stats = {"successful_requests": 0, "timeout_requests": 0, "retried_requests": 0}

    async def execute(self, func, retry_config: Optional[RetryConfig] = None, timeout: Optional[float] = None) -> Any:
        to = timeout or self._default_timeout
        attempts = 0
        max_attempts = 1
        if retry_config:
            max_attempts = retry_config.max_retries + 1
        while attempts < max_attempts:
            try:
                result = await asyncio.wait_for(func(), timeout=to)
                self._stats["successful_requests"] += 1
                return result
            except asyncio.TimeoutError:
                self._stats["timeout_requests"] += 1
                raise TimeoutError()
            except Exception:
                attempts += 1
                if retry_config and attempts < max_attempts:
                    self._stats["retried_requests"] += 1
                    delay = retry_config.get_delay(attempts - 1)
                    await asyncio.sleep(delay)
                else:
                    raise

    def get_stats(self) -> dict:
        return self._stats


class AICacheOptimizer:
    def __init__(self):
        self._vector_cache = VectorSearchCache()
        self._response_cache = AIResponseCache()
        self._batch_optimizer = BatchRetrievalOptimizer()
        self._queue_manager = RequestQueueManager()
        self._request_executor = AIRequestExecutor()

    def get_all_stats(self) -> dict:
        return {
            "vector_search_cache": self._vector_cache.get_stats(),
            "ai_response_cache": self._response_cache.get_stats(),
            "batch_optimizer": {},
            "queue_manager": self._queue_manager.get_stats(),
            "request_executor": self._request_executor.get_stats(),
        }


_instance: Optional[AICacheOptimizer] = None


def get_ai_cache_optimizer() -> AICacheOptimizer:
    global _instance
    if _instance is None:
        _instance = AICacheOptimizer()
    return _instance
''')

write("ai/assistant.py", '''"""AI legal assistant service."""
from __future__ import annotations
import time
from typing import Optional
from dataclasses import dataclass

from app.services.ai.session import SessionManager
from app.services.ai.core import AICore


@dataclass
class ParsedReference:
    content: str
    knowledge_id: Optional[int] = None
    similarity: float = 0.0


class AILegalAssistant:
    def __init__(self):
        self._session_manager = SessionManager()
        self.conversation_histories = self._session_manager.conversation_histories
        self._last_seen = self._session_manager._last_seen
        self._max_sessions = 100
        self._max_messages_per_session = 50
        self._disclaimer_manager = None

    def get_or_create_session(self, session_id: str) -> str:
        return self._session_manager.get_or_create_session(session_id)

    def clear_session(self, session_id: str) -> None:
        self._session_manager.clear_session(session_id)

    def _evict_if_needed(self) -> None:
        self._session_manager._evict_if_needed()

    def _append_disclaimer(self, answer: str, risk_level=None, strategy=None) -> str:
        if self._disclaimer_manager is None:
            try:
                from app.services.disclaimer import DisclaimerManager
                self._disclaimer_manager = DisclaimerManager()
            except Exception:
                return answer
        disclaimer = self._disclaimer_manager.get_disclaimer(risk_level=risk_level, strategy=strategy)
        if disclaimer:
            return f"{answer}\\n\\n---\\n{disclaimer}"
        return answer

    def _normalize_history(self, history: list[dict]) -> list[dict]:
        return self._session_manager._normalize_history(history)

    def _count_tokens(self, text: str, model: str = "gpt-4") -> int:
        return AICore._count_tokens(text, model)

    def _estimate_cost_usd(self, model: Optional[str], prompt_tokens: int, completion_tokens: int) -> Optional[float]:
        return AICore._estimate_cost_usd(model, prompt_tokens, completion_tokens)

    def _build_context(self, references: list[tuple]) -> str:
        if not references:
            return "暂无相关法律条文参考"
        parts = []
        for i, (content, metadata, score) in enumerate(references, 1):
            parts.append(f"{i}. {content}")
        return "\\n\\n".join(parts)

    def _parse_references(self, references: list[tuple]) -> list[ParsedReference]:
        result = []
        for content, metadata, similarity in references:
            kid = metadata.get("knowledge_id")
            parsed_kid = None
            if kid is not None:
                try:
                    parsed_kid = int(kid)
                except (ValueError, TypeError):
                    parsed_kid = None
            result.append(ParsedReference(content=content, knowledge_id=parsed_kid, similarity=similarity))
        return result

    def _model_candidates(self) -> list[str]:
        try:
            from app.core.config import get_settings
            settings = get_settings()
            primary = getattr(settings, 'ai_model', '')
            fallbacks = getattr(settings, 'ai_fallback_models', []) or []
            candidates = [primary] + fallbacks
            return list(dict.fromkeys(c for c in candidates if c and c.strip()))
        except Exception:
            return []

    def _encoding_for_model(self, model: Optional[str]):
        return AICore._encoding_for_model(model)

    def _llm_for_model(self, model: str):
        try:
            from langchain_openai import ChatOpenAI
            from app.core.config import get_settings
            settings = get_settings()
            return ChatOpenAI(
                model=model,
                openai_api_key=settings.openai_api_key,
                openai_api_base=getattr(settings, 'openai_base_url', None),
            )
        except Exception:
            return None
''')

# ============================================================
# app.services.action_cards
# ============================================================
write("action_cards/__init__.py", '''"""Action cards service."""
from __future__ import annotations
from typing import Optional


class ActionCardConfig:
    def __init__(self):
        self._cards: dict[str, dict] = {}
        self._next_id = 1

    def register_card(self, card_id: str, name: str, description: str, trigger_keywords: list[str], action_type: str, priority: int = 0) -> dict:
        self._cards[card_id] = {
            "id": card_id, "name": name, "description": description,
            "trigger_keywords": trigger_keywords, "action_type": action_type,
            "priority": priority, "enabled": True,
        }
        return {"id": card_id, "name": name, "registered": True}

    def get_card(self, card_id: str) -> dict:
        return self._cards.get(card_id, {})

    def list_cards(self) -> list[dict]:
        return list(self._cards.values())


class ActionCardTrigger:
    def __init__(self):
        self._config = ActionCardConfig()

    def detect_triggers(self, message: str, context: Optional[dict] = None) -> list[dict]:
        results = []
        message_lower = message.lower()
        for card in self._config.list_cards():
            if not card.get("enabled", True):
                continue
            for kw in card.get("trigger_keywords", []):
                if kw.lower() in message_lower:
                    results.append({
                        "card_id": card["id"], "card_name": card["name"],
                        "trigger_keyword": kw, "priority": card.get("priority", 0),
                    })
                    break
        results.sort(key=lambda x: x["priority"], reverse=True)
        return results[:5]


class ActionCardExecutor:
    def __init__(self):
        self._trigger = ActionCardTrigger()
        self._executions: dict[str, dict] = {}
        self._next_exec_id = 1

    def execute_card(self, card_id: str, user_id: int, session_id: str, params: Optional[dict] = None) -> dict:
        card = self._trigger._config.get_card(card_id)
        if not card:
            return {"success": False, "error": "卡片不存在"}
        exec_id = f"exec_{self._next_exec_id}_{user_id}"
        self._next_exec_id += 1
        action_result = {}
        at = card.get("action_type", "info")
        if at == "generate_document":
            action_result = {"document_id": f"doc_{exec_id}", "status": "generated"}
        elif at == "recommend_lawyer":
            action_result = {"lawyer_id": f"lawyer_{exec_id}", "status": "recommended"}
        elif at == "create_reminder":
            action_result = {"reminder_id": f"rem_{exec_id}", "status": "created"}
        self._executions[exec_id] = {"card_id": card_id, "user_id": user_id, "params": params or {}}
        return {"success": True, "card_id": card_id, "action_type": at, "execution_id": exec_id, "action_result": action_result}

    def get_user_executions(self, user_id: int) -> list[dict]:
        return [e for e in self._executions.values() if e["user_id"] == user_id]


class ActionCardService:
    def __init__(self):
        self._config = ActionCardConfig()
        self._trigger = ActionCardTrigger()
        self._executor = ActionCardExecutor()

    def register_default_cards(self) -> list[dict]:
        defaults = [
            ("generate_contract", "生成合同", "生成合同文档", ["合同", "协议"], "generate_document", 10),
            ("recommend_lawyer", "推荐律师", "推荐专业律师", ["律师", "咨询"], "recommend_lawyer", 9),
            ("create_reminder", "创建提醒", "创建法律提醒", ["提醒", "到期"], "create_reminder", 8),
            ("calculate_fee", "费用计算", "计算法律费用", ["费用", "收费"], "info", 7),
        ]
        results = []
        for cid, name, desc, kws, at, pri in defaults:
            results.append(self._config.register_card(cid, name, desc, kws, at, pri))
        return results

    async def detect_and_execute(self, message: str, user_id: int, session_id: str, context: Optional[dict] = None) -> dict:
        triggers = self._trigger.detect_triggers(message, context)
        if not triggers:
            return {"detected": False, "message": "未检测到可执行的动作"}
        executions = []
        for t in triggers[:2]:
            result = self._executor.execute_card(t["card_id"], user_id, session_id)
            executions.append(result)
        return {"detected": True, "triggered_count": len(triggers), "executions": executions}

    async def get_cards(self) -> list[dict]:
        return self._config.list_cards()

    async def get_user_history(self, user_id: int) -> list[dict]:
        return self._executor.get_user_executions(user_id)


action_card_service = ActionCardService()


async def detect_action_cards(message: str, user_id: int, session_id: str, context: Optional[dict] = None) -> dict:
    return await action_card_service.detect_and_execute(message, user_id, session_id, context)
''')

# ============================================================
# app.services.audit_service
# ============================================================
write("audit_service/__init__.py", '''"""Audit service."""
from __future__ import annotations
import enum
import uuid
import contextvars
from datetime import datetime, timezone
from typing import Optional, Any
from dataclasses import dataclass, field


class AuditAction(enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    EXPORT = "export"
    IMPORT = "import"
    ADMIN_ACTION = "admin_action"
    API_CALL = "api_call"
    SYSTEM = "system"


class AuditSeverity(enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLogEntry:
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[dict] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    severity: AuditSeverity = AuditSeverity.INFO
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Optional[dict] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id, "action": self.action.value,
            "resource_type": self.resource_type, "resource_id": self.resource_id,
            "timestamp": self.timestamp, "success": self.success,
        }


_audit_context: contextvars.ContextVar[Optional[dict]] = contextvars.ContextVar("audit_context", default=None)


class AuditContext:
    def __init__(self, user_id=None, username=None, ip_address=None, request_id=None):
        self._data = {"user_id": user_id, "username": username, "ip_address": ip_address, "request_id": request_id}

    async def __aenter__(self):
        self._token = _audit_context.set(self._data)
        return self._data

    async def __aexit__(self, *args):
        _audit_context.reset(self._token)


class AuditLogger:
    def __init__(self, async_mode: bool = True, batch_size: int = 100, flush_interval: float = 5.0):
        self.async_mode = async_mode
        self.batch_size = batch_size
        self.flush_interval = flush_interval

    def create_entry(self, action: AuditAction, resource_type: str, resource_id: Optional[str] = None, **kwargs) -> AuditLogEntry:
        return AuditLogEntry(action=action, resource_type=resource_type, resource_id=resource_id, **kwargs)


def get_current_audit_context() -> Optional[dict]:
    return _audit_context.get()


_logger_instance: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AuditLogger(async_mode=False)
    return _logger_instance


def log_audit(action: AuditAction, resource_type: str, **kwargs) -> AuditLogEntry:
    logger = get_audit_logger()
    return logger.create_entry(action, resource_type, **kwargs)
''')

# ============================================================
# app.services.content_moderation
# ============================================================
write("content_moderation/__init__.py", '''"""Content moderation service."""
from __future__ import annotations
from typing import Optional


class KeywordFilter:
    def __init__(self):
        self._keywords: dict[str, dict] = {}
        self._next_id = 1

    def add_keyword(self, keyword: str, category: str = "general", severity: str = "medium") -> dict:
        kid = f"KW-{self._next_id:04d}"
        self._next_id += 1
        self._keywords[keyword] = {"keyword_id": kid, "keyword": keyword, "category": category, "severity": severity}
        return {"keyword_id": kid, "keyword": keyword, "category": category}

    def check_content(self, content: str, categories: Optional[list[str]] = None) -> dict:
        matched = []
        risk_score = 0
        for kw, info in self._keywords.items():
            if categories and info["category"] not in categories:
                continue
            if kw in content:
                matched.append(info)
                severity_scores = {"high": 30, "medium": 20, "low": 10}
                risk_score += severity_scores.get(info["severity"], 10)
        return {"is_safe": len(matched) == 0, "risk_score": risk_score, "matched_count": len(matched), "matched_keywords": matched}

    def get_keywords_by_category(self, category: str) -> list[dict]:
        return [info for info in self._keywords.values() if info["category"] == category]


class ContentModerationService:
    def __init__(self):
        self._contents: dict[int, dict] = {}
        self._next_id = 1
        self._keyword_filter = KeywordFilter()

    async def submit_content(self, user_id: int, content_type: str, content: str) -> dict:
        cid = self._next_id
        self._next_id += 1
        self._contents[cid] = {"id": cid, "user_id": user_id, "content_type": content_type, "content": content, "status": "pending", "check_result": None, "final_decision": None}
        return {"content_id": cid, "status": "pending", "risk_score": 0}

    async def ai_review(self, content_id: int) -> dict:
        entry = self._contents.get(content_id)
        if not entry:
            return {"success": False, "error": "内容不存在"}
        content = entry.get("content", "")
        flags = []
        is_safe = True
        unsafe_keywords = {"诈骗": "potential_fraud", "赌博": "gambling", "色情": "pornographic"}
        for kw, flag in unsafe_keywords.items():
            if kw in content:
                flags.append(flag)
                is_safe = False
        confidence = 0.95 if is_safe else 0.85
        entry["check_result"] = {"risk_level": "low" if is_safe else "high", "flags": flags}
        return {"success": True, "is_safe": is_safe, "confidence": confidence, "flags": flags}

    async def make_decision(self, content_id: int, decision: str = "auto") -> dict:
        entry = self._contents.get(content_id)
        if not entry:
            return {"success": False, "error": "内容不存在"}
        if decision == "auto":
            check = entry.get("check_result", {})
            final = "approved" if check.get("risk_level", "high") == "low" else "rejected"
        else:
            final = decision
        entry["final_decision"] = final
        return {"success": True, "decision": final}

    async def get_moderation_stats(self) -> dict:
        total = len(self._contents)
        approved = sum(1 for c in self._contents.values() if c.get("final_decision") == "approved")
        return {"total_content": total, "approved": approved, "approval_rate": approved / total if total > 0 else 0.0}

    async def report_content(self, reporter_id: int, content_id: int, reason: str) -> dict:
        return {"report_id": content_id, "status": "pending"}

    def get_total_checks(self) -> int:
        return len(self._contents)

    def get_blocked_count(self) -> int:
        return sum(1 for c in self._contents.values() if c.get("final_decision") == "rejected")

    def get_warning_count(self) -> int:
        return sum(1 for c in self._contents.values() if c.get("check_result", {}).get("risk_level") == "high")

    def get_passed_count(self) -> int:
        return sum(1 for c in self._contents.values() if c.get("final_decision") == "approved")

    def get_block_rate(self) -> float:
        total = len(self._contents)
        if total == 0:
            return 0.0
        return round(self.get_blocked_count() / total * 100, 2)

    def get_category_count(self, category: str) -> int:
        return sum(1 for c in self._contents.values() if c.get("content_type") == category)


content_moderation_service = ContentModerationService()


async def submit_content_for_moderation(user_id: int, content_type: str, content: str) -> dict:
    return await content_moderation_service.submit_content(user_id, content_type, content)


async def ai_review_content(content_id: int) -> dict:
    return await content_moderation_service.ai_review(content_id)


async def get_moderation_stats() -> dict:
    return await content_moderation_service.get_moderation_stats()
''')

# ============================================================
# app.services.content_quality
# ============================================================
write("content_quality/__init__.py", '''"""Content quality scoring service."""
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
        return {"total_content": total, "quality_distribution": dist, "total_votes": sum(s["vote_stats"]["up"] + s["vote_stats"]["down"] for s in self._scores.values())}


content_quality_service = ContentQualityScoringService()


async def rate_content(content_id: str, user_id: int, content_text: str, category: str = "general", vote_type: Optional[str] = None) -> dict:
    return await content_quality_service.rate_content(content_id, user_id, content_text, category, vote_type)


async def get_quality_score(content_id: str) -> dict:
    return await content_quality_service.get_quality_score(content_id)
''')

# ============================================================
# app.services.content_safety
# ============================================================
write("content_safety/__init__.py", '''"""Content safety filter service."""
from __future__ import annotations
import enum
import re
from dataclasses import dataclass, field
from typing import Optional


class RiskLevel(enum.Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass
class SafetyCheckResult:
    risk_level: RiskLevel = RiskLevel.SAFE
    should_log: bool = False
    suggestion: Optional[str] = None
    triggered_rules: list[str] = field(default_factory=list)


class ContentSafetyFilter:
    BLOCKED_PATTERNS = ["杀人", "自杀方法", "制造炸弹"]
    HIGH_RISK_PATTERNS = ["自杀", "自残", "伤害他人"]
    SENSITIVE_PATTERNS = {"政治敏感": ["政府腐败", "政治"]}

    PHONE_PATTERN = re.compile(r"1[3-9]\\d{9}")
    ID_CARD_PATTERN = re.compile(r"\\d{17}[\\dXx]")

    def check_input(self, text: str) -> SafetyCheckResult:
        for p in self.BLOCKED_PATTERNS:
            if p in text:
                return SafetyCheckResult(risk_level=RiskLevel.BLOCKED, should_log=True, suggestion="该内容已被拦截", triggered_rules=[f"blocked:{p}"])
        for p in self.HIGH_RISK_PATTERNS:
            if p in text:
                return SafetyCheckResult(risk_level=RiskLevel.HIGH, should_log=True, suggestion=None, triggered_rules=[f"high_risk:{p}"])
        for category, patterns in self.SENSITIVE_PATTERNS.items():
            for p in patterns:
                if p in text:
                    return SafetyCheckResult(risk_level=RiskLevel.MEDIUM, should_log=True, suggestion=None, triggered_rules=[f"sensitive:{category}"])
        return SafetyCheckResult(risk_level=RiskLevel.SAFE, should_log=False, suggestion=None, triggered_rules=[])

    def sanitize_output(self, text: str) -> str:
        text = self.PHONE_PATTERN.sub("[电话号码已隐藏]", text)
        text = self.ID_CARD_PATTERN.sub("[身份证号已隐藏]", text)
        return text
''')

# ============================================================
# app.services.ai_response_strategy
# ============================================================
write("ai_response_strategy/__init__.py", '''"""AI response strategy service."""
from __future__ import annotations
import enum


class ResponseStrategy(enum.Enum):
    GENERAL_LEGAL = "general_legal"
    REDIRECT = "redirect"
''')

print("\\n=== Batch 1 complete ===")
