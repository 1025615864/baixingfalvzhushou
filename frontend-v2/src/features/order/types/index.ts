/**
 * Order（订单管理）类型定义
 */

// ==================== 核心类型 ====================

/** 订单状态 */
export type OrderStatus = 
  | 'pending'      // 待支付
  | 'paid'         // 已支付
  | 'processing'   // 处理中
  | 'completed'    // 已完成
  | 'cancelled'    // 已取消
  | 'refunded';    // 已退款

/** 订单类型 */
export type OrderType = 
  | 'consultation'  // 咨询订单
  | 'document'      // 文档订单
  | 'membership'    // 会员订单
  | 'service'       // 服务订单
  | 'other';        // 其他

/** 支付方式 */
export type PaymentMethod = 
  | 'wechat'    // 微信支付
  | 'alipay'    // 支付宝
  | 'balance'   // 余额支付
  | 'card'      // 银行卡
  | 'other';    // 其他

/** 订单 */
export interface Order {
  id: number;
  orderNo: string;
  orderType: OrderType;
  title: string;
  amount: number;
  actualAmount: number;
  status: OrderStatus;
  paymentMethod: PaymentMethod | null;
  createdAt: string;
  paidAt: string | null;
  description?: string;
  userId?: number;
}

/** 订单列表项（简化版） */
export interface OrderListItem {
  id: number;
  orderNo: string;
  orderType: OrderType;
  title: string;
  amount: number;
  status: OrderStatus;
  createdAt: string;
}

/** 退款申请 */
export interface RefundRequest {
  orderNo: string;
  reason: string;
  amount?: number;  // 部分退款时指定金额
}

/** 退款结果 */
export interface RefundResult {
  success: boolean;
  message: string;
  refundId?: string;
  refundAmount?: number;
}

// ==================== 筛选和分页类型 ====================

/** 订单筛选条件 */
export interface OrderFilterParams {
  status?: OrderStatus;
  orderType?: OrderType;
  startDate?: string;
  endDate?: string;
  keyword?: string;  // 搜索关键词（订单号或标题）
}

/** 分页请求参数 */
export interface PaginationParams {
  page: number;
  pageSize: number;
}

/** 订单列表请求 */
export interface GetOrderListRequest extends Partial<PaginationParams>, OrderFilterParams {}

/** 订单列表响应 */
export interface GetOrderListResponse {
  items: Order[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// ==================== API 请求/响应类型 ====================

/** 获取订单详情请求 */
export interface GetOrderDetailRequest {
  orderNo: string;
}

/** 获取订单详情响应 */
export interface GetOrderDetailResponse {
  order: Order;
}

/** 取消订单请求 */
export interface CancelOrderRequest {
  orderNo: string;
}

/** 取消订单响应 */
export interface CancelOrderResponse {
  success: boolean;
  message: string;
}

/** 申请退款请求 */
export interface ApplyRefundRequest {
  orderNo: string;
  reason: string;
  amount?: number;
}

/** 申请退款响应 */
export interface ApplyRefundResponse {
  success: boolean;
  message: string;
  refundId?: string;
  refundAmount?: number;
}

/** 订单统计 */
export interface OrderStats {
  totalOrders: number;
  totalAmount: number;
  pendingCount: number;
  completedCount: number;
  cancelledCount: number;
}

/** 获取订单统计响应 */
export interface GetOrderStatsResponse {
  stats: OrderStats;
}