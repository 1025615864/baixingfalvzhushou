/**
 * 推广链接 Hook
 * 使用 React Query 管理推广链接相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  LawyerPromotionLink,
  CreatePromotionLinkRequest,
  UpdatePromotionLinkRequest,
  PromotionLinkListResponse,
  PromotionLinkStats,
} from '../types';
import {
  getPromotionLinks as getPromotionLinksApi,
  createPromotionLink as createPromotionLinkApi,
  getPromotionLink as getPromotionLinkApi,
  updatePromotionLink as updatePromotionLinkApi,
  deletePromotionLink as deletePromotionLinkApi,
  getPromotionLinkStats as getPromotionLinkStatsApi,
} from '../api';

// Query Keys
const PROMOTION_KEYS = {
  all: ['lawyer', 'promotions'] as const,
  lists: () => [...PROMOTION_KEYS.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...PROMOTION_KEYS.lists(), filters] as const,
  details: () => [...PROMOTION_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...PROMOTION_KEYS.details(), id] as const,
  stats: (id: string) => [...PROMOTION_KEYS.all, 'stats', id] as const,
} as const;

/**
 * 获取推广链接列表
 */
export function usePromotionLinks(params: {
  isActive?: boolean;
  page?: number;
  pageSize?: number;
} = {}) {
  return useQuery<PromotionLinkListResponse, Error>({
    queryKey: PROMOTION_KEYS.list(params),
    queryFn: () => getPromotionLinksApi('me', params),
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * 获取推广链接详情
 */
export function usePromotionLink(linkId: string) {
  return useQuery<LawyerPromotionLink, Error>({
    queryKey: PROMOTION_KEYS.detail(linkId),
    queryFn: () => getPromotionLinkApi('me', linkId),
    staleTime: 5 * 60 * 1000,
    enabled: !!linkId,
  });
}

/**
 * 获取推广链接统计
 */
export function usePromotionLinkStats(linkId: string) {
  return useQuery<PromotionLinkStats, Error>({
    queryKey: PROMOTION_KEYS.stats(linkId),
    queryFn: () => getPromotionLinkStatsApi(linkId),
    staleTime: 1 * 60 * 1000, // 1分钟缓存
    enabled: !!linkId,
  });
}

/**
 * 创建推广链接
 */
export function useCreatePromotionLink() {
  const queryClient = useQueryClient();

  return useMutation<LawyerPromotionLink, Error, CreatePromotionLinkRequest>({
    mutationFn: (data) => createPromotionLinkApi('me', data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROMOTION_KEYS.lists() });
    },
  });
}

/**
 * 更新推广链接
 */
export function useUpdatePromotionLink() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ linkId, data }: { linkId: string; data: UpdatePromotionLinkRequest }) =>
      updatePromotionLinkApi(linkId, data),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: PROMOTION_KEYS.lists() });
      void queryClient.invalidateQueries({ queryKey: PROMOTION_KEYS.detail(variables.linkId) });
    },
  });
}

/**
 * 删除推广链接
 */
export function useDeletePromotionLink() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (linkId: string) => deletePromotionLinkApi(linkId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROMOTION_KEYS.lists() });
    },
  });
}

/**
 * 生成推广链接URL
 */
export function generatePromotionUrl(linkCode: string): string {
  return `${window.location.origin}/p/${linkCode}`;
}

/**
 * 复制推广链接到剪贴板
 */
export async function copyPromotionLink(linkCode: string): Promise<boolean> {
  const url = generatePromotionUrl(linkCode);
  try {
    await navigator.clipboard.writeText(url);
    return true;
  } catch {
    return false;
  }
}