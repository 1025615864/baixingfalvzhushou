/**
 * 支付系统 React Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useEffect, useRef } from 'react';

import { paymentApi } from '../api';
import type {
  Order,
  OrderListResponse,
  CreateOrderRequest,
  CreateOrderResponse,
  PayOrderRequest,
  PayOrderResponse,
  BalanceInfo,
  BalanceTransactionListResponse,
  PricingInfo,
  OrderListParams,
  PaymentStatus,
  PaymentPollingStatus,
} from '../types';

// Query Keys
export const paymentQueryKeys = {
  all: ['payment'] as const,
  orders: () => [...paymentQueryKeys.all, 'orders'] as const,
  orderList: (params: OrderListParams) => [...paymentQueryKeys.orders(), 'list', params] as const,
  orderDetail: (orderNo: string) => [...paymentQueryKeys.orders(), 'detail', orderNo] as const,
  balance: () => [...paymentQueryKeys.all, 'balance'] as const,
  transactions: () => [...paymentQueryKeys.all, 'transactions'] as const,
  transactionList: (page: number, pageSize: number) => 
    [...paymentQueryKeys.transactions(), 'list', page, pageSize] as const,
  pricing: () => [...paymentQueryKeys.all, 'pricing'] as const,
};

/**
 * 获取订单列表
 * @param params 查询参数
 */
export function useOrderList(params: OrderListParams = {}) {
  return useQuery<OrderListResponse, Error>({
    queryKey: paymentQueryKeys.orderList(params),
    queryFn: () => paymentApi.getOrders(params),
    staleTime: 1000 * 30, // 30秒
  });
}

/**
 * 获取订单详情
 * @param orderNo 订单号
 * @param enabled 是否启用查询
 */
export function useOrderDetail(orderNo: string, enabled: boolean = true) {
  return useQuery<Order, Error>({
    queryKey: paymentQueryKeys.orderDetail(orderNo),
    queryFn: () => paymentApi.getOrderDetail(orderNo),
    enabled: enabled && !!orderNo,
    staleTime: 1000 * 10, // 10秒
  });
}

/**
 * 创建订单
 */
export function useCreateOrder() {
  const queryClient = useQueryClient();

  return useMutation<CreateOrderResponse, Error, CreateOrderRequest>({
    mutationFn: paymentApi.createOrder,
    onSuccess: () => {
      // 创建成功后刷新订单列表
      void queryClient.invalidateQueries({ queryKey: paymentQueryKeys.orders() });
      void queryClient.invalidateQueries({ queryKey: paymentQueryKeys.balance() });
    },
  });
}

/**
 * 支付订单
 */
export function usePayOrder() {
  const queryClient = useQueryClient();

  return useMutation<PayOrderResponse, Error, { orderNo: string; data: PayOrderRequest }>({
    mutationFn: ({ orderNo, data }) => paymentApi.payOrder(orderNo, data),
    onSuccess: (_, variables) => {
      // 支付成功后刷新相关数据
      void queryClient.invalidateQueries({ queryKey: paymentQueryKeys.orderDetail(variables.orderNo) });
      void queryClient.invalidateQueries({ queryKey: paymentQueryKeys.orders() });
      void queryClient.invalidateQueries({ queryKey: paymentQueryKeys.balance() });
      void queryClient.invalidateQueries({ queryKey: paymentQueryKeys.transactions() });
    },
  });
}

/**
 * 取消订单
 */
export function useCancelOrder() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, string>({
    mutationFn: paymentApi.cancelOrder,
    onSuccess: () => {
      // 取消成功后刷新订单列表
      void queryClient.invalidateQueries({ queryKey: paymentQueryKeys.orders() });
    },
  });
}

/**
 * 获取余额信息
 */
export function useBalance() {
  return useQuery<BalanceInfo, Error>({
    queryKey: paymentQueryKeys.balance(),
    queryFn: paymentApi.getBalance,
    staleTime: 1000 * 30, // 30秒
  });
}

/**
 * 获取余额交易记录
 * @param page 页码
 * @param pageSize 每页数量
 */
export function useBalanceTransactions(page: number = 1, pageSize: number = 20) {
  return useQuery<BalanceTransactionListResponse, Error>({
    queryKey: paymentQueryKeys.transactionList(page, pageSize),
    queryFn: () => paymentApi.getBalanceTransactions(page, pageSize),
    staleTime: 1000 * 60, // 60秒
  });
}

/**
 * 获取价格表
 */
export function usePricing() {
  return useQuery<PricingInfo, Error>({
    queryKey: paymentQueryKeys.pricing(),
    queryFn: paymentApi.getPricing,
    staleTime: 1000 * 60 * 5, // 5分钟
  });
}

/**
 * 支付状态轮询 Hook
 * @param orderNo 订单号
 * @param initialStatus 初始状态
 * @param onSuccess 支付成功回调
 * @param onFailure 支付失败回调
 * @param maxAttempts 最大轮询次数，默认60次（约2分钟）
 * @param interval 轮询间隔，默认2秒
 */
