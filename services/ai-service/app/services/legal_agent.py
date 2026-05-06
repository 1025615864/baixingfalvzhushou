"""法律助手Agent - LangGraph状态机工作流 v2 - 支持流式"""
import json
import asyncio
import time
import logging
from typing import Annotated, Literal, TypedDict, AsyncIterator, Optional, Any
from collections import deque

from langgraph.graph import StateGraph, END
from langgraph.types import StreamWriter

from app.config.settings import get_settings
from app.services.llm_client import call_llm_with_fallback, LLMResponse, DegradedResponse, get_resilient_llm_client
from app.services.metrics import get_metrics_collector

settings = get_settings()
logger = logging.getLogger(__name__)


class StreamingBuffer:
    """流式缓冲区 - 用于在节点和事件循环之间传递tokens"""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._done = False
        self._tokens = []

    async def put(self, token: str):
        await self._queue.put(token)

    async def put_all(self, tokens: list):
        for token in tokens:
            await self.put(token)

    def done(self):
        self._done = True

    async def aiter(self):
        while not self._done or not self._queue.empty():
            try:
                token = await asyncio.wait_for(self._queue.get(), timeout=0.01)
                self._tokens.append(token)
                yield token
            except asyncio.TimeoutError:
                if self._done:
                    break

    def get_tokens(self) -> list:
        return self._tokens


_streaming_buffer: Optional[StreamingBuffer] = None


def get_streaming_buffer() -> Optional[StreamingBuffer]:
    return _streaming_buffer


def set_streaming_buffer(buffer: Optional[StreamingBuffer]):
    global _streaming_buffer
    _streaming_buffer = buffer


class AgentState(TypedDict):
    """Agent全局状态定义"""
    user_query: str
    chat_history: list[dict[str, str]]
    intent: str
    search_query: str
    retrieved_docs: list[dict]
    draft_response: str
    final_response: str
    error_flag: bool
    hallucination_feedback: str
    iteration_count: int
    stream_mode: bool
    writer: Optional[Any]
    prompt_tokens: int
    completion_tokens: int
    model_name: str


CHITCHAT_RESPONSES = [
    "你好！我是法律助手。如果你有法律相关的问题，欢迎随时向我咨询，比如劳动纠纷、合同问题、婚姻家庭等方面的法律咨询。",
    "今天天气真不错！有什么法律问题我可以帮你的吗？",
    "很高兴和你聊天！不过我更擅长解决法律问题哦，有什么法律困扰可以告诉我。"
]


class Stage:
    STAGE_INTENT = "analyzing_intent"
    STAGE_QUERY_REWRITE = "rewriting_query"
    STAGE_RETRIEVAL = "retrieving_knowledge"
    STAGE_GENERATION = "generating"
    STAGE_HALLUCINATION_CHECK = "checking_hallucination"
    STAGE_DONE = "done"


async def send_stage_event(writer: Optional[StreamWriter], stage: str, data: dict = None):
    """发送阶段事件"""
    if writer:
        writer({
            "event": "stage",
            "stage": stage,
            "data": data or {}
        })


async def send_token_event(writer: Optional[StreamWriter], token: str):
    """发送token事件"""
    if writer:
        writer({
            "event": "token",
            "content": token
        })


def Intent_Analyzer(state: AgentState) -> AgentState:
    """Node 1: 意图识别 - 判断是闲聊还是法律咨询"""
    start_time = time.time()
    user_query = state["user_query"]
    legal_keywords = ["法律", "劳动", "合同", "工资", "赔偿", "纠纷", "权益", "违法",
                      "仲裁", "起诉", "律师", "法院", "法条", "规定", "老板", "公司",
                      "离婚", "继承", "房产", "债务", "侵权", "工伤", "补偿", "赔偿"]

    is_legal = any(keyword in user_query for keyword in legal_keywords)

    state["intent"] = "legal" if is_legal else "chitchat"

    latency_ms = int((time.time() - start_time) * 1000)
    try:
        metrics = get_metrics_collector()
        asyncio.create_task(metrics.record_node_latency("Intent_Analyzer", latency_ms))
    except Exception:
        pass

    return state


