/**
 * Membership（会员系统）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/membership 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  UserMembership,
  MembershipBenefits,
  ConversionStats,
  RevenueStats,
  MembershipOrder,
  GetMembershipInfoResponse,
  GetMembershipLevelsResponse,
  GetMembershipBenefitsResponse,
  CreateMembershipOrderRequest,
  CreateMembershipOrderResponse,
  GetConversionHistoryRequest,
  GetConversionHistoryResponse,
  GetConversionStatsResponse,
  GetRevenueStatsResponse,
  GetMembershipOrdersResponse,
  UpgradeMembershipRequest,
  UpgradeMembershipResponse,
  CancelMembershipOrderRequest,
  CancelMembershipOrderResponse,
} from '../types';


// API 基础路径
const API_BASE = '/membership';

// ==================== 后端响应类型定义 ====================

/** 后端历史记录项 */
interface BackendHistoryItem {
  order_no: string;
  order_type: string | null;
  amount: number;
  paid_at: string | null;
}

/** 后端历史记录响应 */
interface BackendHistoryResponse {
  items: BackendHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

// ==================== API 方法 ====================

/**
 * 获取当前用户会员信息
 */
export async function apiGetMembershipInfo(): Promise<UserMembership> {
  const response = await apiClient.get<GetMembershipInfoResponse>(`${API_BASE}/me`);
  return response.data.membership;
}

/**
 * 获取所有会员等级配置
 */
export async function apiGetMembershipLevels(): Promise<MembershipBenefits[]> {
  const response = await apiClient.get<GetMembershipLevelsResponse>(`${API_BASE}/benefits`);
  return response.data.levels;
}

/**
 * 获取指定等级的会员权益
 */
export async function apiGetMembershipBenefits(tier: string): Promise<MembershipBenefits> {
  const response = await apiClient.get<GetMembershipBenefitsResponse>(`${API_BASE}/benefits/${tier}`);
  return response.data.benefits;
}

/**
 * 创建会员订单
 */
export async function apiCreateMembershipOrder(
  request: CreateMembershipOrderRequest
): Promise<CreateMembershipOrderResponse> {
  const response = await apiClient.post<CreateMembershipOrderResponse>(`${API_BASE}/orders`, {
    tier: request.tier,
    duration: request.duration,
    payment_method: request.paymentMethod,
  });
  return response.data;
}

/**
 * 获取会员订单列表
 */
export async function apiGetMembershipOrders(): Promise<MembershipOrder[]> {
  const response = await apiClient.get<GetMembershipOrdersResponse>(`${API_BASE}/orders`);
  return response.data.orders;
}

/**
 * 获取转化历史记录
 */
export async function apiGetConversionHistory(
  params: GetConversionHistoryRequest = {}
): Promise<GetConversionHistoryResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));

  const url = `${API_BASE}/history${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await apiClient.get<BackendHistoryResponse>(url);

  return {
    items: response.data.items.map((item) => ({
      orderNo: item.order_no,
      orderType: item.order_type,
      amount: item.amount,
      paidAt: item.paid_at,
    })),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

/**
 * 获取转化统计
 */
export async function apiGetConversionStats(days: number = 30): Promise<ConversionStats> {
  const response = await apiClient.get<GetConversionStatsResponse>(`${API_BASE}/stats/conversions?days=${days}`);
  return response.data.stats;
}

/**
 * 获取收入统计
 */
export async function apiGetRevenueStats(): Promise<RevenueStats> {
  const response = await apiClient.get<GetRevenueStatsResponse>(`${API_BASE}/stats/revenue`);
  return response.data.stats;
}

/**
 * 升级会员
 */
export async function apiUpgradeMembership(
  request: UpgradeMembershipRequest
): Promise<UpgradeMembershipResponse> {
  const response = await apiClient.post<UpgradeMembershipResponse>(`${API_BASE}/upgrade`, {
    tier: request.tier,
    duration: request.duration,
  });
  return response.data;
}

/**
 * 取消会员订单
 */
export async function apiCancelMembershipOrder(
  request: CancelMembershipOrderRequest
): Promise<CancelMembershipOrderResponse> {
  const response = await apiClient.post<CancelMembershipOrderResponse>(
    `${API_BASE}/orders/${request.orderId}/cancel`
  );
  return response.data;
}