/**
 * AI质量监控（AI Quality）类型定义
 */

// ==================== 质量指标相关类型 ====================

/** 响应时间统计 */
export interface ResponseTimeStats {
  avg_ms: number;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
  min_ms: number;
  max_ms: number;
}

/** 质量评分分布 */
export interface QualityScoreDistribution {
  excellent: number;
  good: number;
  average: number;
  poor: number;
  avg: number;
  satisfaction_rate: number;
}

/** 错误分布 */
export interface ErrorDistribution {
  total: number;
  timeout: number;
  rate_limit: number;
  token_exceeded: number;
  context_length: number;
  service_unavailable: number;
  unknown: number;
}

/** AI质量指标 */
export interface AIMetrics {
  total_conversations: number;
  successful_conversations: number;
  error_count: number;
  success_rate: number;
  response_time: ResponseTimeStats;
  quality_score: QualityScoreDistribution;
  error_distribution: ErrorDistribution;
  topic_distribution: Record<string, number>;
  tool_usage: Record<string, number>;
  positive_feedback: number;
  negative_feedback: number;
  helpful_responses: number;
  unhelpful_responses: number;
  timestamp: string;
}

/** 仪表板汇总数据 */
export interface DashboardSummary {
  total_conversations: number;
  success_rate: number;
  avg_response_time_ms: number;
  avg_quality_score: number;
  satisfaction_rate: number;
}

/** 趋势数据 */
export interface TrendData {
  response_time_trend: 'increasing' | 'decreasing' | 'stable';
  quality_trend: 'increasing' | 'decreasing' | 'stable';
  satisfaction_trend: 'increasing' | 'decreasing' | 'stable';
}

/** 仪表板数据 */
export interface DashboardData {
  summary: DashboardSummary;
  response_time: ResponseTimeStats;
  quality_distribution: Record<string, number>;
  topic_distribution: Record<string, number>;
  tool_usage: Record<string, number>;
  error_distribution: ErrorDistribution;
  feedback: {
    positive: number;
    negative: number;
  };
  trend: TrendData;
}

// ==================== 会话质量相关类型 ====================

/** 质量等级 */
export type QualityLevel = 'excellent' | 'good' | 'average' | 'poor' | 'unknown';

/** 会话质量项 */
export interface SessionQuality {
  id: string;
  session_id: string;
  user_id: number | null;
  user_name: string | null;
  message_count: number;
  total_response_time_ms: number;
  avg_response_time_ms: number;
  quality_score: number | null;
  quality_level: QualityLevel;
  was_helpful: boolean | null;
  topics: string[];
  tools_used: string[];
  error_count: number;
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
}

/** 会话详情 */
export interface SessionDetail extends SessionQuality {
  messages: SessionMessage[];
  feedback: SessionFeedback | null;
}

/** 会话消息 */
export interface SessionMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  response_time_ms: number | null;
  tokens_used: number | null;
  quality_score: number | null;
}

/** 会话反馈 */
export interface SessionFeedback {
  id: string;
  is_helpful: boolean;
  rating: number | null;
  comment: string | null;
  created_at: string;
}

/** 会话列表请求 */
export interface GetSessionQualityListRequest {
  page?: number;
  page_size?: number;
  quality_level?: QualityLevel;
  start_date?: string;
  end_date?: string;
  user_id?: number;
  search?: string;
}

/** 会话列表响应 */
export interface GetSessionQualityListResponse {
  sessions: SessionQuality[];
  total: number;
  page: number;
  page_size: number;
}

/** 会话详情请求 */
export interface GetSessionDetailRequest {
  session_id: string;
}

/** 会话详情响应 */
export interface GetSessionDetailResponse {
  session: SessionDetail;
}

// ==================== 质量告警相关类型 ====================

/** 告警级别 */
export type AlertLevel = 'critical' | 'warning' | 'info';

/** 告警状态 */
export type AlertStatus = 'active' | 'acknowledged' | 'resolved';

