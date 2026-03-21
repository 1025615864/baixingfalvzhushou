"""
AI Legal Assistant - Agent State Definitions

定义 LangGraph 工作流中的全局状态数据结构
"""

from typing import TypedDict, List, Optional
from datetime import datetime


class RetrievedDocument(TypedDict):
    """检索到的法律文档结构"""
    chunk_id: str
    text: str
    law_name: str
    part: str
    chapter: str
    article_num: str
    effective_date: str
    category: str
    score: float


class AgentState(TypedDict):
    """
    LangGraph 全局状态字典

    维护法律助手工作流中的所有状态信息
    """
    user_query: str
    chat_history: List[dict]
    intent: Optional[str]
    search_query: Optional[str]
    retrieved_docs: List[RetrievedDocument]
    draft_response: Optional[str]
    final_response: Optional[str]
    error_flag: bool
    error_message: Optional[str]
    retry_count: int
    created_at: str


def get_initial_state(user_query: str, chat_history: List[dict] | None = None) -> AgentState:
    """
    初始化 Agent 状态

    Args:
        user_query: 用户原始问题
        chat_history: 历史对话上下文

    Returns:
        AgentState: 初始状态字典
    """
    return AgentState(
        user_query=user_query,
        chat_history=list(chat_history) if chat_history else [],
        intent=None,
        search_query=None,
        retrieved_docs=[],
        draft_response=None,
        final_response=None,
        error_flag=False,
        error_message=None,
        retry_count=0,
        created_at=datetime.now().isoformat()
    )
