/**
 * Analytics（数据分析统计）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/analytics 端点
 */

import { apiClient } from "@/shared/lib/api/client";

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
  LogBehaviorRequest,
  LogBehaviorResponse,
  ResourceViewCountResponse,
  PaginationRequest,
} from '../types';

// API 基础路径
const API_BASE = '/analytics';

/** 后端关键指标响应 */
interface BackendMetricsResponse {
  dau: number;
  mau: number;
  total_revenue: number;
  paying_users: number;
  timestamp: string;
}

/** 后端用户行为数据 */
interface BackendUserBehaviorResponse {
  activity_trend: Array<{
    date: string;
    active_users: number;
    new_users: number;
    returning_users: number;
  }>;
  feature_usage: Array<{
    feature: string;
    usage_count: number;
    percentage: number;
    color?: string;
  }>;
  total_sessions: number;
  average_session_duration: number;
}

/** 后端收入数据 */
interface BackendRevenueResponse {
  trend: Array<{
    date: string;
    revenue: number;
    membership?: number;
    consultation?: number;
    other?: number;
  }>;
  sources: Array<{
    name: string;
    value: number;
    percentage: number;
    color: string;
  }>;
  total: number;
}

/** 后端转化漏斗响应 */
interface BackendConversionFunnelResponse {
  steps: Array<{
    name: string;
    count: number;
    conversion_rate: number;
    drop_rate: number;
    color?: string;
  }>;
  total_users: number;
  overall_conversion: number;
  start_date: string;
  end_date: string;
}

/** 后端漏斗分析响应 */
interface BackendFunnelAnalysisResponse {
  start_date: string;
  end_date: string;
  steps: Array<{
    name: string;
    count: number;
    conversion_rate: number;
    drop_rate: number;
  }>;
}

/** 后端留存分析响应 */
interface BackendRetentionResponse {
  cohort_date: string;
  cohort_count: number;
  retention: Array<{
    day: number;
    count: number;
    rate: number;
  }>;
}

/** 后端行为日志项 */
interface BackendBehaviorLogItem {
  id: number;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  metadata: string | null;
  created_at: string;
}

/** 后端行为历史响应 */
interface BackendBehaviorHistoryResponse {
  user_id: number;
  total: number;
  items: BackendBehaviorLogItem[];
}

/** 后端行为日志响应 */
interface BackendLogBehaviorResponse {
  id: number;
  user_id: number | null;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  metadata: string | null;
  created_at: string;
}

/** 后端资源浏览次数响应 */
interface BackendResourceViewCountResponse {
  resource_type: string;
  resource_id: number;
  view_count: number;
}

/** 后端行为统计响应 */
interface BackendActionStatisticsResponse {
  start_date: string;
  end_date: string;
  items: Array<{
    action: string;
    count: number;
  }>;
}

// ==================== 转换函数 ====================

/**
 * 获取数据概览
 * 通过组合多个 Dashboard 端点数据实现
 */
export async function apiGetOverview(): Promise<OverviewData> {
  try {
    // 并行获取多个数据源
    const [metricsRes, userBehaviorRes, revenueRes] = await Promise.all([
      apiClient.get<BackendMetricsResponse>(`${API_BASE}/dashboard/metrics`),
      apiClient.get<BackendUserBehaviorResponse>(`${API_BASE}/dashboard/user-behavior`),
      apiClient.get<BackendRevenueResponse>(`${API_BASE}/dashboard/revenue`),
    ]);

    const metrics = metricsRes.data;
    const userBehavior = userBehaviorRes.data;
    const revenue = revenueRes.data;

    // 获取今日和昨日的数据
    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];

    const todayActivity = userBehavior.activity_trend.find(
      (item) => item.date === today
    );
    const yesterdayActivity = userBehavior.activity_trend.find(
      (item) => item.date === yesterday
    );
    const todayRevenue = revenue.trend.find((item) => item.date === today);
    const yesterdayRevenue = revenue.trend.find((item) => item.date === yesterday);

    return {
      users: {
        totalUsers: metrics.mau,
        newUsersToday: todayActivity?.new_users ?? 0,
        newUsersThisWeek: 0,
        newUsersThisMonth: 0,
        activeUsersToday: metrics.dau,
        activeUsersYesterday: yesterdayActivity?.active_users ?? 0,
        activeUsersThisWeek: 0,
        activeUsersThisMonth: 0,
      },
      revenue: {
        today: todayRevenue?.revenue ?? 0,
        yesterday: yesterdayRevenue?.revenue ?? 0,
        thisWeek: 0,
        thisMonth: revenue.total,
        total: metrics.total_revenue,
      },
      content: {
        totalPosts: 0,
        totalConsultations: 0,
        totalDocuments: 0,
        totalContracts: 0,
      },
      engagement: {
        avgSessionDuration: userBehavior.average_session_duration,
        totalSessions: userBehavior.total_sessions,
        bounceRate: 0,
      },
    };
  } catch (error) {
    console.error('获取概览数据失败:', error);
    // 返回默认数据
    return {
      users: {
        totalUsers: 0,
        newUsersToday: 0,
        newUsersThisWeek: 0,
        newUsersThisMonth: 0,
        activeUsersToday: 0,
        activeUsersYesterday: 0,
        activeUsersThisWeek: 0,
        activeUsersThisMonth: 0,
      },
      revenue: {
        today: 0,
        yesterday: 0,
        thisWeek: 0,
        thisMonth: 0,
        total: 0,
      },
      content: {
        totalPosts: 0,
        totalConsultations: 0,
        totalDocuments: 0,
        totalContracts: 0,
      },
      engagement: {
        avgSessionDuration: 0,
        totalSessions: 0,
        bounceRate: 0,
      },
    };
  }
}

