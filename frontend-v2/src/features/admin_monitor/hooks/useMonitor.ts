/**
 * Admin Monitor（系统监控）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  HealthCheckResponse,
  MetricsSummaryResponse,
  ApiMetricsResponse,
  AiMetricsResponse,
  UserMetrics,
  BusinessMetrics,
  AlertsResponse,
  AlertRulesResponse,
  QueryStatsResponse,
  SystemInfo,
  DatabaseStatus,
  CacheStatus,
  WebSocketStatus,
  LogsResponse,
  DailyReport,
  DashboardStats,
  LogFilters,
  ResourceUsageData,
  RequestTrendData,
} from '../types';
import { api } from '../api';

// ==================== Query Keys ====================

const MONITOR_QUERY_KEYS = {
  health: ['monitor', 'health'] as const,
  metrics: (hours?: number) => ['monitor', 'metrics', hours] as const,
  apiMetrics: (endpoint?: string, hours?: number) => ['monitor', 'apiMetrics', endpoint, hours] as const,
  aiMetrics: (hours?: number) => ['monitor', 'aiMetrics', hours] as const,
  userMetrics: ['monitor', 'userMetrics'] as const,
  businessMetrics: ['monitor', 'businessMetrics'] as const,
  alerts: (hours?: number, level?: string) => ['monitor', 'alerts', hours, level] as const,
  alertRules: ['monitor', 'alertRules'] as const,
  queryStats: ['monitor', 'queryStats'] as const,
  systemInfo: ['monitor', 'systemInfo'] as const,
  databaseStatus: ['monitor', 'databaseStatus'] as const,
  cacheStatus: ['monitor', 'cacheStatus'] as const,
  websocketStatus: ['monitor', 'websocketStatus'] as const,
  logs: (filters?: LogFilters) => ['monitor', 'logs', filters] as const,
  dailyReport: (date?: string) => ['monitor', 'dailyReport', date] as const,
  dashboard: ['monitor', 'dashboard'] as const,
} as const;

// ==================== 刷新间隔常量 ====================

const REFRESH_INTERVAL = 30 * 1000; // 30秒自动刷新

// ==================== 健康检查 Hooks ====================

/**
 * 获取健康检查 Hook
 */
export function useHealthCheck() {
  return useQuery<HealthCheckResponse>({
    queryKey: MONITOR_QUERY_KEYS.health,
    queryFn: api.getHealth,
    staleTime: 30 * 1000, // 30秒缓存
    refetchInterval: REFRESH_INTERVAL,
  });
}

// ==================== 指标 Hooks ====================

/**
 * 获取监控指标 Hook
 */
export function useMetrics(hours?: number) {
  return useQuery<MetricsSummaryResponse>({
    queryKey: MONITOR_QUERY_KEYS.metrics(hours),
    queryFn: () => api.getMetrics(hours),
    staleTime: 30 * 1000,
    refetchInterval: REFRESH_INTERVAL,
  });
}

/**
 * 获取API指标 Hook
 */
export function useApiMetrics(endpoint?: string, hours?: number) {
  return useQuery<ApiMetricsResponse>({
    queryKey: MONITOR_QUERY_KEYS.apiMetrics(endpoint, hours),
    queryFn: () => api.getApiMetrics(endpoint, hours),
    staleTime: 60 * 1000, // 1分钟缓存
    refetchInterval: REFRESH_INTERVAL,
    enabled: true,
  });
}

/**
 * 获取AI指标 Hook
 */
export function useAiMetrics(hours?: number) {
  return useQuery<AiMetricsResponse>({
    queryKey: MONITOR_QUERY_KEYS.aiMetrics(hours),
    queryFn: () => api.getAiMetrics(hours),
    staleTime: 30 * 1000,
    refetchInterval: REFRESH_INTERVAL,
  });
}

/**
 * 获取用户指标 Hook
 */
export function useUserMetrics() {
  return useQuery<UserMetrics>({
    queryKey: MONITOR_QUERY_KEYS.userMetrics,
    queryFn: api.getUserMetrics,
    staleTime: 30 * 1000,
    refetchInterval: REFRESH_INTERVAL,
  });
}

