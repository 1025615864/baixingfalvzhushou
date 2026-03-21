/**
 * Membership（会员系统）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/membership 端点
 
 会员等级体系：
 - free: 免费用户
 - monthly: 月度会员 ¥29/月
 - annual: 年度会员 ¥299/年 (享8.6折)
 - lifetime: 终身会员 ¥999 (一次购买终身权益)
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  UserMembership,
  MembershipPricing,
  MembershipBenefits,
  MembershipOrder,
  CreateMembershipOrderRequest,
  CreateMembershipOrderResponse,
  GetConversionHistoryRequest,
  GetConversionHistoryResponse,
  ConversionStats,
  UpgradeMembershipRequest,
  UpgradeMembershipResponse,
  CancelMembershipOrderRequest,
  CancelMembershipOrderResponse,
} from '../types';


// API 基础路径
const API_BASE = '/membership';

// ==================== 后端响应类型定义 ====================

/** 后端会员详细信息 */
interface BackendMembershipDetail {
  user_id: number;
  level: string;
  level_name: string;
  start_date: string | null;
  end_date: string | null;
  auto_renew: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  benefits: MembershipBenefits | null;
  is_vip: boolean;
}

/** 后端价格配置 */
interface _BackendPricing {
  tier: string;
  name: string;
  monthly_price: number;
  annual_price: number;
  annual_discount: number;
  lifetime_price: number;
  savings_annual: number;
}

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

/** 创建订单响应 */
interface BackendCreateOrderResponse {
  order_no: string;
  amount: number;
  payment_url: string | null;
}

/** 升级响应 */
interface BackendUpgradeResponse {
  success: boolean;
  order_no: string;
  payment_url: string | null;
}

// ==================== API 方法 ====================

/**
 * 获取会员价格配置
 */
export async function apiGetMembershipPricing(): Promise<MembershipPricing[]> {
  const response = await apiClient.get<{ tier: string; name: string; monthly_price: number; annual_price: number; annual_discount: number; lifetime_price: number; savings_annual: number }[]>(`${API_BASE}/pricing`);
  return response.data.map((item) => ({
    tier: item.tier as MembershipPricing['tier'],
    name: item.name,
    monthlyPrice: item.monthly_price,
    annualPrice: item.annual_price,
    annualDiscount: item.annual_discount,
    lifetimePrice: item.lifetime_price,
    savingsAnnual: item.savings_annual,
  }));
}

/**
 * 获取当前用户会员信息
 */
export async function apiGetMembershipInfo(): Promise<UserMembership> {
  const response = await apiClient.get<BackendMembershipDetail>(`${API_BASE}/me`);
  return {
    userId: response.data.user_id,
    level: response.data.level as UserMembership['level'],
    levelName: response.data.level_name,
    startDate: response.data.start_date,
    endDate: response.data.end_date,
    autoRenew: response.data.auto_renew,
    isActive: response.data.is_active,
    createdAt: response.data.created_at,
    updatedAt: response.data.updated_at,
    benefits: response.data.benefits,
    isVip: response.data.is_vip,
  };
}

/**
 * 获取所有会员等级配置
 */
export async function apiGetMembershipLevels(): Promise<MembershipBenefits[]> {
  const response = await apiClient.get<MembershipBenefits[]>(`${API_BASE}/benefits`);
  return response.data;
}

/**
 * 获取指定等级的会员权益
 */
export async function apiGetMembershipBenefits(tier: string): Promise<MembershipBenefits> {
  const response = await apiClient.get<MembershipBenefits>(`${API_BASE}/benefits/${tier}`);
  return response.data;
}

/**
 * 创建会员订单
 */
export async function apiCreateMembershipOrder(
  request: CreateMembershipOrderRequest
): Promise<CreateMembershipOrderResponse> {
  const response = await apiClient.post<BackendCreateOrderResponse>(`${API_BASE}/orders`, {
    tier: request.tier,
    duration: request.duration,
    payment_method: request.paymentMethod,
  });
  return {
    order: {
      id: response.data.order_no,
      tier: request.tier,
      orderNo: response.data.order_no,
      amount: response.data.amount,
      status: 'pending',
      createdAt: new Date().toISOString(),
    },
    paymentUrl: response.data.payment_url ?? undefined,
  };
}

/**
 * 获取会员订单列表
 */
export async function apiGetMembershipOrders(): Promise<MembershipOrder[]> {
  const response = await apiClient.get<{ items: MembershipOrder[]; total: number; page: number; page_size: number }>(`${API_BASE}/orders`);
  return response.data.items;
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

/** 后端转化统计类型 */
interface BackendConversionStats {
  total_conversions: number;
  conversion_rate: number;
  revenue: number;
  period: string;
}

/** 收入统计类型 */
interface RevenueStats {
  total_revenue: number;
  monthly_revenue: number;
  average_order_value: number;
  period: string;
}

/**
 * 获取转化统计
 */
export async function apiGetConversionStats(days: number = 30): Promise<ConversionStats> {
  const response = await apiClient.get<BackendConversionStats>(`${API_BASE}/stats/conversions?days=${days}`);
  return {
    totalConversions: response.data.total_conversions,
    totalAmount: response.data.revenue,
    conversionTypes: {
      all: response.data.total_conversions,
    },
    periodDays: Number.parseInt(response.data.period, 10) || days,
  };
}

/**
 * 获取收入统计
 */
export async function apiGetRevenueStats(): Promise<RevenueStats> {
  const response = await apiClient.get<RevenueStats>(`${API_BASE}/stats/revenue`);
  return response.data;
}

/**
 * 升级会员
 */
export async function apiUpgradeMembership(
  request: UpgradeMembershipRequest
): Promise<UpgradeMembershipResponse> {
  const response = await apiClient.post<BackendUpgradeResponse>(`${API_BASE}/upgrade`, {
    tier: request.tier,
    duration: request.duration,
  });
  return {
    success: response.data.success,
    order: {
      id: response.data.order_no,
      tier: request.tier,
      orderNo: response.data.order_no,
      amount: 0,
      status: 'pending',
      createdAt: new Date().toISOString(),
    },
    paymentUrl: response.data.payment_url ?? '',
  };
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