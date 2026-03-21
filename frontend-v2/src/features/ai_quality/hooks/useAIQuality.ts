/**
 * AI质量监控（AI Quality）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  AIMetrics,
  DashboardData,
  QualityTrendData,
  GetSessionQualityListRequest,
  GetSessionQualityListResponse,
  GetSessionDetailRequest,
  SessionDetail,
  GetQualityAlertsRequest,
  GetQualityAlertsResponse,
  AcknowledgeAlertRequest,
  ResolveAlertRequest,
  ReviewSessionRequest,
  ReviewStats,
  GetAILogsRequest,
  GetAILogsResponse,
} from '../types';
import {
  apiGetAIMetrics,
  apiGetDashboardData,
  apiGetQualityTrend,
  apiGetSessionQuality,
  apiGetSessionDetail,
  apiReviewSession,
  apiGetReviewStats,
  apiGetQualityAlerts,
  apiAcknowledgeAlert,
  apiResolveAlert,
  apiGetAILogs,
  apiGetAIQualityHealth,
} from '../api';

// ==================== Query Keys ====================

const AI_QUALITY_QUERY_KEYS = {
  metrics: ['ai-quality', 'metrics'] as const,
  dashboard: ['ai-quality', 'dashboard'] as const,
  trend: (days: number) => ['ai-quality', 'trend', days] as const,
  sessions: (params?: GetSessionQualityListRequest) => ['ai-quality', 'sessions', params] as const,
  sessionDetail: (sessionId: string) => ['ai-quality', 'session', sessionId] as const,
  alerts: (params?: GetQualityAlertsRequest) => ['ai-quality', 'alerts', params] as const,
  reviewStats: ['ai-quality', 'review-stats'] as const,
  logs: (params?: GetAILogsRequest) => ['ai-quality', 'logs', params] as const,
  health: ['ai-quality', 'health'] as const,
} as const;

// ==================== 质量指标 Hooks ====================

/**
 * 获取AI质量指标 Hook
 */
export function useAIMetrics(enabled: boolean = true) {
  return useQuery<AIMetrics>({
    queryKey: AI_QUALITY_QUERY_KEYS.metrics,
    queryFn: apiGetAIMetrics,
    staleTime: 30 * 1000, // 30秒缓存
    refetchInterval: enabled ? 60 * 1000 : false, // 每分钟自动刷新
    enabled,
  });
}

/**
 * 获取仪表板数据 Hook
 */
export function useDashboardData(enabled: boolean = true) {
  return useQuery<DashboardData>({
    queryKey: AI_QUALITY_QUERY_KEYS.dashboard,
    queryFn: apiGetDashboardData,
    staleTime: 30 * 1000,
    refetchInterval: enabled ? 60 * 1000 : false,
    enabled,
  });
}

/**
 * 获取质量趋势数据 Hook
 */
export function useQualityTrend(days: number = 7, enabled: boolean = true) {
  return useQuery<QualityTrendData>({
    queryKey: AI_QUALITY_QUERY_KEYS.trend(days),
    queryFn: () => apiGetQualityTrend(days),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled,
  });
}

// ==================== 会话质量 Hooks ====================

/**
 * 获取会话质量列表 Hook
 */
export function useSessionQuality(params: GetSessionQualityListRequest = {}, enabled: boolean = true) {
  return useQuery<GetSessionQualityListResponse>({
    queryKey: AI_QUALITY_QUERY_KEYS.sessions(params),
    queryFn: () => apiGetSessionQuality(params),
    staleTime: 30 * 1000,
    enabled,
  });
}

/**
 * 获取会话详情 Hook
 */
export function useSessionDetail(request: GetSessionDetailRequest) {
  return useQuery<SessionDetail>({
    queryKey: AI_QUALITY_QUERY_KEYS.sessionDetail(request.session_id),
    queryFn: async () => {
      const response = await apiGetSessionDetail(request);
      return response.session;
    },
    staleTime: 60 * 1000,
    enabled: !!request.session_id,
  });
}

/**
 * 人工审核会话 Hook
 */
export function useReviewSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ReviewSessionRequest) => apiReviewSession(request),
    onSuccess: (_data, variables) => {
      // 审核成功后刷新会话详情和列表
      void queryClient.invalidateQueries({
        queryKey: AI_QUALITY_QUERY_KEYS.sessionDetail(variables.session_id),
      });
      void queryClient.invalidateQueries({
        queryKey: ['ai-quality', 'sessions'],
      });
      // 刷新审核统计
      void queryClient.invalidateQueries({
        queryKey: AI_QUALITY_QUERY_KEYS.reviewStats,
      });
    },
  });
}

/**
 * 获取审核统计 Hook
 */
export function useReviewStats() {
  return useQuery<ReviewStats>({
    queryKey: AI_QUALITY_QUERY_KEYS.reviewStats,
    queryFn: apiGetReviewStats,
    staleTime: 60 * 1000,
  });
}

// ==================== 质量告警 Hooks ====================

/**
 * 获取质量告警列表 Hook
 */
export function useQualityAlerts(params: GetQualityAlertsRequest = {}, enabled: boolean = true) {
  return useQuery<GetQualityAlertsResponse>({
    queryKey: AI_QUALITY_QUERY_KEYS.alerts(params),
    queryFn: () => apiGetQualityAlerts(params),
    staleTime: 30 * 1000,
    enabled,
    refetchInterval: enabled
      ? (query) => {
          // 如果有活跃告警，每30秒刷新一次
          const data = query.state.data;
          if (data?.summary?.active && data.summary.active > 0) {
            return 30 * 1000;
          }
          return 60 * 1000;
        }
      : false,
  });
}

/**
 * 确认告警 Hook
 */
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AcknowledgeAlertRequest) => apiAcknowledgeAlert(request),
    onSuccess: () => {
      // 确认成功后刷新告警列表
      void queryClient.invalidateQueries({
        queryKey: ['ai-quality', 'alerts'],
      });
    },
  });
}

/**
 * 解决告警 Hook
 */
export function useResolveAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ResolveAlertRequest) => apiResolveAlert(request),
    onSuccess: () => {
      // 解决成功后刷新告警列表
      void queryClient.invalidateQueries({
        queryKey: ['ai-quality', 'alerts'],
      });
    },
  });
}

// ==================== 日志 Hooks ====================

/**
 * 获取AI日志列表 Hook
 */
export function useAILogs(params: GetAILogsRequest = {}, enabled: boolean = true) {
  return useQuery<GetAILogsResponse>({
    queryKey: AI_QUALITY_QUERY_KEYS.logs(params),
    queryFn: () => apiGetAILogs(params),
    staleTime: 30 * 1000,
    enabled,
  });
}

// ==================== 系统状态 Hooks ====================

/**
 * 获取AI质量监控健康状态 Hook
 */
export function useAIQualityHealth() {
  return useQuery<{
    status: string;
    total_conversations: number;
    last_updated: string;
  }>({
    queryKey: AI_QUALITY_QUERY_KEYS.health,
    queryFn: apiGetAIQualityHealth,
    staleTime: 60 * 1000,
    refetchInterval: 60 * 1000,
  });
}