/**
 * 支付系统API封装
 */

import apiClient from "@/shared/lib/api/client";

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
  // 支付回调管理类型
  PaymentCallback,
  GetCallbacksRequest,
  GetCallbacksResponse,
  // 结算统计类型
  GetSettlementStatsRequest,
  GetSettlementStatsResponse,
  // 退款类型
  Refund,
  CreateRefundRequest,
  CreateRefundResponse,
  GetRefundsRequest,
  GetRefundsResponse,
} from '../types';


const PAYMENT_BASE = '/payment';

/**
 * 获取订单列表
 * @param params 查询参数
 * @returns 订单列表响应
 * 注意：修正参数名与后端对齐 - 后端使用 status 而非 status_filter
 */
export async function getOrders(params: OrderListParams = {}): Promise<OrderListResponse> {
  const { page = 1, page_size = 20, status_filter } = params;
  const response = await apiClient.get<OrderListResponse>(`${PAYMENT_BASE}/orders`, {
    params: {
      page,
      page_size,
      ...(status_filter && { status: status_filter }),  // 后端使用 status 参数
    },
  });
  return response.data;
}

/**
 * 获取订单详情
 * @param orderNo 订单号
 * @returns 订单详情
 */
export async function getOrderDetail(orderNo: string): Promise<Order> {
  const response = await apiClient.get<Order>(`${PAYMENT_BASE}/orders/${orderNo}`);
  return response.data;
}

/**
 * 创建订单
 * @param data 创建订单请求数据
 * @returns 创建订单响应
 */
export async function createOrder(data: CreateOrderRequest): Promise<CreateOrderResponse> {
  const response = await apiClient.post<CreateOrderResponse>(`${PAYMENT_BASE}/orders`, data);
  return response.data;
}

/**
 * 支付订单
 * @param orderNo 订单号
 * @param data 支付请求数据
 * @returns 支付响应
 */
export async function payOrder(orderNo: string, data: PayOrderRequest): Promise<PayOrderResponse> {
  const response = await apiClient.post<PayOrderResponse>(`${PAYMENT_BASE}/orders/${orderNo}/pay`, data);
  return response.data;
}

/**
 * 取消订单
 * @param orderNo 订单号
 * @returns 取消结果
 */
export async function cancelOrder(orderNo: string): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>(`${PAYMENT_BASE}/orders/${orderNo}/cancel`);
  return response.data;
}

/**
 * 获取用户余额
 * @returns 余额信息
 */
export async function getBalance(): Promise<BalanceInfo> {
  const response = await apiClient.get<BalanceInfo>(`${PAYMENT_BASE}/balance`);
  return response.data;
}

/**
 * 获取余额交易记录
 * @param page 页码
 * @param pageSize 每页数量
 * @returns 交易记录列表
 */
export async function getBalanceTransactions(
  page: number = 1,
  pageSize: number = 20
): Promise<BalanceTransactionListResponse> {
  const response = await apiClient.get<BalanceTransactionListResponse>(`${PAYMENT_BASE}/balance/transactions`, {
    params: {
      page,
      page_size: pageSize,
    },
  });
  return response.data;
}

/**
 * 获取价格表
 * @returns 价格表信息
 */
export async function getPricing(): Promise<PricingInfo> {
  const response = await apiClient.get<PricingInfo>(`${PAYMENT_BASE}/pricing`);
  return response.data;
}

// ==================== 退款API ====================

/**
 * 申请退款
 * @param data 退款请求数据
 * @returns 退款响应
 */
export async function createRefund(data: CreateRefundRequest): Promise<CreateRefundResponse> {
  const response = await apiClient.post<{
    refund_no: string;
    order_no: string;
    amount: number;
    status: string;
    reason: string | null;
    created_at: string;
  }>(`${PAYMENT_BASE}/refunds`, {
    order_no: data.orderNo,
    amount: data.amount,
    reason: data.reason,
  });

  return {
    refundNo: response.data.refund_no,
    orderNo: response.data.order_no,
    amount: response.data.amount,
    status: response.data.status as Refund['status'],
    reason: response.data.reason,
    createdAt: response.data.created_at,
  };
}

/**
 * 获取退款详情
 * @param refundNo 退款单号
 * @returns 退款详情
 */
