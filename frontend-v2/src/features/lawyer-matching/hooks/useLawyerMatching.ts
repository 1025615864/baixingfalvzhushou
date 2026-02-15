/**
 * Lawyer-Matching（律师匹配）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { queryKeys } from '@/lib/queryKeys';

import type {
  LawyerMatchResult,
  LawyerDetail,
  Booking,
  LawyerReview,
  ReviewStats,
  LawyerOnlineInfo,
  GetRecommendationsRequest,
  GetBookingsRequest,
  GetReviewsRequest,
  CreateBookingRequest,
  SubmitReviewRequest,
  CancelBookingRequest,
  SearchLawyersRequest,
  MatchingCriteria,
} from '../types';
import {
  apiGetRecommendations,
  apiGetLawyerDetail,
  apiSearchLawyers,
  apiCreateBooking,
  apiGetBookings,
  apiCancelBooking,
  apiGetReviews,
  apiSubmitReview,
  apiGetOnlineStatus,
  apiGetLawyerOnlineStatus,
} from '../api';


// ==================== Recommendation Hooks ====================

/**
 * 获取推荐律师 Hook
 */
export function useLawyerRecommendations(
  queryText: string,
  criteria?: MatchingCriteria,
  limit: number = 10
) {
  return useQuery<LawyerMatchResult[]>({
    queryKey: queryKeys.lawyers.recommendations(queryText, criteria),
    queryFn: async () => {
      const request: GetRecommendationsRequest = {
        queryText,
        domains: criteria?.domains,
        limit,
        criteria,
      };
      const response = await apiGetRecommendations(request);
      return response.recommendations;
    },
    enabled: queryText.length > 0,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== Lawyer Detail Hooks ====================

/**
 * 获取律师详情 Hook
 */
export function useLawyerDetail(lawyerId: string) {
  return useQuery<LawyerDetail>({
    queryKey: queryKeys.lawyers.detail(lawyerId),
    queryFn: async () => {
      const response = await apiGetLawyerDetail({ lawyerId });
      return response.lawyer;
    },
    enabled: !!lawyerId,
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

// ==================== Search Hooks ====================

/**
 * 搜索律师 Hook
 */
export function useLawyerSearch(request: SearchLawyersRequest) {
  return useQuery<{
    lawyers: LawyerDetail[];
    total: number;
    hasMore: boolean;
  }>({
    queryKey: queryKeys.lawyers.search(request),
    queryFn: async () => {
      const response = await apiSearchLawyers(request);
      return {
        lawyers: response.lawyers.map((lawyer) => ({
          ...lawyer,
          phone: undefined,
          email: undefined,
        })),
        total: response.total,
        hasMore: response.hasMore,
      };
    },
    staleTime: 5 * 60 * 1000,
  });
}

// ==================== Booking Hooks ====================

/**
 * 获取预约列表 Hook
 */
export function useBookings(params: GetBookingsRequest = {}) {
  return useQuery<Booking[]>({
    queryKey: queryKeys.bookings.list({ status: params.status }),
    queryFn: async () => {
      const response = await apiGetBookings(params);
      return response.bookings;
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 创建预约 Hook
 */
export function useCreateBooking() {
  const queryClient = useQueryClient();

  return useMutation<
    { success: boolean; booking: Booking; paymentUrl?: string },
    Error,
    CreateBookingRequest
  >({
    mutationFn: apiCreateBooking,
    onSuccess: () => {
      // 创建成功后刷新预约列表
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bookings.list(),
      });
    },
  });
}

/**
 * 取消预约 Hook
 */
export function useCancelBooking() {
  const queryClient = useQueryClient();

  return useMutation<
    { success: boolean; refundAmount?: number },
    Error,
    CancelBookingRequest
  >({
    mutationFn: apiCancelBooking,
    onSuccess: () => {
      // 取消成功后刷新预约列表
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bookings.list(),
      });
    },
  });
}

// ==================== Review Hooks ====================

/**
 * 获取评价列表 Hook
 */
export function useLawyerReviews(lawyerId: string, params?: Omit<GetReviewsRequest, 'lawyerId'>) {
  return useQuery<{
    reviews: LawyerReview[];
    total: number;
    stats: ReviewStats;
  }>({
    queryKey: queryKeys.lawyers.reviews(lawyerId, params),
    queryFn: async () => {
      const request: GetReviewsRequest = {
        lawyerId,
        ...params,
      };
      const response = await apiGetReviews(request);
      return {
        reviews: response.reviews,
        total: response.total,
        stats: response.stats,
      };
    },
    enabled: !!lawyerId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 提交评价 Hook
 */
export function useSubmitReview() {
  const queryClient = useQueryClient();

  return useMutation<LawyerReview, Error, SubmitReviewRequest>({
    mutationFn: async (request) => {
      const response = await apiSubmitReview(request);
      return response.review;
    },
    onSuccess: (_, variables) => {
      // 提交成功后刷新评价列表
      void queryClient.invalidateQueries({
        queryKey: queryKeys.lawyers.reviews(variables.lawyerId),
      });
      // 刷新律师详情（评分可能已更新）
      void queryClient.invalidateQueries({
        queryKey: queryKeys.lawyers.detail(variables.lawyerId),
      });
    },
  });
}

// ==================== Online Status Hooks ====================

/**
 * 获取多个律师在线状态 Hook
 */
export function useLawyersOnlineStatus(lawyerIds: string[]) {
  return useQuery<LawyerOnlineInfo[]>({
    queryKey: queryKeys.lawyers.onlineStatus(lawyerIds),
    queryFn: async () => {
      const response = await apiGetOnlineStatus({ lawyerIds });
      return response.statuses;
    },
    enabled: lawyerIds.length > 0,
    refetchInterval: 30 * 1000, // 每30秒刷新一次
    staleTime: 10 * 1000, // 10秒缓存
  });
}

/**
 * 获取单个律师在线状态 Hook
 */
export function useLawyerOnlineStatus(lawyerId: string) {
  return useQuery<LawyerOnlineInfo>({
    queryKey: ['lawyers', 'online-status-single', lawyerId] as const,
    queryFn: async () => {
      return apiGetLawyerOnlineStatus(lawyerId);
    },
    enabled: !!lawyerId,
    refetchInterval: 30 * 1000, // 每30秒刷新一次
    staleTime: 10 * 1000, // 10秒缓存
  });
}

// ==================== Combined Hooks ====================

/**
 * 获取律师完整信息（详情 + 评价 + 在线状态）Hook
 */
export function useLawyerFullInfo(lawyerId: string) {
  const { data: detail, isLoading: isDetailLoading } = useLawyerDetail(lawyerId);
  const { data: reviewsData, isLoading: isReviewsLoading } = useLawyerReviews(
    lawyerId,
    { limit: 5, sortBy: 'newest' }
  );
  const { data: onlineInfo, isLoading: isOnlineLoading } = useLawyerOnlineStatus(
    lawyerId
  );

  return {
    lawyer: detail,
    reviews: reviewsData?.reviews ?? [],
    reviewStats: reviewsData?.stats,
    onlineInfo,
    isLoading: isDetailLoading || isReviewsLoading || isOnlineLoading,
  };
}