/**
 * AI 咨询模块 API 层
 */

import { apiClient } from "@/shared/lib/api/client";

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


// API 基础路径
const API_BASE = '/ai';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
  code?: string;
  message?: string;
}

/** 后端原始消息元数据接口 */
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

/**
 * 安全获取 JSON 响应
 */
async function safeJson<T>(response: Response): Promise<T> {
  const data = await response.json() as T;
  return data;
}

/**
 * 获取 API 错误信息
 */
function getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiErrorResponse).detail || defaultMsg;
  }
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return (error as ApiErrorResponse).message || defaultMsg;
  }
  return defaultMsg;
}

/**
 * 获取错误码
 */
function getErrorCode(error: unknown): AIConsultationErrorCode {
  if (typeof error === 'object' && error !== null && 'code' in error) {
    const code = (error as ApiErrorResponse).code;
    if (code && isValidErrorCode(code)) {
      return code as AIConsultationErrorCode;
    }
  }
  return 'INTERNAL_ERROR';
}

/**
 * 验证错误码
 */
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

/**
 * 创建错误对象
 */
function createError(error: unknown): AIConsultationError {
  return {
    code: getErrorCode(error),
    message: getErrorMessage(error, '未知错误'),
    details: typeof error === 'object' && error !== null 
      ? error as Record<string, unknown> 
      : undefined,
  };
}

/**
 * 转换后端元数据为前端元数据
 */
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

// ==================== 会话管理 API ====================

/**
 * 创建新会话
 */
export async function apiCreateSession(
  request: CreateSessionRequest
): Promise<CreateSessionResponse> {
  const response = await apiClient.post<CreateSessionResponse>(`${API_BASE}/consultations`, {
    title: request.title,
    initial_message: request.initialMessage,
    category: request.category,
  });

  return response.data;
}

/**
 * 获取会话列表
 */
export async function apiGetSessions(
  params: GetSessionsRequest = {}
): Promise<GetSessionsResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));
  if (params.status) searchParams.set('status', params.status);

  const url = `${API_BASE}/consultations${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ 
      detail: '获取会话列表失败',
      code: 'INTERNAL_ERROR',
    }));
    throw new Error(getErrorMessage(error, '获取会话列表失败'));
  }

  const data = await safeJson<{
    sessions: Array<{
      id: string;
      user_id: string;
      title: string;
      status: string;
      created_at: string;
      updated_at: string;
      last_activity_at: string;
      context?: {
        category?: string;
        domain?: string;
        user_intent?: string;
      };
    }>;
    total: number;
    page: number;
    total_pages: number;
  }>(response);

  return {
    sessions: data.sessions.map(s => ({
      id: s.id,
      userId: s.user_id,
      title: s.title,
      status: s.status as 'active' | 'archived' | 'deleted',
      createdAt: s.created_at,
      updatedAt: s.updated_at,
      lastActivityAt: s.last_activity_at,
      context: s.context ? {
        category: s.context.category,
        domain: s.context.domain,
        userIntent: s.context.user_intent,
      } : undefined,
      messages: [],
    })),
    total: data.total,
    page: data.page,
    totalPages: data.total_pages,
  };
}

/**
 * 获取会话详情
 */
export async function apiGetSession(sessionId: string): Promise<AISession> {
  const response = await fetch(`${API_BASE}/consultations/${sessionId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ 
      detail: '获取会话详情失败',
      code: 'SESSION_NOT_FOUND',
    }));
    throw new Error(getErrorMessage(error, '获取会话详情失败'));
  }

  const data = await safeJson<{
    id: string;
    user_id: string;
    title: string;
    status: string;
    created_at: string;
    updated_at: string;
    last_activity_at: string;
    context?: {
      category?: string;
      domain?: string;
      user_intent?: string;
    };
    messages: Array<{
      id: string;
      session_id: string;
      role: string;
      content: string;
      status: string;
      created_at: string;
      updated_at: string;
      metadata?: BackendMessageMetadata;
    }>;
  }>(response);

  return {
    id: data.id,
    userId: data.user_id,
    title: data.title,
    status: data.status as 'active' | 'archived' | 'deleted',
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    lastActivityAt: data.last_activity_at,
    context: data.context ? {
      category: data.context.category,
      domain: data.context.domain,
      userIntent: data.context.user_intent,
    } : undefined,
    messages: data.messages.map(m => ({
      id: m.id,
      sessionId: m.session_id,
      role: m.role as 'user' | 'assistant' | 'system',
      content: m.content,
      status: m.status as 'sending' | 'streaming' | 'completed' | 'error',
      createdAt: m.created_at,
      updatedAt: m.updated_at,
      metadata: transformMetadata(m.metadata),
    })),
  };
}

/**
 * 获取会话历史消息
 */
