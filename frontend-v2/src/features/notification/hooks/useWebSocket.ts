// ============================================
// WebSocket React Hooks
// ============================================

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';

import {
  WebSocketConfig,
  WebSocketConnectionState,
  WebSocketConnectionStatus,
  WebSocketMessage,
  NotificationData,
  ChatMessageData,
  WebSocketEventHandlers,
} from '../types/websocket';
import {
  WebSocketService,
  createWebSocketService,
} from '../services/websocketService';

// ============================================
// useWebSocket - 基础WebSocket连接Hook
// ============================================

/**
 * useWebSocket Hook 返回的对象
 */
export interface UseWebSocketReturn {
  /** 当前连接状态 */
  status: WebSocketConnectionStatus;
  /** 是否已连接 */
  isConnected: boolean;
  /** 连接函数 */
  connect: () => void;
  /** 断开连接函数 */
  disconnect: () => void;
  /** 发送消息函数 */
  send: (message: unknown) => boolean;
  /** WebSocket服务实例 */
  service: WebSocketService | null;
}

/**
 * 基础WebSocket连接Hook
 * @param config - WebSocket配置
 * @param handlers - 事件处理器
 */
export function useWebSocket(
  config: WebSocketConfig,
  handlers: WebSocketEventHandlers = {}
): UseWebSocketReturn {
  // 使用ref保存service实例，避免重复创建
  const serviceRef = useRef<WebSocketService | null>(null);
  
  // 连接状态
  const [status, setStatus] = useState<WebSocketConnectionStatus>({
    state: WebSocketConnectionState.DISCONNECTED,
    isConnected: false,
    reconnectAttempts: 0,
  });

  // 初始化service
  if (!serviceRef.current) {
    serviceRef.current = createWebSocketService(config, {
      ...handlers,
      onConnect: () => {
        setStatus((prev) => ({
          ...prev,
          state: WebSocketConnectionState.CONNECTED,
          isConnected: true,
          reconnectAttempts: 0,
        }));
        handlers.onConnect?.();
      },
      onDisconnect: (code, reason) => {
        setStatus((prev) => ({
          ...prev,
          state: WebSocketConnectionState.DISCONNECTED,
          isConnected: false,
          lastDisconnectedAt: new Date(),
        }));
        handlers.onDisconnect?.(code, reason);
      },
      onError: (error) => {
        setStatus((prev) => ({
          ...prev,
          state: WebSocketConnectionState.ERROR,
          error,
        }));
        handlers.onError?.(error);
      },
      onReconnecting: (attempt) => {
        setStatus((prev) => ({
          ...prev,
          state: WebSocketConnectionState.RECONNECTING,
          reconnectAttempts: attempt,
        }));
        handlers.onReconnecting?.(attempt);
      },
      onReconnected: () => {
        setStatus((prev) => ({
          ...prev,
          state: WebSocketConnectionState.CONNECTED,
          isConnected: true,
          lastConnectedAt: new Date(),
        }));
        handlers.onReconnected?.();
      },
    });
  }

  // 连接函数
  const connect = useCallback(() => {
    serviceRef.current?.connect();
  }, []);

  // 断开连接函数
  const disconnect = useCallback(() => {
    serviceRef.current?.disconnect();
  }, []);

  // 发送消息函数
  const send = useCallback((message: unknown): boolean => {
    return serviceRef.current?.send(message) ?? false;
  }, []);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      serviceRef.current?.disconnect();
    };
  }, []);

  // 当配置变化时更新
  useEffect(() => {
    serviceRef.current?.updateConfig(config);
  }, [config]);

  return {
    status,
    isConnected: status.isConnected,
    connect,
    disconnect,
    send,
    service: serviceRef.current,
  };
}

// ============================================
// useNotificationStream - 通知流订阅Hook
// ============================================

/**
 * useNotificationStream Hook 返回的对象
 */
export interface UseNotificationStreamReturn {
  /** 通知列表 */
  notifications: NotificationData[];
  /** 最新通知 */
  latestNotification: NotificationData | null;
  /** 是否已连接 */
  isConnected: boolean;
  /** 清空通知列表 */
  clearNotifications: () => void;
  /** 标记通知已读 */
  markAsRead: (id: number) => void;
}

/**
 * 通知流订阅Hook
 * @param url - WebSocket URL
 * @param token - 认证Token
 * @param autoConnect - 是否自动连接
 */
