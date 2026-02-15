/**
 * 快捷回复模板 Hook
 * 使用 React Query 管理快捷回复模板相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  LawyerReplyTemplate,
  CreateReplyTemplateRequest,
  UpdateReplyTemplateRequest,
  ReplyTemplateListResponse,
  ReplyTemplateCategoriesResponse,
  UseReplyTemplateResponse,
} from '../types';
import {
  getReplyTemplates as getReplyTemplatesApi,
  getReplyTemplateCategories as getReplyTemplateCategoriesApi,
  createReplyTemplate as createReplyTemplateApi,
  getReplyTemplate as getReplyTemplateApi,
  updateReplyTemplate as updateReplyTemplateApi,
  deleteReplyTemplate as deleteReplyTemplateApi,
  useReplyTemplate as applyReplyTemplateApi,
} from '../api';

// Query Keys
const TEMPLATE_KEYS = {
  all: ['lawyer', 'replyTemplates'] as const,
  lists: () => [...TEMPLATE_KEYS.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...TEMPLATE_KEYS.lists(), filters] as const,
  details: () => [...TEMPLATE_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...TEMPLATE_KEYS.details(), id] as const,
  categories: () => [...TEMPLATE_KEYS.all, 'categories'] as const,
} as const;

/**
 * 获取快捷回复模板列表
 */
export function useReplyTemplates(params: {
  category?: string;
  isActive?: boolean;
  page?: number;
  pageSize?: number;
} = {}) {
  return useQuery<ReplyTemplateListResponse, Error>({
    queryKey: TEMPLATE_KEYS.list(params),
    queryFn: () => getReplyTemplatesApi(params),
    staleTime: 2 * 60 * 1000, // 2分钟缓存
  });
}

/**
 * 获取模板分类列表
 */
export function useReplyTemplateCategories() {
  return useQuery<ReplyTemplateCategoriesResponse, Error>({
    queryKey: TEMPLATE_KEYS.categories(),
    queryFn: getReplyTemplateCategoriesApi,
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

/**
 * 获取快捷回复模板详情
 */
export function useReplyTemplate(templateId: string) {
  return useQuery<LawyerReplyTemplate, Error>({
    queryKey: TEMPLATE_KEYS.detail(templateId),
    queryFn: () => getReplyTemplateApi(templateId),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: !!templateId,
  });
}

/**
 * 创建快捷回复模板
 */
export function useCreateReplyTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateReplyTemplateRequest) => createReplyTemplateApi(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.lists() });
    },
  });
}

/**
 * 更新快捷回复模板
 */
export function useUpdateReplyTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ templateId, data }: { templateId: string; data: UpdateReplyTemplateRequest }) =>
      updateReplyTemplateApi(templateId, data),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.lists() });
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.detail(variables.templateId) });
    },
  });
}

/**
 * 删除快捷回复模板
 */
export function useDeleteReplyTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (templateId: string) => deleteReplyTemplateApi(templateId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.lists() });
    },
  });
}

/**
 * 使用快捷回复模板
 */
export function useUseReplyTemplate() {
  const queryClient = useQueryClient();

  return useMutation<UseReplyTemplateResponse, Error, string>({
    mutationFn: (templateId: string) => applyReplyTemplateApi(templateId),
    onSuccess: () => {
      // 使用后增加使用次数
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.lists() });
    },
  });
}