def Query_Rewriter(state: AgentState) -> AgentState:
    """Node 2: 检索词重写 - 将大白话转换为专业法律检索词"""
    start_time = time.time()
    user_query = state["user_query"]

    rewrite_prompts = {
        "不发工资": "劳动法 拖欠工资 劳动报酬 解除劳动合同 经济补偿",
        "老板不给钱": "劳动合同 拖欠报酬 违法解除 劳动仲裁 经济补偿金",
        "被开除": "违法解除劳动合同 赔偿金 劳动仲裁 程序",
        "工伤": "工伤认定 工伤赔偿 劳动能力鉴定",
        "不签合同": "未签劳动合同 双倍工资 劳动仲裁",
        "加班费": "加班工资 延时加班 休息日加班 法定节假日加班",
        "被辞退": "违法解除劳动合同 赔偿金 劳动仲裁 程序 正当理由",
        "拖欠工资": "拖欠工资 劳动报酬 用人单位支付 经济补偿",
        "合同纠纷": "合同违约 合同解除 损害赔偿 合同效力",
        "离婚": "离婚 夫妻共同财产分割 子女抚养权 婚姻无效",
        "交通事故": "交通事故责任 人身损害赔偿 保险理赔",
    }

    search_query = user_query
    for colloquial, legal in rewrite_prompts.items():
        if colloquial in user_query:
            search_query = legal
            break

    if state["intent"] == "legal" and search_query == user_query:
        search_query = f"{user_query} 法律依据 规定 条款"

    state["search_query"] = search_query

    latency_ms = int((time.time() - start_time) * 1000)
    try:
        metrics = get_metrics_collector()
        asyncio.create_task(metrics.record_node_latency("Query_Rewriter", latency_ms))
    except Exception:
        pass

    return state


async def Legal_Retriever(state: AgentState) -> AgentState:
    """Node 3: 法律文档检索 - 三级RAG Fallback"""
    from app.services.rag_retrieval import retrieve_with_fallback

    start_time = time.time()
    search_query = state["search_query"]
    writer = state.get("writer")
    existing_docs = state.get("retrieved_docs", [])

    await send_stage_event(writer, Stage.STAGE_RETRIEVAL, {"status": "searching", "query": search_query})

    if existing_docs and len(existing_docs) >= 2:
        latency_ms = int((time.time() - start_time) * 1000)
        try:
            metrics = get_metrics_collector()
            await metrics.record_rag_query(
                cached=True,
                level="pre_retrieved",
                latency_ms=latency_ms,
                similarity=max([d.get("distance", 1.0) for d in existing_docs]) if existing_docs else 0.0
            )
            await metrics.record_node_latency("Legal_Retriever", latency_ms)
        except Exception:
            pass
        return {"retrieved_docs": existing_docs}

    try:
        result = await retrieve_with_fallback(query=search_query, intent=state["intent"], top_k=5)

        docs = []
        for doc in result.docs:
            docs.append({
                "id": doc.id,
                "text": doc.content,
                "metadata": doc.metadata,
                "source": doc.source,
                "distance": 1.0 - doc.similarity
            })

        state["retrieved_docs"] = docs

        latency_ms = int((time.time() - start_time) * 1000)
        try:
            metrics = get_metrics_collector()
            await metrics.record_rag_query(
                cached=False,
                level=result.retrieval_level,
                latency_ms=latency_ms,
                similarity=max([d.similarity for d in result.docs]) if result.docs else 0.0
            )
            await metrics.record_node_latency("Legal_Retriever", latency_ms)
        except Exception:
            pass

        await send_stage_event(writer, Stage.STAGE_RETRIEVAL, {
            "status": "completed",
            "count": len(docs),
            "level": result.retrieval_level,
            "latency_ms": result.latency_ms
        })

    except Exception as e:
        state["retrieved_docs"] = []
        await send_stage_event(writer, Stage.STAGE_RETRIEVAL, {"status": "error", "error": str(e)})

    return state


