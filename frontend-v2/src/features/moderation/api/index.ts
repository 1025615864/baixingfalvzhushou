/**
 * Moderation（内容审核）API 层
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  ModerationStats,
  GetModerationQueueRequest,
  GetModerationQueueResponse,
  GetModerationRecordsRequest,
  GetModerationRecordsResponse,
  SubmitReviewRequest,
  SubmitReviewResponse,
  BatchReviewRequest,
  BatchReviewResponse,
  GetModerationStatsResponse,
  GetContentDetailResponse,
  CheckKeywordsRequest,
  CheckKeywordsResponse,
} from '../types';


// API 基础路径
const API_BASE = '/moderation';

/**
 * 获取审核队列
 */
export async function apiGetModerationQueue(
  params?: GetModerationQueueRequest
): Promise<GetModerationQueueResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  if (params?.contentType) searchParams.set('content_type', params.contentType);
  if (params?.riskLevel) searchParams.set('risk_level', params.riskLevel);
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.pageSize) searchParams.set('page_size', params.pageSize.toString());

  const url = `${API_BASE}/queue${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await apiClient.get<GetModerationQueueResponse>(url);

  if (!response.data) {
    throw new Error('获取审核队列失败');
  }

  return response.data;
}

/**
 * 获取审核记录
 */
export async function apiGetModerationRecords(
  params?: GetModerationRecordsRequest
): Promise<GetModerationRecordsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.contentType) searchParams.set('content_type', params.contentType);
  if (params?.action) searchParams.set('action', params.action);
  if (params?.reviewerId) searchParams.set('reviewer_id', params.reviewerId);
  if (params?.startDate) searchParams.set('start_date', params.startDate);
  if (params?.endDate) searchParams.set('end_date', params.endDate);
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.pageSize) searchParams.set('page_size', params.pageSize.toString());

  const url = `${API_BASE}/records${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await apiClient.get<GetModerationRecordsResponse>(url);

  if (!response.data) {
    throw new Error('获取审核记录失败');
  }

  return response.data;
}

/**
 * 提交审核
 */
export async function apiSubmitReview(
  request: SubmitReviewRequest
): Promise<SubmitReviewResponse> {
  const response = await apiClient.post<SubmitReviewResponse>(`${API_BASE}/${request.id}/review`, {
    action: request.action,
    reason: request.reason,
    note: request.note,
  });

  return response.data;
}

/**
 * 批量审核
 */
export async function apiBatchReview(
  request: BatchReviewRequest
): Promise<BatchReviewResponse> {
  const response = await apiClient.post<BatchReviewResponse>(`${API_BASE}/batch-review`, {
    ids: request.ids,
    action: request.action,
    reason: request.reason,
    note: request.note,
  });

  return response.data;
}

/**
 * 获取审核统计
 */
export async function apiGetModerationStats(
  startDate?: string,
  endDate?: string
): Promise<ModerationStats> {
  const searchParams = new URLSearchParams();
  if (startDate) searchParams.set('start_date', startDate);
  if (endDate) searchParams.set('end_date', endDate);

  const url = `${API_BASE}/stats${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await apiClient.get<GetModerationStatsResponse>(url);

  if (!response.data) {
    throw new Error('获取审核统计失败');
  }

  return response.data.stats;
}

/**
 * 获取内容详情
 */
export async function apiGetContentDetail(
  contentId: string,
  contentType: string
): Promise<GetContentDetailResponse> {
  const response = await apiClient.get<GetContentDetailResponse>(`${API_BASE}/content/${contentType}/${contentId}`);
  return response.data;
}

/**
 * 关键词检查
 */
export async function apiCheckKeywords(
  request: CheckKeywordsRequest
): Promise<CheckKeywordsResponse> {
  const response = await apiClient.post<{
    flagged: boolean;
    keywords_found: string[];
    risk_score: number;
    categories: string[];
    severity: string;
  }>(`${API_BASE}/keyword/check`, {
    content: request.content,
    categories: request.categories,
  });

  const data = response.data;

  return {
    hasSensitiveWords: data.flagged,
    riskScore: data.risk_score,
    matches: data.keywords_found.map((keyword, index) => ({
      keyword,
      category: data.categories[0] || 'unknown',
      severity: data.severity as 'high' | 'medium' | 'low',
      position: index,
      length: keyword.length,
    })),
    categories: data.categories,
  };
}

/**
 * 获取公开审核统计（无需管理员权限）
 */
export async function apiGetPublicModerationStats(): Promise<{
  total_checks: number;
  blocked_count: number;
  warning_count: number;
  passed_count: number;
  block_rate: number;
  categories: Record<string, number>;
}> {
  const response = await apiClient.get<{
    total_checks: number;
    blocked_count: number;
    warning_count: number;
    passed_count: number;
    block_rate: number;
    categories: Record<string, number>;
  }>(`${API_BASE}/stats`);

  return response.data;
}