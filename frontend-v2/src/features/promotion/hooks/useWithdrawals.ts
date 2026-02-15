/**
 * 提现管理 Hook（管理员用）
 * 使用 React Query 管理提现相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  WithdrawalItem,
  WithdrawalDetail,
  WithdrawalStats,
  GetWithdrawalsRequest,
  ReviewWithdrawalRequest,
} from '../types';
import {
  apiGetWithdrawalsAdmin,
  apiGetWithdrawalDetail,
  apiReviewWithdrawal,
  apiExportWithdrawals,
} from '../api';

// Query Keys
const WITHDRAWAL_KEYS = {
  all: ['promotion', 'withdrawals', 'admin'] as const,
  list: (params: GetWithdrawalsRequest) => [...WITHDRAWAL_KEYS.all, 'list', params] as const,
  detail: (id: string) => [...WITHDRAWAL_KEYS.all, 'detail', id] as const,
} as const;

/**
 * 获取提现列表（管理员用）
 */
export function useWithdrawalsAdmin(params: GetWithdrawalsRequest = {}) {
  return useQuery<{
    items: WithdrawalItem[];
    total: number;
    page: number;
    pageSize: number;
    stats: WithdrawalStats;
  }, Error>({
    queryKey: WITHDRAWAL_KEYS.list(params),
    queryFn: () => apiGetWithdrawalsAdmin(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 获取提现详情（管理员用）
 */
export function useWithdrawalDetail(id: string | null) {
  return useQuery<WithdrawalDetail, Error>({
    queryKey: WITHDRAWAL_KEYS.detail(id ?? ''),
    queryFn: () => apiGetWithdrawalDetail(id!),
    enabled: !!id,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 审核提现申请（管理员用）
 */
export function useReviewWithdrawal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: ReviewWithdrawalRequest }) =>
      apiReviewWithdrawal(id, request),
    onSuccess: () => {
      // 审核成功后刷新提现列表和详情
      void queryClient.invalidateQueries({ queryKey: WITHDRAWAL_KEYS.all });
    },
  });
}

/**
 * 导出提现记录（管理员用）
 */
export function useExportWithdrawals() {
  return useMutation({
    mutationFn: (params: Omit<GetWithdrawalsRequest, 'page' | 'pageSize'>) =>
      apiExportWithdrawals(params),
  });
}