export function usePaymentPolling(
  orderNo: string | null,
  initialStatus: PaymentStatus = 'pending',
  onSuccess?: () => void,
  onFailure?: (error: Error) => void,
  maxAttempts: number = 60,
  interval: number = 2000
) {
  const [pollingStatus, setPollingStatus] = useState<PaymentPollingStatus>(
    initialStatus === 'paid' ? 'success' : 'polling'
  );
  const [attempts, setAttempts] = useState(0);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const queryClient = useQueryClient();

  const startPolling = useCallback(() => {
    if (!orderNo || initialStatus === 'paid') {
      setPollingStatus('success');
      return;
    }

    setPollingStatus('polling');
    setAttempts(0);

    // 定义轮询函数，但不返回 Promise
    const poll = (): void => {
      void (async () => {
        try {
          const order = await paymentApi.getOrderDetail(orderNo);
          
          if (order.status === 'paid') {
            setPollingStatus('success');
            if (pollingRef.current) {
              clearInterval(pollingRef.current);
              pollingRef.current = null;
            }
            // 刷新相关数据
            void queryClient.invalidateQueries({ queryKey: paymentQueryKeys.orderDetail(orderNo) });
            void queryClient.invalidateQueries({ queryKey: paymentQueryKeys.orders() });
            void queryClient.invalidateQueries({ queryKey: paymentQueryKeys.balance() });
            onSuccess?.();
            return;
          }

          if (order.status === 'failed' || order.status === 'cancelled') {
            setPollingStatus('failed');
            if (pollingRef.current) {
              clearInterval(pollingRef.current);
              pollingRef.current = null;
            }
            onFailure?.(new Error(`订单状态: ${order.status}`));
            return;
          }

          setAttempts((prev) => {
            const newAttempts = prev + 1;
            if (newAttempts >= maxAttempts) {
              setPollingStatus('timeout');
              if (pollingRef.current) {
                clearInterval(pollingRef.current);
                pollingRef.current = null;
              }
              onFailure?.(new Error('支付超时'));
            }
            return newAttempts;
          });
        } catch (error) {
          setPollingStatus('failed');
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          onFailure?.(error instanceof Error ? error : new Error('查询失败'));
        }
      })();
    };

    // 立即执行一次
    poll();

    // 设置轮询
    pollingRef.current = setInterval(poll, interval);
  }, [orderNo, initialStatus, maxAttempts, interval, onSuccess, onFailure, queryClient]);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    setPollingStatus('polling');
    setAttempts(0);
  }, []);

  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  return {
    pollingStatus,
    attempts,
    startPolling,
    stopPolling,
  };
}

/**
 * 支付流程 Hook
 * 封装完整的支付流程：创建订单 -> 选择支付方式 -> 支付 -> 轮询状态
 */
export function usePaymentFlow() {
  const [currentOrder, setCurrentOrder] = useState<CreateOrderResponse | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<string | null>(null);
  const [payUrl, setPayUrl] = useState<string | null>(null);
  
  const createOrderMutation = useCreateOrder();
  const payOrderMutation = usePayOrder();
  const cancelOrderMutation = useCancelOrder();

  const {
    pollingStatus,
    startPolling,
    stopPolling,
  } = usePaymentPolling(
    currentOrder?.order_no ?? null,
    'pending',
    () => {
      // 支付成功
      setCurrentOrder(null);
      setPaymentMethod(null);
      setPayUrl(null);
    },
    () => {
      // 支付失败
      setPayUrl(null);
    }
  );

  const createOrder = useCallback(async (data: CreateOrderRequest) => {
    const result = await createOrderMutation.mutateAsync(data);
    setCurrentOrder(result);
    return result;
  }, [createOrderMutation]);

  const payOrder = useCallback(async (method: string) => {
    if (!currentOrder) {
      throw new Error('没有待支付的订单');
    }

    const result = await payOrderMutation.mutateAsync({
      orderNo: currentOrder.order_no,
      data: { payment_method: method as PayOrderRequest['payment_method'] },
    });

    setPaymentMethod(method);
    
    if (result.pay_url) {
      setPayUrl(result.pay_url);
    }

    // 开始轮询支付状态
    startPolling();

    return result;
  }, [currentOrder, payOrderMutation, startPolling]);

  const cancelOrder = useCallback(async () => {
    if (!currentOrder) {
      return;
    }

    await cancelOrderMutation.mutateAsync(currentOrder.order_no);
    setCurrentOrder(null);
    setPaymentMethod(null);
    setPayUrl(null);
    stopPolling();
  }, [currentOrder, cancelOrderMutation, stopPolling]);

  const reset = useCallback(() => {
    setCurrentOrder(null);
    setPaymentMethod(null);
    setPayUrl(null);
    stopPolling();
  }, [stopPolling]);

  return {
    // 状态
    currentOrder,
    paymentMethod,
    payUrl,
    pollingStatus,
    
    // 操作
    createOrder,
    payOrder,
    cancelOrder,
    reset,
    
    // Mutation 状态
    isCreating: createOrderMutation.isPending,
    isPaying: payOrderMutation.isPending,
    isCancelling: cancelOrderMutation.isPending,
    createError: createOrderMutation.error,
    payError: payOrderMutation.error,
  };
}