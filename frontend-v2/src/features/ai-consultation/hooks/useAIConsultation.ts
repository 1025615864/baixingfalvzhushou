/**
 * AI 咨询模块自定义 Hooks
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  AIMessage,
  AISession,
  SendMessageRequest,
  CreateSessionRequest,
  GetSessionsRequest,
  GetSessionHistoryRequest,
  StreamChunk,
  AIMessageStatus,
  AIConsultationError,
} from '../types';
import {
  apiGetSessions,
  apiGetSession,
  apiGetSessionHistory,
  apiCreateSession,
  apiDeleteSession,
  apiSendMessage,
  apiSendMessageStream,
  type StreamController,
} from '../api';

// ==================== Query Keys ====================

const AI_CONSULTATION_QUERY_KEYS = {
  sessions: (params?: GetSessionsRequest) => ['ai-consultation', 'sessions', params] as const,
  session: (sessionId: string) => ['ai-consultation', 'session', sessionId] as const,
  sessionHistory: (params: GetSessionHistoryRequest) => ['ai-consultation', 'history', params] as const,
} as const;

// ==================== Sessions Hooks ====================

/**
 * 获取会话列表 Hook
 */
export function useSessions(params: GetSessionsRequest = {}) {
  return useQuery<AISession[]>({
    queryKey: AI_CONSULTATION_QUERY_KEYS.sessions(params),
    queryFn: async () => {
      const response = await apiGetSessions(params);
      return response.sessions;
    },
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 获取会话详情 Hook
 */
export function useSession(sessionId: string | undefined) {
  return useQuery<AISession>({
    queryKey: AI_CONSULTATION_QUERY_KEYS.session(sessionId || ''),
    queryFn: () => apiGetSession(sessionId),
    enabled: !!sessionId,
    staleTime: 10 * 1000, // 10秒缓存
  });
}

/**
 * 获取会话历史消息 Hook
 */
export function useSessionHistory(params: GetSessionHistoryRequest | undefined) {
  return useQuery<AIMessage[]>({
    queryKey: AI_CONSULTATION_QUERY_KEYS.sessionHistory(params || { sessionId: '' }),
    queryFn: async () => {
      if (!params) return [];
      const response = await apiGetSessionHistory(params);
      return response.messages;
    },
    enabled: !!params?.sessionId,
    staleTime: 10 * 1000, // 10秒缓存
  });
}

// ==================== Session Management Hooks ====================

/**
 * 创建会话 Hook
 */
export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation<AISession, Error, CreateSessionRequest>({
    mutationFn: async (request) => {
      const response = await apiCreateSession(request);
      // 获取新创建的会话详情
      return apiGetSession(response.sessionId);
    },
    onSuccess: () => {
      // 创建成功后，刷新会话列表
      void queryClient.invalidateQueries({ queryKey: ['ai-consultation', 'sessions'] });
    },
  });
}

/**
 * 删除会话 Hook
 */
export function useDeleteSession() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: apiDeleteSession,
    onSuccess: () => {
      // 删除成功后，刷新会话列表
      void queryClient.invalidateQueries({ queryKey: ['ai-consultation', 'sessions'] });
    },
  });
}

// ==================== Message Hooks ====================

/**
 * 发送消息 Hook（非流式）
 */
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiSendMessage,
    onSuccess: (_, variables) => {
      // 发送成功后，刷新会话历史
      if (variables.sessionId) {
        void queryClient.invalidateQueries({
          queryKey: AI_CONSULTATION_QUERY_KEYS.session(variables.sessionId),
        });
        void queryClient.invalidateQueries({
          queryKey: ['ai-consultation', 'history', { sessionId: variables.sessionId }],
        });
      }
    },
  });
}

// ==================== Stream Message Hook ====================

/** 流式消息状态 */
interface StreamState {
  /** 是否正在流式响应 */
  isStreaming: boolean;
  /** 当前流式内容 */
  content: string;
  /** 完整消息 */
  message: AIMessage | null;
  /** 错误信息 */
  error: AIConsultationError | null;
}

/** 流式消息 Hook 返回类型 */
interface UseStreamMessageReturn {
  /** 流式状态 */
  streamState: StreamState;
  /** 发送流式消息 */
  sendStreamMessage: (request: SendMessageRequest) => void;
  /** 中止流式响应 */
  abortStream: () => void;
  /** 重置流式状态 */
  resetStream: () => void;
}

/**
 * 发送流式消息 Hook
 */