async def Draft_Generator(state: AgentState) -> AgentState:
    """Node 4: 草稿生成 - 使用ResilientLLM"""
    start_time = time.time()
    user_query = state["user_query"]
    retrieved_docs = state["retrieved_docs"]
    hallucination_feedback = state.get("hallucination_feedback", "")
    iteration = state.get("iteration_count", 0)
    writer = state.get("writer")

    await send_stage_event(writer, Stage.STAGE_GENERATION, {"status": "started"})

    docs_context = "\n\n".join([
        f"【法条{i+1}】{doc['metadata'].get('law_name', '未知')} {doc['metadata'].get('article_num', '')}\n{doc.get('text', doc.get('content', ''))}"
        for i, doc in enumerate(retrieved_docs)
    ]) if retrieved_docs else "（未检索到相关法律条文）"

    system_prompt = """你是一位专业的法律助手，擅长根据法律条文为用户提供准确的法律咨询。
你必须严格基于提供的法律条文来回答问题，严禁编造或引用不在参考范围内的法律条文。
回答结构必须遵循"事实认定 -> 适用法条 -> 法律建议"的三段论格式。"""

    if hallucination_feedback:
        user_prompt = f"""{hallucination_feedback}

请重新生成回答，严格基于以下法律条文：

{ docs_context }

用户问题：{user_query}

请按以下格式重新生成回答：
【事实认定】
根据您的描述...

【适用法条】
1. [法条名称] [条款号]：[相关内容]
2. ...

【法律建议】
1. 具体建议
2. ...
"""
    else:
        user_prompt = f"""基于以下法律条文回答用户问题：

{docs_context}

用户问题：{user_query}

请按以下格式生成回答：
【事实认定】
根据您的描述...

【适用法条】
1. [法条名称] [条款号]：[相关内容]
2. ...

【法律建议】
1. 具体建议
2. ...
"""

    try:
        response: LLMResponse = await call_llm_with_fallback(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )

        state["draft_response"] = response.content

        latency_ms = int((time.time() - start_time) * 1000)
        try:
            metrics = get_metrics_collector()
            await metrics.record_llm_call(
                success=True,
                latency_ms=response.latency_ms or latency_ms,
                tokens_used=response.tokens_used or 0
            )
            await metrics.record_node_latency("Draft_Generator", latency_ms)
        except Exception:
            pass

        await send_stage_event(writer, Stage.STAGE_GENERATION, {
            "status": "completed",
            "tokens": response.tokens_used or 0,
            "latency_ms": response.latency_ms or latency_ms
        })

    except Exception as e:
        state["draft_response"] = f"生成回答时出错：{str(e)}"
        try:
            metrics = get_metrics_collector()
            await metrics.record_llm_call(success=False, latency_ms=int((time.time() - start_time) * 1000))
            await metrics.record_node_latency("Draft_Generator", int((time.time() - start_time) * 1000))
        except Exception:
            pass
        await send_stage_event(writer, Stage.STAGE_GENERATION, {"status": "error", "error": str(e)})

    return state


