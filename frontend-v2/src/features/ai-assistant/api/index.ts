/**
 * AI Assistant（AI助手）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/ai 端点
 */

import { apiClient } from "@/shared/lib/api/client";

// API 基础路径
const API_BASE = '/ai';

// ==================== 后端响应类型定义 ====================

/** 法律引用 */
interface BackendLawReference {
  law_name: string;
  article: string;
  content: string;
  relevance: number;
  similarity: number;
  source?: string;
  source_url?: string;
  source_version?: string;
  source_hash?: string;
  knowledge_id?: number;
  ingest_batch_id?: string;
}

/** 检索质量信息 */
interface BackendSearchQualityInfo {
  total_candidates: number;
  qualified_count: number;
  avg_similarity: number;
  confidence: string;
}

/** AI聊天响应 */
interface BackendChatResponse {
  session_id: string;
  answer: string;
  references: BackendLawReference[];
  assistant_message_id?: number;
  strategy_used?: string;
  strategy_reason?: string;
  confidence?: string;
  risk_level?: string;
  search_quality?: BackendSearchQualityInfo;
  disclaimer?: string;
  model_used?: string;
  fallback_used?: boolean;
  model_attempts?: string[];
  intent?: string;
  needs_clarification?: boolean;
  clarifying_questions?: string[];
  created_at: string;
}

/** AI流式聊天响应片段 */
interface BackendStreamChunk {
  delta: string;
  session_id: string;
  references?: BackendLawReference[];
  done?: boolean;
  error?: string;
}

/** 消息响应 */
interface BackendMessageResponse {
  id: number;
  role: string;
  content: string;
  references?: string | null;
  rating?: number | null;
  feedback?: string | null;
  created_at: string;
}

/** 咨询会话响应 */
interface BackendConsultationResponse {
  id: number;
  session_id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  messages: BackendMessageResponse[];
}

/** 咨询列表项 */
interface BackendConsultationListItem {
  id: number;
  session_id: string;
  title?: string;
  created_at: string;
  message_count: number;
}

/** 分享链接响应 */
interface BackendShareLinkResponse {
  token: string;
  share_path: string;
  expires_at: string;
}

/** 分享的消息响应 */
interface BackendSharedMessageResponse {
  role: string;
  content: string;
  references?: string | null;
  created_at?: string;
}

/** 分享的咨询响应 */
interface BackendSharedConsultationResponse {
  session_id: string;
  title?: string;
  created_at?: string;
  messages: BackendSharedMessageResponse[];
}

/** 文件分析响应 */
interface BackendFileAnalyzeResponse {
  filename: string;
  content_type?: string;
  text_chars: number;
  text_preview: string;
  summary: string;
}

/** 语音转写响应 */
interface BackendTranscribeResponse {
  text: string;
  segment_index?: number;
  is_final?: boolean;
}

/** 快捷回复响应 */
interface BackendQuickRepliesResponse {
  replies: string[];
}

/** 评价响应 */
interface BackendRatingResponse {
  success: boolean;
  message: string;
}

// ==================== 前端类型定义 ====================

/** 法律引用 */
export interface LawReference {
  lawName: string;
  article: string;
  content: string;
  relevance: number;
  similarity: number;
  source?: string;
  sourceUrl?: string;
  sourceVersion?: string;
  sourceHash?: string;
  knowledgeId?: number;
  ingestBatchId?: string;
}

/** 检索质量信息 */
export interface SearchQualityInfo {
  totalCandidates: number;
  qualifiedCount: number;
  avgSimilarity: number;
  confidence: string;
}

/** AI聊天响应 */
export interface ChatResponse {
  sessionId: string;
  answer: string;
  references: LawReference[];
  assistantMessageId?: number;
  strategyUsed?: string;
  strategyReason?: string;
  confidence?: string;
  riskLevel?: string;
  searchQuality?: SearchQualityInfo;
  disclaimer?: string;
  modelUsed?: string;
  fallbackUsed?: boolean;
  modelAttempts?: string[];
  intent?: string;
  needsClarification?: boolean;
  clarifyingQuestions?: string[];
  createdAt: string;
}

