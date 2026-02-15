/**
 * Analytics（数据分析统计）React Query 键
 * 遵循统一命名规范：模块名 + 资源名 + 操作/参数
 */

export const analyticsKeys = {
  // 概览数据
  overview: ['analytics', 'overview'] as const,

  // 用户统计
  userStatistics: ['analytics', 'userStatistics'] as const,

  // 转化漏斗
  conversionFunnel: (startDate?: string, endDate?: string) =>
    ['analytics', 'conversionFunnel', { startDate, endDate }] as const,

  // 漏斗分析
  funnelAnalysis: (startDate: string, endDate: string) =>
    ['analytics', 'funnelAnalysis', { startDate, endDate }] as const,

  // 趋势数据
  trendData: (metric: string, period: string, startDate?: string, endDate?: string) =>
    ['analytics', 'trendData', { metric, period, startDate, endDate }] as const,

  // 留存分析
  retention: (cohortDate: string, retentionDays?: number[]) =>
    ['analytics', 'retention', { cohortDate, retentionDays }] as const,

  // Dashboard 指标
  dashboardMetrics: ['analytics', 'dashboardMetrics'] as const,

  // 收入统计
  revenue: (startDate?: string, endDate?: string) =>
    ['analytics', 'revenue', { startDate, endDate }] as const,

  // 用户行为
  userBehavior: ['analytics', 'userBehavior'] as const,

  // 行为历史
  behaviorHistory: (params?: { action?: string; resourceType?: string; limit?: number; offset?: number }) =>
    ['analytics', 'behaviorHistory', params] as const,

  // 资源浏览次数
  resourceViewCount: (resourceType: string, resourceId: number) =>
    ['analytics', 'resourceViewCount', { resourceType, resourceId }] as const,

  // 行为统计
  actionStatistics: (startDate?: string, endDate?: string, action?: string) =>
    ['analytics', 'actionStatistics', { startDate, endDate, action }] as const,
} as const;