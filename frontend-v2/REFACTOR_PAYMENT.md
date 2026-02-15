# Payment 模块重构计划

## 1. 设计目标

借鉴旧前端 `frontend/src/features/payment` 的完整功能，按照新前端架构规范重构。

## 2. 核心功能

- [ ] 订单管理（创建、支付、取消）
- [ ] 余额查询
- [ ] 交易记录
- [ ] 银行卡管理

## 3. API 设计

```typescript
// features/payment/api/index.ts
import { api } from '@/shared/lib/api/client';
import type { PaymentOrder, CreateOrderRequest } from '../types';

// 订单相关
export const getOrders = (params?: { page?: number; status_filter?: string }) =>
  api.get<PaymentOrder[]>('/payment/orders', { params });

export const getOrderDetail = (orderNo: string) =>
  api.get<PaymentOrder>(`/payment/orders/${orderNo}`);

export const createOrder = (data: CreateOrderRequest) =>
  api.post<PaymentOrder>('/payment/orders', data);

export const payOrder = (orderNo: string, data: { payment_method: string }) =>
  api.post(`/payment/orders/${orderNo}/pay`, data);

export const cancelOrder = (orderNo: string) =>
  api.post(`/payment/orders/${orderNo}/cancel`);

// 余额相关
export const getBalance = () =>
  api.get<{ balance: number }>('/payment/balance');

export const getTransactions = (params?: { page?: number; page_size?: number }) =>
  api.get<Transaction[]>('/payment/transactions', { params });
```

## 4. Hooks 设计

```typescript
// features/payment/hooks/usePaymentOrders.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentApi } from '../api';

const paymentQueryKeys = {
  all: ['payment'] as const,
  orders: (params) => [...paymentQueryKeys.all, 'orders', params] as const,
  orderDetail: (orderNo: string) => [...paymentQueryKeys.all, 'order', orderNo] as const,
  balance: () => [...paymentQueryKeys.all, 'balance'] as const,
  transactions: (params) => [...paymentQueryKeys.all, 'transactions', params] as const,
};

export function usePaymentOrders(params?: { page?: number; status_filter?: string }) {
  return useQuery({
    queryKey: paymentQueryKeys.orders(params),
    queryFn: () => paymentApi.getOrders(params),
    staleTime: 30 * 1000,
  });
}

export function usePaymentOrderDetail(orderNo: string) {
  return useQuery({
    queryKey: paymentQueryKeys.orderDetail(orderNo),
    queryFn: () => paymentApi.getOrderDetail(orderNo),
    enabled: !!orderNo,
    staleTime: 5 * 60 * 1000,
  });
}

export function usePaymentBalance() {
  return useQuery({
    queryKey: paymentQueryKeys.balance(),
    queryFn: () => paymentApi.getBalance(),
    staleTime: 60 * 1000,
  });
}

export function useCreatePaymentOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateOrderRequest) => paymentApi.createOrder(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: paymentQueryKeys.orders() });
    },
  });
}

export function usePayOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ orderNo, data }: { orderNo: string; data: { payment_method: string } }) =>
      paymentApi.payOrder(orderNo, data),
    onSuccess: (_, { orderNo }) => {
      queryClient.invalidateQueries({ queryKey: paymentQueryKeys.orderDetail(orderNo) });
      queryClient.invalidateQueries({ queryKey: paymentQueryKeys.orders() });
    },
  });
}
```

## 5. 类型定义

```typescript
// features/payment/types/index.ts
export interface PaymentOrder {
  id: number;
  order_no: string;
  order_type: string;
  amount: number;
  status: 'pending' | 'paid' | 'cancelled' | 'refunded';
  payment_method?: string;
  created_at: string;
  paid_at?: string;
}

export interface CreateOrderRequest {
  order_type: string;
  amount: number;
  title: string;
}

export interface Transaction {
  id: number;
  type: 'income' | 'expense';
  amount: number;
  balance: number;
  description: string;
  created_at: string;
}
```

## 6. 任务清单

- [ ] 创建 features/payment/api/index.ts
- [ ] 创建 features/payment/hooks/usePaymentOrders.ts
- [ ] 创建 features/payment/hooks/usePaymentBalance.ts
- [ ] 创建 features/payment/types/index.ts
- [ ] 创建 features/payment/index.ts (barrel export)
- [ ] 添加单元测试
- [ ] ESLint 检查通过
