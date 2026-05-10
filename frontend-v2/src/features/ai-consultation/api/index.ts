/**
 * AI 咨询模块 API 层
 * 对齐后端 AI 微服务实际端点:
 *   POST /api/v1/ai/chat          - 非流式对话
 *   POST /api/v1/ai/chat/stream   - 流式SSE对话
 *   GET  /api/v1/ai/sessions/{user_id} - 获取会话列表
 *   GET  /api/v1/ai/sessions/{session_id}/history - 获取会话历史
 */

import axios from 'axios';

import { getToken } from '@/shared/lib/security/tokenStorage';

import type {
  AISession,
  SendMessageRequest,
  SendMessageResponse,
  CreateSessionRequest,
  CreateSessionResponse,
  GetSessionsRequest,
  GetSessionsResponse,
  GetSessionHistoryRequest,
  GetSessionHistoryResponse,
  StreamChunk,
  AIConsultationError,
  AIConsultationErrorCode,
  AIMessageMetadata,
  ShareLinkResponse,
  SharedConsultationResponse,
  CreateShareRequest,
  TranscriptionResponse,
  VoiceUploadRequest,
  FileAnalysisResponse,
  FileUploadRequest,
} from '../types';


const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api';
const AI_BASE = `${API_BASE}/v1/ai`;

interface ApiErrorResponse {
  detail?: string;
  code?: string;
  message?: string;
}

interface BackendMessageMetadata {
  confidence?: number;
  sources?: Array<{
    id: string;
    title: string;
    url?: string;
    type: string;
    relevance_score?: number;
  }>;
  legal_references?: Array<{
    law_name: string;
    article_number: string;
    content: string;
    full_text_url?: string;
  }>;
  suggested_actions?: Array<{
    type: string;
    label: string;
    description?: string;
    params?: Record<string, string>;
  }>;
  model_info?: {
    model: string;
    version?: string;
    provider?: string;
  };
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  processing_time?: number;
}

function _getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiErrorResponse).detail || defaultMsg;
  }
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return (error as ApiErrorResponse).message || defaultMsg;
  }
  return defaultMsg;
}

function getErrorCode(error: unknown): AIConsultationErrorCode {
  if (typeof error === 'object' && error !== null && 'code' in error) {
    const code = (error as ApiErrorResponse).code;
    if (code && isValidErrorCode(code)) {
      return code as AIConsultationErrorCode;
    }
  }
  return 'INTERNAL_ERROR';
}

function isValidErrorCode(code: string): code is AIConsultationErrorCode {
  const validCodes: AIConsultationErrorCode[] = [
    'SESSION_NOT_FOUND',
    'SESSION_EXPIRED',
    'MESSAGE_TOO_LONG',
    'RATE_LIMIT_EXCEEDED',
    'MODEL_UNAVAILABLE',
    'INVALID_REQUEST',
    'UNAUTHORIZED',
    'INTERNAL_ERROR',
  ];
  return validCodes.includes(code as AIConsultationErrorCode);
}

function createError(error: unknown): AIConsultationError {
  return {
    code: getErrorCode(error),
    message: _getErrorMessage(error, '未知错误'),
    details: typeof error === 'object' && error !== null
      ? error as Record<string, unknown>
      : undefined,
  };
}

