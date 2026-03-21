"""
AI Legal Assistant - Agent Module

基于 LangGraph 的法律助手核心模块
"""

from .state import AgentState, RetrievedDocument, get_initial_state
from .nodes import (
    intent_analyzer,
    query_rewriter,
    legal_retriever,
    draft_generator,
    hallucination_checker,
    casual_chat_handler
)
from .nodes_async import (
    intent_analyzer as async_intent_analyzer,
    query_rewriter as async_query_rewriter,
    legal_retriever as async_legal_retriever,
    draft_generator as async_draft_generator,
    hallucination_checker as async_hallucination_checker,
    casual_chat_handler as async_casual_chat_handler,
)
from .graph import (
    build_legal_assistant_graph,
    compile_legal_assistant_graph,
    legal_assistant_graph,
    route_after_intent,
    route_after_hallucination_check,
    should_continue
)
from .graph_async import (
    build_legal_assistant_graph as build_async_graph,
    compile_legal_assistant_graph as compile_async_graph,
    legal_assistant_graph as legal_assistant_graph_async,
)

__all__ = [
    "AgentState",
    "RetrievedDocument",
    "get_initial_state",
    "intent_analyzer",
    "query_rewriter",
    "legal_retriever",
    "draft_generator",
    "hallucination_checker",
    "casual_chat_handler",
    "async_intent_analyzer",
    "async_query_rewriter",
    "async_legal_retriever",
    "async_draft_generator",
    "async_hallucination_checker",
    "async_casual_chat_handler",
    "build_legal_assistant_graph",
    "compile_legal_assistant_graph",
    "legal_assistant_graph",
    "build_async_graph",
    "compile_async_graph",
    "legal_assistant_graph_async",
    "route_after_intent",
    "route_after_hallucination_check",
    "should_continue",
]
