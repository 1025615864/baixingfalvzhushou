"""
AI Legal Assistant - 异步状态图

支持异步节点的 LangGraph 状态机
"""

from langgraph.graph import StateGraph, END
from .state import AgentState, get_initial_state
from .nodes_async import (
    intent_analyzer,
    query_rewriter,
    legal_retriever,
    draft_generator,
    hallucination_checker,
    casual_chat_handler
)


def route_after_intent(state: AgentState) -> str:
    """意图分析后的路由"""
    intent = state.get("intent", "casual")
    if intent == "casual":
        return "casual"
    return "legal"


def route_after_hallucination_check(state: AgentState) -> str:
    """幻觉校验后的路由"""
    if state.get("error_flag", False) and state.get("retry_count", 0) < 3:
        return "regenerate"
    return "finalize"


def build_legal_assistant_graph() -> StateGraph:
    """
    构建法律助手的状态机图

    节点流程:
    START -> Intent_Analyzer -> [闲聊] -> casual_chat_handler -> END
                            |
                            v [法律咨询]
                         Query_Rewriter
                            |
                            v
                        Legal_Retriever
                            |
                            v
                        Draft_Generator
                            |
                            v
                      Hallucination_Checker
                            |
                            v [有幻觉且重试<3]
                         [重新生成] ---> Draft_Generator
                            |
                            v [校验通过]
                          END

    Returns:
        StateGraph: 构建好的状态机图（未编译）
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("intent_analyzer", intent_analyzer)
    workflow.add_node("query_rewriter", query_rewriter)
    workflow.add_node("legal_retriever", legal_retriever)
    workflow.add_node("draft_generator", draft_generator)
    workflow.add_node("hallucination_checker", hallucination_checker)
    workflow.add_node("casual_chat_handler", casual_chat_handler)

    workflow.set_entry_point("intent_analyzer")

    workflow.add_conditional_edges(
        "intent_analyzer",
        route_after_intent,
        {
            "casual": "casual_chat_handler",
            "legal": "query_rewriter"
        }
    )

    workflow.add_edge("casual_chat_handler", END)

    workflow.add_edge("query_rewriter", "legal_retriever")
    workflow.add_edge("legal_retriever", "draft_generator")
    workflow.add_edge("draft_generator", "hallucination_checker")

    workflow.add_conditional_edges(
        "hallucination_checker",
        route_after_hallucination_check,
        {
            "regenerate": "draft_generator",
            "finalize": END
        }
    )

    return workflow


def compile_legal_assistant_graph():
    """编译法律助手状态机图"""
    workflow = build_legal_assistant_graph()
    return workflow.compile()


legal_assistant_graph = compile_legal_assistant_graph()