async def Hallucination_Checker(state: AgentState) -> AgentState:
    """Node 5: 幻觉与合规校验"""
    start_time = time.time()
    draft_response = state["draft_response"]
    retrieved_docs = state["retrieved_docs"]
    writer = state.get("writer")

    await send_stage_event(writer, Stage.STAGE_HALLUCINATION_CHECK, {"status": "checking"})

    docs_context = "\n".join([
        f"- {doc['metadata'].get('law_name', '未知')} {doc['metadata'].get('article_num', '')}: {doc.get('text', doc.get('content', ''))[:100]}..."
        for doc in retrieved_docs
    ]) if retrieved_docs else "（无参考法条，使用通用法律知识）"

    if not retrieved_docs or all(not doc.get('text', doc.get('content', '')) for doc in retrieved_docs):
        state["final_response"] = "抱歉，我目前无法检索到相关的法律条文信息。但根据一般的劳动法常识：\n\n1. 用人单位应当按时足额支付劳动者工资\n2. 拖欠工资可向劳动监察部门投诉\n3. 可申请劳动仲裁维护权益\n4. 建议保留相关证据（工资条、劳动合同等）\n\n如需准确的法律建议，请稍后重试或咨询专业律师。"
        state["error_flag"] = False
        state["hallucination_feedback"] = ""
        state["iteration_count"] = 1
        return state

    system_prompt = """你是一位严谨的法律合规审核员，负责检查法律回答是否存在幻觉或超出参考范围的问题。
你必须严格检查回答中引用的法律条文是否在参考范围内。"""

    user_prompt = f"""请检查以下法律回答是否严格基于提供的法律条文，是否存在幻觉或主观编造：

【待检查回答】
{draft_response}

【参考法律条文】
{docs_context}

请仔细检查：
1. 回答中引用的法律条文是否都在上述参考范围内？
2. 回答中是否有任何主观编造的内容？
3. 回答中的法律建议是否合理且有据可依？

请按以下JSON格式返回检查结果（只需返回JSON，不要有其他内容）：
{{
    "has_hallucination": true/false,
    "issues": ["问题1描述", "问题2描述"]（如果没有问题则为空数组）,
    "feedback": "如果有问题，请简要说明需要修改的方向"
}}"""

    try:
        response: LLMResponse = await call_llm_with_fallback(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=500
        )

        result_text = response.content

        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result_data = json.loads(json_match.group())
            has_hallucination = result_data.get("has_hallucination", False)
            issues = result_data.get("issues", [])
            feedback = result_data.get("feedback", "")
        else:
            has_hallucination = False
            issues = []
            feedback = ""

        latency_ms = int((time.time() - start_time) * 1000)
        try:
            metrics = get_metrics_collector()
            await metrics.record_llm_call(
                success=True,
                latency_ms=response.latency_ms or latency_ms,
                tokens_used=response.tokens_used or 0
            )
            await metrics.record_node_latency("Hallucination_Checker", latency_ms)
        except Exception:
            pass

    except Exception as e:
        has_hallucination = False
        issues = []
        feedback = ""
        try:
            metrics = get_metrics_collector()
            await metrics.record_llm_call(success=False, latency_ms=int((time.time() - start_time) * 1000))
        except Exception:
            pass

    current_iteration = state.get("iteration_count", 0) + 1

    await send_stage_event(writer, Stage.STAGE_HALLUCINATION_CHECK, {
        "status": "completed",
        "has_hallucination": has_hallucination,
        "iteration": current_iteration
    })

    if has_hallucination and issues and current_iteration < 3:
        state["error_flag"] = True
        state["hallucination_feedback"] = f"【幻觉检测警告】\n" + "\n".join(f"- {issue}" for issue in issues)
        state["hallucination_feedback"] += f"\n\n{feedback}\n\n请严格基于检索到的法条重新生成回答。"
        state["iteration_count"] = current_iteration
        state["final_response"] = ""
    else:
        state["error_flag"] = False
        state["hallucination_feedback"] = ""
        state["final_response"] = draft_response
        state["iteration_count"] = current_iteration

    return state


def route_after_intent(state: AgentState) -> Literal["Query_Rewriter", "chitchat_end"]:
    """意图识别后的路由"""
    if state["intent"] == "legal":
        return "Query_Rewriter"
    return "chitchat_end"


def route_after_hallucination(state: AgentState) -> Literal["Draft_Generator", END]:
    """幻觉校验后的路由"""
    if state["error_flag"] and state["iteration_count"] < 3:
        return "Draft_Generator"
    return END


def chitchat_response(state: AgentState) -> AgentState:
    """闲聊回复节点"""
    start_time = time.time()
    import random
    response = random.choice(CHITCHAT_RESPONSES)
    state["final_response"] = response

    latency_ms = int((time.time() - start_time) * 1000)
    try:
        metrics = get_metrics_collector()
        asyncio.create_task(metrics.record_node_latency("chitchat_response", latency_ms))
    except Exception:
        pass

    return state


def build_legal_agent_graph() -> StateGraph:
    """构建法律助手状态机图"""
    graph = StateGraph(AgentState)

    graph.add_node("Intent_Analyzer", Intent_Analyzer)
    graph.add_node("Query_Rewriter", Query_Rewriter)
    graph.add_node("Legal_Retriever", Legal_Retriever)
    graph.add_node("Draft_Generator", Draft_Generator)
    graph.add_node("Hallucination_Checker", Hallucination_Checker)
    graph.add_node("chitchat_response", chitchat_response)

    graph.set_entry_point("Intent_Analyzer")

    graph.add_conditional_edges(
        "Intent_Analyzer",
        route_after_intent,
        {
            "Query_Rewriter": "Query_Rewriter",
            "chitchat_end": "chitchat_response"
        }
    )

    graph.add_edge("Query_Rewriter", "Legal_Retriever")
    graph.add_edge("Legal_Retriever", "Draft_Generator")
    graph.add_edge("Draft_Generator", "Hallucination_Checker")

    graph.add_conditional_edges(
        "Hallucination_Checker",
        route_after_hallucination,
        {
            "Draft_Generator": "Draft_Generator",
            END: END
        }
    )

    graph.add_edge("chitchat_response", END)

    return graph.compile()


