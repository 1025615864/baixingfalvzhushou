"""
AI Legal Assistant - Core Nodes

实现 LangGraph 工作流中的 5 个核心节点函数
"""

import re
from typing import Literal
from .state import AgentState, RetrievedDocument


MOCK_RETRIEVED_DOCS: list[RetrievedDocument] = [
    {
        "chunk_id": "labor_law_30",
        "text": "用人单位应当按时足额支付劳动者的工资，不得克扣或者无故拖欠。",
        "law_name": "中华人民共和国劳动法",
        "part": "第五章 工资",
        "chapter": "第三节 工资保障",
        "article_num": "第五十条",
        "effective_date": "2018-12-29",
        "category": "劳动法,工资支付",
        "score": 0.95
    },
    {
        "chunk_id": "labor_contract_law_46",
        "text": "用人单位有下列情形之一的，劳动者可以解除劳动合同：（一）未按照劳动合同约定提供劳动保护或者劳动条件的；（二）未及时足额支付劳动报酬的；...",
        "law_name": "中华人民共和国劳动合同法",
        "part": "第二章 劳动合同的订立",
        "chapter": "第三节 劳动合同的履行和变更",
        "article_num": "第三十八条",
        "effective_date": "2012-12-28",
        "category": "劳动合同法,劳动报酬",
        "score": 0.92
    },
    {
        "chunk_id": "labor_contract_law_47",
        "text": "经济补偿按劳动者在本单位工作的年限，每满一年支付一个月工资的标准向劳动者支付。",
        "law_name": "中华人民共和国劳动合同法",
        "part": "第五章 特别规定",
        "chapter": "第一节 集体合同",
        "article_num": "第四十七条",
        "effective_date": "2012-12-28",
        "category": "劳动合同法,经济补偿",
        "score": 0.88
    }
]


def intent_classifier(query: str) -> Literal["legal", "casual"]:
    """
    简单意图分类器（Mock实现）

    实际项目中应调用 LLM 进行意图识别
    """
    legal_keywords = [
        "怎么办", "违法吗", "合法吗", "赔偿", "补偿", "纠纷",
        "劳动", "合同", "债务", "侵权", "离婚", "继承",
        "老板", "工资", "拖欠", "开除", "辞职"
    ]
    for keyword in legal_keywords:
        if keyword in query:
            return "legal"
    return "casual"


def intent_analyzer(state: AgentState) -> AgentState:
    """
    Node 1: Intent_Analyzer (意图识别)

    判断用户输入是"日常闲聊"还是"法律咨询"

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 AgentState
    """
    user_query = state["user_query"]

    intent = intent_classifier(user_query)

    state["intent"] = intent

    return state


def query_rewriter(state: AgentState) -> AgentState:
    """
    Node 2: Query_Rewriter (检索词重写)

    将用户的大白话重写为专业的法律检索词

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 AgentState
    """
    user_query = state["user_query"]

    query_mapping = {
        "老板不发工资怎么办": "劳动法 拖欠工资 劳动监察 工资支付",
        "公司拖欠工资": "劳动合同法 工资支付 劳动仲裁 经济补偿",
        "被公司开除了": "劳动合同法 解除劳动合同 违法解除 赔偿金",
        "不签合同": "劳动合同法 劳动合同订立 双倍工资",
        "加班不给加班费": "劳动法 加班费 工作时间 工资报酬",
    }

    search_query = query_mapping.get(user_query, user_query)

    state["search_query"] = search_query

    return state


def legal_retriever(state: AgentState) -> AgentState:
    """
    Node 3: Legal_Retriever (法律文档检索)

    调用 RAG 系统，从向量数据库中提取最相关的 top-k 条法律条文

    这里使用 Mock 数据模拟检索结果

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 AgentState
    """
    search_query = state.get("search_query", state["user_query"])

    retrieved_docs = MOCK_RETRIEVED_DOCS.copy()

    state["retrieved_docs"] = retrieved_docs

    return state


def draft_generator(state: AgentState) -> AgentState:
    """
    Node 4: Draft_Generator (草稿生成)

    严格基于 retrieved_docs 和 user_query，
    按照"事实认定 -> 适用法条 -> 法律建议"的三段论结构生成初稿

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 AgentState
    """
    user_query = state["user_query"]
    retrieved_docs = state.get("retrieved_docs", [])

    if not retrieved_docs:
        draft = "抱歉，我暂时没有找到相关的法律条文来回答您的问题。建议您咨询专业律师。"
        state["draft_response"] = draft
        return state

    law_citations = []
    for doc in retrieved_docs:
        citation = f"《{doc['law_name']}》{doc['article_num']}：{doc['text']}"
        law_citations.append(citation)

    draft = f"""根据您的问题“{user_query}”，我为您提供了以下法律分析：

【事实认定】
您描述的情况涉及用人单位支付劳动报酬的问题。

【适用法条】
{chr(10).join(law_citations)}

【法律建议】
1. 首先，建议您保留相关证据，如工资条、考勤记录、劳动合同等；
2. 可以先与用人单位协商，要求按时足额支付工资；
3. 如协商不成，可向当地劳动监察部门投诉举报；
4. 也可以向劳动仲裁委员会申请劳动仲裁，维护自身合法权益；
5. 必要时，可通过诉讼途径解决争议。

请注意，以上仅供参考，具体情况建议咨询专业律师。
"""
    state["draft_response"] = draft

    return state


def hallucination_checker(state: AgentState) -> AgentState:
    """
    Node 5: Hallucination_Checker (幻觉与合规校验)

    由另一个独立的 LLM Prompt 检查 draft_response 是否超出了
    retrieved_docs 的范围，严禁主观编造法条

    这里使用 Mock 实现，实际项目中应调用独立的 LLM 进行校验

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 AgentState
    """
    draft_response = state.get("draft_response") or ""
    retrieved_docs = state.get("retrieved_docs", [])
    retry_count = state.get("retry_count", 0)

    has_hallucination = False
    error_message = None

    hallucination_keywords = ["有期徒刑", "拘役", "罚金", "刑事", "犯罪"]
    for keyword in hallucination_keywords:
        if keyword in draft_response and not any(keyword in (doc.get("text") or "") for doc in retrieved_docs):
            has_hallucination = True
            error_message = f"检测到可能超出检索范围的表述：{keyword}"

    if "编造" in draft_response or "虚构" in draft_response:
        has_hallucination = True
        error_message = "检测到可能存在编造内容的表述"

    if has_hallucination and retry_count < 3:
        state["error_flag"] = True
        state["error_message"] = error_message
        state["retry_count"] = retry_count + 1
    else:
        state["error_flag"] = False
        state["error_message"] = None
        state["final_response"] = draft_response

    return state


def casual_chat_handler(state: AgentState) -> AgentState:
    """
    闲聊处理节点

    当 Intent_Analyzer 判断为闲聊时，调用普通 LLM 进行回复

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 AgentState
    """
    user_query = state["user_query"]

    casual_responses = {
        "你好": "您好！我是 AI 法律助手，专注于为您提供专业的法律咨询服务。请问有什么法律问题可以帮您解答？",
        "你是谁": "我是一个基于大语言模型的法律助手，可以帮助您解答劳动法、合同法等领域的法律问题。",
    }

    response = casual_responses.get(user_query, f"您好！您说的是'{user_query}'，这看起来不像是法律问题。如果您有法律方面的疑问，请随时向我咨询！")

    state["final_response"] = response

    return state
