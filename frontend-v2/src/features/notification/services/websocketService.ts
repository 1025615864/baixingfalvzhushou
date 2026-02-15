// ============================================
// WebSocket 服务 - 连接管理、心跳、重连
// ============================================

import {
  WebSocketConfig,
  WebSocketConnectionState,
  WebSocketConnectionStatus,
  WebSocketMessage,
  WebSocketMessageType,
  QueuedMessage,
  WebSocketEventHandlers,
} from '../types/websocket';

/**
 * 生成唯一ID
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * 默认配置
 */
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

/**
 * WebSocket 服务类
 */
export class WebSocketService {
  /** WebSocket 实例 */
  private ws: WebSocket | null = null;
  
  /** 配置 */
  private config: Required<WebSocketConfig>;
  
  /** 事件处理器 */
  private handlers: WebSocketEventHandlers;
  
  /** 当前状态 */
  private status: WebSocketConnectionStatus;
  
  /** 重连计时器 */
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  
  /** 心跳计时器 */
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  
  /** 连接超时计时器 */
  private connectionTimeoutTimer: ReturnType<typeof setTimeout> | null = null;
  
  /** 消息队列（离线消息缓存） */
  private messageQueue: QueuedMessage[] = [];
  
  /** 是否正在手动关闭 */
  private isManualClose = false;
  
  /** 最后收到 pong 的时间 */
  private lastPongTime = 0;
  
  /** 延迟计算起始时间 */
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

  /**
   * 获取当前连接状态
   */
  getConnectionStatus(): WebSocketConnectionStatus {
    return { ...this.status };
  }

  /**
   * 是否已连接
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * 建立连接
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.CONNECTING) {
      console.warn('[WebSocket] 连接中，请勿重复连接');
      return;
    }

    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('[WebSocket] 已连接，请勿重复连接');
      return;
    }

    this.isManualClose = false;
    this.updateStatus(WebSocketConnectionState.CONNECTING);

    try {
      // 构建带认证参数的 URL
      const url = this.buildUrl();
      
      // 创建 WebSocket 连接
      const ws = new WebSocket(url, this.config.protocols);
      this.ws = ws;

      // 绑定事件
      ws.onopen = () => this.handleOpen();
      ws.onclose = (event: CloseEvent) => this.handleClose(event);
      ws.onerror = (event: Event) => this.handleWebSocketError(event);
      ws.onmessage = (event: MessageEvent) => this.handleMessage(event);

      // 设置连接超时
      this.setConnectionTimeout();
    } catch (error) {
      this.handleError(error instanceof Error ? error : new Error(String(error)));
    }
  }

  /**
   * 断开连接
   */
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

  /**
   * 发送消息
   */
  send(message: unknown): boolean {
    if (!this.isConnected()) {
      // 如果未连接，将消息加入队列
      this.enqueueMessage(message);
      return false;
    }

    try {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      this.ws?.send(data);
      return true;
    } catch (error) {
      console.error('[WebSocket] 发送消息失败:', error);
      this.enqueueMessage(message);
      return false;
    }
  }

  /**
   * 发送 ping（心跳）
   * 后端期望接收字符串 "ping"，返回字符串 "pong"
   */
  ping(): boolean {
    this.pingStartTime = Date.now();
    // 发送字符串 "ping" 以匹配后端协议
    return this.send('ping');
  }

  /**
   * 更新状态
   */
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

    // 记录连接/断开时间
    if (state === WebSocketConnectionState.CONNECTED) {
      this.status.lastConnectedAt = new Date();
    } else if (state === WebSocketConnectionState.DISCONNECTED) {
      this.status.lastDisconnectedAt = new Date();
    }

