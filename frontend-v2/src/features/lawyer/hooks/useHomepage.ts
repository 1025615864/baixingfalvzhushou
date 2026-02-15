/**
 * 律师主页 Hook
 * 使用 React Query 管理律师主页相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  LawyerHomepage,
  LawyerHomepagePublic,
  CreateHomepageRequest,
  UpdateHomepageRequest,
} from '../types';
import {
  getMyHomepage as getMyHomepageApi,
  createHomepage as createHomepageApi,
  updateHomepage as updateHomepageApi,
  publishHomepage as publishHomepageApi,
  unpublishHomepage as unpublishHomepageApi,
  getPublicHomepage as getPublicHomepageApi,
} from '../api';

// Query Keys
const HOMEPAGE_KEYS = {
  all: ['lawyer', 'homepage'] as const,
  my: () => [...HOMEPAGE_KEYS.all, 'my'] as const,
  public: (lawyerId: string) => [...HOMEPAGE_KEYS.all, 'public', lawyerId] as const,
} as const;

/**
 * 获取我的主页
 */
export function useMyHomepage() {
  return useQuery<LawyerHomepage, Error>({
    queryKey: HOMEPAGE_KEYS.my(),
    queryFn: getMyHomepageApi,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    retry: false,
  });
}

/**
 * 获取公开主页
 */
export function usePublicHomepage(lawyerId: string) {
  return useQuery<LawyerHomepagePublic, Error>({
    queryKey: HOMEPAGE_KEYS.public(lawyerId),
    queryFn: () => getPublicHomepageApi(lawyerId),
    staleTime: 10 * 60 * 1000, // 10分钟缓存
    enabled: !!lawyerId,
  });
}

/**
 * 创建主页
 */
export function useCreateHomepage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateHomepageRequest) => createHomepageApi(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: HOMEPAGE_KEYS.my() });
    },
  });
}

/**
 * 更新主页
 */
export function useUpdateHomepage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateHomepageRequest) => updateHomepageApi(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: HOMEPAGE_KEYS.my() });
    },
  });
}

/**
 * 发布主页
 */
export function usePublishHomepage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: publishHomepageApi,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: HOMEPAGE_KEYS.my() });
    },
  });
}

/**
 * 取消发布主页
 */
export function useUnpublishHomepage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: unpublishHomepageApi,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: HOMEPAGE_KEYS.my() });
    },
  });
}

/**
 * 检查主页是否存在
 */
export function useHasHomepage(): boolean {
  const { data, isError } = useMyHomepage();
  return !!data && !isError;
}

/**
 * 获取主页公开URL
 */
export function useHomepagePublicUrl(lawyerId: string | undefined): string | null {
  if (!lawyerId) return null;
  return `${window.location.origin}/lawyers/${lawyerId}/homepage`;
}