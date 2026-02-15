/**
 * Points（积分系统）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/points 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  PointsBalance,
  GetPointsHistoryRequest,
  GetPointsHistoryResponse,
  GetProductsResponse,
  ExchangeProductRequest,
  ExchangeProductResponse,
  CheckInResult,
  GetDailyStatsResponse,
  GetRulesResponse,
  GetLeaderboardResponse,
  GetOrdersResponse,
  PointsProduct,
} from '../types';


// API 基础路径
const API_BASE = '/points';

// ==================== 后端响应类型定义 ====================

/** 后端积分余额响应 */
interface BackendBalanceResponse {
  balance: number;
  continuous_days: number;
}

/** 后端积分历史项 */
interface BackendPointsHistoryItem {
  id: string;
  action: string;
  points: number;
  balance_after: number;
  description?: string;
  created_at: string;
}

/** 后端积分历史响应 */
interface BackendHistoryResponse {
  history: BackendPointsHistoryItem[];
  total?: number;
  limit: number;
  offset: number;
}

/** 后端积分商品 */
interface BackendPointsProduct {
  id: string;
  name: string;
  description: string;
  points_required: number;
  product_type: string;
  image_url?: string;
  stock: number;
  status: string;
  metadata?: Record<string, unknown>;
}

/** 后端商品列表响应 */
interface BackendProductsResponse {
  products: BackendPointsProduct[];
}

/** 后端商品详情响应 */
interface BackendProductDetailResponse {
  product: BackendPointsProduct & { metadata?: Record<string, unknown> };
}

/** 后端兑换订单 */
interface BackendExchangeOrder {
  id: string;
  product_id: string;
  product_name: string;
  points_spent: number;
  status: string;
  created_at: string;
  completed_at?: string;
}

/** 后端兑换响应 */
interface BackendExchangeResponse {
  success: boolean;
  order: BackendExchangeOrder;
}

/** 后端签到响应 */
interface BackendCheckInResponse {
  message: string;
  points_earned: number;
  continuous_days: number;
  total_points: number;
}

/** 后端每日统计项 */
interface BackendDailyStat {
  action: string;
  count: number;
}

/** 后端每日统计响应 */
interface BackendDailyStatsResponse {
  stats: BackendDailyStat[];
}

/** 后端积分规则 */
interface BackendPointsRule {
  action: string;
  points: number;
  daily_limit: number;
  description: string;
}

/** 后端积分规则响应 */
interface BackendRulesResponse {
  rules: BackendPointsRule[];
}

/** 后端排行榜项 */
interface BackendLeaderboardItem {
  user_id: string;
  username: string;
  avatar?: string;
  total_points: number;
  rank: number;
}

/** 后端排行榜响应 */
interface BackendLeaderboardResponse {
  leaderboard: BackendLeaderboardItem[];
}

/** 后端订单列表响应 */
interface BackendOrdersResponse {
  orders: BackendExchangeOrder[];
}

// ==================== 转换函数 ====================

/**
 * 转换后端商品到前端格式
 */
function mapBackendToProduct(data: BackendPointsProduct): PointsProduct {
  return {
    id: data.id,
    name: data.name,
    description: data.description,
    pointsRequired: data.points_required,
    productType: data.product_type as 'physical' | 'virtual' | 'service' | 'coupon',
    imageUrl: data.image_url,
    stock: data.stock,
    status: data.status as 'active' | 'inactive',
  };
}

// ==================== 积分余额 API ====================

/**
 * 获取积分余额
 */
export async function apiGetPointsBalance(): Promise<PointsBalance> {
  const response = await apiClient.get<BackendBalanceResponse>(`${API_BASE}/balance`);
  
  return {
    balance: response.data.balance,
    continuousDays: response.data.continuous_days,
  };
}

// ==================== 积分历史 API ====================

/**
 * 获取积分历史记录
 */
export async function apiGetPointsHistory(
  params: GetPointsHistoryRequest = {}
): Promise<GetPointsHistoryResponse> {
  const response = await apiClient.get<BackendHistoryResponse>(`${API_BASE}/history`, {
    params: {
      limit: params.limit,
      offset: params.offset,
      action_type: params.actionTypes,
      start_date: params.startDate,
      end_date: params.endDate,
    },
  });

  return {
    history: response.data.history.map(item => ({
      id: String(item.id),
      action: item.action,
      points: item.points,
      balanceAfter: item.balance_after,
      description: item.description,
      createdAt: item.created_at,
    })),
    total: response.data.total ?? response.data.history.length,
    limit: response.data.limit ?? params.limit ?? 20,
    offset: response.data.offset ?? params.offset ?? 0,
  };
}

