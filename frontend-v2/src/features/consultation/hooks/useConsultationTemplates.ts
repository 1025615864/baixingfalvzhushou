/**
 * 咨询模板管理 Hook（管理员用）
 * 使用 React Query 管理咨询模板相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  ConsultationTemplate,
  GetConsultationTemplatesRequest,
  GetConsultationTemplatesResponse,
  CreateConsultationTemplateRequest,
  UpdateConsultationTemplateRequest,
} from '../types';
import {
  apiGetConsultationTemplates,
  apiGetConsultationTemplate,
  apiCreateConsultationTemplate,
  apiUpdateConsultationTemplate,
  apiDeleteConsultationTemplate,
  apiPublishConsultationTemplate,
} from '../api';

// Query Keys
const TEMPLATE_KEYS = {
  all: ['consultation', 'templates', 'admin'] as const,
  list: (params: GetConsultationTemplatesRequest) => [...TEMPLATE_KEYS.all, 'list', params] as const,
  detail: (id: string) => [...TEMPLATE_KEYS.all, 'detail', id] as const,
} as const;

/**
 * 获取咨询模板列表（管理员用）
 */
export function useConsultationTemplates(params: GetConsultationTemplatesRequest = {}) {
  return useQuery<GetConsultationTemplatesResponse, Error>({
    queryKey: TEMPLATE_KEYS.list(params),
    queryFn: () => apiGetConsultationTemplates(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 获取咨询模板详情（管理员用）
 */
export function useConsultationTemplate(id: string | null) {
  return useQuery<ConsultationTemplate, Error>({
    queryKey: TEMPLATE_KEYS.detail(id ?? ''),
    queryFn: () => apiGetConsultationTemplate(id!),
    enabled: !!id,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 创建咨询模板（管理员用）
 */
export function useCreateConsultationTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateConsultationTemplateRequest) => apiCreateConsultationTemplate(request),
    onSuccess: () => {
      // 创建成功后刷新模板列表
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
    },
  });
}

/**
 * 更新咨询模板（管理员用）
 */
export function useUpdateConsultationTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateConsultationTemplateRequest }) =>
      apiUpdateConsultationTemplate(id, request),
    onSuccess: (_, variables) => {
      // 更新成功后刷新模板列表和详情
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.detail(variables.id) });
    },
  });
}

/**
 * 删除咨询模板（管理员用）
 */
export function useDeleteConsultationTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiDeleteConsultationTemplate(id),
    onSuccess: () => {
      // 删除成功后刷新模板列表
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
    },
  });
}

/**
 * 发布咨询模板（管理员用）
 */
export function usePublishConsultationTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiPublishConsultationTemplate(id),
    onSuccess: (_, id) => {
      // 发布成功后刷新模板列表和详情
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.detail(id) });
    },
  });
}