/**
 * 获取业务指标 Hook
 */
export function useBusinessMetrics() {
  return useQuery<BusinessMetrics>({
    queryKey: MONITOR_QUERY_KEYS.businessMetrics,
    queryFn: api.getBusinessMetrics,
    staleTime: 60 * 1000,
    refetchInterval: REFRESH_INTERVAL,
  });
}

// ==================== 告警 Hooks ====================

/**
 * 获取告警列表 Hook
 */
export function useAlerts(hours?: number, level?: string) {
  return useQuery<AlertsResponse>({
    queryKey: MONITOR_QUERY_KEYS.alerts(hours, level),
    queryFn: () => api.getAlerts(hours, level),
    staleTime: 30 * 1000,
    refetchInterval: REFRESH_INTERVAL,
  });
}

/**
 * 获取告警规则 Hook
 */
export function useAlertRules() {
  return useQuery<AlertRulesResponse>({
    queryKey: MONITOR_QUERY_KEYS.alertRules,
    queryFn: api.getAlertRules,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 启用告警规则 Mutation
 */
export function useEnableAlertRule() {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean; message: string }, Error, string>({
    mutationFn: api.enableAlertRule,
    onSuccess: () => {
      // 成功后刷新告警规则列表
      void queryClient.invalidateQueries({ queryKey: MONITOR_QUERY_KEYS.alertRules });
    },
  });
}

/**
 * 禁用告警规则 Mutation
 */
export function useDisableAlertRule() {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean; message: string }, Error, string>({
    mutationFn: api.disableAlertRule,
    onSuccess: () => {
      // 成功后刷新告警规则列表
      void queryClient.invalidateQueries({ queryKey: MONITOR_QUERY_KEYS.alertRules });
    },
  });
}

// ==================== 查询统计 Hooks ====================

/**
 * 获取查询统计 Hook
 */
export function useQueryStats() {
  return useQuery<QueryStatsResponse>({
    queryKey: MONITOR_QUERY_KEYS.queryStats,
    queryFn: api.getQueryStats,
    staleTime: 60 * 1000,
    refetchInterval: REFRESH_INTERVAL,
  });
}

/**
 * 重置查询统计 Mutation
 */
export function useResetQueryStats() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, void>({
    mutationFn: api.resetQueryStats,
    onSuccess: () => {
      // 成功后刷新查询统计
      void queryClient.invalidateQueries({ queryKey: MONITOR_QUERY_KEYS.queryStats });
    },
  });
}

// ==================== 系统信息 Hooks ====================

/**
 * 获取系统信息 Hook
 */
export function useSystemInfo() {
  return useQuery<SystemInfo>({
    queryKey: MONITOR_QUERY_KEYS.systemInfo,
    queryFn: api.getSystemInfo,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    refetchInterval: 5 * 60 * 1000, // 5分钟刷新
  });
}

// ==================== 服务状态 Hooks ====================

/**
 * 获取数据库状态 Hook
 */
export function useDatabaseStatus() {
  return useQuery<DatabaseStatus>({
    queryKey: MONITOR_QUERY_KEYS.databaseStatus,
    queryFn: api.getDatabaseStatus,
    staleTime: 30 * 1000,
    refetchInterval: REFRESH_INTERVAL,
  });
}

/**
 * 获取缓存状态 Hook
 */
export function useCacheStatus() {
  return useQuery<CacheStatus>({
    queryKey: MONITOR_QUERY_KEYS.cacheStatus,
    queryFn: api.getCacheStatus,
    staleTime: 30 * 1000,
    refetchInterval: REFRESH_INTERVAL,
  });
}

/**
 * 获取WebSocket状态 Hook
 */
export function useWebSocketStatus() {
  return useQuery<WebSocketStatus>({
    queryKey: MONITOR_QUERY_KEYS.websocketStatus,
    queryFn: api.getWebSocketStatus,
    staleTime: 10 * 1000, // 10秒缓存
    refetchInterval: 10 * 1000, // 10秒刷新
  });
}

// ==================== 日志 Hooks ====================

/**
 * 获取系统日志 Hook
 */
