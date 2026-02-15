/**
 * Knowledge-Admin（知识库管理）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import type {
  KnowledgeArticle,
  KnowledgeArticleListItem,
  KnowledgeCategory,
  KnowledgeStats,
  CreateArticleRequest,
  UpdateArticleRequest,
  GetArticlesRequest,
  SearchKnowledgeRequest,
  BatchImportRequest,
} from '../types';
import {
  apiGetArticles,
  apiGetArticle,
  apiCreateArticle,
  apiUpdateArticle,
  apiDeleteArticle,
  apiGetCategories,
  apiCreateCategory,
  apiGetStats,
  apiSearchKnowledge,
  apiBatchImport,
  apiImportSample,
} from '../api';

// ==================== Query Keys ====================

const QUERY_KEYS = {
  articles: ['knowledge', 'articles'] as const,
  article: (id: number) => ['knowledge', 'articles', id] as const,
  categories: ['knowledge', 'categories'] as const,
  stats: ['knowledge', 'stats'] as const,
  search: (keyword: string) => ['knowledge', 'search', keyword] as const,
};

// ==================== Queries ====================

/**
 * 获取文章列表
 */
export function useArticles(request: GetArticlesRequest = {}) {
  return useQuery<{ items: KnowledgeArticleListItem[]; total: number }, Error>({
    queryKey: [...QUERY_KEYS.articles, request],
    queryFn: () => apiGetArticles(request),
    staleTime: 5 * 60 * 1000, // 5分钟
  });
}

/**
 * 获取单篇文章
 */
export function useArticle(articleId: number | null) {
  return useQuery<KnowledgeArticle, Error>({
    queryKey: articleId ? QUERY_KEYS.article(articleId) : ['knowledge', 'articles', 'null'],
    queryFn: () => {
      if (!articleId) throw new Error('文章ID不能为空');
      return apiGetArticle(articleId);
    },
    enabled: !!articleId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取分类列表
 */
export function useCategories(includeCount = false) {
  return useQuery<KnowledgeCategory[], Error>({
    queryKey: [...QUERY_KEYS.categories, includeCount],
    queryFn: () => apiGetCategories(includeCount),
    staleTime: 10 * 60 * 1000, // 10分钟
  });
}

/**
 * 获取知识库统计
 */
export function useKnowledgeStats() {
  return useQuery<KnowledgeStats, Error>({
    queryKey: QUERY_KEYS.stats,
    queryFn: apiGetStats,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 搜索知识
 */
export function useKnowledgeSearch(request: SearchKnowledgeRequest) {
  return useQuery<{ items: KnowledgeArticleListItem[]; total: number }, Error>({
    queryKey: [...QUERY_KEYS.search(request.keyword), request],
    queryFn: () => apiSearchKnowledge(request),
    enabled: !!request.keyword && request.keyword.length > 0,
    staleTime: 2 * 60 * 1000, // 2分钟
  });
}

// ==================== Mutations ====================

/**
 * 创建文章
 */
export function useCreateArticle() {
  const queryClient = useQueryClient();

  return useMutation<KnowledgeArticle, Error, CreateArticleRequest>({
    mutationFn: apiCreateArticle,
    onSuccess: () => {
      // 创建成功后，刷新文章列表和统计
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.articles });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.stats });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.categories });
    },
  });
}

/**
 * 更新文章
 */
export function useUpdateArticle() {
  const queryClient = useQueryClient();

  return useMutation<
    KnowledgeArticle,
    Error,
    { articleId: number; request: UpdateArticleRequest }
  >({
    mutationFn: ({ articleId, request }) => apiUpdateArticle(articleId, request),
    onSuccess: (_, variables) => {
      // 更新成功后，刷新相关缓存
      void queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.article(variables.articleId),
      });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.articles });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.stats });
    },
  });
}

/**
 * 删除文章
 */
export function useDeleteArticle() {
  const queryClient = useQueryClient();

  return useMutation<boolean, Error, number>({
    mutationFn: apiDeleteArticle,
    onSuccess: () => {
      // 删除成功后，刷新所有相关缓存
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.articles });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.stats });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.categories });
    },
  });
}

/**
 * 创建分类
 */
export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation<KnowledgeCategory, Error, { name: string; description?: string }>({
    mutationFn: ({ name, description }) => apiCreateCategory({ name, description }),
    onSuccess: () => {
      // 创建成功后，刷新分类列表
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.categories });
    },
  });
}

/**
 * 批量导入知识
 */
export function useBatchImport() {
  const queryClient = useQueryClient();

  return useMutation<
    { success: number; failed: number; total: number; message: string },
    Error,
    BatchImportRequest
  >({
    mutationFn: apiBatchImport,
    onSuccess: () => {
      // 导入成功后，刷新所有相关缓存
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.articles });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.stats });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.categories });
    },
  });
}

/**
 * 导入示例数据
 */
export function useImportSample() {
  const queryClient = useQueryClient();

  return useMutation<
    { success: number; failed: number; total: number; message: string },
    Error
  >({
    mutationFn: apiImportSample,
    onSuccess: () => {
      // 导入成功后，刷新所有相关缓存
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.articles });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.stats });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.categories });
    },
  });
}

// ==================== 工具 Hooks ====================

/**
 * 知识库管理综合 Hook
 */
export function useKnowledgeAdmin() {
  const _queryClient = useQueryClient();

  const {
    data: articlesData,
    isLoading: isLoadingArticles,
    error: articlesError,
    refetch: refetchArticles,
  } = useArticles();

  const {
    data: categories,
    isLoading: isLoadingCategories,
    error: categoriesError,
    refetch: refetchCategories,
  } = useCategories(true);

  const {
    data: stats,
    isLoading: isLoadingStats,
    error: statsError,
    refetch: refetchStats,
  } = useKnowledgeStats();

  const createArticle = useCreateArticle();
  const updateArticle = useUpdateArticle();
  const deleteArticle = useDeleteArticle();
  const createCategory = useCreateCategory();
  const batchImport = useBatchImport();
  const importSample = useImportSample();

  /**
   * 刷新所有知识库相关数据
   */
  const refreshAll = useCallback(() => {
    return Promise.all([
      refetchArticles(),
      refetchCategories(),
      refetchStats(),
    ]);
  }, [refetchArticles, refetchCategories, refetchStats]);

  return {
    // 数据
    articles: articlesData?.items ?? [],
    totalArticles: articlesData?.total ?? 0,
    categories: categories ?? [],
    stats,

    // 加载状态
    isLoading: isLoadingArticles || isLoadingCategories || isLoadingStats,
    isLoadingArticles,
    isLoadingCategories,
    isLoadingStats,

    // 错误
    error: articlesError || categoriesError || statsError,

    // 操作方法
    createArticle,
    updateArticle,
    deleteArticle,
    createCategory,
    batchImport,
    importSample,

    // 刷新方法
    refetchArticles,
    refetchCategories,
    refetchStats,
    refreshAll,
  };
}