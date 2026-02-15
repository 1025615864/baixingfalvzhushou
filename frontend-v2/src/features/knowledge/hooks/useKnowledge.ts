/**
 * 知识库 React Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  KnowledgeArticle,
  GetArticlesRequest,
  GetArticlesResponse,
  SearchArticlesRequest,
  SearchArticlesResponse,
  KnowledgeStats,
  GetCategoriesResponse,
  CreateArticleRequest,
  UpdateArticleRequest,
} from '../types';
import { knowledgeApi } from '../api';
import { knowledgeKeys } from '../api/queryKeys';

/**
 * 获取法律知识列表 Hook
 */
export function useKnowledge(params: GetArticlesRequest = {}) {
  return useQuery<GetArticlesResponse, Error>({
    queryKey: knowledgeKeys.list(params),
    queryFn: () => knowledgeApi.getArticles(params),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 获取单个法律知识详情 Hook
 */
export function useKnowledgeDetail(articleId: string | undefined) {
  return useQuery<KnowledgeArticle, Error>({
    queryKey: knowledgeKeys.detail(articleId || ''),
    queryFn: () => knowledgeApi.getArticle(articleId!),
    enabled: !!articleId, // 只有articleId存在时才执行查询
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

/**
 * 搜索法律知识 Hook
 */
export function useKnowledgeSearch(params: SearchArticlesRequest) {
  return useQuery<SearchArticlesResponse, Error>({
    queryKey: knowledgeKeys.search(params),
    queryFn: () => knowledgeApi.searchArticles(params),
    enabled: params.query.length > 0, // 只有有查询内容时才执行
    staleTime: 2 * 60 * 1000, // 2分钟缓存
  });
}

/**
 * 获取分类列表 Hook
 */
export function useCategories() {
  return useQuery<GetCategoriesResponse, Error>({
    queryKey: knowledgeKeys.categories(),
    queryFn: () => knowledgeApi.getCategories(),
    staleTime: 30 * 60 * 1000, // 30分钟缓存，分类不常变化
  });
}

/**
 * 获取知识库统计 Hook
 */
export function useKnowledgeStats() {
  return useQuery<KnowledgeStats, Error>({
    queryKey: knowledgeKeys.stats(),
    queryFn: () => knowledgeApi.getKnowledgeStats(),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 创建法律知识 Mutation
 */
export function useCreateKnowledge() {
  const queryClient = useQueryClient();

  return useMutation<KnowledgeArticle, Error, CreateArticleRequest>({
    mutationFn: (data) => knowledgeApi.createArticle(data),
    onSuccess: async () => {
      // 创建成功后，使列表缓存失效
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.lists() });
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.stats() });
    },
  });
}

/**
 * 更新法律知识 Mutation
 */
export function useUpdateKnowledge() {
  const queryClient = useQueryClient();

  return useMutation<KnowledgeArticle, Error, { id: string; data: UpdateArticleRequest }>({
    mutationFn: ({ id, data }) => knowledgeApi.updateArticle(id, data),
    onSuccess: async (_, variables) => {
      // 更新成功后，使详情和列表缓存失效
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.detail(variables.id) });
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.lists() });
    },
  });
}

/**
 * 删除法律知识 Mutation
 */
export function useDeleteKnowledge() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, string>({
    mutationFn: (id) => knowledgeApi.deleteArticle(id),
    onSuccess: async () => {
      // 删除成功后，使列表和统计缓存失效
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.lists() });
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.stats() });
    },
  });
}