legal_agent_graph = build_legal_agent_graph()


async def stream_legal_agent(
    user_query: str,
    chat_history: list[dict[str, str]] = None,
    session_id: str = None,
    retrieved_docs: list[dict] = None
) -> AsyncIterator[dict]:
    """流式法律助手 - 支持中间状态输出

    注意: 由于LangGraph的on_llm_stream事件限制，token级流式暂不可用。
    当前通过stage事件提供粗粒度流式反馈。
    """

    initial_state: AgentState = {
        "user_query": user_query,
        "chat_history": chat_history or [],
        "intent": "",
        "search_query": "",
        "retrieved_docs": retrieved_docs or [],
        "draft_response": "",
        "final_response": "",
        "error_flag": False,
        "hallucination_feedback": "",
        "iteration_count": 0,
        "stream_mode": True,
        "writer": None
    }

    async for event in legal_agent_graph.astream_events(initial_state, version="v2"):
        node_name = event.get("name")
        event_type = event.get("event")

        if event_type == "on_chain_start":
            if node_name == "Intent_Analyzer":
                yield {"stage": Stage.STAGE_INTENT, "status": "started"}
            elif node_name == "Query_Rewriter":
                yield {"stage": Stage.STAGE_QUERY_REWRITE, "status": "started"}
            elif node_name == "Legal_Retriever":
                yield {"stage": Stage.STAGE_RETRIEVAL, "status": "started"}
            elif node_name == "Draft_Generator":
                yield {"stage": Stage.STAGE_GENERATION, "status": "started"}
            elif node_name == "Hallucination_Checker":
                yield {"stage": Stage.STAGE_HALLUCINATION_CHECK, "status": "started"}

        elif event_type == "on_chain_end":
            if isinstance(event.get("data"), dict):
                data = event["data"]

                if node_name == "Intent_Analyzer":
                    intent = data.get("intent", "")
                    if not intent:
                        output_data = data.get("output", {})
                        intent = output_data.get("intent", "") if isinstance(output_data, dict) else ""
                    yield {"stage": Stage.STAGE_INTENT, "status": "completed", "intent": intent}

                elif node_name == "Query_Rewriter":
                    query = data.get("search_query", "")
                    yield {"stage": Stage.STAGE_QUERY_REWRITE, "status": "completed", "query": query}

                elif node_name == "Legal_Retriever":
                    docs = data.get("retrieved_docs", [])
                    yield {"stage": Stage.STAGE_RETRIEVAL, "status": "completed", "count": len(docs)}

                elif node_name == "Draft_Generator":
                    yield {"stage": Stage.STAGE_GENERATION, "status": "completed"}

                elif node_name == "Hallucination_Checker":
                    output_data = {}
                    if isinstance(data, dict):
                        output_data = data.get("output", {})
                    final = output_data.get("final_response", "") if isinstance(output_data, dict) else ""
                    error_flag = output_data.get("error_flag", False) if isinstance(output_data, dict) else False
                    iteration = output_data.get("iteration_count", 0) if isinstance(output_data, dict) else 0
                    yield {"stage": Stage.STAGE_HALLUCINATION_CHECK, "status": "completed"}
                    if not error_flag:
                        yield {"stage": Stage.STAGE_DONE, "response": final, "iteration": iteration}

                elif node_name == "chitchat_response":
                    response = data.get("final_response", "")
                    if not response:
                        output_data = data.get("output", {})
                        response = output_data.get("final_response", "") if isinstance(output_data, dict) else ""
                    yield {"stage": Stage.STAGE_DONE, "response": response}

    yield {"stage": Stage.STAGE_DONE, "status": "complete"}


if __name__ == "__main__":
    print("=" * 60)
    print("法律助手 Agent - LangGraph 状态机 v2 (流式支持)")
    print("=" * 60)

    async def test_stream():
        query = "老板不发工资怎么办？"
        print(f"\n用户问题: {query}")
        print("-" * 40)

        async for event in stream_legal_agent(query):
            if "stage" in event:
                print(f"[{event['stage']}] {event['status']}")
            if "token" in event:
                print(event["token"], end="", flush=True)
            if "response" in event:
                print(f"\n[最终回答]\n{event['response']}")

    import asyncio
    asyncio.run(test_stream())
