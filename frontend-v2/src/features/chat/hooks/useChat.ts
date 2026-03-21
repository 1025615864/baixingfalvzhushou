// ============================================
// Chat Hook - 聊天功能
// 连接后端真实 API
// ============================================

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/shared/lib/api/client';

import type { ChatMessage } from '../types';


// 查询 keys
export const chatKeys = {
  all: ['chat'] as const,
  sessions: () => [...chatKeys.all, 'sessions'] as const,
  messages: (sessionId: string) => [...chatKeys.all, 'messages', sessionId] as const,
};

// 后端 ChatResponse 接口（与后端 schemas/ai.py 对齐）
interface BackendChatResponse {
  session_id: string;
  answer: string;
  references: Array<{
    law_name: string;
    article: string;
    content: string;
    relevance: number;
    similarity: number;
    source?: string;
    source_url?: string;
  }>;
  assistant_message_id?: number;
  strategy_used?: string;
  confidence?: string;
  risk_level?: string;
  disclaimer?: string;
  intent?: string;
  needs_clarification?: boolean;
  clarifying_questions?: string[];
}

// 前端使用的响应接口
export interface SendMessageResponse {
  content: string;
  sessionId: string;
  metadata?: {
    sources?: string[];
    confidence?: number;
    suggestedQuestions?: string[];
    references?: BackendChatResponse['references'];
    assistantMessageId?: number;
  };
}

// 后端咨询列表项接口
interface BackendConsultationListItem {
  id: number;
  session_id: string;
  title: string | null;
  created_at: string;
  message_count: number;
}

// 后端咨询详情接口
interface BackendConsultationDetail {
  id: number;
  session_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages: Array<{
    id: number;
    role: string;
    content: string;
    references: string | null;
    rating: number | null;
    feedback: string | null;
    created_at: string;
  }>;
}

interface UseSendMessageOptions {
  onSuccess?: (data: SendMessageResponse) => void;
  onError?: (error: Error) => void;
}

export function useSendMessage(options: UseSendMessageOptions = {}) {
  return useMutation({
    mutationFn: async (data: { sessionId?: string; content: string }): Promise<SendMessageResponse> => {
      // 转换为后端期望的格式
      const payload = {
        message: data.content,
        session_id: data.sessionId || null,
      };
      const response = await api.post<BackendChatResponse>('/ai/chat', payload);
      
      // 转换后端响应为前端格式
      return {
        content: response.answer,
        sessionId: response.session_id,
        metadata: {
          sources: response.references?.map(ref => ref.law_name || ref.source || '未知来源'),
          confidence: response.confidence ?
            (response.confidence === 'high' ? 0.9 :
             response.confidence === 'medium' ? 0.7 : 0.5) : undefined,
          suggestedQuestions: response.clarifying_questions,
          references: response.references,
          assistantMessageId: response.assistant_message_id,
        },
      };
    },
    onSuccess: (data) => {
      options.onSuccess?.(data);
    },
    onError: (error) => {
      options.onError?.(error instanceof Error ? error : new Error(String(error)));
    },
  });
}

// 获取聊天历史
export function useChatHistory(sessionId: string) {
  return useQuery({
    queryKey: chatKeys.messages(sessionId),
    queryFn: async (): Promise<ChatMessage[]> => {
      if (!sessionId) return [];
      
      const response = await api.get<BackendConsultationDetail>(`/ai/consultations/${sessionId}`);
      
      // 转换后端消息格式为前端格式
      return response.messages.map(msg => ({
        id: String(msg.id),
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
        timestamp: msg.created_at,
        status: 'completed' as const,
        metadata: msg.references ? {
          sources: [msg.references],
        } : undefined,
      }));
    },
    enabled: !!sessionId,
  });
}

// 获取所有会话
export function useChatSessions() {
  return useQuery({
    queryKey: chatKeys.sessions(),
    queryFn: async (): Promise<Array<{ id: string; title: string; updatedAt: string }>> => {
      const response = await api.get<BackendConsultationListItem[]>('/ai/consultations');
      
      // 转换后端格式为前端格式
      return response.map(item => ({
        id: item.session_id,
        title: item.title || '未命名对话',
        updatedAt: item.created_at,
      }));
    },
  });
}

// 创建新会话（发送第一条消息时后端会自动创建）
export function useCreateChatSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (_title: string): Promise<{ id: string; title: string }> => {
      // 后端在发送消息时会自动创建会话，这里只需要返回一个临时ID
      // 实际的会话ID会在第一条消息发送后由后端返回
      const tempId = `temp-${Date.now()}`;
      return Promise.resolve({ id: tempId, title: _title });
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
      await api.delete(`/ai/consultations/${sessionId}`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
    },
  });
}