/**
 * 获取用户统计
 */
export async function apiGetUserStatistics(): Promise<UserStatisticsOverview> {
  const response = await apiClient.get<BackendMetricsResponse>(`${API_BASE}/dashboard/metrics`);

  const data = response.data;

  return {
    totalUsers: data.mau,
    newUsersToday: data.dau,
    newUsersThisWeek: 0,
    newUsersThisMonth: 0,
    activeUsersToday: data.dau,
    activeUsersYesterday: 0,
    activeUsersThisWeek: 0,
    activeUsersThisMonth: data.mau,
  };
}

/**
 * 获取转化漏斗数据
 * 使用 Dashboard 转化漏斗端点
 */
export async function apiGetConversionFunnel(
  startDate?: string,
  endDate?: string
): Promise<ConversionFunnelData> {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  const response = await apiClient.get<BackendConversionFunnelResponse>(
    `${API_BASE}/dashboard/conversion`,
    { params }
  );

  const data = response.data;

  return {
    steps: data.steps.map((step) => ({
      name: step.name,
      count: step.count,
      conversionRate: step.conversion_rate,
      dropRate: step.drop_rate,
      color: step.color,
    })),
    totalUsers: data.total_users,
    overallConversion: data.overall_conversion,
    startDate: data.start_date,
    endDate: data.end_date,
  };
}

/**
 * 获取漏斗分析（自定义漏斗步骤）
 */
export async function apiGetFunnelAnalysis(
  request: ConversionFunnelRequest
): Promise<ConversionFunnelResponse> {
  const response = await apiClient.post<BackendFunnelAnalysisResponse>(
    `${API_BASE}/funnel/conversion`,
    {
      start_date: request.startDate,
      end_date: request.endDate,
      funnel_steps: request.funnelSteps.map((step) => ({
        name: step.name,
        action: step.action,
        resource_type: step.resourceType,
        condition: step.condition,
      })),
    }
  );

  const data = response.data;

  return {
    startDate: data.start_date,
    endDate: data.end_date,
    steps: data.steps.map((step) => ({
      name: step.name,
      count: step.count,
      conversionRate: step.conversion_rate,
      dropRate: step.drop_rate,
    })),
  };
}

/**
 * 获取趋势数据
 * 注意：后端暂无此端点，使用 Dashboard 收入趋势作为替代
 */
export async function apiGetTrendData(
  metric: string,
  period: string,
  startDate?: string,
  endDate?: string
): Promise<TrendData> {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  const response = await apiClient.get<BackendRevenueResponse>(
    `${API_BASE}/dashboard/revenue`,
    { params }
  );

  const data = response.data;

  // 根据 metric 返回不同的数据
  const trendData = data.trend.map((item) => {
    let value = 0;
    switch (metric) {
      case 'revenue':
        value = item.revenue;
        break;
      case 'membership':
        value = item.membership ?? 0;
        break;
      case 'consultation':
        value = item.consultation ?? 0;
        break;
      case 'other':
        value = item.other ?? 0;
        break;
      default:
        value = item.revenue;
    }
    return {
      date: item.date,
      value,
      label: item.date,
    };
  });

  return {
    metricName: metric,
    data: trendData,
    period,
  };
}

/**
 * 获取留存分析
 */
export async function apiGetRetention(request: RetentionRequest): Promise<RetentionResponse> {
  const response = await apiClient.post<BackendRetentionResponse>(`${API_BASE}/retention`, {
    cohort_date: request.cohortDate,
    retention_days: request.retentionDays || [1, 7, 30],
  });

  const data = response.data;

  return {
    cohortDate: data.cohort_date,
    cohortCount: data.cohort_count,
    retention: data.retention.map((item) => ({
      day: item.day,
      count: item.count,
      rate: item.rate,
    })),
  };
}

/**
 * 获取 Dashboard 关键指标
 */
export async function apiGetDashboardMetrics(): Promise<MetricsResponse> {
  const response = await apiClient.get<BackendMetricsResponse>(`${API_BASE}/dashboard/metrics`);

  const data = response.data;

  return {
    dau: data.dau,
    mau: data.mau,
    totalRevenue: data.total_revenue,
    payingUsers: data.paying_users,
    timestamp: data.timestamp,
  };
}

/**
 * 获取收入统计
 */
