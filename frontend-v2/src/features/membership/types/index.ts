/**
 * Membership（会员系统）类型定义
 
 会员等级体系：
 - free: 免费用户
 - monthly: 月度会员 ¥29/月
 - annual: 年度会员 ¥299/年 (享8.6折)
 - lifetime: 终身会员 ¥999 (一次购买终身权益)
 */

// ==================== 核心类型 ====================

/** 会员等级 */
export type MembershipTier = 'free' | 'monthly' | 'annual' | 'lifetime';

/** 会员价格配置 */
export interface MembershipPricing {
  tier: MembershipTier;
  name: string;
  monthlyPrice: number;
  annualPrice: number;
  annualDiscount: number;
  lifetimePrice: number;
  savingsAnnual: number;
}

/** 会员权益配置 */
export interface MembershipBenefits {
  tier: MembershipTier;
  name: string;
  dailyAiChatLimit: number;
  dailyDocumentLimit: number;
  unlimitedAiChat: boolean;
  videoConsultationDiscount: number;
  freeVideoConsultationsPerMonth: number;
  prioritySupport: boolean;
  advancedFeatures: boolean;
  apiAccess: boolean;
  customBranding: boolean;
  pointsMultiplier: number;
  contractReviewPerMonth: number;
  unlimitedContractReview: boolean;
  lawyerConsultationDiscount: number;
}

/** 用户会员详细信息 */
export interface UserMembership {
  userId: number;
  level: MembershipTier;
  levelName: string;
  startDate: string | null;
  endDate: string | null;
  autoRenew: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  benefits: MembershipBenefits | null;
  isVip: boolean;
}

/** 用户会员信息（旧格式兼容） */
export interface UserMembershipLegacy {
  tier: MembershipTier;
  isVip: boolean;
  benefits: MembershipBenefits | null;
  quota: {
    aiChat: {
      limit: number;
      used: number;
      remaining: number;
    };
    documentGenerate: {
      limit: number;
      used: number;
      remaining: number;
    };
  };
}

/** 转化历史项 */
export interface ConversionHistoryItem {
  orderNo: string;
  orderType: string | null;
  amount: number;
  paidAt: string | null;
}

/** 转化统计 */
export interface ConversionStats {
  totalConversions: number;
  totalAmount: number;
  conversionTypes: Record<string, number>;
  periodDays: number;
}

/** 收入统计 */
export interface RevenueStats {
  totalRevenue: number;
  orderCount: number;
  avgOrderValue: number;
  byOrderType: Record<string, {
    count: number;
    amount: number;
  }>;
}

/** 会员订单 */
export interface MembershipOrder {
  id: string;
  tier: MembershipTier;
  orderNo: string;
  amount: number;
  status: 'pending' | 'paid' | 'cancelled' | 'refunded';
  createdAt: string;
  paidAt?: string;
  expiresAt?: string;
}

// ==================== API 请求/响应类型 ====================

/** 获取会员信息响应 */
export interface GetMembershipInfoResponse {
  membership: UserMembership;
}

/** 获取会员等级列表响应 */
export interface GetMembershipLevelsResponse {
  levels: MembershipBenefits[];
}

/** 获取会员权益响应 */
export interface GetMembershipBenefitsResponse {
  benefits: MembershipBenefits;
}

/** 创建会员订单请求 */
export interface CreateMembershipOrderRequest {
  tier: MembershipTier;
  duration: 'month' | 'quarter' | 'year';
  paymentMethod: 'alipay' | 'wechat';
}

/** 创建会员订单响应 */
export interface CreateMembershipOrderResponse {
  order: MembershipOrder;
  paymentUrl?: string;
}

/** 获取转化历史请求 */
export interface GetConversionHistoryRequest {
  page?: number;
  pageSize?: number;
}

/** 获取转化历史响应 */
export interface GetConversionHistoryResponse {
  items: ConversionHistoryItem[];
  total: number;
  page: number;
  pageSize: number;
}

/** 获取转化统计响应 */
export interface GetConversionStatsResponse {
  stats: ConversionStats;
}

/** 获取收入统计响应 */
export interface GetRevenueStatsResponse {
  stats: RevenueStats;
}

/** 升级会员请求 */
export interface UpgradeMembershipRequest {
  tier: MembershipTier;
  duration: 'month' | 'quarter' | 'year';
}

/** 升级会员响应 */
export interface UpgradeMembershipResponse {
  success: boolean;
  order: MembershipOrder;
  paymentUrl: string;
}

/** 取消订单请求 */
export interface CancelMembershipOrderRequest {
  orderId: string;
}

/** 取消订单响应 */
export interface CancelMembershipOrderResponse {
  success: boolean;
  message: string;
}

/** 获取订单列表响应 */
export interface GetMembershipOrdersResponse {
  orders: MembershipOrder[];
  total: number;
}