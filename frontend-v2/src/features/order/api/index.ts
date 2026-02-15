/**
 * Order（订单管理）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/payment 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  Order,
  GetOrderListRequest,
  GetOrderListResponse,
  GetOrderDetailRequest,
  GetOrderDetailResponse,
  CancelOrderRequest,
  CancelOrderResponse,
  ApplyRefundRequest,
  ApplyRefundResponse,
  OrderStats,
} from '../types';


// API 基础路径
const API_BASE = '/payment';

// ==================== 后端响应类型定义 ====================

/** 后端订单响应 */
interface BackendOrderResponse {
  id: number;
  order_no: string;
  order_type: string;
  amount: number;
  actual_amount: number;
  status: string;
  payment_method: string | null;
  title: string;
  created_at: string;
  paid_at: string | null;
}

/** 后端订单列表响应 */
interface BackendOrderListResponse {
  items: BackendOrderResponse[];
  total: number;
}

/** 后端退款响应 */
interface BackendRefundResponse {
  success: boolean;
  message: string;
  refund_id?: string;
  refund_amount?: number;
}

/** 后端订单统计响应 */
interface BackendOrderStatsResponse {
  total_orders: number;
  total_amount: number;
  pending_count: number;
  completed_count: number;
  cancelled_count: number;
}

// ==================== 转换函数 ====================

/**
 * 转换后端订单到前端格式
 */
function mapBackendToOrder(data: BackendOrderResponse): Order {
  return {
    id: data.id,
    orderNo: data.order_no,
    orderType: data.order_type as Order['orderType'],
    amount: data.amount,
    actualAmount: data.actual_amount,
    status: data.status as Order['status'],
    paymentMethod: data.payment_method as Order['paymentMethod'],
    title: data.title,
    createdAt: data.created_at,
    paidAt: data.paid_at,
  };
}

// ==================== API 方法 ====================

/**
 * 订单相关 API
 */
export const orderApi = {
  /**
   * 获取订单列表
   * @param params - 查询参数
   * @returns 订单列表响应
   */
  getOrderList: async (
    params: GetOrderListRequest = {}
  ): Promise<GetOrderListResponse> => {
    const { page = 1, pageSize = 20, status } = params;

    const queryParams = new URLSearchParams();
    queryParams.append('page', String(page));
    queryParams.append('page_size', String(pageSize));

    if (status) {
      queryParams.append('status_filter', status);
    }

    const url = `${API_BASE}/orders?${queryParams.toString()}`;
    const response = await apiClient.get<BackendOrderListResponse>(url);

    const total = response.data.total;
    const totalPages = Math.ceil(total / pageSize);

    return {
      items: response.data.items.map(mapBackendToOrder),
      total,
      page,
      pageSize,
      totalPages,
    };
  },

  /**
   * 获取订单详情
   * @param request - 请求参数
   * @returns 订单详情响应
   */
  getOrderDetail: async (
    request: GetOrderDetailRequest
  ): Promise<GetOrderDetailResponse> => {
    const response = await apiClient.get<BackendOrderResponse>(
      `${API_BASE}/orders/${request.orderNo}`
    );

    return {
      order: mapBackendToOrder(response.data),
    };
  },

  /**
   * 取消订单
   * @param request - 请求参数
   * @returns 取消订单响应
   */
  cancelOrder: async (
    request: CancelOrderRequest
  ): Promise<CancelOrderResponse> => {
    const response = await apiClient.post<{ message: string }>(
      `${API_BASE}/orders/${request.orderNo}/cancel`
    );

    return {
      success: true,
      message: response.data.message,
    };
  },

  /**
   * 申请退款
   * @param request - 请求参数
   * @returns 申请退款响应
   */
  applyRefund: async (
    request: ApplyRefundRequest
  ): Promise<ApplyRefundResponse> => {
    const response = await apiClient.post<BackendRefundResponse>(
      `${API_BASE}/orders/${request.orderNo}/refund`,
      {
        reason: request.reason,
        amount: request.amount,
      }
    );

    return {
      success: response.data.success,
      message: response.data.message,
      refundId: response.data.refund_id,
      refundAmount: response.data.refund_amount,
    };
  },

  /**
   * 获取订单统计
   * @returns 订单统计数据
   */
  getOrderStats: async (): Promise<OrderStats> => {
    const response = await apiClient.get<BackendOrderStatsResponse>(
      `${API_BASE}/orders/stats`
    );

    return {
      totalOrders: response.data.total_orders,
      totalAmount: response.data.total_amount,
      pendingCount: response.data.pending_count,
      completedCount: response.data.completed_count,
      cancelledCount: response.data.cancelled_count,
    };
  },
};

// 默认导出
export default orderApi;

// ==================== 独立函数导出 ====================

export async function apiGetOrderList(params: GetOrderListRequest = {}): Promise<GetOrderListResponse> {
  return orderApi.getOrderList(params);
}

export async function apiGetOrderDetail(request: GetOrderDetailRequest): Promise<GetOrderDetailResponse> {
  return orderApi.getOrderDetail(request);
}

export async function apiCancelOrder(request: CancelOrderRequest): Promise<CancelOrderResponse> {
  return orderApi.cancelOrder(request);
}

export async function apiApplyRefund(request: ApplyRefundRequest): Promise<ApplyRefundResponse> {
  return orderApi.applyRefund(request);
}

export async function apiGetOrderStats(): Promise<OrderStats> {
  return orderApi.getOrderStats();
}