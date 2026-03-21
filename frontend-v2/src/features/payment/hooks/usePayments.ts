/**
 * 支付系统 Hooks
 *
 * 使用真实后端API进行数据获取
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  getOrders,
  getOrderDetail,
  createOrder,
  payOrder,
  cancelOrder,
  getBalance,
  getBalanceTransactions,
  getPricing,
  createRefund,
  getRefundDetail,
  getRefunds,
} from '../api';
import type {
  Order,
  PaymentStatus,
  PaymentMethod,
  OrderType,
  CreateOrderRequest,
  CreateOrderResponse,
  PayOrderRequest,
  PayOrderResponse,
  BalanceInfo,
  BalanceTransaction,
  OrderListParams,
  Refund,
  GetRefundsRequest,
} from '../types';

// 状态配置
export const statusConfig: Record<PaymentStatus, { label: string; color: string }> = {
  pending: { label: '待支付', color: 'bg-yellow-100 text-yellow-800' },
  paid: { label: '已支付', color: 'bg-green-100 text-green-800' },
  cancelled: { label: '已取消', color: 'bg-gray-100 text-gray-800' },
  refunded: { label: '已退款', color: 'bg-purple-100 text-purple-800' },
  failed: { label: '支付失败', color: 'bg-red-100 text-red-800' },
};

export const typeNames: Record<OrderType, string> = {
  consultation: '咨询订单',
  service: '服务订单',
  vip: 'VIP会员',
  recharge: '余额充值',
  light_consult_review: '轻咨询审核',
};

/**
 * 获取订单列表 Hook
 */
export function useOrders(params: OrderListParams = {}) {
  return useQuery<Order[]>({
    queryKey: ['orders', params],
    queryFn: async () => {
      const response = await getOrders(params);
      return response.items || [];
    },
  });
}

/**
 * 获取订单详情 Hook
 */
export function useOrderDetail(orderNo: string | undefined) {
  return useQuery<Order>({
    queryKey: ['order', orderNo],
    queryFn: async () => {
      // 类型安全：queryFn只在enabled为true时调用
      const no = orderNo;
      if (!no) throw new Error('orderNo is required');
      return getOrderDetail(no);
    },
    enabled: !!orderNo,
  });
}

/**
 * 获取用户余额 Hook
 */
export function useBalance() {
  return useQuery<BalanceInfo>({
    queryKey: ['balance'],
    queryFn: getBalance,
    staleTime: 30000, // 30秒内不重新请求
  });
}

/**
 * 获取余额交易记录 Hook
 */
export function useBalanceTransactions(page: number = 1, pageSize: number = 20) {
  return useQuery<{ items: BalanceTransaction[]; total: number }>({
    queryKey: ['balance-transactions', page, pageSize],
    queryFn: () => getBalanceTransactions(page, pageSize),
  });
}

/**
 * 获取价格表 Hook
 */
export function usePricing() {
  return useQuery({
    queryKey: ['pricing'],
    queryFn: getPricing,
    staleTime: 300000, // 5分钟内不重新请求
  });
}

/**
 * 创建订单 Hook
 */
export function useCreateOrder() {
  const queryClient = useQueryClient();

  return useMutation<CreateOrderResponse, Error, CreateOrderRequest>({
    mutationFn: createOrder,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}

/**
 * 支付订单 Hook
 */
export function usePayOrder() {
  const queryClient = useQueryClient();

  return useMutation<PayOrderResponse, Error, { orderNo: string; data: PayOrderRequest }>({
    mutationFn: ({ orderNo, data }) => payOrder(orderNo, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['orders'] });
      void queryClient.invalidateQueries({ queryKey: ['balance'] });
      void queryClient.invalidateQueries({ queryKey: ['balance-transactions'] });
    },
  });
}

/**
 * 取消订单 Hook
 */
