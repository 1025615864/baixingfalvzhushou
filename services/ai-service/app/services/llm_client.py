import os
import asyncio
import time
import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from openai import AsyncOpenAI, OpenAIError
import httpx

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    latency_ms: int
    provider: str


class CircuitBreaker:
    """熔断器"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = CircuitState.CLOSED
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("Circuit breaker: OPEN -> HALF_OPEN")
        return self._state

    def record_success(self):
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._half_open_calls = 0

    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker: CLOSED -> OPEN (failures: {self._failure_count})")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        if self.state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpenError("Circuit breaker is HALF_OPEN, max calls reached")
            self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


class CircuitBreakerOpenError(Exception):
    pass


class LLMTimeoutError(Exception):
    pass


class DegradedResponse:
    """降级回答模板"""

    TEMPLATES = {
        "busy": "您好！当前咨询人数较多，AI助手响应可能有所延迟。您的问题已记录，我们会尽快为您解答。您也可以尝试拨打法律咨询热线：12348。",
        "unavailable": "抱歉，当前AI助手服务暂时不可用。请您稍后再试，或联系客服获取人工法律咨询服务。",
        "rate_limit": "您好！您今天的AI咨询次数已达上限，建议您明日再来使用或选择人工咨询服务。",
        "fallback": "抱歉，我目前无法针对您的具体问题给出准确的法律建议。建议您：1. 拨打12348法律咨询热线；2. 到当地法律援助中心咨询；3. 预约专业律师面谈。",
        "context_length": "您的问题内容较长，建议您拆分成多个简短问题分别咨询，这样我可以给出更准确的回答。",
    }

    @classmethod
    def get(cls, reason: str = "fallback") -> str:
        return cls.TEMPLATES.get(reason, cls.TEMPLATES["fallback"])


class ResilientLLMClient:
    """弹性LLM客户端 - 支持熔断、降级、多Provider"""

    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_threshold,
            recovery_timeout=settings.circuit_breaker_timeout
        )

        self.providers = [
            {
                "name": "primary",
                "base_url": settings.openai_base_url,
                "api_key": settings.openai_api_key,
                "model": settings.llm_model,
                "timeout": 30,
                "max_retries": 2,
            }
        ]

        if settings.secondary_llm_url:
            self.providers.append({
                "name": "secondary",
                "base_url": settings.secondary_llm_url,
                "api_key": settings.secondary_llm_key or "",
                "model": settings.secondary_llm_model,
                "timeout": 45,
                "max_retries": 1,
            })

        self._clients = {}
        self._initialize_clients()

    def _initialize_clients(self):
        for provider in self.providers:
            self._clients[provider["name"]] = AsyncOpenAI(
                api_key=provider["api_key"],
                base_url=provider["base_url"],
                timeout=httpx.Timeout(provider["timeout"])
            )

    async def _invoke_llm(
        self,
        provider: dict,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> LLMResponse:
        """调用单个LLM Provider"""
        start_time = time.time()
        client = self._clients.get(provider["name"])

        if not client:
            raise ValueError(f"Unknown provider: {provider['name']}")

        response = await client.chat.completions.create(
            model=provider["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        if stream:
            content = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content += chunk.choices[0].delta.content
        else:
            content = response.choices[0].message.content

        latency_ms = int((time.time() - start_time) * 1000)
        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0

        return LLMResponse(
            content=content,
            model=provider["model"],
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            provider=provider["name"]
        )

    async def _call_with_retry(
        self,
        provider: dict,
        messages: list,
        temperature: float,
        max_tokens: int,
        max_retries: int = 2
    ) -> LLMResponse:
        """带重试的LLM调用（指数退避）"""
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return await asyncio.wait_for(
                    self._invoke_llm(provider, messages, temperature, max_tokens),
                    timeout=provider["timeout"]
                )
            except asyncio.TimeoutError:
                last_error = LLMTimeoutError(f"Timeout on {provider['name']} (attempt {attempt + 1})")
                logger.warning(f"LLM timeout: {provider['name']}, attempt {attempt + 1}")
            except OpenAIError as e:
                last_error = e
                logger.warning(f"LLM error: {provider['name']}, attempt {attempt + 1}, error: {e}")

            if attempt < max_retries:
                wait_time = (2 ** attempt) * 0.5
                await asyncio.sleep(wait_time)

        raise last_error or LLMTimeoutError(f"All retries failed for {provider['name']}")

    async def call(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> LLMResponse:
        """弹性LLM调用 - 自动熔断+Provider切换+降级"""
        if system_prompt:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            full_messages = messages

        for provider in self.providers:
            try:
                result = await self.circuit_breaker.call(
                    self._call_with_retry,
                    provider,
                    full_messages,
                    temperature,
                    max_tokens,
                    max_retries=provider.get("max_retries", 2)
                )
                logger.info(f"LLM call succeeded via {provider['name']}, latency: {result.latency_ms}ms")
                return result

            except CircuitBreakerOpenError:
                logger.warning(f"Circuit breaker OPEN for {provider['name']}, trying next provider")
                continue
            except (LLMTimeoutError, OpenAIError) as e:
                logger.error(f"LLM call failed for {provider['name']}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error for {provider['name']}: {e}")
                continue

        logger.error("All LLM providers failed, returning degraded response")
        return self._degraded_response()

    def _degraded_response(self) -> LLMResponse:
        """返回降级回答"""
        return LLMResponse(
            content=DegradedResponse.get("fallback"),
            model="degraded",
            tokens_used=0,
            latency_ms=0,
            provider="none"
        )

    async def stream_call(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ):
        """流式LLM调用"""
        if system_prompt:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            full_messages = messages

        for provider in self.providers:
            try:
                client = self._clients.get(provider["name"])
                if not client:
                    continue

                response = await client.chat.completions.create(
                    model=provider["model"],
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                return response

            except Exception as e:
                logger.error(f"Stream call failed for {provider['name']}: {e}")
                continue

        return None


_resilient_llm_client: Optional[ResilientLLMClient] = None


def get_resilient_llm_client() -> ResilientLLMClient:
    global _resilient_llm_client
    if _resilient_llm_client is None:
        _resilient_llm_client = ResilientLLMClient()
    return _resilient_llm_client


async def call_llm_with_fallback(
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    system_prompt: Optional[str] = None
) -> LLMResponse:
    """便捷函数：带熔断降级的LLM调用"""
    client = get_resilient_llm_client()
    return await client.call(messages, temperature, max_tokens, system_prompt)