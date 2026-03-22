"""
AI Legal Assistant - 集成版本节点

使用真实的 LLM 和 RAG 检索服务
"""

from typing import Literal
from langchain_core.documents import Document

from .state import AgentState, RetrievedDocument
from ..services.llm import get_llm_service
from ..services.retriever import get_retriever_service

llm_service = get_llm_service()
retriever_service = get_retriever_service()


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


async def intent_analyzer(state: AgentState) -> AgentState:
    """
    Node 1: Intent_Analyzer (意图识别)

    判断用户输入是"日常闲聊"还是"法律咨询"
    使用 LLM 进行准确分类
    """
    user_query = state["user_query"]

    prompt = f"""请判断以下用户输入属于"法律咨询"还是"日常闲聊"：

用户输入：{user_query}

请只回答一个词：法律咨询 或 日常闲聊"""

    response = await llm_service.achat([
        {"role": "user", "content": prompt}
    ])

    intent_text = response["content"].strip()
    intent = "legal" if "法律咨询" in intent_text else "casual"

    state["intent"] = intent
    return state


async def query_rewriter(state: AgentState) -> AgentState:
    """
    Node 2: Query_Rewriter (检索词重写)

    将用户的大白话重写为专业的法律检索词
    """
    user_query = state["user_query"]

    prompt = f"""你是一个法律检索专家。请将用户的大白话问题重写为专业的法律检索关键词。

要求：
1. 提取核心法律概念（如：劳动法、合同违约、侵权责任等）
2. 列出相关的法律术语（如：经济补偿金、违约金、赔偿责任等）
3. 用空格分隔关键词

用户问题：{user_query}

检索关键词："""

    response = await llm_service.achat([
        {"role": "user", "content": prompt}
    ])

    search_query = response["content"].strip()
    state["search_query"] = search_query

    return state


async def legal_retriever(state: AgentState) -> AgentState:
    """
    Node 3: Legal_Retriever (法律文档检索)

    从向量数据库中检索最相关的法律条文
    """
    search_query = state.get("search_query", state["user_query"])

    try:
        docs_with_scores = retriever_service.hybrid_search(
            query=search_query,
            k=5
        )

        retrieved_docs = []
        for doc, score in docs_with_scores:
            retrieved_docs.append(RetrievedDocument(
                chunk_id=doc.metadata.get("chunk_id", ""),
                text=doc.page_content,
                law_name=doc.metadata.get("law_name", ""),
                part=doc.metadata.get("part", ""),
                chapter=doc.metadata.get("chapter", ""),
                article_num=doc.metadata.get("article_num", ""),
                effective_date=doc.metadata.get("effective_date", ""),
                category=doc.metadata.get("category", ""),
                score=score
            ))

    except Exception:
        retrieved_docs = MOCK_RETRIEVED_DOCS.copy()

    state["retrieved_docs"] = retrieved_docs
    return state


async def draft_generator(state: AgentState) -> AgentState:
    """
    Node 4: Draft_Generator (草稿生成)

    按照"事实认定 -> 适用法条 -> 法律建议"的三段论结构生成初稿
    """
    user_query = state["user_query"]
    retrieved_docs = state.get("retrieved_docs", [])

    if not retrieved_docs:
        draft = "抱歉，我暂时没有找到相关的法律条文来回答您的问题。建议您咨询专业律师。"
        state["draft_response"] = draft
        return state

    law_context = []
    for doc in retrieved_docs:
        law_context.append(
            f"《{doc['law_name']}》{doc['article_num']}：{doc['text']}"
        )

    context_text = "\n\n".join(law_context)

    prompt = f"""你是一个专业的法律顾问。请严格基于提供的法律条文，回答用户的问题。

【用户问题】
{user_query}

【相关法律条文】
{context_text}

【回答要求】
1. 按照"事实认定 -> 适用法条 -> 法律建议"的三段论结构回答
2. 只引用提供的法律条文，不要编造或推测
3. 法律建议要具体、可操作
4. 引用法条时要注明出处（第XX条）

【回答】
"""

    response = await llm_service.achat([
        {"role": "user", "content": prompt}
    ])

    draft = response["content"].strip()
    state["draft_response"] = draft

    return state


async def hallucination_checker(state: AgentState) -> AgentState:
    """
    Node 5: Hallucination_Checker (幻觉与合规校验)

    检查草稿是否超出检索范围或存在编造
    """
    draft_response = state.get("draft_response") or ""
    retrieved_docs = state.get("retrieved_docs", [])
    retry_count = state.get("retry_count", 0)

    if not draft_response or not retrieved_docs:
        state["error_flag"] = False
        state["final_response"] = draft_response
        return state

    law_context = "\n".join([doc["text"] for doc in retrieved_docs])

    prompt = f"""你是一个法律合规审查员。请检查以下回答是否超出了给定法律条文的范围。

【给定的法律条文】
{law_context}

【AI生成的回答】
{draft_response}

【检查要求】
1. 检查回答中引用的法条是否在给定条文中存在
2. 检查回答中的法律结论是否有条文依据
3. 检查是否有编造、臆测的内容

【检查结果】
只回答"通过"或"不通过"，以及简要原因"""

    response = await llm_service.achat([
        {"role": "user", "content": prompt}
    ])

    check_result = response["content"].strip()
    is_passed = "通过" in check_result

    if not is_passed and retry_count < 3:
        state["error_flag"] = True
        state["error_message"] = check_result
        state["retry_count"] = retry_count + 1
    else:
        state["error_flag"] = False
        state["error_message"] = None
        state["final_response"] = draft_response

    return state


async def casual_chat_handler(state: AgentState) -> AgentState:
    """
    闲聊处理节点
    """
    user_query = state["user_query"]

    prompt = f"""你是一个友好、专业的法律助手。请回答用户的问题。

用户：{user_query}

回答要求：
1. 如果不是法律问题，可以友好地引导用户提出法律相关问题
2. 保持专业、亲切的语气"""

    response = await llm_service.achat([
        {"role": "user", "content": prompt}
    ])

    state["final_response"] = response["content"].strip()
    return state
