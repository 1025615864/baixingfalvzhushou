/**
 * News-Admin（新闻管理）类型定义
 * 对齐后端 API: backend/app/routers/news/admin.py
 */

// ==================== 核心类型 ====================

/** 新闻审核状态 */
export type NewsReviewStatus = 'pending' | 'approved' | 'rejected';

/** 新闻分类 */
export type NewsCategory = 'general' | 'policy' | 'case' | 'interpret';

/** AI 风险等级 */
export type AIRiskLevel = 'unknown' | 'low' | 'medium' | 'high';

/** 抓取运行状态 */
export type IngestRunStatus = 'running' | 'success' | 'failed';

/** 新闻文章 */
export interface NewsArticle {
  id: number;
  title: string;
  summary: string | null;
  content: string;
  coverImage: string | null;
  category: NewsCategory;
  source: string | null;
  sourceUrl: string | null;
  sourceSite: string | null;
  author: string | null;
  viewCount: number;
  favoriteCount: number;
  isFavorited: boolean;
  aiRiskLevel: AIRiskLevel | null;
  aiKeywords: string[] | null;
  isTop: boolean;
  isPublished: boolean;
  reviewStatus: NewsReviewStatus | null;
  reviewReason: string | null;
  reviewedAt: string | null;
  publishedAt: string | null;
  scheduledPublishAt: string | null;
  scheduledUnpublishAt: string | null;
  createdAt: string;
  updatedAt: string;
}

/** 管理员新闻列表项 */
export interface NewsAdminListItem {
  id: number;
  title: string;
  summary: string | null;
  coverImage: string | null;
  category: NewsCategory;
  source: string | null;
  sourceUrl: string | null;
  sourceSite: string | null;
  author: string | null;
  viewCount: number;
  favoriteCount: number;
  aiRiskLevel: AIRiskLevel | null;
  aiKeywords: string[] | null;
  isTop: boolean;
  isPublished: boolean;
  reviewStatus: NewsReviewStatus | null;
  reviewReason: string | null;
  reviewedAt: string | null;
  publishedAt: string | null;
  scheduledPublishAt: string | null;
  scheduledUnpublishAt: string | null;
  createdAt: string;
  updatedAt: string;
}

/** AI 标注信息 */
export interface AIAnnotation {
  summary: string | null;
  riskLevel: AIRiskLevel;
  sensitiveWords: string[];
  highlights: string[];
  keywords: string[];
  duplicateOfNewsId: number | null;
  processedAt: string | null;
}

/** 完整新闻详情 */
export interface NewsDetail extends NewsArticle {
  aiAnnotation: AIAnnotation | null;
}

/** 新闻评论 */
export interface NewsComment {
  id: number;
  newsId: number;
  userId: number;
  content: string;
  reviewStatus: NewsReviewStatus | null;
  reviewReason: string | null;
  reviewedAt: string | null;
  createdAt: string;
  isDeleted: boolean;
  author: {
    id: number;
    username: string;
    nickname: string | null;
    avatar: string | null;
  } | null;
  news: {
    id: number;
    title: string;
  } | null;
}

/** 新闻专题 */
export interface NewsTopic {
  id: number;
  title: string;
  description: string | null;
  coverImage: string | null;
  isActive: boolean;
  sortOrder: number;
  autoCategory: string | null;
  autoKeyword: string | null;
  autoLimit: number;
  createdAt: string;
  updatedAt: string;
}

/** 新闻来源 */
export interface NewsSource {
  id: number;
  name: string;
  sourceType: string;
  feedUrl: string;
  site: string | null;
  category: string | null;
  isEnabled: boolean;
  fetchTimeoutSeconds: number;
  maxItemsPerFeed: number;
  lastRunAt: string | null;
  lastSuccessAt: string | null;
  lastError: string | null;
  lastErrorAt: string | null;
  createdAt: string;
  updatedAt: string;
}

/** 新闻来源健康状态 */
export interface NewsSourceHealth {
  sourceId: number;
  recentTotal: number;
  recentFailed: number;
  failureRate: number;
  lastStatus: string | null;
  lastRunAt: string | null;
  lastSuccessAt: string | null;
  lastError: string | null;
  lastErrorAt: string | null;
}

/** 抓取运行记录 - 对齐后端 NewsIngestRun 模型 */
export interface NewsIngestRun {
  id: number;
  sourceId: number | null;
  sourceName: string | null;
  feedUrl: string | null;
  status: IngestRunStatus;
  fetched: number;
  inserted: number;
  skipped: number;
  errors: number;
  lastError: string | null;
  startedAt: string;
  finishedAt: string | null;
  createdAt: string;
}

/** 分类统计 */
export interface CategoryCount {
  category: string;
  count: number;
}

// ==================== API 请求/响应类型 ====================

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

/** 获取新闻列表请求 */
export interface GetNewsListRequest {
  page?: number;
  pageSize?: number;
  category?: string;
  keyword?: string;
  riskLevel?: AIRiskLevel;
  sourceSite?: string;
  reviewStatus?: NewsReviewStatus;
  isPublished?: boolean;
  isTop?: boolean;
  from?: string;
  to?: string;
}

/** 创建新闻请求 */
export interface CreateNewsRequest {
  title: string;
  summary?: string | null;
  content: string;
  coverImage?: string | null;
  category: NewsCategory;
  source?: string | null;
  sourceUrl?: string | null;
  sourceSite?: string | null;
  author?: string | null;
  isTop?: boolean;
  isPublished?: boolean;
  reviewStatus?: NewsReviewStatus | null;
  reviewReason?: string | null;
  scheduledPublishAt?: string | null;
  scheduledUnpublishAt?: string | null;
}

