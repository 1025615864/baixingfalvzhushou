/**
 * Points（积分系统）类型定义
 */

// ==================== 核心类型 ====================

/** 积分动作类型 */
export type PointsAction =
  | 'sign_in'          // 签到
  | 'post_create'      // 发帖
  | 'comment_create'   // 评论
  | 'like'             // 点赞
  | 'share'            // 分享
  | 'consultation_complete'  // 完成咨询
  | 'document_upload'  // 上传文档
  | 'profile_complete' // 完善资料
  | 'invite_friend'    // 邀请好友
  | 'exchange_product' // 兑换商品
  | 'bonus';           // 奖励

/** 积分记录类型 */
export interface PointsTransaction {
  id: string;
  action: string;
  points: number;
  balanceAfter: number;
  description?: string;
  createdAt: string;
}

/** 积分余额 */
export interface PointsBalance {
  balance: number;
  continuousDays: number;
}

/** 积分商品类型 */
export type ProductType = 'physical' | 'virtual' | 'service' | 'coupon';

/** 积分商品 */
export interface PointsProduct {
  id: string;
  name: string;
  description: string;
  pointsRequired: number;
  productType: ProductType;
  imageUrl?: string;
  stock: number;
  status: 'active' | 'inactive';
}

/** 兑换订单状态 */
export type OrderStatus = 'pending' | 'completed' | 'cancelled';

/** 兑换订单 */
export interface ExchangeOrder {
  id: string;
  productId: string;
  productName: string;
  pointsSpent: number;
  status: OrderStatus;
  createdAt: string;
  completedAt?: string;
}

// ==================== 任务相关类型 ====================

/** 积分任务类型 */
export type TaskType = 'daily' | 'one_time' | 'weekly' | 'monthly';

/** 积分任务 */
export interface PointsTask {
  id: string;
  name: string;
  description: string;
  pointsReward: number;
  taskType: TaskType;
  action: string;
  maxDailyCount: number;
  icon?: string;
  completedToday: number;
  isCompleted: boolean;
}

/** 签到结果 */
export interface CheckInResult {
  success: boolean;
  pointsEarned: number;
  continuousDays: number;
  totalPoints: number;
}

// ==================== API 请求/响应类型 ====================

/** 获取积分历史请求 */
export interface GetPointsHistoryRequest {
  limit?: number;
  offset?: number;
  /** 筛选的动作类型 */
  actionTypes?: string[];
  /** 开始日期 */
  startDate?: string;
  /** 结束日期 */
  endDate?: string;
}

/** 获取积分历史响应 */
export interface GetPointsHistoryResponse {
  history: PointsTransaction[];
  total: number;
  limit: number;
  offset: number;
}

/** 分页参数 */
export interface PaginationParams {
  page: number;
  pageSize: number;
}

/** 分页结果 */
export interface PaginationResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/** 兑换商品请求 */
export interface ExchangeProductRequest {
  productId: string;
}

/** 兑换商品响应 */
export interface ExchangeProductResponse {
  success: boolean;
  order: ExchangeOrder;
}

/** 获取商品列表响应 */
export interface GetProductsResponse {
  products: PointsProduct[];
}

/** 获取任务列表响应 */
export interface GetTasksResponse {
  tasks: PointsTask[];
}

/** 每日统计 */
export interface DailyStat {
  action: string;
  count: number;
}

/** 获取每日统计响应 */
export interface GetDailyStatsResponse {
  stats: DailyStat[];
}

/** 积分规则 */
export interface PointsRule {
  action: string;
  points: number;
  dailyLimit: number;
  description: string;
}

/** 获取积分规则响应 */
export interface GetRulesResponse {
  rules: PointsRule[];
}

/** 排行榜项 */
export interface LeaderboardItem {
  userId: string;
  username: string;
  avatar?: string;
  totalPoints: number;
  rank: number;
}

/** 获取排行榜响应 */
export interface GetLeaderboardResponse {
  leaderboard: LeaderboardItem[];
}

/** 获取兑换订单响应 */
export interface GetOrdersResponse {
  orders: ExchangeOrder[];
}