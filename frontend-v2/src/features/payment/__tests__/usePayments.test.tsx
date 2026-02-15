// ============================================
// usePayments Hook 测试
// ============================================

import { vi, type Mock } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as React from 'react';

import {
  useOrders,
  useWalletBalance,
  useTransactions,
  useCreateOrder,
  usePayOrder,
  useCancelOrder,
  useRefundOrder,
  useRechargeWallet,
  statusConfig,
  typeNames,
} from '../hooks/usePayments';

// 创建测试用的 QueryClient
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// 创建包装器
function createWrapper() {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
}

describe('usePayments Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============================================
  // useOrders 测试
  // ============================================
  describe('useOrders', () => {
    it('应该成功获取订单列表', async () => {
      const { result } = renderHook(() => useOrders(), {
        wrapper: createWrapper(),
      });

      // 初始状态应该是 loading
      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 验证返回的订单数据
      expect(result.current.data).toBeDefined();
      expect(Array.isArray(result.current.data)).toBe(true);
      expect(result.current.data?.length).toBeGreaterThan(0);
    });

    it('订单数据应该包含必要的字段', async () => {
      const { result } = renderHook(() => useOrders(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const order = result.current.data?.[0];
      expect(order).toHaveProperty('id');
      expect(order).toHaveProperty('order_no');
      expect(order).toHaveProperty('order_type');
      expect(order).toHaveProperty('amount');
      expect(order).toHaveProperty('status');
      expect(order).toHaveProperty('title');
      expect(order).toHaveProperty('created_at');
    });

    it('订单应该按创建时间降序排列', async () => {
      const { result } = renderHook(() => useOrders(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const orders = result.current.data || [];
      for (let i = 0; i < orders.length - 1; i++) {
        const current = new Date(orders[i].created_at).getTime();
        const next = new Date(orders[i + 1].created_at).getTime();
        expect(current).toBeGreaterThanOrEqual(next);
      }
    });
  });

  // ============================================
  // useWalletBalance 测试
  // ============================================
  describe('useWalletBalance', () => {
    it('应该成功获取钱包余额', async () => {
      const { result } = renderHook(() => useWalletBalance(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data).toHaveProperty('balance');
      expect(result.current.data).toHaveProperty('currency');
      expect(result.current.data?.currency).toBe('CNY');
    });

    it('余额应该是非负数', async () => {
      const { result } = renderHook(() => useWalletBalance(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.balance).toBeGreaterThanOrEqual(0);
    });
  });

  // ============================================
  // useTransactions 测试
  // ============================================
  describe('useTransactions', () => {
    it('应该成功获取交易记录', async () => {
      const { result } = renderHook(() => useTransactions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(Array.isArray(result.current.data)).toBe(true);
    });

    it('交易记录应该包含必要字段', async () => {
      const { result } = renderHook(() => useTransactions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const transaction = result.current.data?.[0];
      if (transaction) {
        expect(transaction).toHaveProperty('id');
        expect(transaction).toHaveProperty('type');
        expect(transaction).toHaveProperty('amount');
        expect(transaction).toHaveProperty('description');
        expect(transaction).toHaveProperty('created_at');
        expect(['income', 'expense']).toContain(transaction.type);
      }
    });
  });

  // ============================================
  // useCreateOrder 测试
  // ============================================
  describe('useCreateOrder', () => {
    it('应该成功创建订单', async () => {
      const { result } = renderHook(() => useCreateOrder(), {
        wrapper: createWrapper(),
      });

      const orderData = {
        title: '测试订单',
        description: '这是一个测试订单',
        amount: 100,
        type: 'consultation' as const,
      };

      await act(async () => {
        result.current.mutate(orderData);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.title).toBe(orderData.title);
      expect(result.current.data?.amount).toBe(orderData.amount);
      expect(result.current.data?.status).toBe('pending');
    });

    it('创建的订单应该生成订单号', async () => {
      const { result } = renderHook(() => useCreateOrder(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({
          title: '测试订单',
          amount: 100,
          type: 'service',
        });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.order_no).toBeDefined();
      expect(result.current.data?.order_no).toMatch(/^ORD/);
    });
  });

  // ============================================
  // usePayOrder 测试
  // ============================================
  describe('usePayOrder', () => {
    it('应该成功支付订单', async () => {
      const { result } = renderHook(() => usePayOrder(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({
          orderId: 1,
          paymentMethod: 'wechat',
        });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.success).toBe(true);
    });
  });

  // ============================================
  // useCancelOrder 测试
  // ============================================
  describe('useCancelOrder', () => {
    it('应该成功取消订单', async () => {
      const { result } = renderHook(() => useCancelOrder(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate(3);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.success).toBe(true);
    });
  });

  // ============================================
  // useRefundOrder 测试
  // ============================================
  describe('useRefundOrder', () => {
    it('应该成功申请退款', async () => {
      const { result } = renderHook(() => useRefundOrder(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({
          orderId: 1,
          reason: '不需要了',
        });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.success).toBe(true);
    });
  });

  // ============================================
  // useRechargeWallet 测试
  // ============================================
  describe('useRechargeWallet', () => {
    it('应该成功充值钱包', async () => {
      const { result } = renderHook(() => useRechargeWallet(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({
          amount: 100,
          paymentMethod: 'wechat',
        });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      }, { timeout: 3000 });

      expect(result.current.data?.success).toBe(true);
    });
  });

  // ============================================
  // 配置常量测试
  // ============================================
  describe('配置常量', () => {
    it('statusConfig 应该包含所有状态', () => {
      const statuses: Array<keyof typeof statusConfig> = [
        'pending',
        'paid',
        'cancelled',
        'refunded',
        'failed',
      ];

      statuses.forEach((status) => {
        expect(statusConfig[status]).toBeDefined();
        expect(statusConfig[status]).toHaveProperty('label');
        expect(statusConfig[status]).toHaveProperty('color');
      });
    });

    it('typeNames 应该包含所有订单类型', () => {
      const types: Array<keyof typeof typeNames> = [
        'consultation',
        'service',
        'vip',
        'recharge',
        'light_consult_review',
      ];

      types.forEach((type) => {
        expect(typeNames[type]).toBeDefined();
        expect(typeof typeNames[type]).toBe('string');
      });
    });

    it('状态标签应该是中文', () => {
      expect(statusConfig.pending.label).toBe('待支付');
      expect(statusConfig.paid.label).toBe('已支付');
      expect(statusConfig.cancelled.label).toBe('已取消');
      expect(statusConfig.refunded.label).toBe('已退款');
      expect(statusConfig.failed.label).toBe('支付失败');
    });

    it('订单类型名称应该是中文', () => {
      expect(typeNames.consultation).toBe('咨询订单');
      expect(typeNames.service).toBe('服务订单');
      expect(typeNames.vip).toBe('VIP会员');
      expect(typeNames.recharge).toBe('余额充值');
    });
  });
});
