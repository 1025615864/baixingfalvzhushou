/**
 * Admin Monitor（系统监控）API 层
 */

import { apiClient } from "@/shared/lib/api/client";

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
} from '../types';


// API 基础路径
const API_BASE = '/admin/monitor';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
}

/**
 * 安全获取 JSON 响应
 */
async function safeJson<T>(response: Response): Promise<T> {
  const data = await response.json() as T;
  return data;
}

/**
 * 获取 API 错误信息
 */
function getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiErrorResponse).detail || defaultMsg;
  }
  return defaultMsg;
}

// ==================== 健康检查 API ====================

/**
 * 获取健康检查
 */
export async function apiGetHealth(): Promise<HealthCheckResponse> {
  const response = await apiClient.get<HealthCheckResponse>(`${API_BASE}/health`);
  return response.data;
}

// ==================== 指标 API ====================

/**
 * 获取监控指标摘要
 */
export async function apiGetMetrics(hours?: number): Promise<MetricsSummaryResponse> {
  const searchParams = new URLSearchParams();
  if (hours) searchParams.set('hours', hours.toString());

  const url = `${API_BASE}/metrics${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await apiClient.get<{
    api_requests?: number;
    errors?: number;
    avg_response_time?: number;
    active_connections?: number;
  }>(url);

  const data = response.data;

  return {
    apiRequests: data.api_requests ?? 0,
    errors: data.errors ?? 0,
    avgResponseTime: data.avg_response_time ?? 0,
    activeConnections: data.active_connections ?? 0,
  };
}

/**
 * 获取API性能指标
 */
export async function apiGetApiMetrics(endpoint?: string, hours?: number): Promise<ApiMetricsResponse> {
  const searchParams = new URLSearchParams();
  if (endpoint) searchParams.set('endpoint', endpoint);
  if (hours) searchParams.set('hours', hours.toString());

  const url = `${API_BASE}/api-metrics${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取API指标失败',
    }));
    throw new Error(getErrorMessage(error, '获取API指标失败'));
  }

  const data = await safeJson<{
    endpoints?: Record<string, unknown>;
    count?: number;
  }>(response);

  // 转换后端数据格式为前端格式
  const endpoints: Record<string, ApiMetricsResponse['endpoints'][string]> = {};
  if (data.endpoints) {
    Object.entries(data.endpoints).forEach(([key, value]) => {
      const v = value as Record<string, number>;
      endpoints[key] = {
        count: v.count ?? 0,
        totalTime: v.total_time ?? 0,
        avgTime: v.avg_time ?? 0,
        minTime: v.min_time ?? 0,
        maxTime: v.max_time ?? 0,
        p50: v.p50 ?? 0,
        p95: v.p95 ?? 0,
        p99: v.p99 ?? 0,
      };
    });
  }

  return {
    endpoints,
    count: data.count ?? 0,
  };
}

/**
 * 获取AI服务指标
 */
export async function apiGetAiMetrics(hours?: number): Promise<AiMetricsResponse> {
  const searchParams = new URLSearchParams();
  if (hours) searchParams.set('hours', hours.toString());

  const url = `${API_BASE}/ai-metrics${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取AI指标失败',
    }));
    throw new Error(getErrorMessage(error, '获取AI指标失败'));
  }

  const data = await safeJson<{
    response_time?: Record<string, number>;
    total_responses?: number;
    total_tokens?: number;
  }>(response);

  const rt = data.response_time ?? {};

  return {
    responseTime: {
      count: rt.count ?? 0,
      totalTime: rt.total_time ?? 0,
      avgTime: rt.avg_time ?? 0,
      minTime: rt.min_time ?? 0,
      maxTime: rt.max_time ?? 0,
      p50: rt.p50 ?? 0,
      p95: rt.p95 ?? 0,
      p99: rt.p99 ?? 0,
    },
    totalResponses: data.total_responses ?? 0,
    totalTokens: data.total_tokens ?? 0,
  };
}

/**
 * 获取用户活跃指标
 */
export async function apiGetUserMetrics(): Promise<UserMetrics> {
  const response = await fetch(`${API_BASE}/user-metrics`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取用户指标失败',
    }));
    throw new Error(getErrorMessage(error, '获取用户指标失败'));
  }

  const data = await safeJson<{
    active_now?: number;
    registered_total?: number;
    vip_users?: number;
  }>(response);

  return {
    activeNow: data.active_now ?? 0,
    registeredTotal: data.registered_total ?? 0,
    vipUsers: data.vip_users ?? 0,
  };
}

/**
 * 获取业务指标
 */
export async function apiGetBusinessMetrics(): Promise<BusinessMetrics> {
  const response = await fetch(`${API_BASE}/business-metrics`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取业务指标失败',
    }));
    throw new Error(getErrorMessage(error, '获取业务指标失败'));
  }

  const data = await safeJson<{
    consultations?: number;
    documents_generated?: number;
    lawyer_bookings?: number;
    posts_created?: number;
  }>(response);

  return {
    consultations: data.consultations ?? 0,
    documentsGenerated: data.documents_generated ?? 0,
    lawyerBookings: data.lawyer_bookings ?? 0,
    postsCreated: data.posts_created ?? 0,
  };
}

// ==================== 告警 API ====================

/**
 * 获取告警列表
 */
export async function apiGetAlerts(hours?: number, level?: string): Promise<AlertsResponse> {
  const searchParams = new URLSearchParams();
  if (hours) searchParams.set('hours', hours.toString());
  if (level) searchParams.set('level', level);

  const url = `${API_BASE}/alerts${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取告警列表失败',
    }));
    throw new Error(getErrorMessage(error, '获取告警列表失败'));
  }

  const data = await safeJson<{
    total?: number;
    alerts?: Array<{
      rule_name?: string;
      level?: string;
      message?: string;
      timestamp?: string;
      resolved?: boolean;
    }>;
  }>(response);

  return {
    total: data.total ?? 0,
    alerts: (data.alerts ?? []).map(alert => ({
      ruleName: alert.rule_name ?? '',
      level: (alert.level ?? 'info') as AlertsResponse['alerts'][number]['level'],
      message: alert.message ?? '',
      timestamp: alert.timestamp ?? '',
      resolved: alert.resolved ?? false,
    })),
  };
}

