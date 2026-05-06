"""WebSocket路由 - 支持实时Agent状态推送"""
import json
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from starlette.websockets import WebSocketState
import httpx

from app.services.chat_orchestrator import ChatOrchestrator, ChatRequest, get_chat_orchestrator
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter()

MAX_CONNECTIONS_PER_USER = 3


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str, user_id: int = 0):
        if user_id > 0:
            if self.user_connections.get(user_id, 0) >= MAX_CONNECTIONS_PER_USER:
                await websocket.close(code=1008, reason="达到最大连接数限制")
                return False

        await websocket.accept()
        async with self._lock:
            self.active_connections[client_id] = websocket
            if user_id > 0:
                self.user_connections[user_id] += 1
        logger.info(f"WebSocket connected: {client_id}, user_id: {user_id}")
        return True

    async def disconnect(self, client_id: str, user_id: int = 0):
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            if user_id > 0:
                self.user_connections[user_id] = max(0, self.user_connections.get(user_id, 1) - 1)
        logger.info(f"WebSocket disconnected: {client_id}, user_id: {user_id}")

    async def send_json(self, client_id: str, data: dict):
        async with self._lock:
            if client_id in self.active_connections:
                websocket = self.active_connections[client_id]
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(data)

    async def broadcast(self, data: dict):
        async with self._lock:
            for client_id, websocket in self.active_connections.items():
                if websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        await websocket.send_json(data)
                    except Exception as e:
                        logger.error(f"Broadcast error for {client_id}: {e}")


class AgentStateTracker:
    """Agent执行状态追踪器"""

    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self._execution_states: Dict[str, dict] = {}

    async def track_execution(
        self,
        client_id: str,
        session_id: str,
        user_query: str
    ):
        """追踪Agent执行状态"""
        self._execution_states[client_id] = {
            "session_id": session_id,
            "user_query": user_query,
            "started_at": datetime.now().isoformat(),
            "current_stage": "initializing",
            "stages": [],
            "final_response": "",
            "error": None
        }

        await self._send_stage(client_id, "initializing", {
            "message": "正在初始化对话..."
        })

    async def _send_stage(
        self,
        client_id: str,
        stage: str,
        data: dict = None,
        completed: bool = False
    ):
        """发送阶段状态"""
        if client_id in self._execution_states:
            state = self._execution_states[client_id]
            state["current_stage"] = stage

            stage_info = {
                "name": stage,
                "completed": completed,
                "timestamp": datetime.now().isoformat(),
                "data": data or {}
            }

            if completed:
                for s in state["stages"]:
                    if s["name"] == stage:
                        s["completed"] = True
                        s["duration_ms"] = data.get("duration_ms", 0) if data else 0
                        break
            else:
                state["stages"].append(stage_info)

            await self.manager.send_json(client_id, {
                "type": "stage_update",
                "stage": stage,
                "completed": completed,
                "data": data,
                "all_stages": state["stages"]
            })

    async def send_token(self, client_id: str, token: str):
        """发送Token"""
        if client_id in self._execution_states:
            state = self._execution_states[client_id]
            state["final_response"] += token

            await self.manager.send_json(client_id, {
                "type": "token",
                "content": token,
                "timestamp": datetime.now().isoformat()
            })

    async def send_done(
        self,
        client_id: str,
        response: str,
        sources: list = None,
        latency_ms: int = 0
    ):
        """发送完成状态"""
        if client_id in self._execution_states:
            state = self._execution_states[client_id]
            state["final_response"] = response
            state["completed_at"] = datetime.now().isoformat()

            total_duration = 0
            for stage in state["stages"]:
                if stage.get("completed") and stage.get("duration_ms"):
                    total_duration += stage["duration_ms"]

            await self.manager.send_json(client_id, {
                "type": "done",
                "response": response,
                "sources": sources or [],
                "latency_ms": latency_ms,
                "total_stages": len(state["stages"]),
                "timestamp": datetime.now().isoformat()
            })

            del self._execution_states[client_id]

    async def send_error(self, client_id: str, error: str):
        """发送错误状态"""
        if client_id in self._execution_states:
            self._execution_states[client_id]["error"] = error

        await self.manager.send_json(client_id, {
            "type": "error",
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

        if client_id in self._execution_states:
            del self._execution_states[client_id]


connection_manager = ConnectionManager()
agent_tracker: Optional[AgentStateTracker] = None


def get_agent_tracker() -> AgentStateTracker:
    global agent_tracker
    if agent_tracker is None:
        agent_tracker = AgentStateTracker(connection_manager)
    return agent_tracker


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
    client_id: Optional[str] = Query(default=None)
):
    """WebSocket聊天端点 - 需要JWT认证"""
    import uuid

    user_id = 0
    if token:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{settings.user_service_url}/api/v1/auth/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    user_data = response.json()
                    user_id = user_data.get("user_id", 0)
                else:
                    await websocket.close(code=4001, reason="无效的认证令牌")
                    return
        except Exception as e:
            logger.error(f"JWT verification failed: {e}")
            await websocket.close(code=4001, reason="认证服务不可用")
            return
    else:
        await websocket.close(code=4001, reason="需要提供认证令牌")
        return

    client_id = client_id or str(uuid.uuid4())

    connected = await connection_manager.connect(websocket, client_id, user_id)
    if not connected:
        return

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "chat":
                user_query = data.get("message", "")
                session_id = data.get("session_id")

                orchestrator = get_chat_orchestrator()
                tracker = get_agent_tracker()

                await tracker.track_execution(client_id, session_id or "", user_query)

                try:
                    request = ChatRequest(
                        user_id=user_id,
                        message=user_query,
                        session_id=session_id
                    )

                    collected_response = ""
                    sources = []

                    async for event in orchestrator.chat_stream(request):
                        event_type = event.get("event")

                        if event_type == "stage":
                            stage = event.get("stage", "")
                            status = event.get("status", "")
                            stage_data = event.get("data", {})

                            await tracker._send_stage(
                                client_id,
                                stage,
                                stage_data,
                                completed=(status == "completed")
                            )

                        elif event_type == "token":
                            token_content = event.get("content", "")
                            collected_response += token_content
                            await tracker.send_token(client_id, token_content)

                        elif event_type == "done":
                            sources = event.get("sources", [])

                    await tracker.send_done(
                        client_id,
                        collected_response,
                        sources=sources
                    )

                except Exception as e:
                    logger.error(f"WebSocket chat error: {e}")
                    await tracker.send_error(client_id, str(e))

            elif data.get("type") == "ping":
                await connection_manager.send_json(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await connection_manager.disconnect(client_id, user_id)


@router.websocket("/ws/status")
async def websocket_status(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None)
):
    """WebSocket状态订阅端点 - 需要JWT认证"""
    import uuid

    user_id = 0
    if token:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{settings.user_service_url}/api/v1/auth/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    user_data = response.json()
                    user_id = user_data.get("user_id", 0)
                else:
                    await websocket.close(code=4001, reason="无效的认证令牌")
                    return
        except Exception as e:
            logger.error(f"JWT verification failed: {e}")
            await websocket.close(code=4001, reason="认证服务不可用")
            return
    else:
        await websocket.close(code=4001, reason="需要提供认证令牌")
        return

    client_id = str(uuid.uuid4())

    connected = await connection_manager.connect(websocket, client_id, user_id)
    if not connected:
        return

    try:
        await connection_manager.send_json(client_id, {
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await connection_manager.send_json(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket status error: {e}")
        await connection_manager.disconnect(client_id, user_id)
