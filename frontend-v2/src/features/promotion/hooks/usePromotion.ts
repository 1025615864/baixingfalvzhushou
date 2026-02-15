/**
 * Promotion（推广系统）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  PromotionLink,
  PromotionStats,
  CommissionRecord,
  PromotionPoster,
  CommissionWithdrawal,
  GetPromotionStatsRequest,
  GetCommissionRecordsRequest,
  GeneratePosterRequest,
  RequestWithdrawalRequest,
} from '../types';
import {
  apiGetPromotionLink,
  apiGeneratePromotionLink,
  apiGetPromotionStats,
  apiGetCommissionRecords,
  apiGeneratePoster,
  apiGetPosters,
  apiRequestWithdrawal,
  apiGetWithdrawals,
  apiGetPromotionRules,
} from '../api';

// ==================== Query Keys ====================

const PROMOTION_QUERY_KEYS = {
  link: ['promotion', 'link'] as const,
  stats: (params?: GetPromotionStatsRequest) => ['promotion', 'stats', params] as const,
  commissions: (params?: GetCommissionRecordsRequest) => ['promotion', 'commissions', params] as const,
  posters: ['promotion', 'posters'] as const,
  withdrawals: ['promotion', 'withdrawals'] as const,
  rules: ['promotion', 'rules'] as const,
} as const;

// ==================== Link Hooks ====================

/**
 * 获取推广链接 Hook
 */
export function usePromotionLink() {
  return useQuery<PromotionLink>({
    queryKey: PROMOTION_QUERY_KEYS.link,
    queryFn: apiGetPromotionLink,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 生成推广链接 Hook
 */
export function useGeneratePromotionLink() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiGeneratePromotionLink,
    onSuccess: () => {
      // 生成成功后，刷新链接数据
      void queryClient.invalidateQueries({ queryKey: PROMOTION_QUERY_KEYS.link });
    },
  });
}

// ==================== Stats Hooks ====================

/**
 * 获取推广统计 Hook
 */
export function usePromotionStats(params: GetPromotionStatsRequest = {}) {
  return useQuery<PromotionStats>({
    queryKey: PROMOTION_QUERY_KEYS.stats(params),
    queryFn: () => apiGetPromotionStats(params),
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Commission Hooks ====================

/**
 * 分页佣金记录结果
 */
export interface PaginatedCommissionResult {
  records: CommissionRecord[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * 获取佣金记录 Hook（支持分页）
 */
export function useCommissionRecords(params: GetCommissionRecordsRequest = {}) {
  return useQuery<PaginatedCommissionResult>({
    queryKey: PROMOTION_QUERY_KEYS.commissions(params),
    queryFn: async () => {
      const response = await apiGetCommissionRecords(params);
      return {
        records: response.records,
        total: response.total,
        limit: params.limit ?? 20,
        offset: params.offset ?? 0,
      };
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Poster Hooks ====================

/**
 * 获取海报列表 Hook
 */
export function usePosters() {
  return useQuery<PromotionPoster[]>({
    queryKey: PROMOTION_QUERY_KEYS.posters,
    queryFn: apiGetPosters,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 生成推广海报 Hook
 */
export function useGeneratePoster() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: GeneratePosterRequest) => apiGeneratePoster(request),
    onSuccess: () => {
      // 生成成功后，刷新海报列表
      void queryClient.invalidateQueries({ queryKey: PROMOTION_QUERY_KEYS.posters });
    },
  });
}

// ==================== Withdrawal Hooks ====================

/**
 * 申请佣金提现 Hook
 */
export function useRequestWithdrawal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: RequestWithdrawalRequest) => apiRequestWithdrawal(request),
    onSuccess: () => {
      // 申请成功后，刷新提现记录和佣金记录
      void queryClient.invalidateQueries({ queryKey: PROMOTION_QUERY_KEYS.withdrawals });
      void queryClient.invalidateQueries({ queryKey: ['promotion', 'commissions'] });
    },
  });
}

/**
 * 获取提现记录 Hook
 */
export function useWithdrawals() {
  return useQuery<CommissionWithdrawal[]>({
    queryKey: PROMOTION_QUERY_KEYS.withdrawals,
    queryFn: apiGetWithdrawals,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Rules Hooks ====================

/**
 * 获取推广规则 Hook
 */
export function usePromotionRules() {
  return useQuery({
    queryKey: PROMOTION_QUERY_KEYS.rules,
    queryFn: apiGetPromotionRules,
    staleTime: 30 * 60 * 1000, // 30分钟缓存，规则不常变化
  });
}