/** 告警类型 */
export type AlertType = 
  | 'high_error_rate'
  | 'slow_response'
  | 'low_quality'
  | 'low_satisfaction'
  | 'service_unavailable'
  | 'token_quota_exceeded';

/** 质量告警 */
export interface QualityAlert {
  id: string;
  type: AlertType;
  level: AlertLevel;
  status: AlertStatus;
  title: string;
  description: string;
  metric_value: number;
  threshold: number;
  session_id: string | null;
  created_at: string;
  acknowledged_at: string | null;
  acknowledged_by: number | null;
  resolved_at: string | null;
  resolved_by: number | null;
}

/** 告警列表请求 */
export interface GetQualityAlertsRequest {
  page?: number;
  page_size?: number;
  level?: AlertLevel;
  status?: AlertStatus;
  type?: AlertType;
  start_date?: string;
  end_date?: string;
}

/** 告警列表响应 */
export interface GetQualityAlertsResponse {
  alerts: QualityAlert[];
  total: number;
  page: number;
  page_size: number;
  summary: {
    critical: number;
    warning: number;
    info: number;
    active: number;
  };
}

/** 确认告警请求 */
export interface AcknowledgeAlertRequest {
  alert_id: string;
  note?: string;
}

/** 确认告警响应 */
export interface AcknowledgeAlertResponse {
  success: boolean;
  alert: QualityAlert;
}

/** 解决告警请求 */
export interface ResolveAlertRequest {
  alert_id: string;
  resolution: string;
}

/** 解决告警响应 */
export interface ResolveAlertResponse {
  success: boolean;
  alert: QualityAlert;
}

// ==================== 人工审核相关类型 ====================

/** 审核结果 */
export type ReviewResult = 'approved' | 'rejected' | 'needs_improvement';

/** 审核请求 */
export interface ReviewSessionRequest {
  session_id: string;
  result: ReviewResult;
  quality_score: number;
  comment: string;
  issues?: string[];
  suggestions?: string[];
}

/** 审核响应 */
export interface ReviewSessionResponse {
  success: boolean;
  review_id: string;
  session: SessionQuality;
}

/** 审核记录 */
export interface ReviewRecord {
  id: string;
  session_id: string;
  reviewer_id: number;
  reviewer_name: string;
  result: ReviewResult;
  quality_score: number;
  comment: string;
  issues: string[];
  suggestions: string[];
  created_at: string;
}

/** 审核统计 */
export interface ReviewStats {
  total_reviewed: number;
  approved: number;
  rejected: number;
  needs_improvement: number;
  avg_quality_score: number;
  pending_count: number;
}

// ==================== 日志相关类型 ====================

/** AI日志条目 */
export interface AILogEntry {
  request_id: string;
  session_id: string | null;
  user_id: number | null;
  message_length: number;
  response_length: number;
  response_time_ms: number;
  quality_score: number | null;
  quality_level: QualityLevel | null;
  was_helpful: boolean | null;
  topics: string[];
  tools_used: string[];
  error_type: string | null;
  timestamp: string;
  level: 'info' | 'warning' | 'error';
}

/** 日志列表请求 */
export interface GetAILogsRequest {
  limit?: number;
  offset?: number;
  level?: 'info' | 'warning' | 'error';
  start_date?: string;
  end_date?: string;
}

/** 日志列表响应 */
export interface GetAILogsResponse {
  logs: AILogEntry[];
  total: number;
  limit: number;
}

// ==================== 图表数据类型 ====================

/** 趋势图表数据点 */
export interface TrendChartDataPoint {
  date: string;
  value: number;
  label?: string;
}

/** 质量趋势数据 */
export interface QualityTrendData {
  dates: string[];
  success_rate: number[];
  avg_quality_score: number[];
  response_time_p95: number[];
  satisfaction_rate: number[];
}

/** 分布图表数据项 */
export interface DistributionChartItem {
  name: string;
  value: number;
  percentage: number;
  color?: string;
}

/** 对比图表数据 */
export interface ComparisonChartData {
  categories: string[];
  series: {
    name: string;
    data: number[];
  }[];
}