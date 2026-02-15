// ============================================
// WebSocket 全局上下文
// ============================================
/* eslint-disable react-refresh/only-export-components */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
  type FC,
} from 'react';

import {
  WebSocketConfig,
  WebSocketConnectionState,
  WebSocketConnectionStatus,
  NotificationData,
  ChatMessageData,
  OrderUpdateData,
  WebSocketEventHandlers,
  RealtimeNotificationConfig,
} from '../types/websocket';
import {
  WebSocketService,
  initGlobalWebSocketService,
} from '../services/websocketService';

// ============================================
// 上下文类型定义
// ============================================

/**
 * WebSocket 上下文状态
 */
export interface WebSocketContextState {
  /** 连接状态 */
  status: WebSocketConnectionStatus;
  /** 是否已连接 */
  isConnected: boolean;
  /** 最新通知 */
  latestNotification: NotificationData | null;
  /** 最新聊天消息 */
  latestChatMessage: ChatMessageData | null;
  /** 最新订单更新 */
  latestOrderUpdate: OrderUpdateData | null;
  /** 未读通知数量 */
  unreadCount: number;
  /** 通知历史 */
  notificationHistory: NotificationData[];
}

/**
 * WebSocket 上下文操作
 */
export interface WebSocketContextActions {
  /** 连接 */
  connect: () => void;
  /** 断开连接 */
  disconnect: () => void;
  /** 发送消息 */
  send: (message: unknown) => boolean;
  /** 标记通知已读 */
  markAsRead: (notificationId: number) => void;
  /** 标记全部已读 */
  markAllAsRead: () => void;
  /** 清空通知历史 */
  clearHistory: () => void;
  /** 更新配置 */
  updateConfig: (config: Partial<WebSocketConfig>) => void;
}

/**
 * WebSocket 上下文值
 */
export interface WebSocketContextValue extends WebSocketContextState, WebSocketContextActions {
  /** WebSocket 服务实例（高级用法） */
  service: WebSocketService | null;
}

// ============================================
// 创建上下文
// ============================================

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

// ============================================
// Provider Props
// ============================================

export interface WebSocketProviderProps {
  /** 子元素 */
  children: ReactNode;
  /** WebSocket URL */
  url: string;
  /** 认证Token */
  token?: string | null;
  /** 是否自动连接 */
  autoConnect?: boolean;
  /** 通知配置 */
  notificationConfig?: RealtimeNotificationConfig;
  /** 自定义事件处理器 */
  eventHandlers?: Partial<WebSocketEventHandlers>;
  /** 最大通知历史数量 */
  maxHistorySize?: number;
}

// ============================================
// Provider 组件
// ============================================

/**
 * WebSocket Provider 组件
 */
