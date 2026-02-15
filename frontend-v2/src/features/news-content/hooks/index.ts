/**
 * News Content React Query Hooks
 * 新闻内容管理和 AI 辅助编辑的 hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { newsContentApi } from '../api';
import type {
  ArticleListParams,
  ArticleDraft,
  DraftListParams,
  TagListParams,
} from '../types';

// Query Keys
export const queryKeys = {
  all: ['news-content'] as const,
  articles: (params?: ArticleListParams) => [...queryKeys.all, 'articles', params] as const,
  article: (id: string) => [...queryKeys.all, 'articles', id] as const,
  drafts: (params?: DraftListParams) => [...queryKeys.all, 'drafts', params] as const,
  draft: (id: string) => [...queryKeys.all, 'drafts', id] as const,
  categories: () => [...queryKeys.all, 'categories'] as const,
  category: (id: string) => [...queryKeys.all, 'categories', id] as const,
  tags: (params?: TagListParams) => [...queryKeys.all, 'tags', params] as const,
  tag: (id: string) => [...queryKeys.all, 'tags', id] as const,
  aiSummary: (id: string) => [...queryKeys.all, 'ai-summary', id] as const,
  aiAnalysis: (id: string) => [...queryKeys.all, 'ai-analysis', id] as const,
  aiTags: (id: string) => [...queryKeys.all, 'ai-tags', id] as const,
};

// ============ 文章相关 Hooks ============

export function useArticles(params?: ArticleListParams) {
  return useQuery({
    queryKey: queryKeys.articles(params),
    queryFn: () => newsContentApi.list(params),
    staleTime: 30 * 1000,
  });
}

export function useArticle(id: string) {
  return useQuery({
    queryKey: queryKeys.article(id),
    queryFn: () => newsContentApi.get(id),
    enabled: Boolean(id),
  });
}

export function useCreateArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof newsContentApi.create>[0]) =>
      newsContentApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.articles() });
    },
  });
}

export function useUpdateArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: Parameters<typeof newsContentApi.update>[1];
    }) => newsContentApi.update(id, data),
    onSuccess: (_, { id }) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.article(id) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.articles() });
    },
  });
}

export function useDeleteArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => newsContentApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.articles() });
    },
  });
}

export function usePublishArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => newsContentApi.publish(id),
    onSuccess: (_, id) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.article(id) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.articles() });
    },
  });
}

export function useArchiveArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => newsContentApi.archive(id),
    onSuccess: (_, id) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.article(id) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.articles() });
    },
  });
}

// ============ 草稿相关 Hooks ============

export function useDrafts(params?: DraftListParams) {
  return useQuery({
    queryKey: queryKeys.drafts(params),
    queryFn: () => newsContentApi.getDrafts(params),
    staleTime: 15 * 1000,
  });
}

export function useDraft(id: string) {
  return useQuery({
    queryKey: queryKeys.draft(id),
    queryFn: () => newsContentApi.getDraft(id),
    enabled: Boolean(id),
  });
}

export function useSaveDraft() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<ArticleDraft>) => newsContentApi.saveDraft(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.drafts() });
    },
  });
}

export function useDeleteDraft() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => newsContentApi.deleteDraft(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.drafts() });
    },
  });
}

// ============ 分类相关 Hooks ============

export function useCategories() {
  return useQuery({
    queryKey: queryKeys.categories(),
    queryFn: () => newsContentApi.getCategories(),
    staleTime: 60 * 1000,
  });
}

export function useCategory(id: string) {
  return useQuery({
    queryKey: queryKeys.category(id),
    queryFn: () => newsContentApi.getCategory(id),
    enabled: Boolean(id),
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof newsContentApi.createCategory>[0]) =>
      newsContentApi.createCategory(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.categories() });
    },
  });
}

export function useUpdateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: Parameters<typeof newsContentApi.updateCategory>[1];
    }) => newsContentApi.updateCategory(id, data),
    onSuccess: (_, { id }) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.category(id) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.categories() });
    },
  });
}

export function useDeleteCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => newsContentApi.deleteCategory(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.categories() });
    },
  });
}

export function useReorderCategories() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (categoryIds: string[]) => newsContentApi.reorderCategories(categoryIds),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.categories() });
    },
  });
}

// ============ 标签相关 Hooks ============

export function useTags(params?: TagListParams) {
  return useQuery({
    queryKey: queryKeys.tags(params),
    queryFn: () => newsContentApi.getTags(params),
    staleTime: 60 * 1000,
  });
}

export function useTag(id: string) {
  return useQuery({
    queryKey: queryKeys.tag(id),
    queryFn: () => newsContentApi.getTag(id),
    enabled: Boolean(id),
  });
}

export function useCreateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof newsContentApi.createTag>[0]) =>
      newsContentApi.createTag(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.tags() });
    },
  });
}

export function useUpdateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: Parameters<typeof newsContentApi.updateTag>[1];
    }) => newsContentApi.updateTag(id, data),
    onSuccess: (_, { id }) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.tag(id) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.tags() });
    },
  });
}

export function useDeleteTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => newsContentApi.deleteTag(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.tags() });
    },
  });
}

// ============ AI 辅助相关 Hooks ============

export function useAISummary(articleId: string) {
  return useQuery({
    queryKey: queryKeys.aiSummary(articleId),
    queryFn: () => newsContentApi.getAISummary(articleId),
    enabled: Boolean(articleId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAIAnalysis(articleId: string) {
  return useQuery({
    queryKey: queryKeys.aiAnalysis(articleId),
    queryFn: () => newsContentApi.getAIAnalysis(articleId),
    enabled: Boolean(articleId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAITags(articleId: string) {
  return useQuery({
    queryKey: queryKeys.aiTags(articleId),
    queryFn: () => newsContentApi.getAITags(articleId),
    enabled: Boolean(articleId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useImproveWithAI() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      articleId,
      options,
    }: {
      articleId: string;
      options?: Parameters<typeof newsContentApi.improveWithAI>[1];
    }) => newsContentApi.improveWithAI(articleId, options),
    onSuccess: (_, { articleId }) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.article(articleId) });
    },
  });
}

export function useGenerateWithAI() {
  return useMutation({
    mutationFn: ({
      prompt,
      options,
    }: {
      prompt: string;
      options?: Parameters<typeof newsContentApi.generateWithAI>[1];
    }) => newsContentApi.generateWithAI(prompt, options),
  });
}

// ============ 图片相关 Hooks ============

export function useUploadImage() {
  return useMutation({
    mutationFn: (file: File) => newsContentApi.uploadImage(file),
  });
}

export function useDeleteImage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => newsContentApi.deleteImage(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.all });
    },
  });
}