export async function apiGetSessionHistory(
  params: GetSessionHistoryRequest
): Promise<GetSessionHistoryResponse> {
  const searchParams = new URLSearchParams();
  if (params.beforeMessageId) searchParams.set('before_message_id', params.beforeMessageId);
  if (params.limit) searchParams.set('limit', String(params.limit));

  const url = `${API_BASE}/consultations/${params.sessionId}/messages${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ 
      detail: '获取会话历史失败',
      code: 'SESSION_NOT_FOUND',
    }));
    throw new Error(getErrorMessage(error, '获取会话历史失败'));
  }

  const data = await safeJson<{
    messages: Array<{
      id: string;
      session_id: string;
      role: string;
      content: string;
      status: string;
      created_at: string;
      updated_at: string;
      metadata?: BackendMessageMetadata;
    }>;
    has_more: boolean;
  }>(response);

  return {
    messages: data.messages.map(m => ({
      id: m.id,
      sessionId: m.session_id,
      role: m.role as 'user' | 'assistant' | 'system',
      content: m.content,
      status: m.status as 'sending' | 'streaming' | 'completed' | 'error',
      createdAt: m.created_at,
      updatedAt: m.updated_at,
      metadata: transformMetadata(m.metadata),
    })),
    hasMore: data.has_more,
  };
}

/**
 * 删除会话
 */
export async function apiDeleteSession(sessionId: string): Promise<void> {
  await apiClient.delete(`${API_BASE}/consultations/${sessionId}`);
}

/**
 * 发送消息（非流式）
 */
export async function apiSendMessage(
  request: SendMessageRequest
): Promise<SendMessageResponse> {
  const response = await apiClient.post<{
    message_id: string;
    session_id: string;
    content: string;
    created_at: string;
    metadata?: BackendMessageMetadata;
  }>(`${API_BASE}/chat`, {
    session_id: request.sessionId,
    content: request.content,
    stream: false,
    context: request.context,
  });

  const data = response.data;

  return {
    messageId: data.message_id,
    sessionId: data.session_id,
    content: data.content,
    createdAt: data.created_at,
    metadata: transformMetadata(data.metadata),
  };
}

// ==================== 流式响应 API ====================

/** 流式响应回调函数类型 */
export type StreamCallback = (chunk: StreamChunk) => void;
export type StreamErrorCallback = (error: AIConsultationError) => void;
export type StreamCompleteCallback = () => void;

/** 流式响应控制接口 */
export interface StreamController {
  /** 中止流式响应 */
  abort: () => void;
}

/**
 * 发送消息（流式响应）
 */
export function apiSendMessageStream(
  request: SendMessageRequest,
  onChunk: StreamCallback,
  onError?: StreamErrorCallback,
  onComplete?: StreamCompleteCallback
): StreamController {
  const abortController = new AbortController();

  fetch(`${API_BASE}/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    credentials: 'include',
    body: JSON.stringify({
      session_id: request.sessionId,
      content: request.content,
      stream: true,
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
      throw new Error(getErrorMessage(errorData, '流式请求失败'));
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('无法读取响应流');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      // eslint-disable-next-line no-constant-condition
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
              const chunk = JSON.parse(data) as StreamChunk;
              onChunk(chunk);
            } catch {
              // 解析失败时作为普通内容处理
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

// ==================== 分享功能 API ====================

/**
 * 创建分享链接
 */
export async function apiCreateShare(request: CreateShareRequest): Promise<ShareLinkResponse> {
  const response = await apiClient.post<{
    token: string;
    share_path: string;
    expires_at: string;
  }>(`${API_BASE}/share`, {
    session_id: request.sessionId,
    expires_days: request.expiresDays ?? 7,
  });

  const data = response.data;

  return {
    token: data.token,
    sharePath: data.share_path,
    expiresAt: data.expires_at,
  };
}

/**
 * 获取分享的咨询内容
 */
export async function apiGetSharedConsultation(token: string): Promise<SharedConsultationResponse> {
  const response = await fetch(`${API_BASE}/share/${token}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取分享内容失败',
      code: 'SHARE_INVALID',
    }));
    throw new Error(getErrorMessage(error, '获取分享内容失败'));
  }

  const data = await safeJson<{
    session_id: string;
    title: string | null;
    created_at: string | null;
    messages: Array<{
      role: string;
      content: string;
      references?: string;
      created_at: string | null;
    }>;
  }>(response);

  return {
    sessionId: data.session_id,
    title: data.title,
    createdAt: data.created_at,
    messages: data.messages.map(m => ({
      role: m.role as 'user' | 'assistant' | 'system',
      content: m.content,
      references: m.references,
      createdAt: m.created_at,
    })),
  };
}

// ==================== 语音转写 API ====================

/**
 * 上传音频进行语音转写
 */
export async function apiTranscribeVoice(request: VoiceUploadRequest): Promise<TranscriptionResponse> {
  const formData = new FormData();
  formData.append('file', request.audioFile);
  if (request.segmentIndex !== undefined) {
    formData.append('segment_index', String(request.segmentIndex));
  }
  if (request.isFinal !== undefined) {
    formData.append('is_final', String(request.isFinal));
  }

  const response = await apiClient.post<{
    text: string;
    segment_index?: number;
    is_final?: boolean;
  }>(`${API_BASE}/transcribe`, formData);

  const data = response.data;

  return {
    text: data.text,
    segmentIndex: data.segment_index,
    isFinal: data.is_final,
  };
}

/**
 * 上传文件进行分析
 */
export async function apiAnalyzeFile(request: FileUploadRequest): Promise<FileAnalysisResponse> {
  const formData = new FormData();
  formData.append('file', request.file);

  const response = await apiClient.post<{
    filename: string;
    content_type?: string | null;
    text_chars: number;
    text_preview: string;
    summary: string;
  }>(`${API_BASE}/files/analyze`, formData);

  const data = response.data;

  return {
    filename: data.filename,
    contentType: data.content_type ?? null,
    textChars: data.text_chars,
    textPreview: data.text_preview,
    summary: data.summary,
  };
}

// ==================== 辅助函数 ====================

/**
 * 解析 SSE 事件流
 */
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