/**
 * 获取告警规则
 */
export async function apiGetAlertRules(): Promise<AlertRulesResponse> {
  const response = await fetch(`${API_BASE}/alert-rules`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取告警规则失败',
    }));
    throw new Error(getErrorMessage(error, '获取告警规则失败'));
  }

  const data = await safeJson<{
    rules?: Array<{
      name?: string;
      description?: string;
      level?: string;
      cooldown_seconds?: number;
      enabled?: boolean;
    }>;
    total?: number;
  }>(response);

  return {
    rules: (data.rules ?? []).map(rule => ({
      name: rule.name ?? '',
      description: rule.description ?? '',
      level: (rule.level ?? 'info') as AlertRulesResponse['rules'][number]['level'],
      cooldownSeconds: rule.cooldown_seconds ?? 0,
      enabled: rule.enabled ?? false,
    })),
    total: data.total ?? 0,
  };
}

/**
 * 启用告警规则
 */
export async function apiEnableAlertRule(ruleName: string): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<{ success: boolean; message: string }>(`${API_BASE}/alert-rules/${encodeURIComponent(ruleName)}/enable`);
  return response.data;
}

/**
 * 禁用告警规则
 */
export async function apiDisableAlertRule(ruleName: string): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<{ success: boolean; message: string }>(`${API_BASE}/alert-rules/${encodeURIComponent(ruleName)}/disable`);
  return response.data;
}

// ==================== 查询统计 API ====================

/**
 * 获取查询统计
 */
export async function apiGetQueryStats(): Promise<QueryStatsResponse> {
  const response = await fetch(`${API_BASE}/query-stats`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取查询统计失败',
    }));
    throw new Error(getErrorMessage(error, '获取查询统计失败'));
  }

  const data = await safeJson<{
    stats?: {
      total_queries?: number;
      slow_queries?: number;
      avg_execution_time?: number;
      max_execution_time?: number;
    };
    slow_queries?: Array<{
      query?: string;
      execution_time?: number;
      timestamp?: string;
      params?: Record<string, unknown>;
    }>;
    optimization_suggestions?: Array<{
      query?: string;
      suggestion?: string;
      priority?: string;
    }>;
  }>(response);

  return {
    stats: {
      totalQueries: data.stats?.total_queries ?? 0,
      slowQueries: data.stats?.slow_queries ?? 0,
      avgExecutionTime: data.stats?.avg_execution_time ?? 0,
      maxExecutionTime: data.stats?.max_execution_time ?? 0,
    },
    slowQueries: (data.slow_queries ?? []).map(sq => ({
      query: sq.query ?? '',
      executionTime: sq.execution_time ?? 0,
      timestamp: sq.timestamp ?? '',
      params: sq.params,
    })),
    optimizationSuggestions: (data.optimization_suggestions ?? []).map(s => ({
      query: s.query ?? '',
      suggestion: s.suggestion ?? '',
      priority: (s.priority ?? 'low') as QueryStatsResponse['optimizationSuggestions'][number]['priority'],
    })),
  };
}

/**
 * 重置查询统计
 */
export async function apiResetQueryStats(): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>(`${API_BASE}/query-stats/reset`);
  return response.data;
}

