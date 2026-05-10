// ============================================
// WebSocket 服务 - 连接管理、心跳、重连
// ============================================

import { logger } from '@/shared/lib/logger';

import {
  WebSocketConfig,
  WebSocketConnectionState,
  WebSocketConnectionStatus,
  WebSocketMessage,
  WebSocketMessageType,
  QueuedMessage,
  WebSocketEventHandlers,
} from '../types/websocket';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

const DEFAULT_CONFIG: Required<WebSocketConfig> = {
  url: '',
  reconnectInterval: 1000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
  connectionTimeout: 10000,
  autoReconnect: true,
  enableHeartbeat: true,
  token: '',
  protocols: [],
  initialMessage: undefined,
};

export class WebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private handlers: WebSocketEventHandlers;
  private status: WebSocketConnectionStatus;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private connectionTimeoutTimer: ReturnType<typeof setTimeout> | null = null;
  private messageQueue: QueuedMessage[] = [];
  private isManualClose = false;
  private lastPongTime = 0;
  private pingStartTime = 0;

  constructor(config: WebSocketConfig, handlers: WebSocketEventHandlers = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.handlers = handlers;
    this.status = {
      state: WebSocketConnectionState.DISCONNECTED,
      isConnected: false,
      reconnectAttempts: 0,
    };
  }

  getConnectionStatus(): WebSocketConnectionStatus {
    return { ...this.status };
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.CONNECTING) {
      logger.warn('连接中，请勿重复连接');
      return;
    }

    if (this.ws?.readyState === WebSocket.OPEN) {
      logger.warn('已连接，请勿重复连接');
      return;
    }

    this.isManualClose = false;
    this.updateStatus(WebSocketConnectionState.CONNECTING);

    try {
      const url = this.buildUrl();
      const ws = new WebSocket(url, this.config.protocols);
      this.ws = ws;

      ws.onopen = () => this.handleOpen();
      ws.onclose = (event: CloseEvent) => this.handleClose(event);
      ws.onerror = (event: Event) => this.handleWebSocketError(event);
      ws.onmessage = (event: MessageEvent) => this.handleMessage(event);

      this.setConnectionTimeout();
    } catch (error) {
      this.handleError(error instanceof Error ? error : new Error(String(error)));
    }
  }

  disconnect(code = 1000, reason = '客户端主动断开'): void {
    this.isManualClose = true;
    this.clearTimers();

    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close(code, reason);
      }
      this.ws = null;
    }

    this.updateStatus(WebSocketConnectionState.DISCONNECTED);
  }

  send(message: unknown): boolean {
    if (!this.isConnected()) {
      this.enqueueMessage(message);
      return false;
    }

    try {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      this.ws?.send(data);
      return true;
    } catch (error) {
      logger.error('发送消息失败:', error);
      this.enqueueMessage(message);
      return false;
    }
  }

  ping(): boolean {
    this.pingStartTime = Date.now();
    return this.send('ping');
  }

  private updateStatus(
    state: WebSocketConnectionState,
    error?: Error,
    latency?: number
  ): void {
    const prevState = this.status.state;

    this.status = {
      ...this.status,
      state,
      isConnected: state === WebSocketConnectionState.CONNECTED,
      error,
      latency,
    };

    if (state === WebSocketConnectionState.CONNECTED) {
      this.status.lastConnectedAt = new Date();
    } else if (state === WebSocketConnectionState.DISCONNECTED) {
      this.status.lastDisconnectedAt = new Date();
    }

    if (prevState !== state) {
      this.handlers.onStateChange?.(prevState, state);
    }
  }

  private buildUrl(): string {
    const url = new URL(this.config.url);
    if (this.config.token) {
      url.searchParams.set('token', this.config.token);
    }
    return url.toString();
  }

  private handleOpen(): void {
    this.clearConnectionTimeout();
    this.status.reconnectAttempts = 0;
    this.updateStatus(WebSocketConnectionState.CONNECTED);
    this.lastPongTime = Date.now();

    if (this.config.initialMessage) {
      this.send(this.config.initialMessage);
    }

    if (this.config.enableHeartbeat) {
      this.startHeartbeat();
    }

    this.flushMessageQueue();
    this.handlers.onConnect?.();
  }

  private handleClose(event: CloseEvent): void {
    this.updateStatus(WebSocketConnectionState.DISCONNECTED);
    this.clearTimers();
    this.handlers.onDisconnect?.(event.code, event.reason);
    if (!this.isManualClose) {
      this.scheduleReconnect();
    }
  }

  private handleWebSocketError(_event: Event): void {
    this.updateStatus(WebSocketConnectionState.ERROR, new Error('WebSocket 错误'));
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const rawData = event.data as string;
      const message = JSON.parse(rawData) as Record<string, unknown>;
      if (message.type === WebSocketMessageType.PING) {
        this.ws?.send('pong');
        return;
      }
      if (message.type === WebSocketMessageType.PONG) {
        const latency = Date.now() - this.pingStartTime;
        this.status.latency = latency;
        return;
      }
      if (message.type === WebSocketMessageType.ERROR) {
        return;
      }
      this.handlers.onMessage?.(message as unknown as WebSocketMessage);
    } catch {
      // 解析消息失败，静默处理
    }
  }

  private setConnectionTimeout(): void {
    this.clearConnectionTimeout();
    this.connectionTimeoutTimer = setTimeout(() => {
      if (this.status.state === WebSocketConnectionState.CONNECTING) {
        this.ws?.close(1006, '连接超时');
        this.updateStatus(WebSocketConnectionState.ERROR, new Error('连接超时'));
      }
    }, this.config.connectionTimeout);
  }

  private clearConnectionTimeout(): void {
    if (this.connectionTimeoutTimer) {
      clearTimeout(this.connectionTimeoutTimer);
      this.connectionTimeoutTimer = null;
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      const timeSinceLastPong = Date.now() - this.lastPongTime;
      const timeout = this.config.heartbeatInterval * 2;

      if (timeSinceLastPong > timeout) {
        this.handlers.onHeartbeatTimeout?.();
        this.ws?.close(1001, '心跳超时');
        return;
      }

      this.ping();
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.status.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.updateStatus(WebSocketConnectionState.ERROR, new Error('重连失败'));
      return;
    }

    this.status.reconnectAttempts++;

    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.status.reconnectAttempts - 1),
      30000
    );

    this.updateStatus(WebSocketConnectionState.RECONNECTING);
    this.handlers.onReconnecting?.(this.status.reconnectAttempts);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private clearTimers(): void {
    this.clearConnectionTimeout();
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private enqueueMessage(message: unknown): void {
    const queuedMessage: QueuedMessage = {
      id: generateId(),
      message,
      enqueuedAt: Date.now(),
      retryCount: 0,
    };
    this.messageQueue.push(queuedMessage);
  }

  private flushMessageQueue(): void {
    if (this.messageQueue.length === 0) return;

    const queue = [...this.messageQueue];
    this.messageQueue = [];

    queue.forEach((item) => {
      const success = this.send(item.message);
      if (!success) {
        this.messageQueue.push({
          ...item,
          retryCount: item.retryCount + 1,
        });
      }
    });

    this.messageQueue = this.messageQueue.filter(
      (item) => item.retryCount < 3
    );
  }

  private handleError(error: Error): void {
    this.updateStatus(WebSocketConnectionState.ERROR, error);
    this.handlers.onError?.(error);
  }

  updateConfig(config: Partial<WebSocketConfig>): void {
    this.config = { ...this.config, ...config };
  }

  updateHandlers(handlers: Partial<WebSocketEventHandlers>): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  getQueueLength(): number {
    return this.messageQueue.length;
  }

  clearQueue(): void {
    this.messageQueue = [];
  }

  destroy(): void {
    this.disconnect(1000, '服务销毁');
    this.clearQueue();
    this.handlers = {};
  }
}

export function createWebSocketService(
  config: WebSocketConfig,
  handlers?: WebSocketEventHandlers
): WebSocketService {
  return new WebSocketService(config, handlers);
}

let globalWebSocketService: WebSocketService | null = null;

export function getGlobalWebSocketService(): WebSocketService | null {
  return globalWebSocketService;
}

export function setGlobalWebSocketService(service: WebSocketService | null): void {
  globalWebSocketService = service;
}

export function initGlobalWebSocketService(
  config: WebSocketConfig,
  handlers?: WebSocketEventHandlers
): WebSocketService {
  if (globalWebSocketService) {
    globalWebSocketService.destroy();
  }
  globalWebSocketService = new WebSocketService(config, handlers);
  return globalWebSocketService;
}
