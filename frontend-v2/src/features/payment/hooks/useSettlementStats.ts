/**
 * 结算统计 Hook（管理员用）
 * 使用 React Query 管理结算统计相关的服务端状态
 */

import { useQuery, useMutation } from '@tanstack/react-query';

import type {
  GetSettlementStatsRequest,
  GetSettlementStatsResponse,
} from '../types';
import {
  apiGetSettlementStats,
  apiExportSettlementReport,
} from '../api';

// Query Keys
const SETTLEMENT_KEYS = {
  all: ['payment', 'settlement', 'admin'] as const,
  stats: (params: GetSettlementStatsRequest) => [...SETTLEMENT_KEYS.all, 'stats', params] as const,
} as const;

/**
 * 获取结算统计（管理员用）
 */
export function useSettlementStats(params: GetSettlementStatsRequest) {
  return useQuery<GetSettlementStatsResponse, Error>({
    queryKey: SETTLEMENT_KEYS.stats(params),
    queryFn: () => apiGetSettlementStats(params),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: !!params.startDate && !!params.endDate,
  });
}

/**
 * 导出结算报表（管理员用）
 */
export function useExportSettlementReport() {
  return useMutation({
    mutationFn: (params: { startDate: string; endDate: string; format?: 'csv' | 'excel' }) =>
      apiExportSettlementReport(params),
  });
}