export function useCancelOrder() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, string>({
    mutationFn: (orderNo) => cancelOrder(orderNo),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}

// ==================== 向后兼容类型和函数 ====================

/** 创建订单DTO（向后兼容） */
export interface CreateOrderDTO {
  title: string;
  description?: string;
  amount: number;
  type: OrderType;
}

/** 钱包余额（向后兼容） */
export interface WalletBalance {
  user_id: string;
  balance: number;
  frozen_balance: number;
  currency: string;
  updated_at: string;
}

/** 交易记录（向后兼容） */
export interface Transaction {
  id: string;
  user_id: string;
  order_id?: string;
  type: 'income' | 'expense';
  amount: number;
  balance: number;
  description: string;
  created_at: string;
}

/**
 * 获取钱包余额 Hook（向后兼容）
 * @deprecated 使用 useBalance 替代
 */
export function useWalletBalance() {
  return useQuery<WalletBalance>({
    queryKey: ['wallet', 'balance'],
    queryFn: async () => {
      const balanceInfo = await getBalance();
      return {
        user_id: '',
        balance: balanceInfo.balance,
        frozen_balance: balanceInfo.frozen,
        currency: 'CNY',
        updated_at: new Date().toISOString(),
      };
    },
    staleTime: 30000,
  });
}

/**
 * 获取交易记录 Hook（向后兼容）
 * @deprecated 使用 useBalanceTransactions 替代
 */
export function useTransactions() {
  return useQuery<Transaction[]>({
    queryKey: ['transactions'],
    queryFn: async () => {
      const result = await getBalanceTransactions(1, 100);
      return result.items.map((item) => ({
        id: String(item.id),
        user_id: '',
        type: item.type === 'recharge' ? 'income' : 'expense' as 'income' | 'expense',
        amount: item.amount,
        balance: item.balance_after,
        description: item.description || '',
        created_at: item.created_at,
      }));
    },
  });
}

/**
 * 申请退款 Hook（向后兼容）
 */
export function useRefundOrder() {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean; refund?: Refund }, Error, { orderNo: string; amount: number; reason?: string }>({
    mutationFn: async ({ orderNo, amount, reason }) => {
      const refund = await createRefund({ orderNo, amount, reason });
      return { success: true, refund };
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['orders'] });
      void queryClient.invalidateQueries({ queryKey: ['balance'] });
      void queryClient.invalidateQueries({ queryKey: ['balance-transactions'] });
      void queryClient.invalidateQueries({ queryKey: ['refunds'] });
    },
  });
}

/**
 * 获取退款列表 Hook
 */
export function useRefunds(params: GetRefundsRequest = {}) {
  return useQuery<{ items: Refund[]; total: number; page: number; pageSize: number }>({
    queryKey: ['refunds', params],
    queryFn: () => getRefunds(params),
  });
}

/**
 * 获取退款详情 Hook
 */
export function useRefundDetail(refundNo: string | undefined) {
  return useQuery<Refund>({
    queryKey: ['refund', refundNo],
    queryFn: async () => {
      // 类型安全：queryFn只在enabled为true时调用
      const no = refundNo;
      if (!no) throw new Error('refundNo is required');
      return getRefundDetail(no);
    },
    enabled: !!refundNo,
  });
}

/**
 * 充值钱包 Hook（向后兼容）
 */
export function useRechargeWallet() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ amount, paymentMethod }: { amount: number; paymentMethod: string }) => {
      // 通过创建充值订单来实现
      const order = await createOrder({
        order_type: 'recharge',
        amount,
        title: '钱包充值',
      });
      // 然后支付订单
      await payOrder(order.order_no, {
        payment_method: paymentMethod as PaymentMethod,
      });
      return { success: true };
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['wallet', 'balance'] });
      void queryClient.invalidateQueries({ queryKey: ['transactions'] });
      void queryClient.invalidateQueries({ queryKey: ['balance'] });
      void queryClient.invalidateQueries({ queryKey: ['balance-transactions'] });
    },
  });
}