function transformMetadata(backendMetadata: BackendMessageMetadata | undefined): AIMessageMetadata | undefined {
  if (!backendMetadata) {
    return undefined;
  }

  return {
    confidence: backendMetadata.confidence,
    sources: backendMetadata.sources?.map(s => ({
      id: s.id,
      title: s.title,
      url: s.url,
      type: s.type as 'law' | 'case' | 'article' | 'document' | 'knowledge_base',
      relevanceScore: s.relevance_score,
    })),
    legalReferences: backendMetadata.legal_references?.map(l => ({
      lawName: l.law_name,
      articleNumber: l.article_number,
      content: l.content,
      fullTextUrl: l.full_text_url,
    })),
    suggestedActions: backendMetadata.suggested_actions?.map(a => ({
      type: a.type as 'consult_lawyer' | 'view_case' | 'generate_document' | 'schedule_appointment' | 'read_article' | 'ask_followup',
      label: a.label,
      description: a.description,
      params: a.params,
    })),
    modelInfo: backendMetadata.model_info,
    tokenUsage: backendMetadata.token_usage ? {
      promptTokens: backendMetadata.token_usage.prompt_tokens,
      completionTokens: backendMetadata.token_usage.completion_tokens,
      totalTokens: backendMetadata.token_usage.total_tokens,
    } : undefined,
    processingTime: backendMetadata.processing_time,
  };
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// ==================== 会话管理 API ====================

export async function apiCreateSession(
  request: CreateSessionRequest
): Promise<CreateSessionResponse> {
  const response = await axios.post<{
    session_id: string;
    message?: { session_id: string; content: string; created_at: string; metadata?: BackendMessageMetadata };
  }>(`${AI_BASE}/chat`, {
    session_id: request.initialMessage ? undefined : undefined,
    message: request.initialMessage || request.title || '你好',
    context: request.category ? { category: request.category } : undefined,
  }, {
    headers: getAuthHeaders(),
    withCredentials: true,
  });

  const data = response.data;
  return {
    sessionId: data.session_id,
    title: request.title || '新对话',
    createdAt: new Date().toISOString(),
  };
}

export async function apiGetSessions(
  params: GetSessionsRequest = {}
): Promise<GetSessionsResponse> {
  const token = getToken();
  let userId = 'me';
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      userId = String(payload.sub || payload.user_id || 'me');
    } catch { /* fallback to 'me' */ }
  }

  const response = await axios.get<{
    items: Array<{
      id: string;
      user_id: string;
      title?: string;
      status?: string;
      created_at: string;
      updated_at?: string;
      context?: { category?: string; domain?: string; user_intent?: string };
    }>;
  }>(`${AI_BASE}/sessions/${userId}`, {
    headers: getAuthHeaders(),
    withCredentials: true,
    params: {
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
    },
  });

  const data = response.data;
  const items = data.items || [];
  return {
    sessions: items.map(s => ({
      id: s.id,
      userId: s.user_id,
      title: s.title || '对话',
      status: (s.status || 'active') as 'active' | 'archived' | 'deleted',
      createdAt: s.created_at,
      updatedAt: s.updated_at || s.created_at,
      lastActivityAt: s.updated_at || s.created_at,
      context: s.context ? {
        category: s.context.category,
        domain: s.context.domain,
        userIntent: s.context.user_intent,
      } : undefined,
      messages: [],
    })),
    total: items.length,
    page: params.page || 1,
    totalPages: 1,
  };
}

export async function apiGetSession(sessionId: string): Promise<AISession> {
  const historyResponse = await axios.get<{
    items: Array<{
      id: string;
      session_id: string;
      role: string;
      content: string;
      status?: string;
      created_at: string;
      updated_at?: string;
      metadata?: BackendMessageMetadata;
    }>;
  }>(`${AI_BASE}/sessions/${sessionId}/history`, {
    headers: getAuthHeaders(),
    withCredentials: true,
  });

  const messages = historyResponse.data.items || [];
  return {
    id: sessionId,
    userId: '',
    title: '对话',
    status: 'active',
    createdAt: messages[0]?.created_at || new Date().toISOString(),
    updatedAt: messages[messages.length - 1]?.updated_at || new Date().toISOString(),
    lastActivityAt: messages[messages.length - 1]?.updated_at || new Date().toISOString(),
    messages: messages.map(m => ({
      id: m.id,
      sessionId: m.session_id,
      role: m.role as 'user' | 'assistant' | 'system',
      content: m.content,
      status: (m.status || 'completed') as 'sending' | 'streaming' | 'completed' | 'error',
      createdAt: m.created_at,
      updatedAt: m.updated_at || m.created_at,
      metadata: transformMetadata(m.metadata),
    })),
  };
}

export async function apiGetSessionHistory(
  params: GetSessionHistoryRequest
): Promise<GetSessionHistoryResponse> {
  const response = await axios.get<{
    items: Array<{
      id: string;
      session_id: string;
      role: string;
      content: string;
      status?: string;
      created_at: string;
      updated_at?: string;
      metadata?: BackendMessageMetadata;
    }>;
  }>(`${AI_BASE}/sessions/${params.sessionId}/history`, {
    headers: getAuthHeaders(),
    withCredentials: true,
    params: {
      ...(params.limit && { limit: params.limit }),
    },
  });

  const data = response.data;
  return {
    messages: (data.items || []).map(m => ({
      id: m.id,
      sessionId: m.session_id,
      role: m.role as 'user' | 'assistant' | 'system',
      content: m.content,
      status: (m.status || 'completed') as 'sending' | 'streaming' | 'completed' | 'error',
      createdAt: m.created_at,
      updatedAt: m.updated_at || m.created_at,
      metadata: transformMetadata(m.metadata),
    })),
    hasMore: false,
  };
}

export async function apiDeleteSession(sessionId: string): Promise<void> {
  console.warn('Delete session API not implemented on backend yet');
}

export async function apiSendMessage(
  request: SendMessageRequest
): Promise<SendMessageResponse> {
  const response = await axios.post<{
    session_id: string;
    message: {
      id?: string;
      content: string;
      created_at?: string;
      metadata?: BackendMessageMetadata;
    };
    model?: string;
    sources?: Array<unknown>;
    intent?: string;
    latency_ms?: number;
  }>(`${AI_BASE}/chat`, {
    session_id: request.sessionId,
    message: request.content,
    context: request.context,
  }, {
    headers: getAuthHeaders(),
    withCredentials: true,
  });

  const data = response.data;
  return {
    messageId: data.message?.id || '',
    sessionId: data.session_id,
    content: data.message?.content || '',
    createdAt: data.message?.created_at || new Date().toISOString(),
    metadata: transformMetadata(data.message?.metadata),
  };
}