// ==================== 系统信息 API ====================

/**
 * 获取系统信息
 */
export async function apiGetSystemInfo(): Promise<SystemInfo> {
  const response = await fetch(`${API_BASE}/system-info`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取系统信息失败',
    }));
    throw new Error(getErrorMessage(error, '获取系统信息失败'));
  }

  const data = await safeJson<{
    platform?: string;
    platform_version?: string;
    processor?: string;
    python_version?: string;
    memory?: {
      total_gb?: number;
      available_gb?: number;
      percent?: number;
    };
    disk?: {
      total_gb?: number;
      free_gb?: number;
      percent?: number;
    };
    cpu?: {
      percent?: number;
      count?: number;
    };
  }>(response);

  return {
    platform: data.platform ?? 'unknown',
    platformVersion: data.platform_version ?? 'unknown',
    processor: data.processor ?? 'unknown',
    pythonVersion: data.python_version ?? 'unknown',
    memory: {
      totalGb: data.memory?.total_gb ?? 0,
      availableGb: data.memory?.available_gb ?? 0,
      percent: data.memory?.percent ?? 0,
    },
    disk: {
      totalGb: data.disk?.total_gb ?? 0,
      freeGb: data.disk?.free_gb ?? 0,
      percent: data.disk?.percent ?? 0,
    },
    cpu: {
      percent: data.cpu?.percent ?? 0,
      count: data.cpu?.count ?? 0,
    },
  };
}

// ==================== 数据库状态 API ====================

/**
 * 获取数据库状态
 */
export async function apiGetDatabaseStatus(): Promise<DatabaseStatus> {
  const response = await fetch(`${API_BASE}/database-status`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取数据库状态失败',
    }));
    throw new Error(getErrorMessage(error, '获取数据库状态失败'));
  }

  const data = await safeJson<{
    status?: string;
    connection?: string;
    version?: string;
    error?: string;
  }>(response);

  return {
    status: (data.status ?? 'unhealthy') as DatabaseStatus['status'],
    connection: data.connection ?? 'unknown',
    version: data.version,
    error: data.error,
  };
}

// ==================== 缓存状态 API ====================

/**
 * 获取缓存状态
 */
export async function apiGetCacheStatus(): Promise<CacheStatus> {
  const response = await fetch(`${API_BASE}/cache-status`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取缓存状态失败',
    }));
    throw new Error(getErrorMessage(error, '获取缓存状态失败'));
  }

  const data = await safeJson<{
    status?: string;
    connection?: string;
    memory?: string;
    clients?: number;
    message?: string;
    error?: string;
  }>(response);

  return {
    status: (data.status ?? 'unhealthy') as CacheStatus['status'],
    connection: data.connection,
    memory: data.memory,
    clients: data.clients,
    message: data.message,
    error: data.error,
  };
}

// ==================== WebSocket状态 API ====================

/**
 * 获取WebSocket状态
 */
export async function apiGetWebSocketStatus(): Promise<WebSocketStatus> {
  const response = await fetch(`${API_BASE}/websocket-status`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取WebSocket状态失败',
    }));
    throw new Error(getErrorMessage(error, '获取WebSocket状态失败'));
  }

  const data = await safeJson<{
    total_connections?: number;
    online_users?: number;
    rooms?: string[];
  }>(response);

  return {
    totalConnections: data.total_connections ?? 0,
    onlineUsers: data.online_users ?? 0,
    rooms: data.rooms ?? [],
  };
}

// ==================== 日志 API ====================

/**
 * 获取系统日志
 */
export async function apiGetLogs(params?: {
  level?: string;
  source?: string;
  startTime?: string;
  endTime?: string;
  limit?: number;
  offset?: number;
}): Promise<LogsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.level) searchParams.set('level', params.level);
  if (params?.source) searchParams.set('source', params.source);
  if (params?.startTime) searchParams.set('start_time', params.startTime);
  if (params?.endTime) searchParams.set('end_time', params.endTime);
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());

  const url = `${API_BASE}/logs${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取系统日志失败',
    }));
    throw new Error(getErrorMessage(error, '获取系统日志失败'));
  }

  const data = await safeJson<{
    total?: number;
    logs?: Array<{
      id?: string;
      timestamp?: string;
      level?: string;
      message?: string;
      source?: string;
      metadata?: Record<string, unknown>;
    }>;
    has_more?: boolean;
  }>(response);

  return {
    total: data.total ?? 0,
    logs: (data.logs ?? []).map(log => ({
      id: log.id ?? '',
      timestamp: log.timestamp ?? '',
      level: (log.level ?? 'info') as LogsResponse['logs'][number]['level'],
      message: log.message ?? '',
      source: log.source ?? '',
      metadata: log.metadata,
    })),
    hasMore: data.has_more ?? false,
  };
}

// ==================== 日报表 API ====================

/**
 * 获取日报表
 */
export async function apiGetDailyReport(date?: string): Promise<DailyReport> {
  const searchParams = new URLSearchParams();
  if (date) searchParams.set('date', date);

  const url = `${API_BASE}/daily-report${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({
      detail: '获取日报表失败',
    }));
    throw new Error(getErrorMessage(error, '获取日报表失败'));
  }

  const data = await safeJson<{
    date?: string;
    summary?: {
      api_requests?: number;
      errors?: number;
      ai_responses?: number;
    };
    health_status?: string;
  }>(response);

  return {
    date: data.date ?? new Date().toISOString().split('T')[0],
    summary: {
      apiRequests: data.summary?.api_requests ?? 0,
      errors: data.summary?.errors ?? 0,
      aiResponses: data.summary?.ai_responses ?? 0,
    },
    healthStatus: (data.health_status ?? 'unhealthy') as DailyReport['healthStatus'],
  };
}

