/**
 * News-Admin（新闻管理）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  NewsAdminListItem,
  NewsDetail,
  NewsComment,
  NewsTopic,
  NewsSource,
  NewsSourceHealth,
  NewsIngestRun,
  CategoryCount,
  NewsStats,
  GetNewsListRequest,
  CreateNewsRequest,
  UpdateNewsRequest,
  ReviewNewsRequest,
  BatchActionRequest,
  GetCommentsRequest,
  ReviewCommentRequest,
  CreateTopicRequest,
  UpdateTopicRequest,
  CreateSourceRequest,
  UpdateSourceRequest,
  GetIngestRunsRequest,
} from '../types';
import {
  apiGetNewsList,
  apiGetNewsDetail,
  apiCreateNews,
  apiUpdateNews,
  apiDeleteNews,
  apiReviewNews,
  apiBatchActionNews,
  apiGetComments,
  apiReviewComment,
  apiDeleteComment,
  apiGetNewsTopics,
  apiCreateNewsTopic,
  apiUpdateNewsTopic,
  apiDeleteNewsTopic,
  apiGetNewsSources,
  apiCreateNewsSource,
  apiUpdateNewsSource,
  apiDeleteNewsSource,
  apiGetNewsSourceHealth,
  apiTriggerIngest,
  apiGetNewsIngestRuns,
  apiGetCategoryStats,
  apiGetNewsStats,
} from '../api';

// ==================== Query Keys ====================

const NEWS_ADMIN_QUERY_KEYS = {
  articles: (params?: GetNewsListRequest) => ['news-admin', 'articles', params] as const,
  article: (id: number) => ['news-admin', 'article', id] as const,
  comments: (params?: GetCommentsRequest) => ['news-admin', 'comments', params] as const,
  topics: ['news-admin', 'topics'] as const,
  sources: ['news-admin', 'sources'] as const,
  sourceHealth: ['news-admin', 'source-health'] as const,
  ingestRuns: (params?: GetIngestRunsRequest) => ['news-admin', 'ingest-runs', params] as const,
  categoryStats: ['news-admin', 'category-stats'] as const,
  newsStats: ['news-admin', 'stats'] as const,
} as const;

// ==================== 文章管理 Hooks ====================

/**
 * 获取新闻列表 Hook
 */
export function useNewsList(params: GetNewsListRequest = {}, enabled = true) {
  return useQuery<{
    items: NewsAdminListItem[];
    total: number;
    page: number;
    pageSize: number;
  }>({
    queryKey: NEWS_ADMIN_QUERY_KEYS.articles(params),
    queryFn: () => apiGetNewsList(params),
    enabled,
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 获取新闻详情 Hook
 */
export function useNewsDetail(id: number) {
  return useQuery<NewsDetail>({
    queryKey: NEWS_ADMIN_QUERY_KEYS.article(id),
    queryFn: () => apiGetNewsDetail(id),
    staleTime: 60 * 1000, // 1分钟缓存
    enabled: id > 0,
  });
}

/**
 * 创建新闻 Hook
 */
export function useCreateNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateNewsRequest) => apiCreateNews(request),
    onSuccess: () => {
      // 创建成功后刷新新闻列表
      void queryClient.invalidateQueries({ queryKey: ['news-admin', 'articles'] });
      // 刷新统计
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.newsStats });
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.categoryStats });
    },
  });
}

/**
 * 更新新闻 Hook
 */
export function useUpdateNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: number; request: UpdateNewsRequest }) => 
      apiUpdateNews(id, request),
    onSuccess: (_data, variables) => {
      // 更新成功后刷新新闻详情和列表
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.article(variables.id) });
      void queryClient.invalidateQueries({ queryKey: ['news-admin', 'articles'] });
    },
  });
}

/**
 * 删除新闻 Hook
 */
export function useDeleteNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => apiDeleteNews(id),
    onSuccess: () => {
      // 删除成功后刷新新闻列表
      void queryClient.invalidateQueries({ queryKey: ['news-admin', 'articles'] });
      // 刷新统计
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.newsStats });
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.categoryStats });
    },
  });
}

/**
 * 审核新闻 Hook
 */
export function useReviewNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: number; request: ReviewNewsRequest }) => 
      apiReviewNews(id, request),
    onSuccess: (_data, variables) => {
      // 审核成功后刷新新闻详情和列表
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.article(variables.id) });
      void queryClient.invalidateQueries({ queryKey: ['news-admin', 'articles'] });
      // 刷新统计
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.newsStats });
    },
  });
}

/**
 * 批量操作新闻 Hook
 */
export function useBatchAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: BatchActionRequest) => apiBatchActionNews(request),
    onSuccess: () => {
      // 批量操作成功后刷新新闻列表
      void queryClient.invalidateQueries({ queryKey: ['news-admin', 'articles'] });
      // 刷新统计
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.newsStats });
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.categoryStats });
    },
  });
}