// ==================== 流式响应 API ====================

export type StreamCallback = (chunk: StreamChunk) => void;
export type StreamErrorCallback = (error: AIConsultationError) => void;
export type StreamCompleteCallback = () => void;

export interface StreamController {
  abort: () => void;
}

export function apiSendMessageStream(
  request: SendMessageRequest,
  onChunk: StreamCallback,
  onError?: StreamErrorCallback,
  onComplete?: StreamCompleteCallback
): StreamController {
  const abortController = new AbortController();

  fetch(`${AI_BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
      'Accept': 'text/event-stream',
    },
    credentials: 'include',
    body: JSON.stringify({
      session_id: request.sessionId,
      message: request.content,
      context: request.context,
    }),
    signal: abortController.signal,
  }).then(async (response) => {
    if (!response.ok) {
      const errorText = await response.text().catch(() => '流式请求失败');
      let errorData: ApiErrorResponse;
      try {
        errorData = JSON.parse(errorText) as ApiErrorResponse;
      } catch {
        errorData = { detail: errorText, code: 'INTERNAL_ERROR' };
      }
      throw new Error(_getErrorMessage(errorData, '流式请求失败'));
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('无法读取响应流');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let currentSessionId = request.sessionId;

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          onComplete?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);

            if (data === '[DONE]') {
              onComplete?.();
              return;
            }

            try {
              const parsed = JSON.parse(data);
              const eventType = parsed.type;

              if (eventType === 'session') {
                currentSessionId = parsed.session_id || currentSessionId;
                onChunk({
                  type: 'metadata',
                  data: JSON.stringify({ sessionId: currentSessionId }),
                });
              } else if (eventType === 'stage') {
                onChunk({
                  type: 'metadata',
                  data: JSON.stringify({ stage: parsed.stage }),
                });
              } else if (eventType === 'token') {
                onChunk({
                  type: 'content',
                  data: parsed.content || '',
                });
              } else if (eventType === 'done') {
                onChunk({
                  type: 'done',
                  data: JSON.stringify({ sessionId: parsed.session_id || currentSessionId }),
                });
              } else if (eventType === 'error') {
                onChunk({
                  type: 'error',
                  data: parsed.error || '未知错误',
                });
              } else {
                onChunk({
                  type: 'content',
                  data: typeof parsed === 'string' ? parsed : JSON.stringify(parsed),
                });
              }
            } catch {
              onChunk({
                type: 'content',
                data: data,
              });
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      throw error;
    } finally {
      reader.releaseLock();
    }
  }).catch((error) => {
    if (error instanceof Error && error.name === 'AbortError') {
      return;
    }
    onError?.(createError(error));
  });

  return {
    abort: () => abortController.abort(),
  };
}

// ==================== 分享功能 API (待后端实现) ====================

export async function apiCreateShare(_request: CreateShareRequest): Promise<ShareLinkResponse> {
  throw new Error('分享功能暂未实现');
}

export async function apiGetSharedConsultation(_token: string): Promise<SharedConsultationResponse> {
  throw new Error('分享功能暂未实现');
}

// ==================== 语音转写 API (待后端实现) ====================

export async function apiTranscribeVoice(_request: VoiceUploadRequest): Promise<TranscriptionResponse> {
  throw new Error('语音转写功能暂未实现');
}

export async function apiAnalyzeFile(_request: FileUploadRequest): Promise<FileAnalysisResponse> {
  throw new Error('文件分析功能暂未实现');
}

// ==================== 辅助函数 ====================

export function parseSSEEvent(line: string): { event?: string; data: string; id?: string } | null {
  if (!line.trim() || line.startsWith(':')) {
    return null;
  }

  const result: { event?: string; data: string; id?: string } = { data: '' };
  const parts = line.split('\n');

  for (const part of parts) {
    if (part.startsWith('event: ')) {
      result.event = part.slice(7);
    } else if (part.startsWith('data: ')) {
      result.data = part.slice(6);
    } else if (part.startsWith('id: ')) {
      result.id = part.slice(4);
    }
  }

  return result;
}

export function convertMessageMetadata<T extends Record<string, unknown>>(
  backendData: T
): T {
  const result: Partial<T> = {};

  for (const [key, value] of Object.entries(backendData)) {
    const camelKey = key.replace(/_([a-z])/g, (match: string, letter: string) => letter.toUpperCase()) as keyof T;
    result[camelKey] = value as T[keyof T];
  }

  return result as T;
}

export function convertMessageMetadataRequest<T extends Record<string, unknown>>(
  frontendData: T
): T {
  const result: Partial<T> = {};

  for (const [key, value] of Object.entries(frontendData)) {
    const snakeKey = key.replace(/([A-Z])/g, '_$1').toLowerCase() as keyof T;
    result[snakeKey] = value as T[keyof T];
  }

  return result as T;
}
