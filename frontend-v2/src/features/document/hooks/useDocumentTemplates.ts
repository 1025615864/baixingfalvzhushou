/**
 * 文档模板管理 Hook（管理员用）
 * 使用 React Query 管理文档模板相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  DocumentTemplate,
  GetDocumentTemplatesRequest,
  GetDocumentTemplatesResponse,
  CreateDocumentTemplateRequest,
  UpdateDocumentTemplateRequest,
  PreviewTemplateRequest,
} from '../types';
import {
  apiGetDocumentTemplates,
  apiGetDocumentTemplate,
  apiCreateDocumentTemplate,
  apiUpdateDocumentTemplate,
  apiDeleteDocumentTemplate,
  apiPublishDocumentTemplate,
  apiPreviewTemplate,
} from '../api';

// Query Keys
const TEMPLATE_KEYS = {
  all: ['document', 'templates', 'admin'] as const,
  list: (params: GetDocumentTemplatesRequest) => [...TEMPLATE_KEYS.all, 'list', params] as const,
  detail: (id: string) => [...TEMPLATE_KEYS.all, 'detail', id] as const,
} as const;

/**
 * 获取文档模板列表（管理员用）
 */
export function useDocumentTemplates(params: GetDocumentTemplatesRequest = {}) {
  return useQuery<GetDocumentTemplatesResponse, Error>({
    queryKey: TEMPLATE_KEYS.list(params),
    queryFn: () => apiGetDocumentTemplates(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 获取文档模板详情（管理员用）
 */
export function useDocumentTemplate(id: string | null) {
  return useQuery<DocumentTemplate, Error>({
    queryKey: TEMPLATE_KEYS.detail(id ?? ''),
    queryFn: () => apiGetDocumentTemplate(id!),
    enabled: !!id,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 创建文档模板（管理员用）
 */
export function useCreateDocumentTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateDocumentTemplateRequest) => apiCreateDocumentTemplate(request),
    onSuccess: () => {
      // 创建成功后刷新模板列表
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
    },
  });
}

/**
 * 更新文档模板（管理员用）
 */
export function useUpdateDocumentTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateDocumentTemplateRequest }) =>
      apiUpdateDocumentTemplate(id, request),
    onSuccess: (_, variables) => {
      // 更新成功后刷新模板列表和详情
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.detail(variables.id) });
    },
  });
}

/**
 * 删除文档模板（管理员用）
 */
export function useDeleteDocumentTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiDeleteDocumentTemplate(id),
    onSuccess: () => {
      // 删除成功后刷新模板列表
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
    },
  });
}

/**
 * 发布文档模板（管理员用）
 */
export function usePublishDocumentTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiPublishDocumentTemplate(id),
    onSuccess: (_, id) => {
      // 发布成功后刷新模板列表和详情
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
      void queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.detail(id) });
    },
  });
}

/**
 * 预览模板（管理员用）
 */
export function usePreviewTemplate() {
  return useMutation({
    mutationFn: (request: PreviewTemplateRequest) => apiPreviewTemplate(request),
  });
}
