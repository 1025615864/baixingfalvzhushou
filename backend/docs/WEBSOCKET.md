# WebSocket 开发指南

## 概述

WebSocket 提供双向实时通信能力，用于实时消息推送、在线状态等功能。

## 连接管理

### 建立连接

```typescript
// src/contexts/WebSocketContext.tsx
import { useEffect, useRef, useState } from 'react';
import { client } from '@/api/client';

interface WebSocketMessage {
  type: string;
  payload: unknown;
}

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  const connect = (token: string) => {
    ws.current = new WebSocket(`${WS_URL}?token=${token}`);

    ws.current.onopen = () => setConnected(true);
    ws.current.onclose = () => setConnected(false);
    ws.current.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      handleMessage(message);
    };
  };

  const send = (type: string, payload: unknown) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type, payload }));
    }
  };

  return { connect, send, connected };
}
```

## 消息格式

### 发送消息

```typescript
// 发送聊天消息
socket.send(JSON.stringify({
  type: 'chat_message',
  payload: {
    conversation_id: '123',
    content: '你好',
  },
}));

// 订阅消息
socket.send(JSON.stringify({
  type: 'subscribe',
  payload: {
    channel: 'user_123',
  },
}));
```

### 接收消息

```typescript
// 处理消息
const handleMessage = (message: WebSocketMessage) => {
  switch (message.type) {
    case 'chat_message':
      // 处理聊天消息
      break;
    case 'notification':
      // 处理通知
      break;
    case 'online_status':
      // 处理在线状态
      break;
  }
};
```

## 心跳机制

```typescript
// 定时发送心跳
useEffect(() => {
  if (!connected) return;

  const heartbeat = setInterval(() => {
    ws.current?.send(JSON.stringify({ type: 'ping' }));
  }, 30000);

  return () => clearInterval(heartbeat);
}, [connected]);
```

## 重连机制

```typescript
const reconnect = () => {
  let attempts = 0;
  const maxAttempts = 5;

  const tryConnect = () => {
    if (attempts >= maxAttempts) {
      console.error('重连失败');
      return;
    }

    attempts++;
    setTimeout(() => {
      connect(token);
      if (!ws.current?.onopen) {
        tryConnect();
      }
    }, Math.min(1000 * Math.pow(2, attempts), 30000));
  };

  tryConnect();
};
```

## 后端实现

```python
# app/routers/websocket.py
from fastapi import WebSocket, WebSocketDisconnect

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handle_message(websocket, message)
    except WebSocketDisconnect:
        await remove_client(websocket)

async def handle_message(websocket: WebSocket, message: dict):
    if message['type'] == 'ping':
        await websocket.send_json({'type': 'pong'})
```
