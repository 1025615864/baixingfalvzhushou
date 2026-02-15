/**
 * Promotion（推广系统）类型定义
 */

// ==================== 后端API原始类型 ====================

/** 邀请历史记录项（后端返回） */
export interface InviteHistoryItem {
  id?: number;
  invited_user_id?: number;
  invited_user_name?: string;
  invited_at: string;
  status: 'pending' | 'claimed';
  reward_amount?: number;
  claimed_at?: string;
}

/** 邀请排行榜项（后端返回） */
export interface InviteRankingItem {
  user_id?: number;
  user_name?: string;
  avatar_url?: string;
  invite_count?: number;
}

// ==================== 核心类型 ====================

/** 推广链接类型 */
export interface PromotionLink {
  id?: string;
  code: string;
  url: string;
  shortUrl?: string;
  qrCodeUrl?: string;
  createdAt: string;
  expiresAt?: string | null;
  status?: 'active' | 'inactive' | 'expired';
  clickCount?: number;
  conversionCount?: number;
}

/** 推广统计类型 */
export interface PromotionStats {
  totalInvited: number;
  totalRegistered: number;
  totalRewards: number;
  pendingRewards: number;
  conversionRate: number;
  period: 'day' | 'week' | 'month' | 'year' | 'all';
  startDate?: string;
  endDate?: string;
  trend?: StatsTrendItem[];
  /** 总佣金（用于结算） */
  totalCommission: number;
  /** 待结算佣金 */
  pendingCommission: number;
  /** 已结算佣金 */
  paidCommission: number;
}

/** 统计趋势项 */
export interface StatsTrendItem {
  date: string;
  clicks: number;
  conversions: number;
  commission: number;
}

/** 佣金记录类型 */
export interface CommissionRecord {
  id: string;
  orderId: string;
  orderAmount: number;
  commissionAmount: number;
  commissionRate: number;
  status: 'pending' | 'confirmed' | 'paid' | 'cancelled';
  sourceUserId?: string;
  sourceUserName?: string;
  createdAt: string;
  confirmedAt?: string;
  paidAt?: string;
  description?: string;
}

/** 推广海报类型 */
export interface PromotionPoster {
  id: string;
  title: string;
  description?: string;
  templateId: string;
  imageUrl: string;
  shareText?: string;
  createdAt: string;
  customData?: Record<string, unknown>;
}

/** 佣金提现请求 */
export interface CommissionWithdrawal {
  id: string;
  amount: number;
  status: 'pending' | 'processing' | 'completed' | 'rejected';
  withdrawalMethod: 'alipay' | 'wechat' | 'bank' | 'reward';
  createdAt: string;
  processedAt?: string;
  remark?: string;
  accountInfo?: Record<string, unknown>;
}

// ==================== API 请求/响应类型 ====================

/** 获取推广链接请求 */
export interface GetPromotionLinkRequest {
  code?: string;
}

/** 获取推广链接响应 */
export interface GetPromotionLinkResponse {
  link: PromotionLink;
}

/** 生成推广链接请求 */
export interface GeneratePromotionLinkRequest {
  expiresInDays?: number;
  customCode?: string;
}

/** 生成推广链接响应 */
export interface GeneratePromotionLinkResponse {
  link: PromotionLink;
}

/** 获取推广统计请求 */
export interface GetPromotionStatsRequest {
  period?: 'day' | 'week' | 'month' | 'year' | 'all';
  startDate?: string;
  endDate?: string;
}

/** 获取推广统计响应 */
export interface GetPromotionStatsResponse {
  stats: PromotionStats;
}

/** 获取佣金记录请求 */
export interface GetCommissionRecordsRequest {
  status?: 'pending' | 'confirmed' | 'paid' | 'cancelled';
  limit?: number;
  offset?: number;
}

/** 获取佣金记录响应 */
export interface GetCommissionRecordsResponse {
  records: CommissionRecord[];
  total: number;
}

/** 生成推广海报请求 */
export interface GeneratePosterRequest {
  templateId?: string;
  customTitle?: string;
  customDescription?: string;
}

