/**
 * 支付回调管理 Hook（管理员用）
 * 使用 React Query 管理支付回调相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  PaymentCallback,
  CallbackStats,
  GetCallbacksRequest,
} from '../types';
import {
  apiGetPaymentCallbacks,
  apiRetryPaymentCallback,
  apiProcessPaymentCallback,
} from '../api';

// Query Keys
const CALLBACK_KEYS = {
  all: ['payment', 'callbacks', 'admin'] as const,
  list: (params: GetCallbacksRequest) => [...CALLBACK_KEYS.all, 'list', params] as const,
} as const;

/**
 * 获取支付回调列表（管理员用）
 */
export function usePaymentCallbacks(params: GetCallbacksRequest = {}) {
  return useQuery<{
    items: PaymentCallback[];
    total: number;
    page: number;
    pageSize: number;
    stats: CallbackStats;
  }, Error>({
    queryKey: CALLBACK_KEYS.list(params),
    queryFn: () => apiGetPaymentCallbacks(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 重试支付回调（管理员用）
 */
export function useRetryPaymentCallback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiRetryPaymentCallback(id),
    onSuccess: () => {
      // 重试成功后刷新回调列表
      void queryClient.invalidateQueries({ queryKey: CALLBACK_KEYS.all });
    },
  });
}

/**
 * 手动处理支付回调（管理员用）
 */
export function useProcessPaymentCallback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, success, note }: { id: string; success: boolean; note?: string }) =>
      apiProcessPaymentCallback(id, success, note),
    onSuccess: () => {
      // 处理成功后刷新回调列表
      void queryClient.invalidateQueries({ queryKey: CALLBACK_KEYS.all });
    },
  });
}
