/**
 * usePromotionStats - 推广统计数据 Hook
 */

import { useQuery } from '@tanstack/react-query';

import type { PromotionStats, GetPromotionStatsRequest } from '../types';
import { apiGetPromotionStats } from '../api';

/**
 * 推广统计数据查询键
 */
const PROMOTION_STATS_KEY = 'promotionStats';

interface UsePromotionStatsOptions {
  /** 是否启用查询 */
  enabled?: boolean;
}

/**
 * 获取推广统计数据 Hook
 * @param params 查询参数
 * @param options 配置选项
 * @returns 推广统计数据
 */
export function usePromotionStats(
  params: GetPromotionStatsRequest = {},
  options: UsePromotionStatsOptions = {}
) {
  const { enabled = true } = options;

  return useQuery<PromotionStats>({
    queryKey: [PROMOTION_STATS_KEY, params],
    queryFn: () => apiGetPromotionStats(params),
    staleTime: 60 * 1000, // 1分钟缓存
    enabled,
  });
}

/**
 * 获取今日推广统计
 */
export function useTodayPromotionStats() {
  const today = new Date().toISOString().split('T')[0];

  return usePromotionStats({
    period: 'day',
    startDate: today,
    endDate: today,
  });
}

/**
 * 获取本周推广统计
 */
export function useWeekPromotionStats() {
  const now = new Date();
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

  return usePromotionStats({
    period: 'week',
    startDate: weekAgo.toISOString().split('T')[0],
    endDate: now.toISOString().split('T')[0],
  });
}

/**
 * 获取本月推广统计
 */
export function useMonthPromotionStats() {
  const now = new Date();
  const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

  return usePromotionStats({
    period: 'month',
    startDate: monthAgo.toISOString().split('T')[0],
    endDate: now.toISOString().split('T')[0],
  });
}