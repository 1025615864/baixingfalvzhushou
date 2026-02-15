// ============================================
// Chat Hook - 聊天功能
// ============================================

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/shared/lib/api/client';

import type { SendMessageRequest, ChatMessage } from '../types';

// 查询 keys
export const chatKeys = {
  all: ['chat'] as const,
  sessions: () => [...chatKeys.all, 'sessions'] as const,
  messages: (sessionId: string) => [...chatKeys.all, 'messages', sessionId] as const,
};

interface SendMessageResponse {
  content: string;
  metadata?: {
    sources?: string[];
    confidence?: number;
    suggestedQuestions?: string[];
  };
}

interface UseSendMessageOptions {
  onSuccess?: (data: SendMessageResponse) => void;
  onError?: (error: Error) => void;
}

export function useSendMessage(options: UseSendMessageOptions = {}) {
  return useMutation({
    mutationFn: async (data: SendMessageRequest): Promise<SendMessageResponse> => {
      const response = await api.post<SendMessageResponse>('/ai/chat', data);
      return response;
    },
    onSuccess: (data) => {
      options.onSuccess?.(data);
    },
    onError: (error) => {
      options.onError?.(error);
    },
  });
}

// 获取聊天历史
export function useChatHistory(sessionId: string) {
  return useQuery({
    queryKey: chatKeys.messages(sessionId),
    queryFn: async (): Promise<ChatMessage[]> => {
      const response = await api.get<ChatMessage[]>(`/ai/sessions/${sessionId}`);
      return response;
    },
    enabled: !!sessionId,
  });
}

// 获取所有会话
export function useChatSessions() {
  return useQuery({
    queryKey: chatKeys.sessions(),
    queryFn: async (): Promise<Array<{ id: string; title: string; updatedAt: string }>> => {
      const response = await api.get<Array<{ id: string; title: string; updatedAt: string }>>('/ai/sessions');
      return response;
    },
  });
}

// 创建新会话
export function useCreateChatSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (title: string): Promise<{ id: string; title: string }> => {
      const response = await api.post<{ id: string; title: string }>('/ai/sessions', { title });
      return response;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
    },
  });
}

// 删除会话
export function useDeleteChatSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sessionId: string): Promise<void> => {
      await api.delete(`/ai/sessions/${sessionId}`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
    },
  });
}