// ==================== 评论管理 Hooks ====================

/**
 * 获取评论列表 Hook
 */
export function useComments(params: GetCommentsRequest = {}) {
  return useQuery<{
    items: NewsComment[];
    total: number;
    page: number;
    pageSize: number;
  }>({
    queryKey: NEWS_ADMIN_QUERY_KEYS.comments(params),
    queryFn: () => apiGetComments(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 审核评论 Hook
 */
export function useReviewComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: number; request: ReviewCommentRequest }) => 
      apiReviewComment(id, request),
    onSuccess: () => {
      // 审核成功后刷新评论列表
      void queryClient.invalidateQueries({ queryKey: ['news-admin', 'comments'] });
    },
  });
}

/**
 * 删除评论 Hook
 */
export function useDeleteComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => apiDeleteComment(id),
    onSuccess: () => {
      // 删除成功后刷新评论列表
      void queryClient.invalidateQueries({ queryKey: ['news-admin', 'comments'] });
    },
  });
}

// ==================== 专题管理 Hooks ====================

/**
 * 获取专题列表 Hook
 */
export function useTopics() {
  return useQuery<NewsTopic[]>({
    queryKey: NEWS_ADMIN_QUERY_KEYS.topics,
    queryFn: apiGetNewsTopics,
    staleTime: 5 * 60 * 1000, // 5分钟缓存，专题不常变化
  });
}

/**
 * 创建专题 Hook
 */
export function useCreateTopic() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateTopicRequest) => apiCreateNewsTopic(request),
    onSuccess: () => {
      // 创建成功后刷新专题列表
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.topics });
    },
  });
}

/**
 * 更新专题 Hook
 */
export function useUpdateTopic() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: number; request: UpdateTopicRequest }) => 
      apiUpdateNewsTopic(id, request),
    onSuccess: () => {
      // 更新成功后刷新专题列表
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.topics });
    },
  });
}

/**
 * 删除专题 Hook
 */
export function useDeleteTopic() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => apiDeleteNewsTopic(id),
    onSuccess: () => {
      // 删除成功后刷新专题列表
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.topics });
    },
  });
}

// ==================== 来源管理 Hooks ====================

/**
 * 获取来源列表 Hook
 */
export function useSources() {
  return useQuery<NewsSource[]>({
    queryKey: NEWS_ADMIN_QUERY_KEYS.sources,
    queryFn: apiGetNewsSources,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 创建来源 Hook
 */
export function useCreateSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateSourceRequest) => apiCreateNewsSource(request),
    onSuccess: () => {
      // 创建成功后刷新来源列表
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.sources });
    },
  });
}

/**
 * 更新来源 Hook
 */
export function useUpdateSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: number; request: UpdateSourceRequest }) => 
      apiUpdateNewsSource(id, request),
    onSuccess: () => {
      // 更新成功后刷新来源列表和健康状态
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.sources });
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.sourceHealth });
    },
  });
}

/**
 * 删除来源 Hook
 */
export function useDeleteSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => apiDeleteNewsSource(id),
    onSuccess: () => {
      // 删除成功后刷新来源列表
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.sources });
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.sourceHealth });
    },
  });
}

/**
 * 获取来源健康状态 Hook
 */
export function useSourceHealth() {
  return useQuery<NewsSourceHealth[]>({
    queryKey: NEWS_ADMIN_QUERY_KEYS.sourceHealth,
    queryFn: apiGetNewsSourceHealth,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 触发来源抓取 Hook
 */
export function useTriggerIngest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sourceId: number) => apiTriggerIngest(sourceId),
    onSuccess: () => {
      // 触发成功后刷新抓取记录和健康状态
      void queryClient.invalidateQueries({ queryKey: ['news-admin', 'ingest-runs'] });
      void queryClient.invalidateQueries({ queryKey: NEWS_ADMIN_QUERY_KEYS.sourceHealth });
    },
  });
}

/**
 * 获取抓取记录 Hook
 */
export function useIngestRuns(params: GetIngestRunsRequest = {}) {
  return useQuery<{
    items: NewsIngestRun[];
    total: number;
    page: number;
    pageSize: number;
  }>({
    queryKey: NEWS_ADMIN_QUERY_KEYS.ingestRuns(params),
    queryFn: () => apiGetNewsIngestRuns(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

// ==================== 统计 Hooks ====================

/**
 * 获取分类统计 Hook
 */
export function useCategoryStats(enabled = true) {
  return useQuery<CategoryCount[]>({
    queryKey: NEWS_ADMIN_QUERY_KEYS.categoryStats,
    queryFn: apiGetCategoryStats,
    enabled,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 获取新闻统计 Hook
 */
export function useNewsStats(enabled = true) {
  return useQuery<NewsStats>({
    queryKey: NEWS_ADMIN_QUERY_KEYS.newsStats,
    queryFn: apiGetNewsStats,
    enabled,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}