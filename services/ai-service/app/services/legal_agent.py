"""法律助手Agent服务

核心设计原则：
1. 独立性：Agent逻辑与外部API解耦，可独立测试和部署
2. 可迭代：支持Prompt版本管理，AB测试，灰度发布
3. 可观测：完整日志记录，质量指标监控，异常告警
4. 可维护：配置驱动，规则引擎，易于调整
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import AISession, AIMessage, AgentConfig
from ..config.settings import get_settings

settings = get_settings()


class CircuitBreaker:
    """熔断器：防止级联故障"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.is_open = False

    def record_success(self):
        self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow().timestamp()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True

    def can_try(self) -> bool:
        if not self.is_open:
            return True
        elapsed = datetime.utcnow().timestamp() - self.last_failure_time
        if elapsed > self.timeout:
            self.is_open = False
            self.failure_count = 0
            return True
        return False


class LegalAgentService:
    """法律助手Agent服务

    核心组件：
    - Agent配置加载（支持版本管理）
    - Prompt模板渲染
    - RAG检索
    - 模型路由与熔断
    - 会话管理
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_threshold,
            timeout=settings.circuit_breaker_timeout,
        )

    async def _get_active_agent_config(self) -> Optional[AgentConfig]:
        """获取当前激活的Agent配置"""
        result = await self.db.execute(
            select(AgentConfig)
            .where(AgentConfig.name == "legal_assistant")
            .where(AgentConfig.is_active == True)
            .order_by(AgentConfig.updated_at.desc())
        )
        return result.scalar_one_or_none()

    async def _get_or_create_session(
        self,
        user_id: int,
        session_id: Optional[int] = None
    ) -> AISession:
        """获取或创建会话"""
        if session_id:
            result = await self.db.execute(
                select(AISession).where(AISession.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                return session

        session = AISession(
            user_id=user_id,
            session_type="legal",
            status="active",
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """调用LLM（支持多模型路由和熔断）"""
        if not self.circuit_breaker.can_try():
            return {
                "content": "服务暂时不可用，请稍后再试",
                "model": "unavailable",
                "sources": [],
            }

        try:
            # 模拟LLM调用
            response = {
                "content": f"这是AI的回复: {messages[-1]['content'] if messages else ''}",
                "model": model or settings.openai_model,
                "tokens": 100,
            }
            self.circuit_breaker.record_success()
            return response

        except Exception as e:
            self.circuit_breaker.record_failure()
            return {
                "content": "AI服务暂时不可用，请稍后再试",
                "model": "error",
                "sources": [],
            }

    async def chat(
        self,
        user_id: int,
        message: str,
        session_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """处理用户对话"""
        # 获取会话
        session = await self._get_or_create_session(user_id, session_id)

        # 保存用户消息
        user_msg = AIMessage(
            session_id=session.id,
            role="user",
            content=message,
        )
        self.db.add(user_msg)

        # 获取Agent配置
        agent_config = await self._get_active_agent_config()

        # 构建Prompt（使用配置的模板）
        system_prompt = (
            agent_config.prompt_template if agent_config
            else "你是一个法律助手，请根据用户提供的问题给出专业的法律建议。"
        )

        # 获取历史消息
        result = await self.db.execute(
            select(AIMessage)
            .where(AIMessage.session_id == session.id)
            .order_by(AIMessage.created_at)
        )
        history = result.scalars().all()

        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:  # 最近10条
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": message})

        # 调用LLM
        response = await self._call_llm(messages)

        # 保存AI回复
        ai_msg = AIMessage(
            session_id=session.id,
            role="assistant",
            content=response["content"],
            model=response["model"],
            tokens_used=response.get("tokens", 0),
        )
        self.db.add(ai_msg)
        await self.db.commit()

        return {
            "session_id": session.id,
            "message": response["content"],
            "model": response["model"],
            "sources": response.get("sources", []),
        }

    async def get_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户会话列表"""
        result = await self.db.execute(
            select(AISession)
            .where(AISession.user_id == user_id)
            .order_by(AISession.updated_at.desc())
        )
        sessions = result.scalars().all()
        return [
            {
                "id": s.id,
                "user_id": s.user_id,
                "session_type": s.session_type,
                "title": s.title,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in sessions
        ]

    async def get_history(self, session_id: int) -> List[Dict[str, Any]]:
        """获取会话历史"""
        result = await self.db.execute(
            select(AIMessage)
            .where(AIMessage.session_id == session_id)
            .order_by(AIMessage.created_at)
        )
        messages = result.scalars().all()
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
