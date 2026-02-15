/**
 * AI 咨询模块类型定义
 */

// ==================== 基础类型 ====================

/** AI 消息角色 */
export type AIMessageRole = 'user' | 'assistant' | 'system';

/** AI 消息状态 */
export type AIMessageStatus = 'sending' | 'streaming' | 'completed' | 'error';

/** 置信度等级 */
export type ConfidenceLevel = 'high' | 'medium' | 'low';

/** 会话状态 */
export type AISessionStatus = 'active' | 'archived' | 'deleted';

/** 录音状态 */
export type RecordingStatus = 'idle' | 'recording' | 'processing' | 'completed' | 'error';

/** 文件上传状态 */
export type FileUploadStatus = 'idle' | 'uploading' | 'processing' | 'completed' | 'error';

// ==================== 消息类型 ====================

/** AI 消息接口 */
export interface AIMessage {
  /** 消息唯一标识 */
  id: string;
  /** 会话 ID */
  sessionId: string;
  /** 消息角色 */
  role: AIMessageRole;
  /** 消息内容 */
  content: string;
  /** 消息状态 */
  status: AIMessageStatus;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
  /** 元数据（可选） */
  metadata?: AIMessageMetadata;
}

/** AI 消息元数据 */
export interface AIMessageMetadata {
  /** 置信度分数 (0-1) */
  confidence?: number;
  /** 引用来源 */
  sources?: AISource[];
  /** 相关法条 */
  legalReferences?: LegalReference[];
  /** 建议操作 */
  suggestedActions?: SuggestedAction[];
  /** 模型信息 */
  modelInfo?: AIModelInfo;
  /** token 使用量 */
  tokenUsage?: TokenUsage;
  /** 处理时间（毫秒） */
  processingTime?: number;
}

/** AI 来源引用 */
export interface AISource {
  /** 来源 ID */
  id: string;
  /** 来源标题 */
  title: string;
  /** 来源链接 */
  url?: string;
  /** 来源类型 */
  type: SourceType;
  /** 相关性分数 */
  relevanceScore?: number;
}

/** 来源类型 */
export type SourceType = 'law' | 'case' | 'article' | 'document' | 'knowledge_base';

/** 法律引用 */
export interface LegalReference {
  /** 法条名称 */
  lawName: string;
  /** 条款编号 */
  articleNumber: string;
  /** 条款内容摘要 */
  content: string;
  /** 完整内容链接 */
  fullTextUrl?: string;
}

/** 建议操作 */
export interface SuggestedAction {
  /** 操作类型 */
  type: ActionType;
  /** 操作标签 */
  label: string;
  /** 操作描述 */
  description?: string;
  /** 操作参数 */
  params?: Record<string, string>;
}

/** 操作类型 */
export type ActionType = 
  | 'consult_lawyer' 
  | 'view_case' 
  | 'generate_document' 
  | 'schedule_appointment' 
  | 'read_article'
  | 'ask_followup';

/** AI 模型信息 */
export interface AIModelInfo {
  /** 模型名称 */
  model: string;
  /** 模型版本 */
  version?: string;
  /** 提供商 */
  provider?: string;
}

/** Token 使用量 */
export interface TokenUsage {
  /** 输入 token 数 */
  promptTokens: number;
  /** 输出 token 数 */
  completionTokens: number;
  /** 总 token 数 */
  totalTokens: number;
}

// ==================== 会话类型 ====================

/** AI 会话接口 */
export interface AISession {
  /** 会话唯一标识 */
  id: string;
  /** 用户 ID */
  userId: string;
  /** 会话标题 */
  title: string;
  /** 会话状态 */
  status: AISessionStatus;
  /** 消息列表 */
  messages: AIMessage[];
  /** 会话上下文 */
  context?: AISessionContext;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
  /** 最后活动时间 */
  lastActivityAt: string;
}

/** 会话上下文 */
export interface AISessionContext {
  /** 咨询类别 */
  category?: string;
  /** 相关领域 */
  domain?: string;
  /** 用户意图 */
  userIntent?: string;
  /** 已收集信息 */
  collectedInfo?: Record<string, unknown>;
}

// ==================== 请求/响应类型 ====================

/** 发送消息请求 */
export interface SendMessageRequest {
  /** 会话 ID（可选，新建会话时为空） */
  sessionId?: string;
  /** 消息内容 */
  content: string;
  /** 是否启用流式响应 */
  stream?: boolean;
  /** 上下文信息 */
  context?: Record<string, unknown>;
}

/** 发送消息响应 */
export interface SendMessageResponse {
  /** 消息 ID */
  messageId: string;
  /** 会话 ID */
  sessionId: string;
  /** AI 回复内容 */
  content: string;
  /** 元数据 */
  metadata?: AIMessageMetadata;
  /** 创建时间 */
  createdAt: string;
}

/** 创建会话请求 */
export interface CreateSessionRequest {
  /** 会话标题 */
  title?: string;
  /** 初始消息 */
  initialMessage?: string;
  /** 咨询类别 */
  category?: string;
}

/** 创建会话响应 */
export interface CreateSessionResponse {
  /** 会话 ID */
  sessionId: string;
  /** 会话标题 */
  title: string;
  /** 创建时间 */
  createdAt: string;
}

