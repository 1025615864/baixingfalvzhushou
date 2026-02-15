/**
 * Analytics（数据分析统计）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  OverviewData,
  UserStatisticsOverview,
  ConversionFunnelData,
  ConversionFunnelRequest,
  ConversionFunnelResponse,
  TrendData,
  RetentionRequest,
  RetentionResponse,
  MetricsResponse,
  RevenueResponse,
  UserBehaviorData,
  ActionStatisticsResponse,
  BehaviorHistoryResponse,
  ResourceViewCountResponse,
  StatCardData,
  FunnelChartDataItem,
  TrendDataPoint,
} from '../types';
import { api } from '../api';

// ==================== Query Keys ====================

const ANALYTICS_QUERY_KEYS = {
  overview: ['analytics', 'overview'] as const,
  userStats: ['analytics', 'userStats'] as const,
  funnel: (startDate?: string, endDate?: string) => ['analytics', 'funnel', startDate, endDate] as const,
  trend: (metric: string, period: string) => ['analytics', 'trend', metric, period] as const,
  retention: (cohortDate: string) => ['analytics', 'retention', cohortDate] as const,
  metrics: ['analytics', 'metrics'] as const,
  revenue: (startDate?: string, endDate?: string) => ['analytics', 'revenue', startDate, endDate] as const,
  userBehavior: ['analytics', 'userBehavior'] as const,
  behaviorHistory: (params?: { action?: string; resourceType?: string; limit?: number }) =>
    ['analytics', 'behaviorHistory', params] as const,
  resourceViewCount: (resourceType: string, resourceId: number) =>
    ['analytics', 'resourceViewCount', resourceType, resourceId] as const,
  actionStats: (startDate?: string, endDate?: string) =>
    ['analytics', 'actionStats', startDate, endDate] as const,
  funnelAnalysis: (params: ConversionFunnelRequest) => ['analytics', 'funnelAnalysis', params] as const,
} as const;

// ==================== Overview Hooks ====================

/**
 * 获取数据概览 Hook
 */