export const WebSocketProvider: FC<WebSocketProviderProps> = ({
  children,
  url,
  token,
  autoConnect = true,
  notificationConfig,
  eventHandlers,
  maxHistorySize = 100,
}) => {
  // WebSocket 服务引用
  const serviceRef = useRef<WebSocketService | null>(null);
  
  // 状态
  const [status, setStatus] = useState<WebSocketConnectionStatus>({
    state: WebSocketConnectionState.DISCONNECTED,
    isConnected: false,
    reconnectAttempts: 0,
  });
  
  const [latestNotification, setLatestNotification] = useState<NotificationData | null>(null);
  const [latestChatMessage, setLatestChatMessage] = useState<ChatMessageData | null>(null);
  const [latestOrderUpdate, setLatestOrderUpdate] = useState<OrderUpdateData | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notificationHistory, setNotificationHistory] = useState<NotificationData[]>([]);

  // 初始化 WebSocket 服务
  useEffect(() => {
    const config: WebSocketConfig = {
      url,
      token: token ?? undefined,
      autoReconnect: true,
      enableHeartbeat: true,
      reconnectInterval: 1000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
    };

    const handlers: WebSocketEventHandlers = {
      onConnect: () => {
        setStatus((prev) => ({
          ...prev,
          state: WebSocketConnectionState.CONNECTED,
          isConnected: true,
          reconnectAttempts: 0,
          lastConnectedAt: new Date(),
        }));
        eventHandlers?.onConnect?.();
      },
      onDisconnect: (code, reason) => {
        setStatus((prev) => ({
          ...prev,
          state: WebSocketConnectionState.DISCONNECTED,
          isConnected: false,
          lastDisconnectedAt: new Date(),
        }));
        eventHandlers?.onDisconnect?.(code, reason);
      },
      onError: (error) => {
        setStatus((prev) => ({
          ...prev,
          state: WebSocketConnectionState.ERROR,
          error,
        }));
        eventHandlers?.onError?.(error);
      },
      onMessage: (message) => {
        eventHandlers?.onMessage?.(message);
      },
      onNotification: (notification) => {
        setLatestNotification(notification);
        setNotificationHistory((prev) => {
          const next = [notification, ...prev];
          return next.slice(0, maxHistorySize);
        });
        if (!notification.isRead) {
          setUnreadCount((prev) => prev + 1);
        }
        
        // 显示桌面通知
        if (notificationConfig?.enableDesktopNotification && Notification.permission === 'granted') {
           
          new Notification(notification.title, {
            body: notification.content,
            icon: notification.senderAvatar,
            tag: String(notification.id),
          });
        }
        
        eventHandlers?.onNotification?.(notification);
      },
      onChatMessage: (message) => {
        setLatestChatMessage(message);
        eventHandlers?.onChatMessage?.(message);
      },
      onOrderUpdate: (update) => {
        setLatestOrderUpdate(update);
        eventHandlers?.onOrderUpdate?.(update);
      },
      onReconnecting: (attempt) => {
        setStatus((prev) => ({
          ...prev,
          state: WebSocketConnectionState.RECONNECTING,
          reconnectAttempts: attempt,
        }));
        eventHandlers?.onReconnecting?.(attempt);
      },
      onReconnected: () => {
        setStatus((prev) => ({
          ...prev,
          state: WebSocketConnectionState.CONNECTED,
          isConnected: true,
          lastConnectedAt: new Date(),
        }));
        eventHandlers?.onReconnected?.();
      },
      onHeartbeatTimeout: () => {
        eventHandlers?.onHeartbeatTimeout?.();
      },
    };

    serviceRef.current = initGlobalWebSocketService(config, handlers);

    return () => {
      serviceRef.current?.destroy();
      serviceRef.current = null;
    };
  }, [url, maxHistorySize, notificationConfig?.enableDesktopNotification, token, eventHandlers, autoConnect]);

  // 自动连接
  useEffect(() => {
    if (autoConnect && token) {
      serviceRef.current?.connect();
    }
  }, [autoConnect, token]);

  // 请求桌面通知权限
  useEffect(() => {
    if (notificationConfig?.enableDesktopNotification && 'Notification' in window) {
      void Notification.requestPermission();
    }
  }, [notificationConfig?.enableDesktopNotification]);

  // ============================================
  // 操作方法
  // ============================================

  const connect = useCallback(() => {
    serviceRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    serviceRef.current?.disconnect();
  }, []);

  const send = useCallback((message: unknown): boolean => {
    return serviceRef.current?.send(message) ?? false;
  }, []);

  const markAsRead = useCallback((notificationId: number) => {
    setNotificationHistory((prev) =>
      prev.map((n) => (n.id === notificationId ? { ...n, isRead: true } : n))
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotificationHistory((prev) => prev.map((n) => ({ ...n, isRead: true })));
    setUnreadCount(0);
  }, []);

  const clearHistory = useCallback(() => {
    setNotificationHistory([]);
    setUnreadCount(0);
  }, []);

  const updateConfig = useCallback((config: Partial<WebSocketConfig>) => {
    serviceRef.current?.updateConfig(config);
  }, []);

  // ============================================
  // 上下文值
  // ============================================

  const value: WebSocketContextValue = {
    // 状态
    status,
    isConnected: status.isConnected,
    latestNotification,
    latestChatMessage,
    latestOrderUpdate,
    unreadCount,
    notificationHistory,
    // 操作
    connect,
    disconnect,
    send,
    markAsRead,
    markAllAsRead,
    clearHistory,
    updateConfig,
    // 服务实例
    service: serviceRef.current,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

// ============================================
// Hooks
// ============================================

/**
 * 使用 WebSocket 上下文
 */
export function useWebSocketContext(): WebSocketContextValue {
  const context = useContext(WebSocketContext);
  
  if (!context) {
    throw new Error('useWebSocketContext 必须在 WebSocketProvider 内部使用');
  }
  
  return context;
}

/**
 * 使用连接状态
 */
export function useConnectionStatus(): WebSocketConnectionStatus {
  const { status } = useWebSocketContext();
  return status;
}

/**
 * 使用通知
 */
export function useNotifications(): {
  unreadCount: number;
  notificationHistory: NotificationData[];
  latestNotification: NotificationData | null;
  markAsRead: (id: number) => void;
  markAllAsRead: () => void;
  clearHistory: () => void;
} {
  const {
    unreadCount,
    notificationHistory,
    latestNotification,
    markAsRead,
    markAllAsRead,
    clearHistory,
  } = useWebSocketContext();

  return {
    unreadCount,
    notificationHistory,
    latestNotification,
    markAsRead,
    markAllAsRead,
    clearHistory,
  };
}

/**
 * 使用聊天消息
 */
export function useChatMessages(): {
  latestChatMessage: ChatMessageData | null;
  isConnected: boolean;
} {
  const { latestChatMessage, isConnected } = useWebSocketContext();
  return { latestChatMessage, isConnected };
}

/**
 * 使用订单更新
 */
export function useOrderUpdates(): {
  latestOrderUpdate: OrderUpdateData | null;
} {
  const { latestOrderUpdate } = useWebSocketContext();
  return { latestOrderUpdate };
}

// ============================================
// HOC
// ============================================

/**
 * WebSocket 高阶组件
 */
export function withWebSocket<P extends object>(
  WrappedComponent: React.ComponentType<P & { webSocket: WebSocketContextValue }>
): FC<P> {
  return function WithWebSocketComponent(props: P) {
    const webSocket = useWebSocketContext();
    return <WrappedComponent {...props} webSocket={webSocket} />;
  };
}

// ============================================
// 默认导出
// ============================================

export default WebSocketContext;
