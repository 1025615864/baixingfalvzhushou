"""
AI Legal Assistant - LangGraph State Graph

将 5 个核心节点串联成可运行的状态机图
"""

from langgraph.graph import StateGraph, END
from .state import AgentState, get_initial_state
from .nodes import (
    intent_analyzer,
    query_rewriter,
    legal_retriever,
    draft_generator,
    hallucination_checker,
    casual_chat_handler
)


def should_continue(state: AgentState) -> str:
    """
    条件边路由函数

    决定在完成一轮校验后是继续循环还是结束

    Args:
        state: 当前 Agent 状态

    Returns:
        str: "regenerate" 继续循环到 Draft_Generator
             "end" 结束流程
    """
    if state.get("error_flag", False) and state.get("retry_count", 0) < 3:
        return "regenerate"
    return "end"


def route_after_intent(state: AgentState) -> str:
    """
    意图分析后的路由

    根据识别的意图决定后续流程

    Args:
        state: 当前 Agent 状态

    Returns:
        str: "casual" 走闲聊流程
             "legal" 走法律咨询流程
    """
    intent = state.get("intent", "casual")
    if intent == "casual":
        return "casual"
    return "legal"


def route_after_hallucination_check(state: AgentState) -> str:
    """
    幻觉校验后的路由

    根据校验结果决定是重新生成还是结束

    Args:
        state: 当前 Agent 状态

    Returns:
        str: "regenerate" 重新生成草稿
             "finalize" 输出最终回复
    """
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
    """
    编译法律助手状态机图

    Returns:
        CompiledStateGraph: 编译后可运行的图
    """
    workflow = build_legal_assistant_graph()
    return workflow.compile()


legal_assistant_graph = compile_legal_assistant_graph()
