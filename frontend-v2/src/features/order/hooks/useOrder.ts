/**
 * Order（订单管理）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  Order,
  GetOrderListRequest,
  GetOrderListResponse,
  OrderStats,
} from '../types';
import {
  apiGetOrderList,
  apiGetOrderDetail,
  apiCancelOrder,
  apiApplyRefund,
  apiGetOrderStats,
} from '../api';

// ==================== Query Keys ====================

const ORDER_QUERY_KEYS = {
  list: (params?: GetOrderListRequest) => ['order', 'list', params] as const,
  detail: (orderNo: string) => ['order', 'detail', orderNo] as const,
  stats: ['order', 'stats'] as const,
} as const;

// ==================== List Hooks ====================

/**
 * 获取订单列表 Hook
 */
export function useOrderList(params: GetOrderListRequest = {}) {
  return useQuery<GetOrderListResponse>({
    queryKey: ORDER_QUERY_KEYS.list(params),
    queryFn: () => apiGetOrderList(params),
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Detail Hooks ====================

/**
 * 获取订单详情 Hook
 */
export function useOrderDetail(orderNo: string) {
  return useQuery<Order>({
    queryKey: ORDER_QUERY_KEYS.detail(orderNo),
    queryFn: async () => {
      const response = await apiGetOrderDetail({ orderNo });
      return response.order;
    },
    enabled: Boolean(orderNo),
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Mutation Hooks ====================

/**
 * 取消订单 Hook
 */
export function useCancelOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiCancelOrder,
    onSuccess: () => {
      // 取消成功后，刷新订单列表和详情
      void queryClient.invalidateQueries({ queryKey: ['order', 'list'] });
      void queryClient.invalidateQueries({ queryKey: ['order', 'detail'] });
      void queryClient.invalidateQueries({ queryKey: ORDER_QUERY_KEYS.stats });
    },
  });
}

/**
 * 申请退款 Hook
 */
export function useApplyRefund() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiApplyRefund,
    onSuccess: () => {
      // 退款申请成功后，刷新订单列表和详情
      void queryClient.invalidateQueries({ queryKey: ['order', 'list'] });
      void queryClient.invalidateQueries({ queryKey: ['order', 'detail'] });
      void queryClient.invalidateQueries({ queryKey: ORDER_QUERY_KEYS.stats });
    },
  });
}

// ==================== Stats Hooks ====================

/**
 * 获取订单统计 Hook
 */
export function useOrderStats() {
  return useQuery<OrderStats>({
    queryKey: ORDER_QUERY_KEYS.stats,
    queryFn: apiGetOrderStats,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}