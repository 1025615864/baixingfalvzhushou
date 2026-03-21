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
from .graph import (
    build_legal_assistant_graph,
    compile_legal_assistant_graph,
    legal_assistant_graph,
    route_after_intent,
    route_after_hallucination_check,
    should_continue
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
    "build_legal_assistant_graph",
    "compile_legal_assistant_graph",
    "legal_assistant_graph",
    "route_after_intent",
    "route_after_hallucination_check",
    "should_continue",
]
