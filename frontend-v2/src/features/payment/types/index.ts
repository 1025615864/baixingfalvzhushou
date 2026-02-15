/**
 * 支付系统类型定义
 */

// 支付状态
export type PaymentStatus = 'pending' | 'paid' | 'cancelled' | 'refunded' | 'failed';

// 支付方式
export type PaymentMethod = 'alipay' | 'wechat' | 'balance' | 'ikunpay';

// 订单类型
export type OrderType = 'consultation' | 'service' | 'vip' | 'recharge' | 'light_consult_review';

// 订单
export interface Order {
  id: number;
  order_no: string;
  order_type: OrderType;
  amount: number;
  actual_amount: number;
  status: PaymentStatus;
  payment_method: PaymentMethod | null;
  title: string;
  created_at: string;
  paid_at: string | null;
  description?: string;
  expires_at?: string;
  related_id?: number;
  related_type?: string;
  trade_no?: string;
}

// 订单列表响应
export interface OrderListResponse {
  items: Order[];
  total: number;
}

// 创建订单请求
export interface CreateOrderRequest {
  order_type: OrderType;
  amount: number;
  title: string;
  description?: string;
  related_id?: number;
  related_type?: string;
}

// 创建订单响应
export interface CreateOrderResponse {
  order_id: number;
  order_no: string;
  amount: number;
  expires_at: string;
}

// 支付请求
export interface PayOrderRequest {
  payment_method: PaymentMethod;
}

// 支付响应
export interface PayOrderResponse {
  message: string;
  payment_method: PaymentMethod;
  amount: number;
  order_no: string;
  pay_url?: string;
  trade_no?: string;
}

// 余额信息
export interface BalanceInfo {
  balance: number;
  frozen: number;
  total_recharged: number;
  total_consumed: number;
}

// 余额交易记录
export interface BalanceTransaction {
  id: number;
  type: 'recharge' | 'consume' | 'refund';
  amount: number;
  balance_after: number;
  description: string | null;
  created_at: string;
}

// 余额交易列表响应
export interface BalanceTransactionListResponse {
  items: BalanceTransaction[];
  total: number;
}

// 价格表
export interface PricingInfo {
  vip: {
    days: number;
    price: number;
  };
  services: {
    light_consult_review: {
      price: number;
    };
  };
  packs: {
    ai_chat: Array<{ count: number; price: number }>;
    document_generate: Array<{ count: number; price: number }>;
  };
}

// 支付状态查询响应
export interface PaymentStatusResponse {
  order_no: string;
  status: PaymentStatus;
  paid_at: string | null;
  trade_no: string | null;
}

// 支付方法配置
export interface PaymentMethodConfig {
  id: PaymentMethod;
  name: string;
  icon: string;
  description: string;
  enabled: boolean;
}

// 支付回调数据
export interface PaymentCallbackData {
  order_no: string;
  trade_no: string;
  payment_method: PaymentMethod;
  amount: string;
  signature: string;
}

// 订单查询参数
export interface OrderListParams {
  page?: number;
  page_size?: number;
  status_filter?: PaymentStatus;
}

// 支付轮询状态
export type PaymentPollingStatus = 'polling' | 'success' | 'failed' | 'timeout';

// 支付结果
export interface PaymentResult {
  success: boolean;
  orderNo: string;
  message: string;
  redirectUrl?: string;
}

// ==================== 支付回调管理类型（管理员用） ====================

// 回调状态
export type CallbackStatus = 'pending' | 'success' | 'failed' | 'retrying';

// 回调来源
export type CallbackSource = 'alipay' | 'wechat' | 'system';

// 回调记录
export interface PaymentCallback {
  id: string;
  orderNo: string;
  tradeNo: string | null;
  source: CallbackSource;
  status: CallbackStatus;
  payload: string;
  response: string | null;
  retryCount: number;
  maxRetries: number;
  nextRetryAt: string | null;
  processedAt: string | null;
  errorMessage: string | null;
  ipAddress: string | null;
  createdAt: string;
  updatedAt: string;
}

// 回调统计
export interface CallbackStats {
  totalCount: number;
  pendingCount: number;
  successCount: number;
  failedCount: number;
  retryingCount: number;
  todayCount: number;
  todaySuccessCount: number;
}

// 获取回调列表请求
export interface GetCallbacksRequest {
  page?: number;
  pageSize?: number;
  status?: CallbackStatus;
  source?: CallbackSource;
  orderNo?: string;
  fromTime?: string;
  toTime?: string;
}

// 获取回调列表响应
export interface GetCallbacksResponse {
  items: PaymentCallback[];
  total: number;
  page: number;
  pageSize: number;
  stats: CallbackStats;
}

// 重试回调请求
export interface RetryCallbackRequest {
  id: string;
}

// 手动处理回调请求
export interface ProcessCallbackRequest {
  id: string;
  success: boolean;
  note?: string;
}

// ==================== 结算统计类型（管理员用） ====================

// 结算统计项
export interface SettlementStatsItem {
  date: string;
  totalAmount: number;
  totalCount: number;
  successAmount: number;
  successCount: number;
  refundAmount: number;
  refundCount: number;
  feeAmount: number;
  netAmount: number;
}

// 结算汇总
export interface SettlementSummary {
  totalAmount: number;
  totalCount: number;
  successAmount: number;
  successCount: number;
  refundAmount: number;
  refundCount: number;
  feeAmount: number;
  netAmount: number;
  averageOrderValue: number;
  successRate: number;
}

// 支付方式统计
export interface PaymentMethodStats {
  method: string;
  amount: number;
  count: number;
  percentage: number;
}

// 结算趋势
export interface SettlementTrend {
  dates: string[];
  amounts: number[];
  counts: number[];
}

// 获取结算统计请求
export interface GetSettlementStatsRequest {
  startDate: string;
  endDate: string;
  groupBy?: 'day' | 'week' | 'month';
}

// 获取结算统计响应
export interface GetSettlementStatsResponse {
  items: SettlementStatsItem[];
  summary: SettlementSummary;
  methodStats: PaymentMethodStats[];
  trend: SettlementTrend;
}

// 导出结算报表请求
export interface ExportSettlementReportRequest {
  startDate: string;
  endDate: string;
  format?: 'csv' | 'excel';
}

// ==================== 退款相关类型 ====================

/** 退款状态 */
export type RefundStatus = 'pending' | 'processing' | 'success' | 'failed';

/** 退款记录 */
export interface Refund {
  refundNo: string;
  orderNo: string;
  amount: number;
  status: RefundStatus;
  reason: string | null;
  createdAt: string;
}

/** 创建退款请求 */
export interface CreateRefundRequest {
  orderNo: string;
  amount: number;
  reason?: string;
}

/** 创建退款响应 */
export interface CreateRefundResponse extends Refund {}

/** 获取退款列表请求 */
export interface GetRefundsRequest {
  page?: number;
  pageSize?: number;
  status?: RefundStatus;
}

/** 获取退款列表响应 */
export interface GetRefundsResponse {
  items: Refund[];
  total: number;
  page: number;
  pageSize: number;
}

// 兼容类型别名
export type PaymentOrder = Order;
export type PaymentOrderStatus = PaymentStatus;