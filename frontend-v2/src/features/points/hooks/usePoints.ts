/**
 * Points（积分系统）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  PointsBalance,
  PointsTransaction,
  PointsProduct,
  ExchangeOrder,
  DailyStat,
  PointsRule,
  LeaderboardItem,
  CheckInResult,
  GetPointsHistoryRequest,
} from '../types';
import {
  apiGetPointsBalance,
  apiGetPointsHistory,
  apiGetPointsProducts,
  apiExchangeProduct,
  apiCheckIn,
  apiGetDailyStats,
  apiGetPointsRules,
  apiGetPointsLeaderboard,
  apiGetExchangeOrders,
} from '../api';

// ==================== Query Keys ====================

const POINTS_QUERY_KEYS = {
  balance: ['points', 'balance'] as const,
  history: (params?: GetPointsHistoryRequest) => ['points', 'history', params] as const,
  products: (type?: string) => ['points', 'products', type] as const,
  orders: (status?: string) => ['points', 'orders', status] as const,
  dailyStats: ['points', 'dailyStats'] as const,
  rules: ['points', 'rules'] as const,
  leaderboard: (topK?: number) => ['points', 'leaderboard', topK] as const,
} as const;

// ==================== Balance Hooks ====================

/**
 * 获取积分余额 Hook
 */
export function usePointsBalance() {
  return useQuery<PointsBalance>({
    queryKey: POINTS_QUERY_KEYS.balance,
    queryFn: apiGetPointsBalance,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== History Hooks ====================

/**
 * 分页结果类型
 */
export interface PaginatedHistoryResult {
  history: PointsTransaction[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * 获取积分历史 Hook（支持分页）
 */
export function usePointsHistory(params: GetPointsHistoryRequest = {}) {
  return useQuery<PaginatedHistoryResult>({
    queryKey: POINTS_QUERY_KEYS.history(params),
    queryFn: async () => {
      const response = await apiGetPointsHistory(params);
      return {
        history: response.history,
        total: response.total,
        limit: response.limit,
        offset: response.offset,
      };
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Product Hooks ====================

/**
 * 获取积分商品列表 Hook
 */
export function usePointsProducts(productType?: string) {
  return useQuery<PointsProduct[]>({
    queryKey: POINTS_QUERY_KEYS.products(productType),
    queryFn: async () => {
      const response = await apiGetPointsProducts(productType);
      return response.products;
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== Exchange Hooks ====================

/**
 * 兑换商品 Hook
 */
export function useExchangeProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiExchangeProduct,
    onSuccess: () => {
      // 兑换成功后，刷新余额和订单列表
      void queryClient.invalidateQueries({ queryKey: POINTS_QUERY_KEYS.balance });
      void queryClient.invalidateQueries({ queryKey: ['points', 'orders'] });
    },
  });
}

// ==================== Order Hooks ====================

/**
 * 获取兑换订单列表 Hook
 */
export function useExchangeOrders(status?: string) {
  return useQuery<ExchangeOrder[]>({
    queryKey: POINTS_QUERY_KEYS.orders(status),
    queryFn: async () => {
      const response = await apiGetExchangeOrders(status);
      return response.orders;
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Check-in Hooks ====================

/**
 * 每日签到 Hook
 */
export function useCheckIn() {
  const queryClient = useQueryClient();

  return useMutation<CheckInResult, Error, void>({
    mutationFn: apiCheckIn,
    onSuccess: () => {
      // 签到成功后，刷新余额、历史记录和每日统计
      void queryClient.invalidateQueries({ queryKey: POINTS_QUERY_KEYS.balance });
      void queryClient.invalidateQueries({ queryKey: ['points', 'history'] });
      void queryClient.invalidateQueries({ queryKey: POINTS_QUERY_KEYS.dailyStats });
    },
  });
}

// ==================== Stats Hooks ====================

/**
 * 获取每日统计 Hook
 */
export function useDailyStats() {
  return useQuery<DailyStat[]>({
    queryKey: POINTS_QUERY_KEYS.dailyStats,
    queryFn: async () => {
      const response = await apiGetDailyStats();
      return response.stats;
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Rules Hooks ====================

/**
 * 获取积分规则 Hook
 */
export function usePointsRules() {
  return useQuery<PointsRule[]>({
    queryKey: POINTS_QUERY_KEYS.rules,
    queryFn: async () => {
      const response = await apiGetPointsRules();
      return response.rules;
    },
    staleTime: 30 * 60 * 1000, // 30分钟缓存，规则不常变化
  });
}

// ==================== Leaderboard Hooks ====================

/**
 * 获取积分排行榜 Hook
 */
export function usePointsLeaderboard(topK: number = 100) {
  return useQuery<LeaderboardItem[]>({
    queryKey: POINTS_QUERY_KEYS.leaderboard(topK),
    queryFn: async () => {
      const response = await apiGetPointsLeaderboard(topK);
      return response.leaderboard;
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}