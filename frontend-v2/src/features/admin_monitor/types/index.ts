/**
 * Admin Monitor（系统监控）类型定义
 */

// ==================== 健康检查相关类型 ====================

/** 健康状态 */
export type HealthStatus = 'healthy' | 'unhealthy' | 'degraded';

/** 健康检查组件 */
export interface HealthComponent {
  name: string;
  status: HealthStatus;
  message?: string;
  responseTime?: number;
}

/** 健康检查响应 */
export interface HealthCheckResponse {
  status: HealthStatus;
  timestamp: string;
  components: HealthComponent[];
}

// ==================== 系统指标相关类型 ====================

/** 系统指标摘要 */
export interface SystemMetrics {
  cpu: {
    percent: number;
    count: number;
  };
  memory: {
    totalGb: number;
    availableGb: number;
    percent: number;
  };
  disk: {
    totalGb: number;
    freeGb: number;
    percent: number;
  };
}

/** 指标摘要响应 */
export interface MetricsSummaryResponse {
  apiRequests: number;
  errors: number;
  avgResponseTime: number;
  activeConnections: number;
}

// ==================== API指标相关类型 ====================

/** API端点指标 */
export interface ApiEndpointMetrics {
  count: number;
  totalTime: number;
  avgTime: number;
  minTime: number;
  maxTime: number;
  p50: number;
  p95: number;
  p99: number;
}

/** API指标响应 */
export interface ApiMetricsResponse {
  endpoints: Record<string, ApiEndpointMetrics>;
  count: number;
}

// ==================== AI指标相关类型 ====================

/** AI服务指标 */
export interface AiMetrics {
  responseTime: {
    count: number;
    totalTime: number;
    avgTime: number;
    minTime: number;
    maxTime: number;
  };
  totalResponses: number;
  totalTokens: number;
}

/** AI指标响应 */
export interface AiMetricsResponse {
  responseTime: ApiEndpointMetrics;
  totalResponses: number;
  totalTokens: number;
}

// ==================== 用户指标相关类型 ====================

/** 用户活跃指标 */
export interface UserMetrics {
  activeNow: number;
  registeredTotal: number;
  vipUsers: number;
}

// ==================== 业务指标相关类型 ====================

/** 业务指标 */
export interface BusinessMetrics {
  consultations: number;
  documentsGenerated: number;
  lawyerBookings: number;
  postsCreated: number;
}

// ==================== 告警相关类型 ====================

/** 告警级别 */
export type AlertLevel = 'info' | 'warning' | 'error' | 'critical';

/** 告警项 */
export interface AlertItem {
  ruleName: string;
  level: AlertLevel;
  message: string;
  timestamp: string;
  resolved: boolean;
}

/** 告警列表响应 */
export interface AlertsResponse {
  total: number;
  alerts: AlertItem[];
}

/** 告警规则 */
export interface AlertRule {
  name: string;
  description: string;
  level: AlertLevel;
  cooldownSeconds: number;
  enabled: boolean;
}

/** 告警规则响应 */
export interface AlertRulesResponse {
  rules: AlertRule[];
  total: number;
}

// ==================== 查询统计相关类型 ====================

/** 查询统计 */
export interface QueryStats {
  totalQueries: number;
  slowQueries: number;
  avgExecutionTime: number;
  maxExecutionTime: number;
}

/** 慢查询项 */
export interface SlowQueryItem {
  query: string;
  executionTime: number;
  timestamp: string;
  params?: Record<string, unknown>;
}

/** 优化建议 */
export interface OptimizationSuggestion {
  query: string;
  suggestion: string;
  priority: 'low' | 'medium' | 'high';
}

/** 查询统计响应 */
export interface QueryStatsResponse {
  stats: QueryStats;
  slowQueries: SlowQueryItem[];
  optimizationSuggestions: OptimizationSuggestion[];
}

// ==================== 系统信息相关类型 ====================

/** 系统信息 */
export interface SystemInfo {
  platform: string;
  platformVersion: string;
  processor: string;
  pythonVersion: string;
  memory: {
    totalGb: number;
    availableGb: number;
    percent: number;
  };
  disk: {
    totalGb: number;
    freeGb: number;
    percent: number;
  };
  cpu: {
    percent: number;
    count: number;
  };
}

// ==================== 数据库状态相关类型 ====================

/** 数据库状态 */
export interface DatabaseStatus {
  status: HealthStatus;
  connection: string;
  version?: string;
  error?: string;
}

// ==================== 缓存状态相关类型 ====================

/** 缓存状态 */
export interface CacheStatus {
  status: HealthStatus | 'not_configured' | 'unavailable';
  connection?: string;
  memory?: string;
  clients?: number;
  message?: string;
  error?: string;
}

// ==================== WebSocket状态相关类型 ====================

/** WebSocket状态 */
export interface WebSocketStatus {
  totalConnections: number;
  onlineUsers: number;
  rooms: string[];
}

// ==================== 日志相关类型 ====================

/** 日志级别 */
export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

/** 日志项 */
export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  source: string;
  metadata?: Record<string, unknown>;
}

/** 日志列表响应 */
export interface LogsResponse {
  total: number;
  logs: LogEntry[];
  hasMore: boolean;
}

// ==================== 日报表相关类型 ====================

/** 日报表 */
export interface DailyReport {
  date: string;
  summary: {
    apiRequests: number;
    errors: number;
    aiResponses: number;
  };
  healthStatus: HealthStatus;
}

// ==================== Dashboard统计相关类型 ====================

/** Dashboard统计数据 */
export interface DashboardStats {
  health: HealthCheckResponse;
  system: SystemMetrics;
  apiMetrics: ApiMetricsResponse;
  aiMetrics: AiMetricsResponse;
  userMetrics: UserMetrics;
  businessMetrics: BusinessMetrics;
  alerts: AlertsResponse;
  databaseStatus: DatabaseStatus;
  cacheStatus: CacheStatus;
  websocketStatus: WebSocketStatus;
}

// ==================== 图表数据相关类型 ====================

/** 时间序列数据点 */
export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

/** 资源使用数据 */
export interface ResourceUsageData {
  timestamps: string[];
  cpu: number[];
  memory: number[];
  disk: number[];
}

/** 请求趋势数据 */
export interface RequestTrendData {
  timestamps: string[];
  requests: number[];
  errors: number[];
  avgResponseTime: number[];
}

// ==================== 组件Props类型 ====================

/** 指标卡片Props */
export interface MetricCardProps {
  title: string;
  value: number | string;
  unit?: string;
  change?: number;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon?: string;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  loading?: boolean;
}

/** 告警列表Props */
export interface AlertListProps {
  alerts: AlertItem[];
  onResolve?: (alertId: string) => void;
  onDismiss?: (alertId: string) => void;
  loading?: boolean;
}

/** 日志查看器Props */
export interface LogViewerProps {
  logs: LogEntry[];
  onLoadMore?: () => void;
  onFilterChange?: (filters: LogFilters) => void;
  hasMore?: boolean;
  loading?: boolean;
}

/** 日志过滤器 */
export interface LogFilters {
  level?: LogLevel;
  source?: string;
  startTime?: string;
  endTime?: string;
  search?: string;
}

/** 监控图表Props */
export interface MonitorChartsProps {
  resourceData?: ResourceUsageData;
  requestData?: RequestTrendData;
  timeRange?: '1h' | '6h' | '24h' | '7d';
  onTimeRangeChange?: (range: '1h' | '6h' | '24h' | '7d') => void;
  loading?: boolean;
}