export async function apiGetRevenue(startDate?: string, endDate?: string): Promise<RevenueResponse> {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  const response = await apiClient.get<BackendRevenueResponse>(
    `${API_BASE}/dashboard/revenue`,
    { params }
  );

  const data = response.data;

  return {
    trend: data.trend.map((item) => ({
      date: item.date,
      revenue: item.revenue,
      membership: item.membership,
      consultation: item.consultation,
      other: item.other,
    })),
    sources: data.sources.map((source) => ({
      name: source.name,
      value: source.value,
      percentage: source.percentage,
      color: source.color,
    })),
    total: data.total,
  };
}

/**
 * 获取用户行为数据
 */
export async function apiGetUserBehavior(): Promise<UserBehaviorData> {
  const response = await apiClient.get<BackendUserBehaviorResponse>(
    `${API_BASE}/dashboard/user-behavior`
  );

  const data = response.data;

  return {
    activityTrend: data.activity_trend.map((item) => ({
      date: item.date,
      activeUsers: item.active_users,
      newUsers: item.new_users,
      returningUsers: item.returning_users,
    })),
    featureUsage: data.feature_usage.map((item) => ({
      feature: item.feature,
      usageCount: item.usage_count,
      percentage: item.percentage,
      color: item.color,
    })),
    totalSessions: data.total_sessions,
    averageSessionDuration: data.average_session_duration,
  };
}

/**
 * 记录用户行为
 */
export async function apiLogBehavior(request: LogBehaviorRequest): Promise<LogBehaviorResponse> {
  const response = await apiClient.post<BackendLogBehaviorResponse>(`${API_BASE}/log`, {
    action: request.action,
    resource_type: request.resourceType,
    resource_id: request.resourceId,
    metadata: request.metadata,
    session_id: request.sessionId,
  });

  const data = response.data;

  return {
    id: data.id,
    userId: data.user_id,
    action: data.action,
    resourceType: data.resource_type,
    resourceId: data.resource_id,
    metadata: data.metadata,
    createdAt: data.created_at,
  };
}

/**
 * 获取行为历史
 */
export async function apiGetBehaviorHistory(
  params: PaginationRequest & { action?: string; resourceType?: string } = {}
): Promise<BehaviorHistoryResponse> {
  const queryParams: Record<string, string | number> = {};
  if (params.limit) queryParams.limit = params.limit;
  if (params.offset) queryParams.offset = params.offset;
  if (params.action) queryParams.action = params.action;
  if (params.resourceType) queryParams.resource_type = params.resourceType;

  const response = await apiClient.get<BackendBehaviorHistoryResponse>(`${API_BASE}/history`, {
    params: queryParams,
  });

  const data = response.data;

  return {
    userId: data.user_id,
    total: data.total,
    items: data.items.map((item) => ({
      id: item.id,
      action: item.action,
      resourceType: item.resource_type,
      resourceId: item.resource_id,
      metadata: item.metadata,
      createdAt: item.created_at,
    })),
  };
}

/**
 * 获取资源浏览次数
 */
export async function apiGetResourceViewCount(
  resourceType: string,
  resourceId: number
): Promise<ResourceViewCountResponse> {
  const response = await apiClient.get<BackendResourceViewCountResponse>(
    `${API_BASE}/resource/${resourceType}/${resourceId}/view-count`
  );

  const data = response.data;

  return {
    resourceType: data.resource_type,
    resourceId: data.resource_id,
    viewCount: data.view_count,
  };
}

/**
 * 获取行为统计
 */
export async function apiGetActionStatistics(
  startDate?: string,
  endDate?: string,
  action?: string
): Promise<ActionStatisticsResponse> {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  if (action) params.action = action;

  const response = await apiClient.get<BackendActionStatisticsResponse>(
    `${API_BASE}/statistics/actions`,
    { params }
  );

  const data = response.data;

  return {
    startDate: data.start_date,
    endDate: data.end_date,
    items: data.items.map((item) => ({
      action: item.action,
      count: item.count,
    })),
  };
}

/**
 * Analytics API 对象
 * 统一导出所有 API 方法，使用驼峰命名法
 */
export const api = {
  // 概览相关
  getOverview: apiGetOverview,

  // 用户统计
  getUserStatistics: apiGetUserStatistics,

  // 漏斗分析
  getConversionFunnel: apiGetConversionFunnel,
  getFunnelAnalysis: apiGetFunnelAnalysis,

  // 趋势数据
  getTrendData: apiGetTrendData,

  // 留存分析
  getRetention: apiGetRetention,

  // Dashboard 指标
  getDashboardMetrics: apiGetDashboardMetrics,

  // 收入统计
  getRevenue: apiGetRevenue,

  // 用户行为
  getUserBehavior: apiGetUserBehavior,
  logBehavior: apiLogBehavior,
  getBehaviorHistory: apiGetBehaviorHistory,

  // 资源浏览
  getResourceViewCount: apiGetResourceViewCount,

  // 行为统计
  getActionStatistics: apiGetActionStatistics,
} as const;