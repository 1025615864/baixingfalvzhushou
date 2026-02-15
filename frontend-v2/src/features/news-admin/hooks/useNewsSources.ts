/**
 * News Sources React Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  apiGetNewsSources,
  apiCreateNewsSource,
  apiUpdateNewsSource,
  apiDeleteNewsSource,
  apiTriggerIngest,
  apiGetNewsSourceHealth,
} from '../api';
import { NEWS_ADMIN_QUERY_KEYS } from '../api/queryKeys';
import type { CreateSourceRequest, UpdateSourceRequest } from '../types';

/**
 * 获取新闻源列表
 */
export function useNewsSources() {
  return useQuery({
    queryKey: NEWS_ADMIN_QUERY_KEYS.sources.list(),
    queryFn: apiGetNewsSources,
    staleTime: 5 * 60 * 1000, // 5分钟
  });
}

/**
 * 获取来源健康状态
 */
export function useNewsSourceHealth() {
  return useQuery({
    queryKey: NEWS_ADMIN_QUERY_KEYS.sources.health(),
    queryFn: apiGetNewsSourceHealth,
    staleTime: 60 * 1000, // 1分钟
  });
}

/**
 * 创建新闻源
 */
export function useCreateNewsSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateSourceRequest) => apiCreateNewsSource(request),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: NEWS_ADMIN_QUERY_KEYS.sources.all(),
      });
    },
  });
}

/**
 * 更新新闻源
 */
export function useUpdateNewsSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: number; request: UpdateSourceRequest }) =>
      apiUpdateNewsSource(id, request),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: NEWS_ADMIN_QUERY_KEYS.sources.all(),
      });
    },
  });
}

/**
 * 删除新闻源
 */
export function useDeleteNewsSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => apiDeleteNewsSource(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: NEWS_ADMIN_QUERY_KEYS.sources.all(),
      });
    },
  });
}

/**
 * 手动触发抓取
 */
export function useTriggerIngest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sourceId: number) => apiTriggerIngest(sourceId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: NEWS_ADMIN_QUERY_KEYS.ingestRuns.all(),
      });
    },
  });
}
