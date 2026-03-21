"""
LLM 调用服务 - 支持 OpenAI 兼容 API

提供同步/异步、流式/非流式调用
"""

from typing import Optional, List, Dict, Any, Callable, AsyncIterator
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from ..config.settings import get_settings

settings = get_settings()


class LLMService:
    """
    LLM 调用服务

    支持：
    - OpenAI API 兼容接口
    - 流式输出
    - 函数调用
    - 响应缓存
    """

    def __init__(self):
        self._llm: Optional[ChatOpenAI] = None

    @property
    def llm(self) -> ChatOpenAI:
        """延迟初始化 LLM"""
        if self._llm is None:
            self._llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.llm_model,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                streaming=False
            )
        return self._llm

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        同步聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            stream: 是否流式输出
            **kwargs: 其他参数

        Returns:
            {"content": str, "model": str, "tokens": int}
        """
        langchain_messages = self._convert_messages(messages)

        if stream:
            return self._stream_chat(langchain_messages)
        else:
            response = self.llm.invoke(langchain_messages)
            return {
                "content": response.content,
                "model": response.response_metadata.get("model", settings.llm_model),
                "tokens": response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
            }

    def _stream_chat(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """流式聊天"""
        response = self.llm.invoke(messages)
        content_chunks = []

        for chunk in response:
            if hasattr(chunk, "content"):
                content_chunks.append(chunk.content)

        return {
            "content": "".join(content_chunks),
            "model": settings.llm_model,
            "tokens": 0
        }

    async def achat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        异步聊天请求

        Args:
            messages: 消息列表
            stream: 是否流式输出
            **kwargs: 其他参数

        Returns:
            {"content": str, "model": str, "tokens": int}
        """
        langchain_messages = self._convert_messages(messages)

        if stream:
            return await self._astream_chat(langchain_messages)
        else:
            response = await self.llm.ainvoke(langchain_messages)
            return {
                "content": response.content,
                "model": response.response_metadata.get("model", settings.llm_model),
                "tokens": response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
            }

    async def _astream_chat(
        self,
        messages: List[BaseMessage]
    ) -> Dict[str, Any]:
        """异步流式聊天"""
        response = self.llm.stream(messages)
        content_chunks = []

        async for chunk in response:
            if hasattr(chunk, "content"):
                content_chunks.append(chunk.content)

        return {
            "content": "".join(content_chunks),
            "model": settings.llm_model,
            "tokens": 0
        }

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """转换消息格式"""
        result = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                result.append(SystemMessage(content=content))
            elif role == "user":
                result.append(HumanMessage(content=content))
            else:
                result.append(HumanMessage(content=content))

        return result

    async def astream_response(
        self,
        messages: List[Dict[str, str]],
        callback: Optional[Callable[[str], None]] = None
    ) -> AsyncIterator[str]:
        """
        异步流式响应（用于 Server-Sent Events）

        Args:
            messages: 消息列表
            callback: 可选的回调函数

        Yields:
            响应内容片段
        """
        langchain_messages = self._convert_messages(messages)

        response = await self.llm.astream(langchain_messages)

        async for chunk in response:
            if hasattr(chunk, "content") and chunk.content:
                if callback:
                    callback(chunk.content)
                yield chunk.content


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """获取 LLM 服务单例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
