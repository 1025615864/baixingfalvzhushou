/**
 * Chat API - 聊天功能 API 接口
 * 连接真实后端 API
 *
 * 后端 API 路径：
 * - POST /ai/chat - 发送消息（后端自动创建会话）
 * - GET /ai/consultations - 获取会话列表
 * - GET /ai/consultations/:sessionId - 获取会话详情
 * - DELETE /ai/consultations/:sessionId - 删除会话
 */

import { api } from '@/shared/lib/api/client';

// 后端响应类型
interface BackendChatResponse {
  session_id: string;
  answer: string;
  references: Array<{
    law_name: string;
    article: string;
    content: string;
    relevance: number;
    similarity: number;
  }>;
  assistant_message_id?: number;
  confidence?: string;
}

interface BackendConsultationListItem {
  id: number;
  session_id: string;
  title: string | null;
  created_at: string;
  message_count: number;
}

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
    created_at: string;
  }>;
}

// 获取会话列表
export const getSessions = () =>
  api.get<BackendConsultationListItem[]>('/ai/consultations');

// 获取会话详情
export const getSession = (sessionId: string) =>
  api.get<BackendConsultationDetail>(`/ai/consultations/${sessionId}`);

// 删除会话
export const deleteSession = (sessionId: string) =>
  api.delete<void>(`/ai/consultations/${sessionId}`);

// 发送消息（非流式）- 后端会自动创建会话
export const sendMessage = (data: { message: string; session_id?: string | null }) =>
  api.post<BackendChatResponse>('/ai/chat', data);

// 获取历史消息（通过获取会话详情）
export const getMessages = (sessionId: string) =>
  api.get<BackendConsultationDetail>(`/ai/consultations/${sessionId}`);

// 导出类型供其他模块使用
export type {
  BackendChatResponse,
  BackendConsultationListItem,
  BackendConsultationDetail,
};