export function useAnalyticsOverview() {
  return useQuery<OverviewData>({
    queryKey: ANALYTICS_QUERY_KEYS.overview,
    queryFn: api.getOverview,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 获取格式化的统计卡片数据
 */
export function useStatCardsData(): StatCardData[] {
  const { data: overview } = useAnalyticsOverview();

  if (!overview) {
    return [];
  }

  return [
    {
      title: '总用户数',
      value: overview.users.totalUsers,
      change: overview.users.newUsersToday,
      changeType: 'increase',
      unit: '人',
      icon: 'Users',
    },
    {
      title: '今日活跃用户',
      value: overview.users.activeUsersToday,
      change: Math.round(
        ((overview.users.activeUsersToday - overview.users.activeUsersYesterday || 0) /
          (overview.users.activeUsersYesterday || 1)) *
          100
      ),
      changeType: overview.users.activeUsersToday >= (overview.users.activeUsersYesterday || 0) ? 'increase' : 'decrease',
      unit: '人',
      icon: 'Activity',
    },
    {
      title: '今日收入',
      value: overview.revenue.today,
      change: Math.round(
        ((overview.revenue.today - overview.revenue.yesterday || 0) /
          (overview.revenue.yesterday || 1)) *
          100
      ),
      changeType: overview.revenue.today >= (overview.revenue.yesterday || 0) ? 'increase' : 'decrease',
      unit: '元',
      icon: 'DollarSign',
    },
    {
      title: '总会话数',
      value: overview.engagement.totalSessions,
      change: Math.round(overview.engagement.avgSessionDuration / 60),
      changeType: 'increase',
      unit: '分钟平均时长',
      icon: 'Clock',
    },
  ];
}

// ==================== User Statistics Hooks ====================

/**
 * 获取用户统计 Hook
 */
export function useUserStatistics() {
  return useQuery<UserStatisticsOverview>({
    queryKey: ANALYTICS_QUERY_KEYS.userStats,
    queryFn: api.getUserStatistics,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== Funnel Hooks ====================

/**
 * 获取转化漏斗数据 Hook
 */
export function useConversionFunnel(startDate?: string, endDate?: string) {
  return useQuery<ConversionFunnelData>({
    queryKey: ANALYTICS_QUERY_KEYS.funnel(startDate, endDate),
    queryFn: () => api.getConversionFunnel(startDate, endDate),
    staleTime: 10 * 60 * 1000, // 10分钟缓存
    enabled: true,
  });
}

/**
 * 获取格式化的漏斗图表数据
 */
export function useFunnelChartData(
  startDate?: string,
  endDate?: string
): FunnelChartDataItem[] {
  const { data: funnelData } = useConversionFunnel(startDate, endDate);

  if (!funnelData?.steps) {
    return [];
  }

  return funnelData.steps.map((step, index) => ({
    name: step.name,
    value: step.count,
    conversionRate: step.conversionRate,
    dropRate: step.dropRate,
    color: step.color || `hsl(${210 + index * 30}, 70%, ${50 + index * 5}%)`,
  }));
}

/**
 * 获取漏斗分析 Hook（自定义漏斗步骤）
 */
export function useFunnelAnalysis() {
  const queryClient = useQueryClient();

  return useMutation<ConversionFunnelResponse, Error, ConversionFunnelRequest>({
    mutationFn: api.getFunnelAnalysis,
    onSuccess: (data, variables) => {
      // 成功后缓存结果
      void queryClient.setQueryData(
        ANALYTICS_QUERY_KEYS.funnelAnalysis(variables),
        data
      );
    },
  });
}

// ==================== Trend Hooks ====================

/**
 * 获取趋势数据 Hook
 */
export function useTrendData(metric: string, period: string, startDate?: string, endDate?: string) {
  return useQuery<TrendData>({
    queryKey: ANALYTICS_QUERY_KEYS.trend(metric, period),
    queryFn: () => api.getTrendData(metric, period, startDate, endDate),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: !!metric && !!period,
  });
}

/**
 * 获取格式化的趋势图表数据
 */
export function useTrendChartData(
  metric: string,
  period: string,
  startDate?: string,
  endDate?: string
): TrendDataPoint[] {
  const { data: trendData } = useTrendData(metric, period, startDate, endDate);

  if (!trendData?.data) {
    return [];
  }

  return trendData.data.map(item => ({
    date: item.date,
    value: item.value,
    label: item.label || item.date,
  }));
}

// ==================== Retention Hooks ====================

/**
 * 获取留存分析 Hook
 */
export function useRetention(cohortDate: string, retentionDays?: number[]) {
  const request: RetentionRequest = {
    cohortDate,
    retentionDays: retentionDays || [1, 7, 30],
  };

  return useQuery<RetentionResponse>({
    queryKey: ANALYTICS_QUERY_KEYS.retention(cohortDate),
    queryFn: () => api.getRetention(request),
    staleTime: 60 * 60 * 1000, // 1小时缓存，留存数据不常变化
    enabled: !!cohortDate,
  });
}

// ==================== Dashboard Metrics Hooks ====================

/**
 * 获取 Dashboard 关键指标 Hook
 */
export function useDashboardMetrics() {
  return useQuery<MetricsResponse>({
    queryKey: ANALYTICS_QUERY_KEYS.metrics,
    queryFn: api.getDashboardMetrics,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== Revenue Hooks ====================

/**
 * 获取收入统计 Hook
 */
export function useRevenue(startDate?: string, endDate?: string) {
  return useQuery<RevenueResponse>({
    queryKey: ANALYTICS_QUERY_KEYS.revenue(startDate, endDate),
    queryFn: () => api.getRevenue(startDate, endDate),
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

// ==================== User Behavior Hooks ====================

/**
 * 获取用户行为数据 Hook
 */
export function useUserBehavior() {
  return useQuery<UserBehaviorData>({
    queryKey: ANALYTICS_QUERY_KEYS.userBehavior,
    queryFn: api.getUserBehavior,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== Behavior Log Hooks ====================

/**
 * 记录用户行为 Hook
 */
export function useLogBehavior() {
  return useMutation({
    mutationFn: api.logBehavior,
  });
}

/**
 * 获取行为历史 Hook
 */
export function useBehaviorHistory(params?: {
  action?: string;
  resourceType?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery<BehaviorHistoryResponse>({
    queryKey: ANALYTICS_QUERY_KEYS.behaviorHistory(params),
    queryFn: () => api.getBehaviorHistory(params),
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 获取资源浏览次数 Hook
 */
export function useResourceViewCount(resourceType: string, resourceId: number) {
  return useQuery<ResourceViewCountResponse>({
    queryKey: ANALYTICS_QUERY_KEYS.resourceViewCount(resourceType, resourceId),
    queryFn: () => api.getResourceViewCount(resourceType, resourceId),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: !!resourceType && resourceId > 0,
  });
}

// ==================== Action Statistics Hooks ====================

/**
 * 获取行为统计 Hook
 */
export function useActionStatistics(startDate?: string, endDate?: string, action?: string) {
  return useQuery<ActionStatisticsResponse>({
    queryKey: ANALYTICS_QUERY_KEYS.actionStats(startDate, endDate),
    queryFn: () => api.getActionStatistics(startDate, endDate, action),
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

// ==================== Utility Hooks ====================

/**
 * 刷新所有 Analytics 数据
 */
export function useRefreshAnalytics() {
  const queryClient = useQueryClient();

  return () => {
    void queryClient.invalidateQueries({ queryKey: ['analytics'] });
  };
}

/**
 * 获取日期范围的 Hook（辅助 Hook）
 */
export function useDateRange(defaultDays: number = 30): {
  startDate: string;
  endDate: string;
  setDateRange: (days: number) => void;
} {
  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date(Date.now() - defaultDays * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0];

  const setDateRange = (days: number): void => {
    // 这个函数可以通过状态管理来更新日期范围
    // 这里只是返回计算后的值
    void days;
  };

  return { startDate, endDate, setDateRange };
}