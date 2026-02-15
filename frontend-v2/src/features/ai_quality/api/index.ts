/**
 * AI质量监控（AI Quality）API接口
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  AIMetrics,
  DashboardData,
  GetSessionQualityListRequest,
  GetSessionQualityListResponse,
  GetSessionDetailRequest,
  GetSessionDetailResponse,
  GetQualityAlertsRequest,
  GetQualityAlertsResponse,
  AcknowledgeAlertRequest,
  AcknowledgeAlertResponse,
  ResolveAlertRequest,
  ResolveAlertResponse,
  ReviewSessionRequest,
  ReviewSessionResponse,
  ReviewStats,
  GetAILogsRequest,
  GetAILogsResponse,
  QualityTrendData,
} from '../types';


// ==================== API基础配置 ====================

const BASE_URL = '/system/ai-quality';

// ==================== 质量指标API ====================

/**
 * 获取AI质量指标
 */
export async function apiGetAIMetrics(): Promise<AIMetrics> {
  const response = await apiClient.get<AIMetrics>(`${BASE_URL}/metrics`);
  return response.data;
}

/**
 * 获取仪表板数据
 */
export async function apiGetDashboardData(): Promise<DashboardData> {
  const response = await apiClient.get<DashboardData>(`${BASE_URL}/dashboard`);
  return response.data;
}

/**
 * 获取质量趋势数据
 */
export async function apiGetQualityTrend(days: number = 7): Promise<QualityTrendData> {
  const params = new URLSearchParams({ days: String(days) }).toString();
  const response = await apiClient.get<QualityTrendData>(`${BASE_URL}/trends?${params}`);
  return response.data;
}

// ==================== 会话质量API ====================

/**
 * 获取会话质量列表
 */
export async function apiGetSessionQuality(
  params: GetSessionQualityListRequest = {}
): Promise<GetSessionQualityListResponse> {
  const searchParams = new URLSearchParams();
  
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.quality_level) searchParams.set('quality_level', params.quality_level);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);
  if (params.user_id) searchParams.set('user_id', String(params.user_id));
  if (params.search) searchParams.set('search', params.search);

  const queryString = searchParams.toString();
  const url = queryString ? `${BASE_URL}/sessions?${queryString}` : `${BASE_URL}/sessions`;
  
  const response = await apiClient.get<GetSessionQualityListResponse>(url);
  return response.data;
}

/**
 * 获取会话详情
 */
export async function apiGetSessionDetail(
  request: GetSessionDetailRequest
): Promise<GetSessionDetailResponse> {
  const response = await apiClient.get<GetSessionDetailResponse>(`${BASE_URL}/sessions/${request.session_id}`);
  return response.data;
}

/**
 * 人工审核会话
 */
export async function apiReviewSession(
  request: ReviewSessionRequest
): Promise<ReviewSessionResponse> {
  const response = await apiClient.post<ReviewSessionResponse>(`${BASE_URL}/sessions/${request.session_id}/review`, {
    result: request.result,
    quality_score: request.quality_score,
    comment: request.comment,
    issues: request.issues,
    suggestions: request.suggestions,
  });
  return response.data;
}

/**
 * 获取审核统计
 */
export async function apiGetReviewStats(): Promise<ReviewStats> {
  const response = await apiClient.get<ReviewStats>(`${BASE_URL}/reviews/stats`);
  return response.data;
}

// ==================== 质量告警API ====================

/**
 * 获取质量告警列表
 */
export async function apiGetQualityAlerts(
  params: GetQualityAlertsRequest = {}
): Promise<GetQualityAlertsResponse> {
  const searchParams = new URLSearchParams();
  
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.level) searchParams.set('level', params.level);
  if (params.status) searchParams.set('status', params.status);
  if (params.type) searchParams.set('type', params.type);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const queryString = searchParams.toString();
  const url = queryString ? `${BASE_URL}/alerts?${queryString}` : `${BASE_URL}/alerts`;
  
  const response = await apiClient.get<GetQualityAlertsResponse>(url);
  return response.data;
}

/**
 * 确认告警
 */
export async function apiAcknowledgeAlert(
  request: AcknowledgeAlertRequest
): Promise<AcknowledgeAlertResponse> {
  const response = await apiClient.post<AcknowledgeAlertResponse>(`${BASE_URL}/alerts/${request.alert_id}/acknowledge`, {
    note: request.note,
  });
  return response.data;
}

/**
 * 解决告警
 */
export async function apiResolveAlert(
  request: ResolveAlertRequest
): Promise<ResolveAlertResponse> {
  const response = await apiClient.post<ResolveAlertResponse>(`${BASE_URL}/alerts/${request.alert_id}/resolve`, {
    resolution: request.resolution,
  });
  return response.data;
}

// ==================== 日志API ====================

/**
 * 获取AI日志列表
 */
export async function apiGetAILogs(
  params: GetAILogsRequest = {}
): Promise<GetAILogsResponse> {
  const searchParams = new URLSearchParams();
  
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.offset) searchParams.set('offset', String(params.offset));
  if (params.level) searchParams.set('level', params.level);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const queryString = searchParams.toString();
  const url = queryString ? `${BASE_URL}/logs?${queryString}` : `${BASE_URL}/logs`;
  
  const response = await apiClient.get<GetAILogsResponse>(url);
  return response.data;
}

// ==================== 系统API ====================

/**
 * 获取AI质量监控健康状态
 */
export async function apiGetAIQualityHealth(): Promise<{
  status: string;
  total_conversations: number;
  last_updated: string;
}> {
  const response = await apiClient.get<{ status: string; total_conversations: number; last_updated: string }>(
    `${BASE_URL}/health`
  );
  return response.data;
}

/**
 * 重置统计数据（仅开发环境）
 */
export async function apiResetAIQualityStats(): Promise<{
  message: string;
  previous_stats: {
    total_conversations: number;
    successful_conversations: number;
    avg_quality_score: number;
  };
}> {
  const response = await apiClient.post<{
    message: string;
    previous_stats: {
      total_conversations: number;
      successful_conversations: number;
      avg_quality_score: number;
    };
  }>(`${BASE_URL}/reset`);
  return response.data;
}