export function useLogs(filters?: LogFilters) {
  return useQuery<LogsResponse>({
    queryKey: MONITOR_QUERY_KEYS.logs(filters),
    queryFn: () => api.getLogs(filters),
    staleTime: 10 * 1000,
    refetchInterval: 30 * 1000,
  });
}

// ==================== 日报表 Hooks ====================

/**
 * 获取日报表 Hook
 */
export function useDailyReport(date?: string) {
  return useQuery<DailyReport>({
    queryKey: MONITOR_QUERY_KEYS.dailyReport(date),
    queryFn: () => api.getDailyReport(date),
    staleTime: 5 * 60 * 1000,
  });
}

// ==================== Dashboard Hooks ====================

/**
 * 获取Dashboard数据 Hook
 */
export function useDashboard() {
  return useQuery<DashboardStats>({
    queryKey: MONITOR_QUERY_KEYS.dashboard,
    queryFn: api.getDashboard,
    staleTime: 30 * 1000,
    refetchInterval: REFRESH_INTERVAL,
  });
}

// ==================== 派生数据 Hooks ====================

/**
 * 获取格式化的资源使用数据（用于图表）
 */
export function useResourceUsageData(): ResourceUsageData | undefined {
  const { data: systemInfo } = useSystemInfo();
  const { data: _metrics } = useMetrics();

  if (!systemInfo) {
    return undefined;
  }

  // 生成时间戳（过去1小时，每5分钟一个点）
  const now = new Date();
  const timestamps: string[] = [];
  for (let i = 11; i >= 0; i--) {
    const t = new Date(now.getTime() - i * 5 * 60 * 1000);
    timestamps.push(t.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
  }

  // 模拟历史数据（实际应该从API获取）
  const baseCpu = systemInfo.cpu.percent;
  const baseMemory = systemInfo.memory.percent;
  const baseDisk = systemInfo.disk.percent;

  return {
    timestamps,
    cpu: timestamps.map(() => Math.max(0, Math.min(100, baseCpu + (Math.random() - 0.5) * 20))),
    memory: timestamps.map(() => Math.max(0, Math.min(100, baseMemory + (Math.random() - 0.5) * 10))),
    disk: timestamps.map(() => Math.max(0, Math.min(100, baseDisk + (Math.random() - 0.5) * 5))),
  };
}

/**
 * 获取格式化的请求趋势数据（用于图表）
 */
export function useRequestTrendData(): RequestTrendData | undefined {
  const { data: apiMetrics } = useApiMetrics();
  const { data: metrics } = useMetrics();

  if (!apiMetrics || !metrics) {
    return undefined;
  }

  // 生成时间戳
  const now = new Date();
  const timestamps: string[] = [];
  for (let i = 11; i >= 0; i--) {
    const t = new Date(now.getTime() - i * 5 * 60 * 1000);
    timestamps.push(t.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
  }

  const baseRequests = metrics.apiRequests / 12; // 平均分配到每个时间点
  const baseErrors = metrics.errors / 12;
  const baseResponseTime = metrics.avgResponseTime;

  return {
    timestamps,
    requests: timestamps.map(() => Math.max(0, baseRequests + (Math.random() - 0.5) * baseRequests * 0.4)),
    errors: timestamps.map(() => Math.max(0, baseErrors + (Math.random() - 0.5) * baseErrors * 0.5)),
    avgResponseTime: timestamps.map(() => Math.max(10, baseResponseTime + (Math.random() - 0.5) * 50)),
  };
}

/**
 * 获取状态颜色
 */
export function useStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'green';
    case 'unhealthy':
      return 'red';
    case 'degraded':
      return 'yellow';
    case 'not_configured':
      return 'gray';
    case 'unavailable':
      return 'gray';
    default:
      return 'gray';
  }
}

/**
 * 获取告警级别颜色
 */
export function useAlertLevelColor(level: string): string {
  switch (level) {
    case 'critical':
      return 'red';
    case 'error':
      return 'orange';
    case 'warning':
      return 'yellow';
    case 'info':
      return 'blue';
    default:
      return 'gray';
  }
}