/** 更新新闻请求 */
export interface UpdateNewsRequest {
  title?: string;
  summary?: string | null;
  content?: string;
  coverImage?: string | null;
  category?: NewsCategory;
  source?: string | null;
  sourceUrl?: string | null;
  sourceSite?: string | null;
  author?: string | null;
  isTop?: boolean;
  isPublished?: boolean;
  reviewStatus?: NewsReviewStatus | null;
  reviewReason?: string | null;
  reviewedAt?: string | null;
  publishedAt?: string | null;
  scheduledPublishAt?: string | null;
  scheduledUnpublishAt?: string | null;
}

/** 审核新闻请求 */
export interface ReviewNewsRequest {
  action: 'approve' | 'reject' | 'pending';
  reason?: string | null;
}

/** 批量操作请求 */
export interface BatchActionRequest {
  ids: number[];
  action: string;
  reason?: string | null;
}

/** 批量操作响应 */
export interface BatchActionResponse {
  requested: number[];
  processed: number[];
  missing: number[];
  skipped: number[];
  action: string;
  reason: string | null;
  message: string;
}

/** 获取评论列表请求 */
export interface GetCommentsRequest {
  page?: number;
  pageSize?: number;
  keyword?: string;
  status?: 'pending' | 'approved' | 'rejected';
  includeDeleted?: boolean;
}

/** 审核评论请求 */
export interface ReviewCommentRequest {
  action: 'approve' | 'reject' | 'pending';
  reason?: string | null;
}

/** 创建专题请求 */
export interface CreateTopicRequest {
  title: string;
  description?: string | null;
  coverImage?: string | null;
  isActive?: boolean;
  sortOrder?: number;
  autoCategory?: string | null;
  autoKeyword?: string | null;
  autoLimit?: number;
}

/** 更新专题请求 */
export interface UpdateTopicRequest {
  title?: string;
  description?: string | null;
  coverImage?: string | null;
  isActive?: boolean;
  sortOrder?: number;
  autoCategory?: string | null;
  autoKeyword?: string | null;
  autoLimit?: number;
}

/** 创建来源请求 */
export interface CreateSourceRequest {
  name: string;
  feedUrl: string;
  site?: string | null;
  category?: string | null;
  isEnabled?: boolean;
  fetchTimeoutSeconds?: number;
  maxItemsPerFeed?: number;
}

/** 更新来源请求 */
export interface UpdateSourceRequest {
  name?: string;
  feedUrl?: string;
  site?: string | null;
  category?: string | null;
  isEnabled?: boolean;
  fetchTimeoutSeconds?: number;
  maxItemsPerFeed?: number;
}

/** 获取抓取记录请求 */
export interface GetIngestRunsRequest {
  sourceId?: number;
  status?: IngestRunStatus;
  from?: string;
  to?: string;
  page?: number;
  pageSize?: number;
}

/** 新闻统计 */
export interface NewsStats {
  totalArticles: number;
  publishedArticles: number;
  pendingReview: number;
  rejectedArticles: number;
  topArticles: number;
  totalViews: number;
  todayViews: number;
}

/** 版本历史项 */
export interface NewsVersionItem {
  id: number;
  newsId: number;
  action: string;
  reason: string | null;
  snapshotJson: Record<string, unknown>;
  createdBy: number | null;
  createdAt: string;
}

/** AI 生成请求 */
export interface NewsAIGenerateRequest {
  newsId?: number;
  taskType: string;
  title?: string;
  summary?: string;
  content?: string;
  style?: string;
  wordCountMin?: number;
  wordCountMax?: number;
  append?: boolean;
  useNewsContent?: boolean;
}

/** AI 生成记录 */
export interface NewsAIGeneration {
  id: number;
  userId: number;
  newsId: number | null;
  taskType: string;
  status: string;
  inputJson: Record<string, unknown>;
  outputJson: Record<string, unknown> | null;
  rawOutput: string | null;
  error: string | null;
  createdAt: string;
}

/** 链接检查请求 */
export interface NewsLinkCheckRequest {
  newsId?: number;
  markdown?: string;
  timeoutSeconds?: number;
  maxUrls?: number;
  useNewsContent?: boolean;
}

/** 链接检查结果 */
export interface NewsLinkCheckItem {
  id: number;
  runId: string;
  userId: number;
  newsId: number | null;
  url: string;
  finalUrl: string | null;
  ok: boolean;
  statusCode: number | null;
  error: string | null;
  checkedAt: string;
}

/** 链接检查响应 */
export interface NewsLinkCheckResponse {
  runId: string;
  items: NewsLinkCheckItem[];
}

/** 定时发布项 */
export interface ScheduledNewsItem {
  id: number;
  title: string;
  category: string;
  isPublished: boolean;
  reviewStatus: NewsReviewStatus;
  scheduledPublishAt: string | null;
  scheduledUnpublishAt: string | null;
}

/** 专题报告项 */
export interface NewsTopicReportItem {
  id: number;
  title: string;
  isActive: boolean;
  newsCount: number;
  sortOrder: number;
  manualItemCount: number;
  manualViewCount: number;
  manualFavoriteCount: number;
  manualConversionRate: number;
}
