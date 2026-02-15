import { api } from '@/shared/lib/api/client';
import type {
  ChatSession,
  ChatMessage,
  SendMessageRequest,
} from '@/features/chat/types';

// 获取会话列表
export const getSessions = () => api.get<ChatSession[]>('/chat/sessions');

// 获取会话详情
export const getSession = (sessionId: string) =>
  api.get<ChatSession>(`/chat/sessions/${sessionId}`);

// 创建新会话
export const createSession = () => api.post<ChatSession>('/chat/sessions');

// 删除会话
export const deleteSession = (sessionId: string) =>
  api.delete<void>(`/chat/sessions/${sessionId}`);

// 发送消息（流式）
export const sendMessageStream = async (
  data: SendMessageRequest,
  onChunk: (chunk: string) => void
) => {
  const response = await fetch(
    `${import.meta.env.VITE_API_BASE_URL}/chat/stream`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    throw new Error('发送消息失败');
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('无法读取响应');
  }

  const decoder = new TextDecoder();
  let done = false;
  while (!done) {
    const result = await reader.read();
    done = result.done;
    if (done) break;
    const { value } = result;
    const chunk = decoder.decode(value);
    onChunk(chunk);
  }
};

// 获取历史消息
export const getMessages = (sessionId: string) =>
  api.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);

// 清空会话历史
export const clearSession = (sessionId: string) =>
  api.post<void>(`/chat/sessions/${sessionId}/clear`);