export async function getRefundDetail(refundNo: string): Promise<Refund> {
  const response = await apiClient.get<{
    refund_no: string;
    order_no: string;
    amount: number;
    status: string;
    reason: string | null;
    created_at: string;
  }>(`${PAYMENT_BASE}/refunds/${refundNo}`);

  return {
    refundNo: response.data.refund_no,
    orderNo: response.data.order_no,
    amount: response.data.amount,
    status: response.data.status as Refund['status'],
    reason: response.data.reason,
    createdAt: response.data.created_at,
  };
}

/**
 * 获取退款列表
 * @param params 查询参数
 * @returns 退款列表响应
 */
export async function getRefunds(params: GetRefundsRequest = {}): Promise<GetRefundsResponse> {
  const { page = 1, pageSize = 20, status } = params;
  const searchParams = new URLSearchParams();
  searchParams.set('page', String(page));
  searchParams.set('page_size', String(pageSize));
  if (status) searchParams.set('status', status);

  const response = await apiClient.get<{
    items: Array<{
      refund_no: string;
      order_no: string;
      amount: number;
      status: string;
      reason: string | null;
      created_at: string;
    }>;
    total: number;
    page: number;
    page_size: number;
  }>(`${PAYMENT_BASE}/refunds?${searchParams.toString()}`);

  return {
    items: response.data.items.map((item) => ({
      refundNo: item.refund_no,
      orderNo: item.order_no,
      amount: item.amount,
      status: item.status as Refund['status'],
      reason: item.reason,
      createdAt: item.created_at,
    })),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

/**
 * 支付API对象
 */
export const paymentApi = {
  getOrders,
  getOrderDetail,
  createOrder,
  payOrder,
  cancelOrder,
  getBalance,
  getBalanceTransactions,
  getPricing,
  // 退款
  createRefund,
  getRefundDetail,
  getRefunds,
};

export default paymentApi;

// ==================== 支付回调管理API（管理员用） ====================

const API_BASE = '/payment';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
}

/**
 * 安全获取 JSON 响应
 */
async function safeJson<T>(response: Response): Promise<T> {
  const data = await response.json() as T;
  return data;
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
 * 转换回调数据 snake_case → camelCase
 */
function transformCallback(data: {
  id: number;
  order_no: string;
  trade_no?: string | null;
  source: string;
  status: string;
  payload: string;
  response?: string | null;
  retry_count: number;
  max_retries: number;
  next_retry_at?: string | null;
  processed_at?: string | null;
  error_message?: string | null;
  ip_address?: string | null;
  created_at: string;
  updated_at: string;
}): PaymentCallback {
  return {
    id: String(data.id),
    orderNo: data.order_no,
    tradeNo: data.trade_no ?? null,
    source: data.source as 'alipay' | 'wechat' | 'system',
    status: data.status as 'pending' | 'success' | 'failed' | 'retrying',
    payload: data.payload,
    response: data.response ?? null,
    retryCount: data.retry_count,
    maxRetries: data.max_retries,
    nextRetryAt: data.next_retry_at ?? null,
    processedAt: data.processed_at ?? null,
    errorMessage: data.error_message ?? null,
    ipAddress: data.ip_address ?? null,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 获取支付回调列表（管理员用）
 */
export async function apiGetPaymentCallbacks(
  params: GetCallbacksRequest = {}
): Promise<GetCallbacksResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));
  if (params.status) searchParams.set('status', params.status);
  if (params.source) searchParams.set('source', params.source);
  if (params.orderNo) searchParams.set('order_no', params.orderNo);
  if (params.fromTime) searchParams.set('from_time', params.fromTime);
  if (params.toTime) searchParams.set('to_time', params.toTime);

  const response = await apiClient.get<{
    items: Array<{
      id: number;
      order_no: string;
      trade_no?: string | null;
      source: string;
      status: string;
      payload: string;
      response?: string | null;
      retry_count: number;
      max_retries: number;
      next_retry_at?: string | null;
      processed_at?: string | null;
      error_message?: string | null;
      ip_address?: string | null;
      created_at: string;
      updated_at: string;
    }>;
    total: number;
    page: number;
    page_size: number;
    stats: {
      total_count: number;
      pending_count: number;
      success_count: number;
      failed_count: number;
      retrying_count: number;
      today_count: number;
      today_success_count: number;
    };
  }>(`${API_BASE}/admin/payment/callbacks?${searchParams.toString()}`);

  const data = response.data;

  return {
    items: (data.items ?? []).map(transformCallback),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    stats: {
      totalCount: data.stats.total_count,
      pendingCount: data.stats.pending_count,
      successCount: data.stats.success_count,
      failedCount: data.stats.failed_count,
      retryingCount: data.stats.retrying_count,
      todayCount: data.stats.today_count,
      todaySuccessCount: data.stats.today_success_count,
    },
  };
}

/**
 * 重试支付回调（管理员用）
 */
export async function apiRetryPaymentCallback(id: string): Promise<PaymentCallback> {
  const response = await apiClient.post<{
    id: number;
    order_no: string;
    trade_no?: string | null;
    source: string;
    status: string;
    payload: string;
    response?: string | null;
    retry_count: number;
    max_retries: number;
    next_retry_at?: string | null;
    processed_at?: string | null;
    error_message?: string | null;
    ip_address?: string | null;
    created_at: string;
    updated_at: string;
  }>(`${API_BASE}/admin/payment/callbacks/${id}/retry`, {});

  return transformCallback(response.data);
}

// ==================== 结算统计API（管理员用） ====================

/**
 * 获取结算统计（管理员用）
 */
export async function apiGetSettlementStats(
  params: GetSettlementStatsRequest
): Promise<GetSettlementStatsResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set('start_date', params.startDate);
  searchParams.set('end_date', params.endDate);
  if (params.groupBy) searchParams.set('group_by', params.groupBy);

  const response = await apiClient.get<{
    items: Array<{
      date: string;
      total_amount: number;
      total_count: number;
      success_amount: number;
      success_count: number;
      refund_amount: number;
      refund_count: number;
      fee_amount: number;
      net_amount: number;
    }>;
    summary: {
      total_amount: number;
      total_count: number;
      success_amount: number;
      success_count: number;
      refund_amount: number;
      refund_count: number;
      fee_amount: number;
      net_amount: number;
      average_order_value: number;
      success_rate: number;
    };
    method_stats: Array<{
      method: string;
      amount: number;
      count: number;
      percentage: number;
    }>;
    trend: {
      dates: string[];
      amounts: number[];
      counts: number[];
    };
  }>(`${API_BASE}/admin/payment/settlement-stats?${searchParams.toString()}`);

  const data = response.data;

  return {
    items: (data.items ?? []).map((item) => ({
      date: item.date,
      totalAmount: item.total_amount,
      totalCount: item.total_count,
      successAmount: item.success_amount,
      successCount: item.success_count,
      refundAmount: item.refund_amount,
      refundCount: item.refund_count,
      feeAmount: item.fee_amount,
      netAmount: item.net_amount,
    })),
    summary: {
      totalAmount: data.summary.total_amount,
      totalCount: data.summary.total_count,
      successAmount: data.summary.success_amount,
      successCount: data.summary.success_count,
      refundAmount: data.summary.refund_amount,
      refundCount: data.summary.refund_count,
      feeAmount: data.summary.fee_amount,
      netAmount: data.summary.net_amount,
      averageOrderValue: data.summary.average_order_value,
      successRate: data.summary.success_rate,
    },
    methodStats: (data.method_stats ?? []).map((item) => ({
      method: item.method,
      amount: item.amount,
      count: item.count,
      percentage: item.percentage,
    })),
    trend: {
      dates: data.trend.dates,
      amounts: data.trend.amounts,
      counts: data.trend.counts,
    },
  };
}

