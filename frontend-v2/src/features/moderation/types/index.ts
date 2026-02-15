/**
 * Moderation（内容审核）类型定义
 */

// ==================== 核心类型 ====================

/** 审核状态 */
export type ModerationStatus = 'pending' | 'approved' | 'rejected' | 'flagged';

/** 内容类型 */
export type ContentType = 'post' | 'comment' | 'consultation' | 'document' | 'news' | 'forum_post' | 'forum_comment';

/** 风险等级 */
export type RiskLevel = 'high' | 'medium' | 'low' | 'none';

/** 审核操作类型 */
export type ReviewAction = 'approve' | 'reject' | 'escalate' | 'flag';

/** 审核队列项 */
export interface ModerationQueueItem {
  id: string;
  contentId: string;
  contentType: ContentType;
  content: string;
  title?: string;
  authorId: string;
  authorName: string;
  authorAvatar?: string;
  status: ModerationStatus;
  riskLevel: RiskLevel;
  riskScore: number;
  aiSuggestion?: ReviewAction;
  aiReason?: string;
  keywords?: string[];
  createdAt: string;
  submittedAt: string;
  metadata?: Record<string, unknown>;
}

/** 审核记录 */
export interface ModerationRecord {
  id: string;
  queueItemId: string;
  contentId: string;
  contentType: ContentType;
  content: string;
  title?: string;
  authorId: string;
  authorName: string;
  reviewerId: string;
  reviewerName: string;
  action: ReviewAction;
  reason?: string;
  note?: string;
  riskLevel: RiskLevel;
  riskScore: number;
  processingTime: number; // 处理时长（秒）
  createdAt: string;
  reviewedAt: string;
}

/** 审核统计 */
export interface ModerationStats {
  totalPending: number;
  totalReviewed: number;
  totalApproved: number;
  totalRejected: number;
  totalFlagged: number;
  averageProcessingTime: number;
  todayPending: number;
  todayReviewed: number;
  todayApproved: number;
  todayRejected: number;
  byContentType: Record<ContentType, {
    pending: number;
    approved: number;
    rejected: number;
  }>;
  byRiskLevel: Record<RiskLevel, number>;
  trend: Array<{
    date: string;
    reviewed: number;
    approved: number;
    rejected: number;
  }>;
}

/** 内容预览数据 */
export interface ContentPreviewData {
  id: string;
  contentId: string;
  contentType: ContentType;
  title?: string;
  content: string;
  author: {
    id: string;
    name: string;
    avatar?: string;
  };
  attachments?: Array<{
    id: string;
    type: 'image' | 'file' | 'link';
    url: string;
    name: string;
  }>;
  context?: string; // 上下文信息（如帖子回复的原文）
  createdAt: string;
}

/** 关键词匹配结果 */
export interface KeywordMatch {
  keyword: string;
  category: string;
  severity: 'high' | 'medium' | 'low';
  position: number;
  length: number;
}

/** AI审核结果 */
export interface AIReviewResult {
  suggestion: ReviewAction;
  confidence: number;
  reason: string;
  riskScore: number;
  riskLevel: RiskLevel;
  keywords: KeywordMatch[];
  categories: string[];
}

// ==================== API 请求/响应类型 ====================

/** 获取审核队列请求 */
export interface GetModerationQueueRequest {
  status?: ModerationStatus;
  contentType?: ContentType;
  riskLevel?: RiskLevel;
  page?: number;
  pageSize?: number;
}

/** 获取审核队列响应 */
export interface GetModerationQueueResponse {
  items: ModerationQueueItem[];
  total: number;
  page: number;
  pageSize: number;
}

/** 获取审核记录请求 */
export interface GetModerationRecordsRequest {
  contentType?: ContentType;
  action?: ReviewAction;
  reviewerId?: string;
  startDate?: string;
  endDate?: string;
  page?: number;
  pageSize?: number;
}

/** 获取审核记录响应 */
export interface GetModerationRecordsResponse {
  records: ModerationRecord[];
  total: number;
  page: number;
  pageSize: number;
}

/** 提交审核请求 */
export interface SubmitReviewRequest {
  id: string;
  action: ReviewAction;
  reason?: string;
  note?: string;
}

/** 提交审核响应 */
export interface SubmitReviewResponse {
  success: boolean;
  recordId: string;
  message: string;
}

/** 批量审核请求 */
export interface BatchReviewRequest {
  ids: string[];
  action: ReviewAction;
  reason?: string;
  note?: string;
}

/** 批量审核响应 */
export interface BatchReviewResponse {
  success: boolean;
  processed: number;
  failed: number;
  failedIds?: string[];
  message: string;
}

/** 获取审核统计请求 */
export interface GetModerationStatsRequest {
  startDate?: string;
  endDate?: string;
}

/** 获取审核统计响应 */
export interface GetModerationStatsResponse {
  stats: ModerationStats;
}

/** 获取内容详情请求 */
export interface GetContentDetailRequest {
  contentId: string;
  contentType: ContentType;
}

/** 获取内容详情响应 */
export interface GetContentDetailResponse {
  content: ContentPreviewData;
  aiReview?: AIReviewResult;
  history?: ModerationRecord[];
}

/** 关键词检查请求 */
export interface CheckKeywordsRequest {
  content: string;
  categories?: string[];
}

/** 关键词检查响应 */
export interface CheckKeywordsResponse {
  hasSensitiveWords: boolean;
  riskScore: number;
  matches: KeywordMatch[];
  categories: string[];
}