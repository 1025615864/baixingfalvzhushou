/**
 * Membership（会员系统）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  UserMembership,
  MembershipBenefits,
  ConversionHistoryItem,
  ConversionStats,
  MembershipOrder,
  CreateMembershipOrderRequest,
  GetConversionHistoryRequest,
  UpgradeMembershipRequest,
  CancelMembershipOrderRequest,
} from '../types';
import {
  apiGetMembershipInfo,
  apiGetMembershipLevels,
  apiGetMembershipBenefits,
  apiCreateMembershipOrder,
  apiGetMembershipOrders,
  apiGetConversionHistory,
  apiGetConversionStats,
  apiUpgradeMembership,
  apiCancelMembershipOrder,
} from '../api';

// ==================== Query Keys ====================

const MEMBERSHIP_QUERY_KEYS = {
  membership: ['membership', 'me'] as const,
  levels: ['membership', 'levels'] as const,
  benefits: (tier: string) => ['membership', 'benefits', tier] as const,
  orders: ['membership', 'orders'] as const,
  conversionHistory: (params?: GetConversionHistoryRequest) => ['membership', 'history', params] as const,
  conversionStats: ['membership', 'stats', 'conversions'] as const,
} as const;

// ==================== Membership Hooks ====================

/**
 * 获取当前用户会员信息 Hook
 */
export function useMembershipInfo() {
  return useQuery<UserMembership>({
    queryKey: MEMBERSHIP_QUERY_KEYS.membership,
    queryFn: apiGetMembershipInfo,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 获取所有会员等级列表 Hook
 */
export function useMembershipLevels() {
  return useQuery<MembershipBenefits[]>({
    queryKey: MEMBERSHIP_QUERY_KEYS.levels,
    queryFn: apiGetMembershipLevels,
    staleTime: 30 * 60 * 1000, // 30分钟缓存，等级配置不常变化
  });
}

/**
 * 获取指定等级会员权益 Hook
 */
export function useMembershipBenefits(tier: string) {
  return useQuery<MembershipBenefits>({
    queryKey: MEMBERSHIP_QUERY_KEYS.benefits(tier),
    queryFn: () => apiGetMembershipBenefits(tier),
    enabled: !!tier,
    staleTime: 30 * 60 * 1000, // 30分钟缓存
  });
}

/**
 * 获取会员订单列表 Hook
 */
export function useMembershipOrders() {
  return useQuery<MembershipOrder[]>({
    queryKey: MEMBERSHIP_QUERY_KEYS.orders,
    queryFn: apiGetMembershipOrders,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 创建会员订单 Hook
 */
export function useCreateMembershipOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateMembershipOrderRequest) => apiCreateMembershipOrder(request),
    onSuccess: () => {
      // 创建成功后，刷新订单列表和会员信息
      void queryClient.invalidateQueries({ queryKey: MEMBERSHIP_QUERY_KEYS.orders });
      void queryClient.invalidateQueries({ queryKey: MEMBERSHIP_QUERY_KEYS.membership });
    },
  });
}

/**
 * 升级会员 Hook
 */
export function useUpgradeMembership() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpgradeMembershipRequest) => apiUpgradeMembership(request),
    onSuccess: () => {
      // 升级成功后，刷新会员信息和订单列表
      void queryClient.invalidateQueries({ queryKey: MEMBERSHIP_QUERY_KEYS.membership });
      void queryClient.invalidateQueries({ queryKey: MEMBERSHIP_QUERY_KEYS.orders });
    },
  });
}

/**
 * 取消会员订单 Hook
 */
export function useCancelMembershipOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CancelMembershipOrderRequest) => apiCancelMembershipOrder(request),
    onSuccess: () => {
      // 取消成功后，刷新订单列表
      void queryClient.invalidateQueries({ queryKey: MEMBERSHIP_QUERY_KEYS.orders });
    },
  });
}

// ==================== Conversion Hooks ====================

/**
 * 分页转化历史结果
 */
export interface PaginatedConversionHistory {
  items: ConversionHistoryItem[];
  total: number;
  page: number;
  pageSize: number;
}

/**
 * 获取转化历史 Hook（支持分页）
 */
export function useConversionHistory(params: GetConversionHistoryRequest = {}) {
  return useQuery<PaginatedConversionHistory>({
    queryKey: MEMBERSHIP_QUERY_KEYS.conversionHistory(params),
    queryFn: async () => {
      const response = await apiGetConversionHistory(params);
      return {
        items: response.items,
        total: response.total,
        page: response.page,
        pageSize: response.pageSize,
      };
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 获取转化统计 Hook
 */
export function useConversionStats() {
  return useQuery<ConversionStats>({
    queryKey: MEMBERSHIP_QUERY_KEYS.conversionStats,
    queryFn: () => apiGetConversionStats(30), // 默认30天
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}