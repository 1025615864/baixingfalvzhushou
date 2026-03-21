/**
 * Home（首页）Hooks
 * 优化：增加新用户引导状态查询
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  HomeData,
  HomeBanner,
  QuickAction,
  Recommendation,
  HomeStats,
  GetHomeDataRequest,
  GetRecommendationsRequest,
  TrackClickRequest,
  UpdateInterestsRequest,
} from '../types';
import {
  apiGetHomeData,
  apiGetBanners,
  apiGetQuickActions,
  apiGetRecommendations,
  apiGetHomeStats,
  apiTrackClick,
  apiUpdateInterests,
} from '../api';

// ==================== Onboarding Types ====================
export interface OnboardingStatus {
  has_role: boolean;
  current_step: string;
  current_step_value: number;
  completed?: boolean;
}

// ==================== Query Keys ====================

const HOME_QUERY_KEYS = {
  data: (params?: GetHomeDataRequest) => ['home', 'data', params] as const,
  banners: ['home', 'banners'] as const,
  quickActions: ['home', 'quickActions'] as const,
  recommendations: (params?: GetRecommendationsRequest) =>
    ['home', 'recommendations', params] as const,
  stats: ['home', 'stats'] as const,
} as const;

// ==================== Data Hooks ====================

/**
 * 获取首页完整数据 Hook
 */
export function useHomeData(params: GetHomeDataRequest = {}) {
  return useQuery<HomeData>({
    queryKey: HOME_QUERY_KEYS.data(params),
    queryFn: () => apiGetHomeData(params),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== Banners Hooks ====================

/**
 * 获取首页横幅 Hook
 */
export function useHomeBanners() {
  return useQuery<HomeBanner[]>({
    queryKey: HOME_QUERY_KEYS.banners,
    queryFn: apiGetBanners,
    staleTime: 10 * 60 * 1000, // 10分钟缓存，横幅不常变化
  });
}

// ==================== Quick Actions Hooks ====================

/**
 * 获取快捷入口 Hook
 */
export function useQuickActions() {
  return useQuery<QuickAction[]>({
    queryKey: HOME_QUERY_KEYS.quickActions,
    queryFn: apiGetQuickActions,
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

// ==================== Recommendations Hooks ====================

/**
 * 分页推荐内容结果
 */
export interface PaginatedRecommendationsResult {
  recommendations: Recommendation[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * 获取推荐内容 Hook（支持分页）
 */
export function useRecommendations(params: GetRecommendationsRequest = {}) {
  return useQuery<PaginatedRecommendationsResult>({
    queryKey: HOME_QUERY_KEYS.recommendations(params),
    queryFn: async () => {
      const response = await apiGetRecommendations(params);
      return {
        recommendations: response.recommendations,
        total: response.total,
        limit: params.limit ?? 10,
        offset: params.offset ?? 0,
      };
    },
    staleTime: 3 * 60 * 1000, // 3分钟缓存，推荐内容变化较快
  });
}

// ==================== Stats Hooks ====================

/**
 * 获取首页统计数据 Hook
 */
export function useHomeStats() {
  return useQuery<HomeStats>({
    queryKey: HOME_QUERY_KEYS.stats,
    queryFn: apiGetHomeStats,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== Tracking Hooks ====================

/**
 * 追踪点击行为 Hook
 */
export function useTrackClick() {
  return useMutation({
    mutationFn: (request: TrackClickRequest) => apiTrackClick(request),
  });
}

// ==================== Interests Hooks ====================

/**
 * 更新用户兴趣 Hook
 */
export function useUpdateInterests() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateInterestsRequest) => apiUpdateInterests(request),
    onSuccess: () => {
      // 更新兴趣后，刷新推荐内容
      void queryClient.invalidateQueries({ queryKey: ['home', 'recommendations'] });
    },
  });
}

// ==================== Combined Hook ====================

/**
 * 首页数据聚合 Hook
 * 同时获取横幅、快捷入口、推荐内容和统计数据
 */
export function useHomePageData() {
  const bannersQuery = useHomeBanners();
  const quickActionsQuery = useQuickActions();
  const recommendationsQuery = useRecommendations({ limit: 8 });
  const statsQuery = useHomeStats();

  const isLoading =
    bannersQuery.isLoading ||
    quickActionsQuery.isLoading ||
    recommendationsQuery.isLoading ||
    statsQuery.isLoading;

  const isError =
    bannersQuery.isError ||
    quickActionsQuery.isError ||
    recommendationsQuery.isError ||
    statsQuery.isError;

  const error =
    bannersQuery.error ||
    quickActionsQuery.error ||
    recommendationsQuery.error ||
    statsQuery.error;

  return {
    banners: bannersQuery.data ?? [],
    quickActions: quickActionsQuery.data ?? [],
    recommendations: recommendationsQuery.data?.recommendations ?? [],
    stats: statsQuery.data,
    isLoading,
    isError,
    error,
    refetch: () => {
      void bannersQuery.refetch();
      void quickActionsQuery.refetch();
      void recommendationsQuery.refetch();
      void statsQuery.refetch();
    },
  };
}