/**
 * 导出结算报表（管理员用）
 */
export async function apiExportSettlementReport(
  params: { startDate: string; endDate: string; format?: 'csv' | 'excel' }
): Promise<Blob> {
  const searchParams = new URLSearchParams();
  searchParams.set('start_date', params.startDate);
  searchParams.set('end_date', params.endDate);
  if (params.format) searchParams.set('format', params.format);

  const response = await fetch(`${API_BASE}/admin/payment/settlement-report?${searchParams.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '导出结算报表失败' }));
    throw new Error(getErrorMessage(error, '导出结算报表失败'));
  }

  return response.blob();
}

/**
 * 手动处理支付回调（管理员用）
 */
export async function apiProcessPaymentCallback(
  id: string,
  success: boolean,
  note?: string
): Promise<PaymentCallback> {
  const response = await apiClient.post<{
    id: number;
    order_no: string;
    trade_no?: string | null;
    source: string;
    status: string;
    payload: string;
    response?: string | null;
    retry_count: number;
    max_retries: number;
    next_retry_at?: string | null;
    processed_at?: string | null;
    error_message?: string | null;
    ip_address?: string | null;
    created_at: string;
    updated_at: string;
  }>(`${API_BASE}/admin/payment/callbacks/${id}/process`, {
    success,
    note,
  });

  return transformCallback(response.data);
}