// ==================== 积分商品 API ====================

/**
 * 获取积分商品列表
 */
export async function apiGetPointsProducts(productType?: string): Promise<GetProductsResponse> {
  const response = await apiClient.get<BackendProductsResponse>(`${API_BASE}/products`, {
    params: {
      product_type: productType,
    },
  });

  return {
    products: response.data.products.map(mapBackendToProduct),
  };
}

/**
 * 获取商品详情
 */
export async function apiGetProductDetail(productId: string): Promise<PointsProduct> {
  const response = await apiClient.get<BackendProductDetailResponse>(`${API_BASE}/products/${productId}`);
  return mapBackendToProduct(response.data.product);
}

// ==================== 积分兑换 API ====================

/**
 * 兑换积分商品
 */
export async function apiExchangeProduct(
  request: ExchangeProductRequest
): Promise<ExchangeProductResponse> {
  const response = await apiClient.post<BackendExchangeResponse>(`${API_BASE}/redeem`, {
    product_id: request.productId,
  });

  return {
    success: response.data.success,
    order: {
      id: String(response.data.order.id),
      productId: response.data.order.product_id,
      productName: response.data.order.product_name,
      pointsSpent: response.data.order.points_spent,
      status: response.data.order.status as 'pending' | 'completed' | 'cancelled',
      createdAt: response.data.order.created_at,
    },
  };
}

/**
 * 获取兑换订单列表
 */
export async function apiGetExchangeOrders(
  status?: string,
  limit: number = 20
): Promise<GetOrdersResponse> {
  const response = await apiClient.get<BackendOrdersResponse>(`${API_BASE}/orders`, {
    params: {
      status,
      limit,
    },
  });

  return {
    orders: response.data.orders.map(o => ({
      id: String(o.id),
      productId: o.product_id,
      productName: o.product_name,
      pointsSpent: o.points_spent,
      status: o.status as 'pending' | 'completed' | 'cancelled',
      createdAt: o.created_at,
      completedAt: o.completed_at,
    })),
  };
}

// ==================== 签到 API ====================

/**
 * 每日签到
 */
export async function apiCheckIn(): Promise<CheckInResult> {
  const response = await apiClient.post<BackendCheckInResponse>(`${API_BASE}/check-in`);

  return {
    success: true,
    pointsEarned: response.data.points_earned,
    continuousDays: response.data.continuous_days,
    totalPoints: response.data.total_points,
  };
}

// ==================== 统计与规则 API ====================

/**
 * 获取每日统计
 */
export async function apiGetDailyStats(): Promise<GetDailyStatsResponse> {
  const response = await apiClient.get<BackendDailyStatsResponse>(`${API_BASE}/daily-stats`);

  return {
    stats: response.data.stats.map(s => ({
      action: s.action,
      count: s.count,
    })),
  };
}

/**
 * 获取积分规则
 */
export async function apiGetPointsRules(): Promise<GetRulesResponse> {
  const response = await apiClient.get<BackendRulesResponse>(`${API_BASE}/rules`);

  return {
    rules: response.data.rules.map(r => ({
      action: r.action,
      points: r.points,
      dailyLimit: r.daily_limit,
      description: r.description,
    })),
  };
}

/**
 * 获取积分排行榜
 */
export async function apiGetPointsLeaderboard(topK: number = 100): Promise<GetLeaderboardResponse> {
  const response = await apiClient.get<BackendLeaderboardResponse>(`${API_BASE}/leaderboard`, {
    params: {
      top_k: topK,
    },
  });

  return {
    leaderboard: response.data.leaderboard.map(item => ({
      userId: String(item.user_id),
      username: item.username,
      avatar: item.avatar,
      totalPoints: item.total_points,
      rank: item.rank,
    })),
  };
}

// ==================== 统一导出 ====================

/**
 * Points API 统一导出对象
 */
export const pointsApi = {
  // 积分余额
  getPointsBalance: apiGetPointsBalance,
  
  // 积分历史
  getPointsHistory: apiGetPointsHistory,
  
  // 积分商品
  getPointsProducts: apiGetPointsProducts,
  getProductDetail: apiGetProductDetail,
  
  // 积分兑换
  exchangeProduct: apiExchangeProduct,
  getExchangeOrders: apiGetExchangeOrders,
  
  // 签到
  checkIn: apiCheckIn,
  
  // 统计与规则
  getDailyStats: apiGetDailyStats,
  getPointsRules: apiGetPointsRules,
  getPointsLeaderboard: apiGetPointsLeaderboard,
} as const;

export default pointsApi;