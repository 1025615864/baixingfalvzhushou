/**
 * Home（首页）API 层
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  HomeData,
  HomeBanner,
  QuickAction,
  Recommendation,
  HomeStats,
  GetHomeDataRequest,
  GetHomeDataResponse,
  GetRecommendationsRequest,
  GetRecommendationsResponse,
  GetQuickActionsResponse,
  GetHomeStatsResponse,
  TrackClickRequest,
  TrackClickResponse,
  UpdateInterestsRequest,
  UpdateInterestsResponse,
} from '../types';



// API 基础路径
const API_BASE = '/home';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
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

/**
 * 获取首页完整数据
 */
export async function apiGetHomeData(request: GetHomeDataRequest = {}): Promise<HomeData> {
  const searchParams = new URLSearchParams();
  if (request.includeStats !== undefined) {
    searchParams.set('include_stats', String(request.includeStats));
  }
  if (request.recommendationLimit !== undefined) {
    searchParams.set('recommendation_limit', String(request.recommendationLimit));
  }

  const url = `${API_BASE}/data${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  try {
    const response = await apiClient.get<GetHomeDataResponse>(url);
    return response.data.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, '获取首页数据失败'));
  }
}

/**
 * 获取推荐内容
 */
export async function apiGetRecommendations(
  params: GetRecommendationsRequest = {}
): Promise<{ recommendations: Recommendation[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params.type) searchParams.set('type', params.type);
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.offset) searchParams.set('offset', String(params.offset));

  const url = `${API_BASE}/recommendations${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  try {
    const response = await apiClient.get<GetRecommendationsResponse>(url);
    return {
      recommendations: response.data.recommendations,
      total: response.data.total,
    };
  } catch (error) {
    throw new Error(getErrorMessage(error, '获取推荐内容失败'));
  }
}

/**
 * 获取快捷入口
 */
export async function apiGetQuickActions(): Promise<QuickAction[]> {
  try {
    const response = await apiClient.get<GetQuickActionsResponse>(`${API_BASE}/quick-actions`);
    return response.data.actions;
  } catch (error) {
    throw new Error(getErrorMessage(error, '获取快捷入口失败'));
  }
}

/**
 * 获取首页统计数据
 */
export async function apiGetHomeStats(): Promise<HomeStats> {
  try {
    const response = await apiClient.get<GetHomeStatsResponse>(`${API_BASE}/stats`);
    return response.data.stats;
  } catch (error) {
    throw new Error(getErrorMessage(error, '获取统计数据失败'));
  }
}

/**
 * 获取首页横幅
 */
export async function apiGetBanners(): Promise<HomeBanner[]> {
  try {
    const response = await apiClient.get<{ banners: HomeBanner[] }>(`${API_BASE}/banners`);
    return response.data.banners;
  } catch (error) {
    throw new Error(getErrorMessage(error, '获取横幅数据失败'));
  }
}

/**
 * 追踪点击行为
 */
export async function apiTrackClick(request: TrackClickRequest): Promise<boolean> {
  const response = await apiClient.post<TrackClickResponse>(`${API_BASE}/track-click`, {
    item_id: request.itemId,
    item_type: request.itemType,
    source: request.source,
  });

  return response.data.success;
}

/**
 * 更新用户兴趣
 */
export async function apiUpdateInterests(request: UpdateInterestsRequest): Promise<UpdateInterestsResponse> {
  const response = await apiClient.post<UpdateInterestsResponse>(`${API_BASE}/interests`, {
    interests: request.interests,
  });

  return response.data;
}