export function useStreamMessage(): UseStreamMessageReturn {
  const queryClient = useQueryClient();
  const streamControllerRef = useRef<StreamController | null>(null);

  const [streamState, setStreamState] = useState<StreamState>({
    isStreaming: false,
    content: '',
    message: null,
    error: null,
  });

  // 清理函数
  useEffect(() => {
    return () => {
      if (streamControllerRef.current) {
        streamControllerRef.current.abort();
        streamControllerRef.current = null;
      }
    };
  }, []);

  const sendStreamMessage = useCallback((request: SendMessageRequest) => {
    // 重置状态
    setStreamState({
      isStreaming: true,
      content: '',
      message: null,
      error: null,
    });

    const newMessage: AIMessage = {
      id: `temp-${Date.now()}`,
      sessionId: request.sessionId || '',
      role: 'assistant',
      content: '',
      status: 'streaming' as AIMessageStatus,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const handleChunk = (chunk: StreamChunk): void => {
      switch (chunk.type) {
        case 'content':
          setStreamState((prev) => ({
            ...prev,
            content: prev.content + chunk.data,
          }));
          break;
        case 'metadata':
          if (chunk.metadata) {
            setStreamState((prev) => ({
              ...prev,
              message: prev.message
                ? { ...prev.message, metadata: { ...prev.message.metadata, ...chunk.metadata } }
                : { ...newMessage, metadata: chunk.metadata },
            }));
          }
          break;
        case 'error':
          setStreamState((prev) => ({
            ...prev,
            isStreaming: false,
            error: {
              code: 'INTERNAL_ERROR',
              message: chunk.data,
            },
          }));
          break;
        case 'done':
          // 完成时会触发 onComplete
          break;
        default:
          break;
      }
    };

    const handleError = (error: AIConsultationError): void => {
      setStreamState((prev) => ({
        ...prev,
        isStreaming: false,
        error,
      }));
    };

    const handleComplete = (): void => {
      setStreamState((prev) => {
        const finalMessage: AIMessage = {
          ...newMessage,
          content: prev.content,
          status: 'completed' as AIMessageStatus,
          metadata: prev.message?.metadata,
        };

        // 刷新会话数据
        if (request.sessionId) {
          void queryClient.invalidateQueries({
            queryKey: AI_CONSULTATION_QUERY_KEYS.session(request.sessionId),
          });
        }

        return {
          isStreaming: false,
          content: prev.content,
          message: finalMessage,
          error: null,
        };
      });
    };

    // 启动流式请求
    streamControllerRef.current = apiSendMessageStream(
      request,
      handleChunk,
      handleError,
      handleComplete
    );
  }, [queryClient]);

  const abortStream = useCallback((): void => {
    if (streamControllerRef.current) {
      streamControllerRef.current.abort();
      streamControllerRef.current = null;
      setStreamState((prev) => ({
        ...prev,
        isStreaming: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: '用户取消',
        },
      }));
    }
  }, []);

  const resetStream = useCallback((): void => {
    if (streamControllerRef.current) {
      streamControllerRef.current.abort();
      streamControllerRef.current = null;
    }
    setStreamState({
      isStreaming: false,
      content: '',
      message: null,
      error: null,
    });
  }, []);

  return {
    streamState,
    sendStreamMessage,
    abortStream,
    resetStream,
  };
}

// ==================== Combined Hook ====================

/** 组合 Hook 返回类型 */
interface UseAIConsultationReturn {
  // 会话管理
  sessions: ReturnType<typeof useSessions>;
  currentSession: ReturnType<typeof useSession>;
  sessionHistory: ReturnType<typeof useSessionHistory>;
  createSession: ReturnType<typeof useCreateSession>;
  deleteSession: ReturnType<typeof useDeleteSession>;

  // 消息发送
  sendMessage: ReturnType<typeof useSendMessage>;
  streamMessage: ReturnType<typeof useStreamMessage>;

  // 会话切换
  setCurrentSessionId: (sessionId: string | undefined) => void;
  currentSessionId: string | undefined;
}

/**
 * AI 咨询组合 Hook
 */
export function useAIConsultation(): UseAIConsultationReturn {
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>();

  const sessions = useSessions();
  const currentSession = useSession(currentSessionId);
  const sessionHistory = useSessionHistory(
    currentSessionId ? { sessionId: currentSessionId, limit: 50 } : undefined
  );
  const createSession = useCreateSession();
  const deleteSession = useDeleteSession();
  const sendMessage = useSendMessage();
  const streamMessage = useStreamMessage();

  const handleSetCurrentSessionId = useCallback((sessionId: string | undefined) => {
    setCurrentSessionId(sessionId);
  }, []);

  return {
    sessions,
    currentSession,
    sessionHistory,
    createSession,
    deleteSession,
    sendMessage,
    streamMessage,
    setCurrentSessionId: handleSetCurrentSessionId,
    currentSessionId,
  };
}