/** 消息 */
export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  references?: LawReference[];
  rating?: number;
  feedback?: string;
  createdAt: string;
}

/** 咨询会话 */
export interface Consultation {
  id: number;
  sessionId: string;
  title?: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

/** 咨询列表项 */
export interface ConsultationListItem {
  id: number;
  sessionId: string;
  title?: string;
  createdAt: string;
  messageCount: number;
}

/** 分享链接 */
export interface ShareLink {
  token: string;
  sharePath: string;
  expiresAt: string;
}

/** 分享的咨询内容 */
export interface SharedConsultation {
  sessionId: string;
  title?: string;
  createdAt?: string;
  messages: Array<{
    role: string;
    content: string;
    references?: LawReference[];
    createdAt?: string;
  }>;
}

/** 文件分析结果 */
export interface FileAnalyzeResult {
  filename: string;
  contentType?: string;
  textChars: number;
  textPreview: string;
  summary: string;
}

/** 语音转写结果 */
export interface TranscribeResult {
  text: string;
  segmentIndex?: number;
  isFinal?: boolean;
}

// ==================== 转换函数 ====================

/**
 * 转换后端法律引用到前端格式
 */
function mapBackendToLawReference(data: BackendLawReference): LawReference {
  return {
    lawName: data.law_name,
    article: data.article,
    content: data.content,
    relevance: data.relevance,
    similarity: data.similarity,
    source: data.source,
    sourceUrl: data.source_url,
    sourceVersion: data.source_version,
    sourceHash: data.source_hash,
    knowledgeId: data.knowledge_id,
    ingestBatchId: data.ingest_batch_id,
  };
}

/**
 * 转换后端检索质量信息到前端格式
 */
function mapBackendToSearchQuality(data?: BackendSearchQualityInfo): SearchQualityInfo | undefined {
  if (!data) return undefined;
  return {
    totalCandidates: data.total_candidates,
    qualifiedCount: data.qualified_count,
    avgSimilarity: data.avg_similarity,
    confidence: data.confidence,
  };
}

/**
 * 转换后端消息到前端格式
 */
function mapBackendToMessage(data: BackendMessageResponse): ChatMessage {
  let references: LawReference[] | undefined;
  if (data.references) {
    try {
       
      const parsed: unknown = JSON.parse(data.references);
      if (Array.isArray(parsed)) {
        references = (parsed as BackendLawReference[]).map(mapBackendToLawReference);
      } else if (parsed && typeof parsed === 'object' && 'references' in parsed) {
        const parsedObj = parsed as { references?: BackendLawReference[] };
        if (Array.isArray(parsedObj.references)) {
          references = parsedObj.references.map(mapBackendToLawReference);
        }
      }
    } catch {
      // 解析失败时忽略
    }
  }
  return {
    id: data.id,
    role: data.role as 'user' | 'assistant',
    content: data.content,
    references,
    rating: data.rating ?? undefined,
    feedback: data.feedback ?? undefined,
    createdAt: data.created_at,
  };
}

// ==================== AI 对话 API ====================

/**
 * AI聊天（非流式）
 */
export async function apiChat(message: string, sessionId?: string): Promise<ChatResponse> {
  const response = await apiClient.post<BackendChatResponse>(`${API_BASE}/chat`, {
    message,
    session_id: sessionId,
  });

  return {
    sessionId: response.data.session_id,
    answer: response.data.answer,
    references: response.data.references.map(mapBackendToLawReference),
    assistantMessageId: response.data.assistant_message_id,
    strategyUsed: response.data.strategy_used,
    strategyReason: response.data.strategy_reason,
    confidence: response.data.confidence,
    riskLevel: response.data.risk_level,
    searchQuality: mapBackendToSearchQuality(response.data.search_quality),
    disclaimer: response.data.disclaimer,
    modelUsed: response.data.model_used,
    fallbackUsed: response.data.fallback_used,
    modelAttempts: response.data.model_attempts,
    intent: response.data.intent,
    needsClarification: response.data.needs_clarification,
    clarifyingQuestions: response.data.clarifying_questions,
    createdAt: response.data.created_at,
  };
}

/**
 * AI流式聊天
 */
export async function* apiChatStream(message: string, sessionId?: string): AsyncGenerator<{
  delta: string;
  sessionId: string;
  references?: LawReference[];
  done?: boolean;
  error?: string;
}> {
  const response = await apiClient.post<ReadableStream<Uint8Array>>(
    `${API_BASE}/chat/stream`,
    {
      message,
      session_id: sessionId,
    },
    {
      responseType: 'stream',
    }
  );

  const reader = (response.data as unknown as ReadableStream<Uint8Array>).getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (!line.trim()) continue;

        try {
           
          const data: unknown = JSON.parse(line);
          const chunk = data as BackendStreamChunk;
          yield {
            delta: chunk.delta,
            sessionId: chunk.session_id,
            references: chunk.references?.map(mapBackendToLawReference),
            done: chunk.done,
            error: chunk.error,
          };

          if (chunk.done || chunk.error) {
            return;
          }
        } catch {
          // 忽略解析失败的行
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * 获取快捷回复建议
 */
export async function apiGetQuickReplies(
  userMessage: string,
  assistantAnswer: string,
  references?: LawReference[]
): Promise<string[]> {
  const response = await apiClient.post<BackendQuickRepliesResponse>(
    `${API_BASE}/quick-replies`,
    {
      user_message: userMessage,
      assistant_answer: assistantAnswer,
      references: references?.map(ref => ({
        law_name: ref.lawName,
        article: ref.article,
        content: ref.content,
        relevance: ref.relevance,
        similarity: ref.similarity,
      })),
    }
  );

  return response.data.replies;
}

/**
 * 评价AI回复
 */
export async function apiRateMessage(
  messageId: number,
  rating: 1 | 2 | 3,
  feedback?: string
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<BackendRatingResponse>(`${API_BASE}/rate`, {
    message_id: messageId,
    rating,
    feedback,
  });

  return {
    success: response.data.success,
    message: response.data.message,
  };
}

// ==================== 咨询管理 API ====================

/**
 * 获取咨询列表
 */
export async function apiGetConsultations(
  skip: number = 0,
  limit: number = 20,
  q?: string
): Promise<ConsultationListItem[]> {
  const response = await apiClient.get<BackendConsultationListItem[]>(
    `${API_BASE}/consultations`,
    {
      params: {
        skip,
        limit,
        q,
      },
    }
  );

  return response.data.map(item => ({
    id: item.id,
    sessionId: item.session_id,
    title: item.title,
    createdAt: item.created_at,
    messageCount: item.message_count,
  }));
}

/**
 * 获取咨询详情
 */
export async function apiGetConsultation(sessionId: string): Promise<Consultation> {
  const response = await apiClient.get<BackendConsultationResponse>(
    `${API_BASE}/consultations/${sessionId}`
  );

  return {
    id: response.data.id,
    sessionId: response.data.session_id,
    title: response.data.title,
    createdAt: response.data.created_at,
    updatedAt: response.data.updated_at,
    messages: response.data.messages.map(mapBackendToMessage),
  };
}

/**
 * 删除咨询记录
 */
export async function apiDeleteConsultation(sessionId: string): Promise<{ message: string }> {
  const response = await apiClient.delete<{ message: string }>(
    `${API_BASE}/consultations/${sessionId}`
  );
  return response.data;
}

/**
 * 导出咨询记录
 */
export async function apiExportConsultation(sessionId: string): Promise<Record<string, unknown>> {
  const response = await apiClient.get<Record<string, unknown>>(
    `${API_BASE}/consultations/${sessionId}/export`
  );
  return response.data;
}

/**
 * 生成咨询报告
 */
export async function apiGetConsultationReport(
  sessionId: string,
  format: 'pdf' = 'pdf'
): Promise<Blob> {
  const response = await apiClient.get<Blob>(
    `${API_BASE}/consultations/${sessionId}/report`,
    {
      params: { format },
      responseType: 'blob',
    }
  );
  return response.data;
}

// ==================== 分享 API ====================

/**
 * 创建分享链接
 */
export async function apiCreateShareLink(
  sessionId: string,
  expiresDays: number = 7
): Promise<ShareLink> {
  const response = await apiClient.post<BackendShareLinkResponse>(
    `${API_BASE}/consultations/${sessionId}/share`,
    undefined,
    {
      params: { expires_days: expiresDays },
    }
  );

  return {
    token: response.data.token,
    sharePath: response.data.share_path,
    expiresAt: response.data.expires_at,
  };
}

/**
 * 获取分享的咨询内容（公开访问，无需登录）
 */
export async function apiGetSharedConsultation(token: string): Promise<SharedConsultation> {
  const response = await apiClient.get<BackendSharedConsultationResponse>(
    `${API_BASE}/share/${token}`
  );

  return {
    sessionId: response.data.session_id,
    title: response.data.title,
    createdAt: response.data.created_at,
    messages: response.data.messages.map(msg => {
      let references: LawReference[] | undefined;
      if (msg.references) {
        try {
           
          const parsed: unknown = JSON.parse(msg.references);
          if (Array.isArray(parsed)) {
            references = (parsed as BackendLawReference[]).map(mapBackendToLawReference);
          }
        } catch {
          // 解析失败时忽略
        }
      }
      return {
        role: msg.role,
        content: msg.content,
        references,
        createdAt: msg.created_at,
      };
    }),
  };
}

// ==================== 分析 API ====================

/**
 * 分析文件
 */
export async function apiAnalyzeFile(file: File): Promise<FileAnalyzeResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<BackendFileAnalyzeResponse>(
    `${API_BASE}/files/analyze`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return {
    filename: response.data.filename,
    contentType: response.data.content_type,
    textChars: response.data.text_chars,
    textPreview: response.data.text_preview,
    summary: response.data.summary,
  };
}

// ==================== 语音转写 API ====================

/**
 * 语音转写
 */
export async function apiTranscribe(
  audioFile: File,
  segmentIndex?: number,
  isFinal?: boolean
): Promise<TranscribeResult> {
  const formData = new FormData();
  formData.append('file', audioFile);
  if (segmentIndex !== undefined) {
    formData.append('segment_index', segmentIndex.toString());
  }
  if (isFinal !== undefined) {
    formData.append('is_final', isFinal.toString());
  }

  const response = await apiClient.post<BackendTranscribeResponse>(
    `${API_BASE}/transcribe`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return {
    text: response.data.text,
    segmentIndex: response.data.segment_index,
    isFinal: response.data.is_final,
  };
}

// ==================== 统一导出 ====================

/**
 * AI Assistant API 统一导出对象
 */
export const aiAssistantApi = {
  // AI对话
  chat: apiChat,
  chatStream: apiChatStream,
  getQuickReplies: apiGetQuickReplies,
  rateMessage: apiRateMessage,

  // 咨询管理
  getConsultations: apiGetConsultations,
  getConsultation: apiGetConsultation,
  deleteConsultation: apiDeleteConsultation,
  exportConsultation: apiExportConsultation,
  getConsultationReport: apiGetConsultationReport,

  // 分享
  createShareLink: apiCreateShareLink,
  getSharedConsultation: apiGetSharedConsultation,

  // 分析
  analyzeFile: apiAnalyzeFile,

  // 语音转写
  transcribe: apiTranscribe,
} as const;

export default aiAssistantApi;