/** 生成推广海报响应 */
export interface GeneratePosterResponse {
  poster: PromotionPoster;
}

/** 获取海报列表响应 */
export interface GetPostersResponse {
  posters: PromotionPoster[];
}

/** 申请提现请求 */
export interface RequestWithdrawalRequest {
  amount: number;
  withdrawalMethod: 'alipay' | 'wechat' | 'bank' | 'reward';
  accountInfo: string;
}

/** 申请提现响应 */
export interface RequestWithdrawalResponse {
  withdrawal: CommissionWithdrawal;
}

/** 获取提现记录响应 */
export interface GetWithdrawalsResponse {
  withdrawals: CommissionWithdrawal[];
  total: number;
}

/** 推广规则 */
export interface PromotionRule {
  commissionRate: number;
  minWithdrawalAmount: number;
  settlementPeriod: string;
  description: string;
}

/** 获取推广规则响应 */
export interface GetPromotionRulesResponse {
  rules: PromotionRule;
}

/** 邀请转化分析响应 */
export interface GetInvitationAnalyticsResponse {
  totalVisits: number;
  totalSignups: number;
  conversionRate: number;
  rewardsClaimed: number;
  rewardsPending: number;
}

// ==================== 提现管理类型（管理员用） ====================

/** 提现申请状态 */
export type WithdrawalStatus = 'pending' | 'approved' | 'rejected' | 'completed';

/** 提现申请项（管理员视图） */
export interface WithdrawalItem {
  id: string;
  requestNo: string;
  lawyerId: string;
  lawyerName: string | null;
  lawyerRating: number | null;
  lawyerCompletedCount: number | null;
  platformFeeRate: number | null;
  amount: number;
  fee: number;
  actualAmount: number;
  withdrawMethod: string;
  accountInfoMasked: string;
  status: WithdrawalStatus;
  rejectReason: string | null;
  adminId: string | null;
  reviewedAt: string | null;
  completedAt: string | null;
  remark: string | null;
  createdAt: string;
  updatedAt: string;
}

/** 提现详情（管理员视图） */
export interface WithdrawalDetail extends WithdrawalItem {
  accountInfo: string;
}

/** 提现统计 */
export interface WithdrawalStats {
  totalCount: number;
  totalAmount: number;
  pendingCount: number;
  pendingAmount: number;
  approvedCount: number;
  approvedAmount: number;
  rejectedCount: number;
  rejectedAmount: number;
  completedCount: number;
  completedAmount: number;
}

/** 审核提现请求 */
export interface ReviewWithdrawalRequest {
  approved: boolean;
  rejectReason?: string;
  remark?: string;
}

/** 获取提现列表请求 */
export interface GetWithdrawalsRequest {
  page?: number;
  pageSize?: number;
  status?: WithdrawalStatus;
  keyword?: string;
  fromTime?: string;
  toTime?: string;
}

/** 获取提现列表响应 */
export interface GetWithdrawalsAdminResponse {
  items: WithdrawalItem[];
  total: number;
  page: number;
  pageSize: number;
  stats: WithdrawalStats;
}

/** 后端原始响应类型 */
export interface WithdrawalItemSnake {
  id: number;
  request_no: string;
  lawyer_id: number;
  lawyer_name?: string | null;
  lawyer_rating?: number | null;
  lawyer_completed_count?: number | null;
  platform_fee_rate?: number | null;
  amount: number;
  fee: number;
  actual_amount: number;
  withdraw_method: string;
  account_info_masked: string;
  status: string;
  reject_reason: string | null;
  admin_id: number | null;
  reviewed_at: string | null;
  completed_at: string | null;
  remark: string | null;
  created_at: string;
  updated_at: string;
}

export interface WithdrawalDetailSnake extends WithdrawalItemSnake {
  account_info: string;
}

export interface WithdrawalStatsSnake {
  total_count: number;
  total_amount: number;
  pending_count: number;
  pending_amount: number;
  approved_count: number;
  approved_amount: number;
  rejected_count: number;
  rejected_amount: number;
  completed_count: number;
  completed_amount: number;
}