export function useNotificationStream(
  url: string,
  token: string | null,
  autoConnect = true
): UseNotificationStreamReturn {
  const [notifications, setNotifications] = useState<NotificationData[]>([]);
  const [latestNotification, setLatestNotification] = useState<NotificationData | null>(null);
  const notificationsRef = useRef<NotificationData[]>([]);

  // 配置
  const config = useMemo<WebSocketConfig>(
    () => ({
      url,
      token: token ?? undefined,
      autoReconnect: true,
      enableHeartbeat: true,
    }),
    [url, token]
  );

  // 处理新通知
  const handleNotification = useCallback((notification: NotificationData) => {
    setLatestNotification(notification);
    setNotifications((prev) => {
      const newNotifications = [notification, ...prev];
      notificationsRef.current = newNotifications;
      return newNotifications;
    });
  }, []);

  // 初始化WebSocket
  const { isConnected, connect } = useWebSocket(config, {
    onNotification: handleNotification,
  });

  // 自动连接
  useEffect(() => {
    if (autoConnect && token) {
      connect();
    }
  }, [autoConnect, token, connect]);

  // 清空通知
  const clearNotifications = useCallback(() => {
    setNotifications([]);
    notificationsRef.current = [];
  }, []);

  // 标记已读
  const markAsRead = useCallback((id: number) => {
    setNotifications((prev) => {
      const updated = prev.map((n) =>
        n.id === id ? { ...n, isRead: true } : n
      );
      notificationsRef.current = updated;
      return updated;
    });
  }, []);

  return {
    notifications,
    latestNotification,
    isConnected,
    clearNotifications,
    markAsRead,
  };
}

// ============================================
// useChatMessages - 实时聊天消息Hook
// ============================================

/**
 * useChatMessages Hook 返回的对象
 */
export interface UseChatMessagesReturn {
  /** 消息列表 */
  messages: ChatMessageData[];
  /** 当前打字用户 */
  typingUsers: Map<string, { userId: number; userName: string; timestamp: number }>;
  /** 是否已连接 */
  isConnected: boolean;
  /** 发送消息 */
  sendMessage: (content: string, messageType?: 'text' | 'image' | 'file' | 'voice') => boolean;
  /** 发送打字状态 */
  sendTyping: (isTyping: boolean) => void;
  /** 清空消息 */
  clearMessages: () => void;
}

/**
 * 实时聊天消息Hook
 * @param url - WebSocket URL
 * @param token - 认证Token
 * @param conversationId - 会话ID
 */
export function useChatMessages(
  url: string,
  token: string | null,
  conversationId: string
): UseChatMessagesReturn {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [typingUsers, setTypingUsers] = useState<Map<string, { userId: number; userName: string; timestamp: number }>>(new Map());
  
  // 用于清理过期打字状态的计时器
  const typingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 配置
  const config = useMemo<WebSocketConfig>(
    () => ({
      url,
      token: token ?? undefined,
      autoReconnect: true,
      enableHeartbeat: true,
      initialMessage: {
        type: 'join_conversation',
        conversationId,
      },
    }),
    [url, token, conversationId]
  );

  // 处理新消息
  const handleChatMessage = useCallback((message: ChatMessageData) => {
    if (message.conversationId === conversationId) {
      setMessages((prev) => [...prev, message]);
    }
  }, [conversationId]);

  // 处理打字状态
  const handleTyping = useCallback((data: { conversationId: string; userId: number; userName: string; isTyping: boolean }) => {
    if (data.conversationId !== conversationId) return;

    setTypingUsers((prev) => {
      const next = new Map(prev);
      if (data.isTyping) {
        next.set(String(data.userId), {
          userId: data.userId,
          userName: data.userName,
          timestamp: Date.now(),
        });
      } else {
        next.delete(String(data.userId));
      }
      return next;
    });

    // 清理3秒后过期的打字状态
    if (typingTimerRef.current) {
      clearTimeout(typingTimerRef.current);
    }
    typingTimerRef.current = setTimeout(() => {
      setTypingUsers((prev) => {
        const next = new Map(prev);
        const now = Date.now();
        for (const [key, value] of next.entries()) {
          if (now - value.timestamp > 3000) {
            next.delete(key);
          }
        }
        return next;
      });
    }, 3000);
  }, [conversationId]);

  // 处理打字状态消息
  const handleMessage = useCallback((message: WebSocketMessage) => {
     
    const msg = message as unknown as { type: string; data: { conversationId: string; userId: number; userName: string; isTyping: boolean } };
    if (msg.type === 'typing') {
      handleTyping(msg.data);
    }
  }, [handleTyping]);

  // 初始化WebSocket
  const { isConnected, send } = useWebSocket(config, {
    onChatMessage: handleChatMessage,
    onMessage: handleMessage,
  });

  // 发送消息
  const sendMessage = useCallback((
    content: string,
    messageType: 'text' | 'image' | 'file' | 'voice' = 'text'
  ): boolean => {
    return send({
      type: 'chat_message',
      conversationId,
      content,
      messageType,
      timestamp: Date.now(),
    });
  }, [send, conversationId]);

  // 发送打字状态
  const sendTyping = useCallback((isTyping: boolean): void => {
    send({
      type: 'typing',
      conversationId,
      isTyping,
      timestamp: Date.now(),
    });
  }, [send, conversationId]);

  // 清空消息
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // 清理计时器
  useEffect(() => {
    return () => {
      if (typingTimerRef.current) {
        clearTimeout(typingTimerRef.current);
      }
    };
  }, []);

  return {
    messages,
    typingUsers,
    isConnected,
    sendMessage,
    sendTyping,
    clearMessages,
  };
}