// ==================== Dashboard API ====================

/**
 * 获取Dashboard数据（组合多个端点）
 */
export async function apiGetDashboard(): Promise<DashboardStats> {
  try {
    // 并行获取多个数据源
    const [
      healthRes,
      _metricsRes,
      apiMetricsRes,
      aiMetricsRes,
      userMetricsRes,
      businessMetricsRes,
      alertsRes,
      databaseStatusRes,
      cacheStatusRes,
      websocketStatusRes,
    ] = await Promise.allSettled([
      apiGetHealth(),
      apiGetMetrics(),
      apiGetApiMetrics(),
      apiGetAiMetrics(),
      apiGetUserMetrics(),
      apiGetBusinessMetrics(),
      apiGetAlerts(24),
      apiGetDatabaseStatus(),
      apiGetCacheStatus(),
      apiGetWebSocketStatus(),
    ]);

    const getValue = <T>(result: PromiseSettledResult<T>, defaultValue: T): T => {
      if (result.status === 'fulfilled') {
        return result.value;
      }
      console.error('API调用失败:', result.reason);
      return defaultValue;
    };

    return {
      health: getValue(healthRes, {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        components: [],
      }),
      system: {
        cpu: { percent: 0, count: 0 },
        memory: { totalGb: 0, availableGb: 0, percent: 0 },
        disk: { totalGb: 0, freeGb: 0, percent: 0 },
      },
      apiMetrics: getValue(apiMetricsRes, { endpoints: {}, count: 0 }),
      aiMetrics: getValue(aiMetricsRes, {
        responseTime: {
          count: 0,
          totalTime: 0,
          avgTime: 0,
          minTime: 0,
          maxTime: 0,
          p50: 0,
          p95: 0,
          p99: 0,
        },
        totalResponses: 0,
        totalTokens: 0,
      }),
      userMetrics: getValue(userMetricsRes, { activeNow: 0, registeredTotal: 0, vipUsers: 0 }),
      businessMetrics: getValue(businessMetricsRes, {
        consultations: 0,
        documentsGenerated: 0,
        lawyerBookings: 0,
        postsCreated: 0,
      }),
      alerts: getValue(alertsRes, { total: 0, alerts: [] }),
      databaseStatus: getValue(databaseStatusRes, {
        status: 'unhealthy',
        connection: 'unknown',
      }),
      cacheStatus: getValue(cacheStatusRes, {
        status: 'unhealthy',
      }),
      websocketStatus: getValue(websocketStatusRes, {
        totalConnections: 0,
        onlineUsers: 0,
        rooms: [],
      }),
    };
  } catch (error) {
    console.error('获取Dashboard数据失败:', error);
    throw error;
  }
}

// 导出所有API函数
export const api = {
  getHealth: apiGetHealth,
  getMetrics: apiGetMetrics,
  getApiMetrics: apiGetApiMetrics,
  getAiMetrics: apiGetAiMetrics,
  getUserMetrics: apiGetUserMetrics,
  getBusinessMetrics: apiGetBusinessMetrics,
  getAlerts: apiGetAlerts,
  getAlertRules: apiGetAlertRules,
  enableAlertRule: apiEnableAlertRule,
  disableAlertRule: apiDisableAlertRule,
  getQueryStats: apiGetQueryStats,
  resetQueryStats: apiResetQueryStats,
  getSystemInfo: apiGetSystemInfo,
  getDatabaseStatus: apiGetDatabaseStatus,
  getCacheStatus: apiGetCacheStatus,
  getWebSocketStatus: apiGetWebSocketStatus,
  getLogs: apiGetLogs,
  getDailyReport: apiGetDailyReport,
  getDashboard: apiGetDashboard,
} as const;