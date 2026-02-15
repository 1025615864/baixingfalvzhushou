/**
 * News-Admin（新闻管理）API 层
 * 对齐后端 API: backend/app/routers/news/admin.py
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  NewsSource,
  NewsIngestRun,
  NewsAdminListItem,
  NewsDetail,
  AIAnnotation,
  NewsComment,
  NewsTopic,
  NewsSourceHealth,
  CategoryCount,
  NewsStats,
  PaginatedResponse,
  GetNewsListRequest,
  GetCommentsRequest,
  GetIngestRunsRequest,
  CreateNewsRequest,
  UpdateNewsRequest,
  ReviewNewsRequest,
  BatchActionRequest,
  BatchActionResponse,
  ReviewCommentRequest,
  CreateTopicRequest,
  UpdateTopicRequest,
  CreateSourceRequest,
  UpdateSourceRequest,
} from '../types';

import type {
  NewsSourceBackend,
  NewsIngestRunBackend,
  NewsArticleBackend,
  AIAnnotationBackend,
  NewsCommentBackend,
  NewsTopicBackend,
  NewsSourceHealthBackend,
  NewsSourceListResponseBackend,
  NewsIngestRunListResponseBackend,
  NewsListResponseBackend,
  NewsCommentListResponseBackend,
  NewsTopicListResponseBackend,
  NewsSourceHealthListResponseBackend,
  CategoryStatsResponseBackend,
  NewsStatsResponseBackend,
} from './types';

// API 基础路径
const API_BASE = '/news/admin';

// ==================== 转换函数 ====================

/**
 * 转换新闻来源
 */