// ============================================
// useConnectionStatus - 连接状态监控Hook
// ============================================

/**
 * 连接状态详情
 */
export interface ConnectionStatusDetails {
  /** 当前状态 */
  state: WebSocketConnectionState;
  /** 状态文本 */
  stateText: string;
  /** 是否在线 */
  isOnline: boolean;
  /** 连接时长（毫秒） */
  connectionDuration?: number;
  /** 延迟（毫秒） */
  latency?: number;
  /** 重连次数 */
  reconnectAttempts: number;
  /** 队列中的消息数 */
  queueLength: number;
  /** 最后连接时间 */
  lastConnectedAt?: Date;
  /** 最后断开时间 */
  lastDisconnectedAt?: Date;
}

/**
 * useConnectionStatus Hook 返回的对象
 */
export interface UseConnectionStatusReturn {
  /** 状态详情 */
  status: ConnectionStatusDetails;
  /** 当前状态 */
  state: WebSocketConnectionState;
  /** 是否已连接 */
  isConnected: boolean;
  /** 手动重连 */
  reconnect: () => void;
}

/**
 * 连接状态监控Hook
 * @param service - WebSocketService实例
 */
export function useConnectionStatus(
  service: WebSocketService | null
): UseConnectionStatusReturn {
  const [status, setStatus] = useState<WebSocketConnectionStatus>({
    state: WebSocketConnectionState.DISCONNECTED,
    isConnected: false,
    reconnectAttempts: 0,
  });
  const [connectionDuration, setConnectionDuration] = useState<number>(0);
  const durationTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 状态文本映射
  const stateTextMap: Record<WebSocketConnectionState, string> = {
    [WebSocketConnectionState.CONNECTING]: '连接中',
    [WebSocketConnectionState.CONNECTED]: '已连接',
    [WebSocketConnectionState.DISCONNECTED]: '已断开',
    [WebSocketConnectionState.RECONNECTING]: '重连中',
    [WebSocketConnectionState.ERROR]: '连接错误',
  };

  // 监听状态变化
  useEffect(() => {
    if (!service) return;

    // 初始化状态
    setStatus(service.getConnectionStatus());

    // 定期检查状态
    const interval = setInterval(() => {
      const currentStatus = service.getConnectionStatus();
      setStatus((prev) => {
        // 只在状态变化时更新
        if (prev.state !== currentStatus.state ||
            prev.reconnectAttempts !== currentStatus.reconnectAttempts ||
            prev.latency !== currentStatus.latency) {
          return currentStatus;
        }
        return prev;
      });
    }, 500);

    return () => {
      clearInterval(interval);
    };
  }, [service]);

  // 计算连接时长
  useEffect(() => {
    const connectedAt = status.lastConnectedAt;
    if (status.isConnected && connectedAt) {
      durationTimerRef.current = setInterval(() => {
        setConnectionDuration(Date.now() - connectedAt.getTime());
      }, 1000);
    } else {
      if (durationTimerRef.current) {
        clearInterval(durationTimerRef.current);
        durationTimerRef.current = null;
      }
      setConnectionDuration(0);
    }

    return () => {
      if (durationTimerRef.current) {
        clearInterval(durationTimerRef.current);
      }
    };
  }, [status.isConnected, status.lastConnectedAt]);

  // 手动重连
  const reconnect = useCallback(() => {
    service?.disconnect();
    // 短暂延迟后重连
    setTimeout(() => {
      service?.connect();
    }, 100);
  }, [service]);

  // 状态详情
  const details: ConnectionStatusDetails = {
    state: status.state,
    stateText: stateTextMap[status.state],
    isOnline: status.isConnected,
    connectionDuration: status.isConnected ? connectionDuration : undefined,
    latency: status.latency,
    reconnectAttempts: status.reconnectAttempts,
    queueLength: service?.getQueueLength() ?? 0,
    lastConnectedAt: status.lastConnectedAt,
    lastDisconnectedAt: status.lastDisconnectedAt,
  };

  return {
    status: details,
    state: status.state,
    isConnected: status.isConnected,
    reconnect,
  };
}

// 导出所有hooks
export default {
  useWebSocket,
  useNotificationStream,
  useChatMessages,
  useConnectionStatus,
};