    // 触发状态变化回调（如果需要）
    if (prevState !== state) {
      // console.log(`[WebSocket] 状态变化: ${prevState} -> ${state}`);
    }
  }

  /**
   * 构建 WebSocket URL（添加认证参数）
   */
  private buildUrl(): string {
    const url = new URL(this.config.url);
    
    // 添加 token 到 query 参数
    if (this.config.token) {
      url.searchParams.set('token', this.config.token);
    }
    
    return url.toString();
  }

  /**
   * 连接打开处理
   */
  private handleOpen(): void {
    // console.log('[WebSocket] 连接成功');
    
    this.clearConnectionTimeout();
    this.status.reconnectAttempts = 0;
    this.updateStatus(WebSocketConnectionState.CONNECTED);
    this.lastPongTime = Date.now();

    // 发送初始消息
    if (this.config.initialMessage) {
      this.send(this.config.initialMessage);
    }

    // 启动心跳
    if (this.config.enableHeartbeat) {
      this.startHeartbeat();
    }

    // 发送队列中的消息
    this.flushMessageQueue();

    // 触发回调
    this.handlers.onConnect?.();
  }

  /**
   * 连接关闭处理
   */
  private handleClose(event: CloseEvent): void {
    // console.log(`[WebSocket] 连接关闭: code=${event.code}, reason=${event.reason}`);
    this.updateStatus(WebSocketConnectionState.DISCONNECTED);
    this.clearTimers();
    this.handlers.onDisconnect?.(event.code, event.reason);
    if (!this.isManualClose) {
      this.scheduleReconnect();
    }
  }

  /**
   * 处理 WebSocket 错误
   */
  private handleWebSocketError(_event: Event): void {
    // console.error('[WebSocket] 错误:', event);
    this.updateStatus(WebSocketConnectionState.ERROR, new Error('WebSocket 错误'));
  }

  /**
   * 处理消息
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const rawData = event.data as string;
      const message = JSON.parse(rawData) as Record<string, unknown>;
      // console.log('[WebSocket] 收到消息:', message);
      if (message.type === WebSocketMessageType.PING) {
        this.ws?.send('pong');
        return;
      }
      if (message.type === WebSocketMessageType.PONG) {
        const latency = Date.now() - this.pingStartTime;
        this.status.latency = latency;
        return;
      }
      // 处理 error 类型
      if (message.type === WebSocketMessageType.ERROR) {
        if ('message' in message) {
          // console.error('[WebSocket] 服务器错误:', (message as { message: string }).message);
        }
        return;
      }
      // 触发回调
      this.handlers.onMessage?.(message as unknown as WebSocketMessage);
    } catch {
      // 解析消息失败，静默处理
    }
  }

  /**
   * 设置连接超时
   */
  private setConnectionTimeout(): void {
    this.clearConnectionTimeout();
    
    this.connectionTimeoutTimer = setTimeout(() => {
      if (this.status.state === WebSocketConnectionState.CONNECTING) {
        // console.error('[WebSocket] 连接超时');
        this.ws?.close(1006, '连接超时');
        this.updateStatus(WebSocketConnectionState.ERROR, new Error('连接超时'));
      }
    }, this.config.connectionTimeout);
  }

  /**
   * 清除连接超时
   */
  private clearConnectionTimeout(): void {
    if (this.connectionTimeoutTimer) {
      clearTimeout(this.connectionTimeoutTimer);
      this.connectionTimeoutTimer = null;
    }
  }

  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      // 检查上次收到 pong 的时间
      const timeSinceLastPong = Date.now() - this.lastPongTime;
      const timeout = this.config.heartbeatInterval * 2;

      if (timeSinceLastPong > timeout) {
        // console.warn('[WebSocket] 心跳超时，准备重连');
        this.handlers.onHeartbeatTimeout?.();
        this.ws?.close(1001, '心跳超时');
        return;
      }

      // 发送 ping
      this.ping();
    }, this.config.heartbeatInterval);
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * 安排重连（指数退避策略）
   */
  private scheduleReconnect(): void {
    if (this.status.reconnectAttempts >= this.config.maxReconnectAttempts) {
      // console.error('[WebSocket] 达到最大重连次数，停止重连');
      this.updateStatus(WebSocketConnectionState.ERROR, new Error('重连失败'));
      return;
    }

    this.status.reconnectAttempts++;
    
    // 指数退避：1s, 2s, 4s, 8s... 最大 30s
    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.status.reconnectAttempts - 1),
      30000
    );

    // console.log(`[WebSocket] ${delay}ms 后第 ${this.status.reconnectAttempts} 次重连...`);
    
    this.updateStatus(WebSocketConnectionState.RECONNECTING);
    this.handlers.onReconnecting?.(this.status.reconnectAttempts);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * 清除所有计时器
   */
  private clearTimers(): void {
    this.clearConnectionTimeout();
    this.stopHeartbeat();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * 将消息加入队列
   */
  private enqueueMessage(message: unknown): void {
    const queuedMessage: QueuedMessage = {
      id: generateId(),
      message,
      enqueuedAt: Date.now(),
      retryCount: 0,
    };
    
    this.messageQueue.push(queuedMessage);
    // console.log(`[WebSocket] 消息已入队，当前队列长度: ${this.messageQueue.length}`);
  }

  /**
   * 发送队列中的所有消息
   */
  private flushMessageQueue(): void {
    if (this.messageQueue.length === 0) return;

    // console.log(`[WebSocket] 开始发送队列中的 ${this.messageQueue.length} 条消息`);
    
    const queue = [...this.messageQueue];
    this.messageQueue = [];

    queue.forEach((item) => {
      const success = this.send(item.message);
      if (!success) {
        // 如果发送失败，重新入队
        this.messageQueue.push({
          ...item,
          retryCount: item.retryCount + 1,
        });
      }
    });

    // 清理超过最大重试次数的消息
    this.messageQueue = this.messageQueue.filter(
      (item) => item.retryCount < 3
    );
  }

  /**
   * 错误处理
   */
  private handleError(error: Error): void {
    this.updateStatus(WebSocketConnectionState.ERROR, error);
    this.handlers.onError?.(error);
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<WebSocketConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * 更新事件处理器
   */
  updateHandlers(handlers: Partial<WebSocketEventHandlers>): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  /**
   * 获取队列长度
   */
  getQueueLength(): number {
    return this.messageQueue.length;
  }

  /**
   * 清空消息队列
   */
  clearQueue(): void {
    this.messageQueue = [];
  }

  /**
   * 销毁服务
   */
  destroy(): void {
    this.disconnect(1000, '服务销毁');
    this.clearQueue();
    this.handlers = {};
  }
}

/**
 * 创建 WebSocket 服务实例（工厂函数）
 */
export function createWebSocketService(
  config: WebSocketConfig,
  handlers?: WebSocketEventHandlers
): WebSocketService {
  return new WebSocketService(config, handlers);
}

// 导出单例实例管理
let globalWebSocketService: WebSocketService | null = null;

/**
 * 获取全局 WebSocket 服务实例
 */
export function getGlobalWebSocketService(): WebSocketService | null {
  return globalWebSocketService;
}

/**
 * 设置全局 WebSocket 服务实例
 */
export function setGlobalWebSocketService(service: WebSocketService | null): void {
  globalWebSocketService = service;
}

/**
 * 初始化全局 WebSocket 服务
 */
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