function mapNewsSourceBackendToFrontend(data: NewsSourceBackend): NewsSource {
  return {
    id: data.id,
    name: data.name,
    sourceType: data.source_type,
    feedUrl: data.feed_url,
    site: data.site,
    category: data.category,
    isEnabled: data.is_enabled,
    fetchTimeoutSeconds: data.fetch_timeout_seconds,
    maxItemsPerFeed: data.max_items_per_feed,
    lastRunAt: data.last_run_at,
    lastSuccessAt: data.last_success_at,
    lastError: data.last_error,
    lastErrorAt: data.last_error_at,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 转换抓取运行记录
 */
function mapNewsIngestRunBackendToFrontend(data: NewsIngestRunBackend): NewsIngestRun {
  return {
    id: data.id,
    sourceId: data.source_id,
    sourceName: data.source_name,
    feedUrl: data.feed_url,
    status: data.status,
    fetched: data.fetched,
    inserted: data.inserted,
    skipped: data.skipped,
    errors: data.errors,
    lastError: data.last_error,
    startedAt: data.started_at,
    finishedAt: data.finished_at,
    createdAt: data.created_at,
  };
}

/**
 * 转换新闻文章列表项
 */
function mapNewsArticleBackendToListItem(data: NewsArticleBackend): NewsAdminListItem {
  return {
    id: data.id,
    title: data.title,
    summary: data.summary,
    coverImage: data.cover_image,
    category: data.category as 'general' | 'policy' | 'case' | 'interpret',
    source: data.source,
    sourceUrl: data.source_url,
    sourceSite: data.source_site,
    author: data.author,
    viewCount: data.view_count,
    favoriteCount: data.favorite_count,
    aiRiskLevel: data.ai_risk_level as 'unknown' | 'low' | 'medium' | 'high' | null,
    aiKeywords: data.ai_keywords,
    isTop: data.is_top,
    isPublished: data.is_published,
    reviewStatus: data.review_status as 'pending' | 'approved' | 'rejected' | null,
    reviewReason: data.review_reason,
    reviewedAt: data.reviewed_at,
    publishedAt: data.published_at,
    scheduledPublishAt: data.scheduled_publish_at,
    scheduledUnpublishAt: data.scheduled_unpublish_at,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 转换 AI 标注
 */
function mapAIAnnotationBackendToFrontend(data: AIAnnotationBackend): AIAnnotation {
  return {
    summary: data.summary,
    riskLevel: data.risk_level as 'unknown' | 'low' | 'medium' | 'high',
    sensitiveWords: data.sensitive_words,
    highlights: data.highlights,
    keywords: data.keywords,
    duplicateOfNewsId: data.duplicate_of_news_id,
    processedAt: data.processed_at,
  };
}

/**
 * 转换新闻详情
 */
function mapNewsArticleBackendToDetail(data: NewsArticleBackend & { ai_annotation?: AIAnnotationBackend; is_favorited?: boolean }): NewsDetail {
  return {
    ...mapNewsArticleBackendToListItem(data),
    content: data.content,
    isFavorited: data.is_favorited ?? false,
    aiAnnotation: data.ai_annotation ? mapAIAnnotationBackendToFrontend(data.ai_annotation) : null,
  };
}

/**
 * 转换评论
 */
function mapNewsCommentBackendToFrontend(data: NewsCommentBackend): NewsComment {
  return {
    id: data.id,
    newsId: data.news_id,
    userId: data.user_id,
    content: data.content,
    reviewStatus: data.review_status as 'pending' | 'approved' | 'rejected' | null,
    reviewReason: data.review_reason,
    reviewedAt: data.reviewed_at,
    createdAt: data.created_at,
    isDeleted: data.is_deleted,
    author: data.author,
    news: data.news,
  };
}

/**
 * 转换专题
 */
function mapNewsTopicBackendToFrontend(data: NewsTopicBackend): NewsTopic {
  return {
    id: data.id,
    title: data.title,
    description: data.description,
    coverImage: data.cover_image,
    isActive: data.is_active,
    sortOrder: data.sort_order,
    autoCategory: data.auto_category,
    autoKeyword: data.auto_keyword,
    autoLimit: data.auto_limit,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 转换来源健康状态
 */
function mapNewsSourceHealthBackendToFrontend(data: NewsSourceHealthBackend): NewsSourceHealth {
  return {
    sourceId: data.source_id,
    recentTotal: data.recent_total,
    recentFailed: data.recent_failed,
    failureRate: data.failure_rate,
    lastStatus: data.last_status,
    lastRunAt: data.last_run_at,
    lastSuccessAt: data.last_success_at,
    lastError: data.last_error,
    lastErrorAt: data.last_error_at,
  };
}

// ==================== 新闻源管理 API ====================

/**
 * 获取新闻源列表
 * GET /news/admin/sources
 */
export async function apiGetNewsSources(): Promise<NewsSource[]> {
  const response = await apiClient.get<NewsSourceListResponseBackend>(`${API_BASE}/sources`);
  return response.data.items.map(mapNewsSourceBackendToFrontend);
}

/**
 * 创建新闻源
 * POST /news/admin/sources
 */
export async function apiCreateNewsSource(request: CreateSourceRequest): Promise<NewsSource> {
  const response = await apiClient.post<NewsSourceBackend>(`${API_BASE}/sources`, {
    name: request.name,
    feed_url: request.feedUrl,
    site: request.site,
    category: request.category,
    is_enabled: request.isEnabled,
    fetch_timeout_seconds: request.fetchTimeoutSeconds,
    max_items_per_feed: request.maxItemsPerFeed,
  });
  return mapNewsSourceBackendToFrontend(response.data);
}

/**
 * 更新新闻源
 * PUT /news/admin/sources/{source_id}
 */
export async function apiUpdateNewsSource(id: number, request: UpdateSourceRequest): Promise<NewsSource> {
  const response = await apiClient.put<NewsSourceBackend>(`${API_BASE}/sources/${id}`, {
    name: request.name,
    feed_url: request.feedUrl,
    site: request.site,
    category: request.category,
    is_enabled: request.isEnabled,
    fetch_timeout_seconds: request.fetchTimeoutSeconds,
    max_items_per_feed: request.maxItemsPerFeed,
  });
  return mapNewsSourceBackendToFrontend(response.data);
}

/**
 * 删除新闻源
 * DELETE /news/admin/sources/{source_id}
 */
export async function apiDeleteNewsSource(id: number): Promise<void> {
  await apiClient.delete(`${API_BASE}/sources/${id}`);
}

/**
 * 手动触发抓取
 * POST /news/admin/sources/{source_id}/ingest/run-once
 */
export async function apiTriggerIngest(sourceId: number): Promise<void> {
  await apiClient.post(`${API_BASE}/sources/${sourceId}/ingest/run-once`);
}

/**
 * 获取来源健康状态
 * GET /news/admin/sources/health
 */
export async function apiGetNewsSourceHealth(): Promise<NewsSourceHealth[]> {
  const response = await apiClient.get<NewsSourceHealthListResponseBackend>(`${API_BASE}/sources/health`);
  return response.data.items.map(mapNewsSourceHealthBackendToFrontend);
}

// ==================== 抓取运行记录 API ====================

/**
 * 获取抓取运行记录
 * GET /news/admin/ingest-runs
 */
export async function apiGetNewsIngestRuns(
  params: GetIngestRunsRequest
): Promise<PaginatedResponse<NewsIngestRun>> {
  const searchParams = new URLSearchParams();
  if (params.sourceId) searchParams.set('source_id', String(params.sourceId));
  if (params.status) searchParams.set('status', params.status);
  if (params.from) searchParams.set('from', params.from);
  if (params.to) searchParams.set('to', params.to);
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));

  const url = `${API_BASE}/ingest-runs${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
  const response = await apiClient.get<NewsIngestRunListResponseBackend>(url);

  return {
    items: response.data.items.map(mapNewsIngestRunBackendToFrontend),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

// ==================== 新闻管理 API ====================

/**
 * 获取新闻列表
 * GET /news/admin
 */
export async function apiGetNewsList(
  params: GetNewsListRequest
): Promise<PaginatedResponse<NewsAdminListItem>> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));
  if (params.category) searchParams.set('category', params.category);
  if (params.keyword) searchParams.set('keyword', params.keyword);
  if (params.riskLevel) searchParams.set('risk_level', params.riskLevel);
  if (params.sourceSite) searchParams.set('source_site', params.sourceSite);
  if (params.reviewStatus) searchParams.set('review_status', params.reviewStatus);
  if (params.isPublished !== undefined) searchParams.set('is_published', String(params.isPublished));
  if (params.isTop !== undefined) searchParams.set('is_top', String(params.isTop));
  if (params.from) searchParams.set('from', params.from);
  if (params.to) searchParams.set('to', params.to);

  const url = `${API_BASE}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
  const response = await apiClient.get<NewsListResponseBackend>(url);

  return {
    items: response.data.items.map(mapNewsArticleBackendToListItem),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

/**
 * 获取新闻详情
 * GET /news/admin/{news_id}
 */
export async function apiGetNewsDetail(id: number): Promise<NewsDetail> {
  const response = await apiClient.get<NewsArticleBackend & { ai_annotation?: AIAnnotationBackend }>(
    `${API_BASE}/${id}`
  );
  return mapNewsArticleBackendToDetail(response.data);
}

/**
 * 创建新闻
 * POST /news/admin
 */
export async function apiCreateNews(request: CreateNewsRequest): Promise<NewsAdminListItem> {
  const response = await apiClient.post<NewsArticleBackend>(`${API_BASE}`, {
    title: request.title,
    summary: request.summary,
    content: request.content,
    cover_image: request.coverImage,
    category: request.category,
    source: request.source,
    source_url: request.sourceUrl,
    source_site: request.sourceSite,
    author: request.author,
    is_top: request.isTop,
    is_published: request.isPublished,
    review_status: request.reviewStatus,
    review_reason: request.reviewReason,
    scheduled_publish_at: request.scheduledPublishAt,
    scheduled_unpublish_at: request.scheduledUnpublishAt,
  });
  return mapNewsArticleBackendToListItem(response.data);
}

/**
 * 更新新闻
 * PUT /news/admin/{news_id}
 */
export async function apiUpdateNews(id: number, request: UpdateNewsRequest): Promise<NewsAdminListItem> {
  const response = await apiClient.put<NewsArticleBackend>(`${API_BASE}/${id}`, {
    title: request.title,
    summary: request.summary,
    content: request.content,
    cover_image: request.coverImage,
    category: request.category,
    source: request.source,
    source_url: request.sourceUrl,
    source_site: request.sourceSite,
    author: request.author,
    is_top: request.isTop,
    is_published: request.isPublished,
    review_status: request.reviewStatus,
    review_reason: request.reviewReason,
    reviewed_at: request.reviewedAt,
    published_at: request.publishedAt,
    scheduled_publish_at: request.scheduledPublishAt,
    scheduled_unpublish_at: request.scheduledUnpublishAt,
  });
  return mapNewsArticleBackendToListItem(response.data);
}

/**
 * 删除新闻
 * DELETE /news/admin/{news_id}
 */
export async function apiDeleteNews(id: number): Promise<void> {
  await apiClient.delete(`${API_BASE}/${id}`);
}

/**
 * 审核新闻
 * POST /news/admin/{news_id}/review
 */
export async function apiReviewNews(id: number, request: ReviewNewsRequest): Promise<NewsAdminListItem> {
  const response = await apiClient.post<NewsArticleBackend>(`${API_BASE}/${id}/review`, {
    action: request.action,
    reason: request.reason,
  });
  return mapNewsArticleBackendToListItem(response.data);
}

/**
 * 批量操作新闻
 * POST /news/admin/batch
 */
export async function apiBatchActionNews(request: BatchActionRequest): Promise<BatchActionResponse> {
  const response = await apiClient.post<BatchActionResponse>(`${API_BASE}/batch`, {
    ids: request.ids,
    action: request.action,
    reason: request.reason,
  });
  return response.data;
}

// ==================== 评论管理 API ====================

/**
 * 获取评论列表
 * GET /news/admin/comments
 */
export async function apiGetComments(
  params: GetCommentsRequest
): Promise<PaginatedResponse<NewsComment>> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));
  if (params.keyword) searchParams.set('keyword', params.keyword);
  if (params.includeDeleted) searchParams.set('include_deleted', String(params.includeDeleted));

  const url = `${API_BASE}/comments${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
  const response = await apiClient.get<NewsCommentListResponseBackend>(url);

  return {
    items: response.data.items.map(mapNewsCommentBackendToFrontend),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

/**
 * 审核评论
 * POST /news/admin/comments/{comment_id}/review
 */
export async function apiReviewComment(id: number, request: ReviewCommentRequest): Promise<NewsComment> {
  const response = await apiClient.post<NewsCommentBackend>(`${API_BASE}/comments/${id}/review`, {
    action: request.action,
    reason: request.reason,
  });
  return mapNewsCommentBackendToFrontend(response.data);
}

/**
 * 删除评论
 * DELETE /news/admin/comments/{comment_id}
 */
export async function apiDeleteComment(id: number): Promise<void> {
  await apiClient.delete(`${API_BASE}/comments/${id}`);
}

// ==================== 专题管理 API ====================

/**
 * 获取专题列表
 * GET /news/admin/topics
 */
export async function apiGetNewsTopics(): Promise<NewsTopic[]> {
  const response = await apiClient.get<NewsTopicListResponseBackend>(`${API_BASE}/topics`);
  return response.data.items.map(mapNewsTopicBackendToFrontend);
}

/**
 * 创建专题
 * POST /news/admin/topics
 */
export async function apiCreateNewsTopic(request: CreateTopicRequest): Promise<NewsTopic> {
  const response = await apiClient.post<NewsTopicBackend>(`${API_BASE}/topics`, {
    title: request.title,
    description: request.description,
    cover_image: request.coverImage,
    is_active: request.isActive,
    sort_order: request.sortOrder,
    auto_category: request.autoCategory,
    auto_keyword: request.autoKeyword,
    auto_limit: request.autoLimit,
  });
  return mapNewsTopicBackendToFrontend(response.data);
}

/**
 * 更新专题
 * PUT /news/admin/topics/{topic_id}
 */
export async function apiUpdateNewsTopic(id: number, request: UpdateTopicRequest): Promise<NewsTopic> {
  const response = await apiClient.put<NewsTopicBackend>(`${API_BASE}/topics/${id}`, {
    title: request.title,
    description: request.description,
    cover_image: request.coverImage,
    is_active: request.isActive,
    sort_order: request.sortOrder,
    auto_category: request.autoCategory,
    auto_keyword: request.autoKeyword,
    auto_limit: request.autoLimit,
  });
  return mapNewsTopicBackendToFrontend(response.data);
}

/**
 * 删除专题
 * DELETE /news/admin/topics/{topic_id}
 */
export async function apiDeleteNewsTopic(id: number): Promise<void> {
  await apiClient.delete(`${API_BASE}/topics/${id}`);
}

// ==================== 统计 API ====================

/**
 * 获取分类统计
 * GET /news/admin/categories/stats
 */
export async function apiGetCategoryStats(): Promise<CategoryCount[]> {
  const response = await apiClient.get<CategoryStatsResponseBackend>(`${API_BASE}/categories/stats`);
  return response.data.categories;
}

/**
 * 获取新闻统计
 * GET /news/admin/stats
 */
export async function apiGetNewsStats(): Promise<NewsStats> {
  const response = await apiClient.get<NewsStatsResponseBackend>(`${API_BASE}/stats`);
  return {
    totalArticles: response.data.stats.total_articles,
    publishedArticles: response.data.stats.published_articles,
    pendingReview: response.data.stats.pending_review,
    rejectedArticles: response.data.stats.rejected_articles,
    topArticles: response.data.stats.top_articles,
    totalViews: response.data.stats.total_views,
    todayViews: response.data.stats.today_views,
  };
}

// ==================== 统一导出 ====================

export const newsAdminApi = {
  // 新闻源
  getSources: apiGetNewsSources,
  createSource: apiCreateNewsSource,
  updateSource: apiUpdateNewsSource,
  deleteSource: apiDeleteNewsSource,
  triggerIngest: apiTriggerIngest,
  getSourceHealth: apiGetNewsSourceHealth,

  // 抓取记录
  getIngestRuns: apiGetNewsIngestRuns,

  // 新闻管理
  getNewsList: apiGetNewsList,
  getNewsDetail: apiGetNewsDetail,
  createNews: apiCreateNews,
  updateNews: apiUpdateNews,
  deleteNews: apiDeleteNews,
  reviewNews: apiReviewNews,
  batchActionNews: apiBatchActionNews,

  // 评论管理
  getComments: apiGetComments,
  reviewComment: apiReviewComment,
  deleteComment: apiDeleteComment,

  // 专题管理
  getTopics: apiGetNewsTopics,
  createTopic: apiCreateNewsTopic,
  updateTopic: apiUpdateNewsTopic,
  deleteTopic: apiDeleteNewsTopic,

  // 统计
  getCategoryStats: apiGetCategoryStats,
  getNewsStats: apiGetNewsStats,
} as const;