/** 获取会话列表请求 */
export interface GetSessionsRequest {
  /** 页码 */
  page?: number;
  /** 每页数量 */
  pageSize?: number;
  /** 状态筛选 */
  status?: AISessionStatus;
}

/** 获取会话列表响应 */
export interface GetSessionsResponse {
  /** 会话列表 */
  sessions: AISession[];
  /** 总数 */
  total: number;
  /** 当前页码 */
  page: number;
  /** 总页数 */
  totalPages: number;
}

/** 获取会话历史请求 */
export interface GetSessionHistoryRequest {
  /** 会话 ID */
  sessionId: string;
  /** 消息 ID 偏移（用于分页） */
  beforeMessageId?: string;
  /** 每页数量 */
  limit?: number;
}

/** 获取会话历史响应 */
export interface GetSessionHistoryResponse {
  /** 消息列表 */
  messages: AIMessage[];
  /** 是否有更多消息 */
  hasMore: boolean;
}

// ==================== 分享功能类型 ====================

/** 分享链接响应 */
export interface ShareLinkResponse {
  /** 分享令牌 */
  token: string;
  /** 分享路径 */
  sharePath: string;
  /** 过期时间 */
  expiresAt: string;
}

/** 分享消息 */
export interface SharedMessage {
  /** 角色 */
  role: AIMessageRole;
  /** 内容 */
  content: string;
  /** 引用 */
  references?: string;
  /** 创建时间 */
  createdAt: string | null;
}

/** 分享的咨询会话响应 */
export interface SharedConsultationResponse {
  /** 会话 ID */
  sessionId: string;
  /** 标题 */
  title: string | null;
  /** 创建时间 */
  createdAt: string | null;
  /** 消息列表 */
  messages: SharedMessage[];
}

/** 创建分享请求 */
export interface CreateShareRequest {
  /** 会话 ID */
  sessionId: string;
  /** 过期天数（可选，默认7天） */
  expiresDays?: number;
}

// ==================== 语音转写类型 ====================

/** 语音转写响应 */
export interface TranscriptionResponse {
  /** 转写文本 */
  text: string;
  /** 分段索引 */
  segmentIndex?: number;
  /** 是否为最后一段 */
  isFinal?: boolean;
}

/** 语音上传请求 */
export interface VoiceUploadRequest {
  /** 音频文件 */
  audioFile: File;
  /** 分段索引 */
  segmentIndex?: number;
  /** 是否为最后一段 */
  isFinal?: boolean;
}

/** 语音转写状态 */
export interface TranscriptionState {
  /** 录音状态 */
  recordingStatus: RecordingStatus;
  /** 转写文本 */
  transcript: string;
  /** 错误信息 */
  error: string | null;
  /** 录音时长（秒） */
  duration: number;
}

// ==================== 文件分析类型 ====================

/** 支持的文件类型 */
export type SupportedFileType = 
  | 'application/pdf'
  | 'application/msword'
  | 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  | 'text/plain'
  | 'image/jpeg'
  | 'image/png'
  | 'image/gif'
  | 'image/webp';

/** 文件分析响应 */
export interface FileAnalysisResponse {
  /** 文件名 */
  filename: string;
  /** 文件类型 */
  contentType: string | null;
  /** 提取文本长度 */
  textChars: number;
  /** 提取文本预览 */
  textPreview: string;
  /** 分析摘要 */
  summary: string;
}

/** 文件上传请求 */
export interface FileUploadRequest {
  /** 文件 */
  file: File;
}

/** 文件分析状态 */
export interface FileAnalysisState {
  /** 上传状态 */
  uploadStatus: FileUploadStatus;
  /** 分析结果 */
  result: FileAnalysisResponse | null;
  /** 错误信息 */
  error: string | null;
  /** 进度百分比 */
  progress: number;
}

// ==================== 错误类型 ====================

/** AI 咨询错误码 */
export type AIConsultationErrorCode =
  | 'SESSION_NOT_FOUND'
  | 'SESSION_EXPIRED'
  | 'MESSAGE_TOO_LONG'
  | 'RATE_LIMIT_EXCEEDED'
  | 'MODEL_UNAVAILABLE'
  | 'INVALID_REQUEST'
  | 'UNAUTHORIZED'
  | 'INTERNAL_ERROR'
  | 'SHARE_EXPIRED'
  | 'SHARE_INVALID'
  | 'TRANSCRIPTION_FAILED'
  | 'FILE_TOO_LARGE'
  | 'UNSUPPORTED_FILE_TYPE'
  | 'ANALYSIS_FAILED';

/** AI 咨询错误 */
export interface AIConsultationError {
  /** 错误码 */
  code: AIConsultationErrorCode;
  /** 错误消息 */
  message: string;
  /** 详细错误信息 */
  details?: Record<string, unknown>;
}

// ==================== 流式响应类型 ====================

/** 流式响应块类型 */
export type StreamChunkType = 'content' | 'metadata' | 'error' | 'done';

/** 流式响应块 */
export interface StreamChunk {
  /** 块类型 */
  type: StreamChunkType;
  /** 数据内容 */
  data: string;
  /** 元数据（可选） */
  metadata?: AIMessageMetadata;
}