"""AI Services 模块

提供法律助手Agent、向量数据库、RAG检索、LLM熔断等服务。
"""

from app.services.legal_agent import (
    legal_agent_graph,
    AgentState,
    stream_legal_agent,
)

from app.services.knowledge_vector_store import (
    knowledge_vector_store,
    KnowledgeVectorStore,
    search_knowledge,
)

from app.services.archive_vector_store import (
    archive_vector_store,
    ArchiveVectorStore,
    search_archive,
)

from app.services.backend_rag_client import (
    backend_rag_client,
    BackendRAGClient,
    query_backend_knowledge,
)

from app.services.rag_retrieval import (
    rag_retrieval_service,
    retrieve_with_fallback,
    RetrievalResult,
    RetrievalLevel,
)

from app.services.llm_client import (
    ResilientLLMClient,
    CircuitBreaker,
    CircuitState,
    LLMResponse,
    DegradedResponse,
    call_llm_with_fallback,
    get_resilient_llm_client,
)

from app.services.session_manager import (
    SessionManager,
    SessionInfo,
    ChatMessage,
    get_session_manager,
)

from app.services.agent_executor import (
    AgentExecutor,
    AgentResult,
    StreamEvent,
    get_agent_executor,
)

from app.services.message_persistence import (
    MessagePersistence,
    MessageRecord,
    get_message_persistence,
)

from app.services.chat_orchestrator import (
    ChatOrchestrator,
    ChatRequest,
    ChatResponse,
    get_chat_orchestrator,
)

from app.services.vector_index_sync import (
    VectorIndexEvent,
    VectorIndexEventHandler,
    KafkaEventConsumer,
    KafkaEventProducer,
    start_vector_index_sync,
    stop_vector_index_sync,
)

from app.services.retrieval_cache import (
    RetrievalCache,
    RetrievalCacheService,
    get_retrieval_cache_service,
)

from app.services.metrics import (
    MetricsCollector,
    LLMMetrics,
    RAGMetrics,
    AgentMetrics,
    get_metrics_collector,
)

__all__ = [
    "legal_agent_graph",
    "AgentState",
    "stream_legal_agent",
    "knowledge_vector_store",
    "KnowledgeVectorStore",
    "search_knowledge",
    "archive_vector_store",
    "ArchiveVectorStore",
    "search_archive",
    "backend_rag_client",
    "BackendRAGClient",
    "query_backend_knowledge",
    "rag_retrieval_service",
    "retrieve_with_fallback",
    "RetrievalResult",
    "RetrievalLevel",
    "ResilientLLMClient",
    "CircuitBreaker",
    "CircuitState",
    "LLMResponse",
    "DegradedResponse",
    "call_llm_with_fallback",
    "get_resilient_llm_client",
    "SessionManager",
    "SessionInfo",
    "ChatMessage",
    "get_session_manager",
    "AgentExecutor",
    "AgentResult",
    "StreamEvent",
    "get_agent_executor",
    "MessagePersistence",
    "MessageRecord",
    "get_message_persistence",
    "ChatOrchestrator",
    "ChatRequest",
    "ChatResponse",
    "get_chat_orchestrator",
    "VectorIndexEvent",
    "VectorIndexEventHandler",
    "KafkaEventConsumer",
    "KafkaEventProducer",
    "start_vector_index_sync",
    "stop_vector_index_sync",
    "RetrievalCache",
    "RetrievalCacheService",
    "get_retrieval_cache_service",
    "MetricsCollector",
    "LLMMetrics",
    "RAGMetrics",
    "AgentMetrics",
    "get_metrics_collector",
]