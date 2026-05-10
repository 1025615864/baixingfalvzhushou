/**
 * 前端统一的 API 响应类型定义
 * 
 * 与后端 [`backend/app/core/response.py`](backend/app/core/response.py) 保持一致
 * 支持新版响应格式 (success/message/data/error_code)
 */

import type { ApiError } from './client';

// ============================================================
// 后端错误码映射
// ============================================================

/**
 * 后端错误码范围分配
 * - 通用错误：1000-1999
 * - 用户相关：2000-2999
 * - 支付相关：3000-3999
 * - AI 相关：4000-4999
 * - 业务相关：5000-5999
 * - 内容相关：6000-6999
 * - 论坛相关：7000-7999
 * - 系统相关：8000-8999
 * - 限流相关：9000-9999
 */
export enum BusinessErrorCode {
  // 通用错误 1000-1999
  SUCCESS = 0,
  INVALID_PARAMS = 1001,
  UNAUTHORIZED = 1002,
  FORBIDDEN = 1003,
  NOT_FOUND = 1004,
  INTERNAL_ERROR = 1005,
  CONFLICT = 1006,
  VALIDATION_ERROR = 1007,
  RATE_LIMIT_EXCEEDED = 1008,
  SERVICE_UNAVAILABLE = 1009,

  // 用户相关 2000-2999
  USER_NOT_FOUND = 2001,
  USER_ALREADY_EXISTS = 2002,
  INVALID_CREDENTIALS = 2003,
  TOKEN_EXPIRED = 2004,
  TOKEN_INVALID = 2005,
  EMAIL_VERIFICATION_REQUIRED = 2006,
  PHONE_VERIFICATION_REQUIRED = 2007,

  // 支付相关 3000-3999
  PAYMENT_FAILED = 3001,
  PAYMENT_AMOUNT_MISMATCH = 3002,
  PAYMENT_ORDER_NOT_FOUND = 3003,
  PAYMENT_ORDER_ALREADY_PAID = 3004,
  PAYMENT_ORDER_CANCELLED = 3005,
  PAYMENT_CALLBACK_INVALID = 3006,
  PAYMENT_CALLBACK_DUPLICATE = 3007,
  PAYMENT_METHOD_NOT_SUPPORTED = 3008,
  PAYMENT_PROCESSING_ERROR = 3009,
  PAYMENT_TIMEOUT = 3010,
  INSUFFICIENT_BALANCE = 3011,

  // AI 相关 4000-4999
  AI_SERVICE_UNAVAILABLE = 4001,
  AI_QUOTA_EXCEEDED = 4002,
  AI_REQUEST_TOO_LONG = 4003,
  AI_RESPONSE_INVALID = 4004,
  AI_TIMEOUT = 4005,
  AI_RATE_LIMIT_EXCEEDED = 4006,

  // 业务相关 5000-5999
  INVALID_ORDER_TYPE = 5001,
  ORDER_EXPIRED = 5002,
  RESOURCE_NOT_FOUND = 5003,
  RESOURCE_ALREADY_EXISTS = 5004,
  OPERATION_NOT_ALLOWED = 5005,

  // 内容相关 6000-6999
  CONTENT_NOT_FOUND = 6001,
  CONTENT_ALREADY_PUBLISHED = 6002,
  CONTENT_MODIFICATION_NOT_ALLOWED = 6003,
  CONTENT_VALIDATION_FAILED = 6004,

  // 论坛相关 7000-7999
  FORUM_POST_NOT_FOUND = 7001,
  FORUM_COMMENT_NOT_FOUND = 7002,
  FORUM_POST_LOCKED = 7003,
  FORUM_COMMENT_NOT_ALLOWED = 7004,

  // 系统相关 8000-8999
  SYSTEM_MAINTENANCE = 8001,
  SYSTEM_OVERLOADED = 8002,
  DATABASE_ERROR = 8003,
  CACHE_ERROR = 8004,
  EXTERNAL_SERVICE_ERROR = 8005,
}

/**
 * 错误码范围类型
 */
export type ErrorCodeRange =
  | 'GENERAL'      // 1000-1999
  | 'USER'         // 2000-2999
  | 'PAYMENT'      // 3000-3999
  | 'AI'           // 4000-4999
  | 'BUSINESS'     // 5000-5999
  | 'CONTENT'      // 6000-6999
  | 'FORUM'        // 7000-7999
  | 'SYSTEM'       // 8000-8999
  | 'RATE_LIMIT';  // 9000-9999

/**
 * 根据错误码获取错误码范围
 */
export function getErrorCodeRange(code: number): ErrorCodeRange | null {
  if (code === 0) return 'GENERAL';
  if (code >= 1000 && code < 2000) return 'GENERAL';
  if (code >= 2000 && code < 3000) return 'USER';
  if (code >= 3000 && code < 4000) return 'PAYMENT';
  if (code >= 4000 && code < 5000) return 'AI';
  if (code >= 5000 && code < 6000) return 'BUSINESS';
  if (code >= 6000 && code < 7000) return 'CONTENT';
  if (code >= 7000 && code < 8000) return 'FORUM';
  if (code >= 8000 && code < 9000) return 'SYSTEM';
  if (code >= 9000 && code < 10000) return 'RATE_LIMIT';
  return null;
}

// ============================================================
// 错误消息映射
// ============================================================

/**
 * 错误消息映射表
 * 用于前端根据错误码显示友好的错误提示
 */
export const ERROR_MESSAGES: Record<number, string> = {
  // 通用错误
  [BusinessErrorCode.SUCCESS]: '操作成功',
  [BusinessErrorCode.INVALID_PARAMS]: '请求参数无效',
  [BusinessErrorCode.UNAUTHORIZED]: '未授权，请先登录',
  [BusinessErrorCode.FORBIDDEN]: '禁止访问',
  [BusinessErrorCode.NOT_FOUND]: '资源不存在',
  [BusinessErrorCode.INTERNAL_ERROR]: '服务器内部错误',
  [BusinessErrorCode.CONFLICT]: '资源冲突',
  [BusinessErrorCode.VALIDATION_ERROR]: '数据验证失败',
  [BusinessErrorCode.RATE_LIMIT_EXCEEDED]: '请求过于频繁',
  [BusinessErrorCode.SERVICE_UNAVAILABLE]: '服务暂时不可用',

  // 用户相关
  [BusinessErrorCode.USER_NOT_FOUND]: '用户不存在',
  [BusinessErrorCode.USER_ALREADY_EXISTS]: '用户已存在',
  [BusinessErrorCode.INVALID_CREDENTIALS]: '用户名或密码错误',
  [BusinessErrorCode.TOKEN_EXPIRED]: '登录已过期，请重新登录',
  [BusinessErrorCode.TOKEN_INVALID]: '无效的令牌',
  [BusinessErrorCode.EMAIL_VERIFICATION_REQUIRED]: '需要验证邮箱',
  [BusinessErrorCode.PHONE_VERIFICATION_REQUIRED]: '需要验证手机号',

  // 支付相关
  [BusinessErrorCode.PAYMENT_FAILED]: '支付失败',
  [BusinessErrorCode.PAYMENT_AMOUNT_MISMATCH]: '支付金额不匹配',
  [BusinessErrorCode.PAYMENT_ORDER_NOT_FOUND]: '支付订单不存在',
  [BusinessErrorCode.PAYMENT_ORDER_ALREADY_PAID]: '订单已支付',
  [BusinessErrorCode.PAYMENT_ORDER_CANCELLED]: '订单已取消',
  [BusinessErrorCode.PAYMENT_CALLBACK_INVALID]: '支付回调无效',
  [BusinessErrorCode.PAYMENT_CALLBACK_DUPLICATE]: '重复的支付回调',
  [BusinessErrorCode.PAYMENT_METHOD_NOT_SUPPORTED]: '不支持的支付方式',
  [BusinessErrorCode.PAYMENT_PROCESSING_ERROR]: '支付处理错误',
  [BusinessErrorCode.PAYMENT_TIMEOUT]: '支付超时',
  [BusinessErrorCode.INSUFFICIENT_BALANCE]: '余额不足',

  // AI 相关
  [BusinessErrorCode.AI_SERVICE_UNAVAILABLE]: 'AI 服务不可用',
  [BusinessErrorCode.AI_QUOTA_EXCEEDED]: 'AI 配额已用完',
  [BusinessErrorCode.AI_REQUEST_TOO_LONG]: 'AI 请求超时',
  [BusinessErrorCode.AI_RESPONSE_INVALID]: 'AI 响应无效',
  [BusinessErrorCode.AI_TIMEOUT]: 'AI 服务超时',
  [BusinessErrorCode.AI_RATE_LIMIT_EXCEEDED]: 'AI 请求过于频繁',

  // 业务相关
  [BusinessErrorCode.INVALID_ORDER_TYPE]: '无效的订单类型',
  [BusinessErrorCode.ORDER_EXPIRED]: '订单已过期',
  [BusinessErrorCode.RESOURCE_NOT_FOUND]: '资源不存在',
  [BusinessErrorCode.RESOURCE_ALREADY_EXISTS]: '资源已存在',
  [BusinessErrorCode.OPERATION_NOT_ALLOWED]: '操作不被允许',

  // 内容相关
  [BusinessErrorCode.CONTENT_NOT_FOUND]: '内容不存在',
  [BusinessErrorCode.CONTENT_ALREADY_PUBLISHED]: '内容已发布',
  [BusinessErrorCode.CONTENT_MODIFICATION_NOT_ALLOWED]: '不允许修改内容',
  [BusinessErrorCode.CONTENT_VALIDATION_FAILED]: '内容验证失败',

  // 论坛相关
  [BusinessErrorCode.FORUM_POST_NOT_FOUND]: '帖子不存在',
  [BusinessErrorCode.FORUM_COMMENT_NOT_FOUND]: '评论不存在',
  [BusinessErrorCode.FORUM_POST_LOCKED]: '帖子已锁定',
  [BusinessErrorCode.FORUM_COMMENT_NOT_ALLOWED]: '不允许评论',

  // 系统相关
  [BusinessErrorCode.SYSTEM_MAINTENANCE]: '系统维护中',
  [BusinessErrorCode.SYSTEM_OVERLOADED]: '系统过载',
  [BusinessErrorCode.DATABASE_ERROR]: '数据库错误',
  [BusinessErrorCode.CACHE_ERROR]: '缓存错误',
  [BusinessErrorCode.EXTERNAL_SERVICE_ERROR]: '外部服务错误',
};

/**
 * 获取错误消息
 * @param code 错误码
 * @param fallback 默认消息
 * @returns 错误消息
 */
export function getErrorMessage(code: number, fallback = '未知错误'): string {
  return ERROR_MESSAGES[code] || fallback;
}

// ============================================================
// 分页信息
// ============================================================

/**
 * 分页信息接口
 * 与后端 [`PaginationInfo`](backend/app/core/response.py:160) 保持一致
 */
export interface PaginationInfo {
  /** 当前页码 (从 1 开始) */
  page: number;
  /** 每页大小 */
  page_size: number;
  /** 总记录数 */
  total: number;
  /** 总页数 */
  total_pages: number;
}

// ============================================================
// 统一 API 响应格式
// ============================================================

/**
 * 基础 API 响应接口
 * 与后端 [`ApiResponse`](backend/app/core/response.py:176) 保持一致
 *
 * 成功响应示例:
 * ```json
 * {
 *   "success": true,
 *   "message": "获取成功",
 *   "data": { "id": 1, "name": "test" },
 *   "error_code": null
 * }
 * ```
 *
 * 错误响应示例:
 * ```json
 * {
 *   "success": false,
 *   "message": "资源不存在",
 *   "data": null,
 *   "error_code": 1004
 * }
 * ```
 */
export interface ApiResponse<T = unknown> {
  /** 请求是否成功 */
  success: boolean;
  /** 响应消息 */
  message: string;
  /** 响应数据 */
  data: T | null;
  /** 错误码 (成功时为 null) */
  error_code?: number | null;
}

/**
 * 分页响应接口
 * 与后端 [`PaginatedResponse`](backend/app/core/response.py:206) 保持一致
 *
 * 示例:
 * ```json
 * {
 *   "success": true,
 *   "message": "获取成功",
 *   "data": [{ "id": 1 }, { "id": 2 }],
 *   "pagination": {
 *     "page": 1,
 *     "page_size": 20,
 *     "total": 100,
 *     "total_pages": 5
 *   }
 * }
 * ```
 */
export interface PaginatedResponse<T = unknown> {
  /** 请求是否成功 */
  success: boolean;
  /** 响应消息 */
  message: string;
  /** 数据列表 */
  data: T[];
  /** 分页信息 */
  pagination: PaginationInfo;
}

/**
 * 错误响应接口 (API 响应格式)
 */
export interface ApiResponseError {
  /** 始终为 false */
  success: false;
  /** 错误消息 */
  message: string;
  /** 始终为 null */
  data: null;
  /** 错误码 */
  error_code: number;
  /** 额外的错误详情 (可选) */
  details?: unknown[];
}

// ============================================================
// 类型守卫
// ============================================================

/**
 * 判断是否为成功响应
 */
export function isSuccessResponse<T>(
  response: ApiResponse<T> | ApiError
): response is ApiResponse<T> {
  return 'success' in response && response.success === true;
}

/**
 * 判断是否为错误响应
 */
export function isErrorResponse<T>(
  response: ApiResponse<T> | ApiError
): response is ApiError {
  return !('success' in response) || response.success !== true;
}

/**
 * 判断是否为分页响应
 */
export function isPaginatedResponse<T>(
  response: ApiResponse<T> | PaginatedResponse<T>
): response is PaginatedResponse<T> {
  return (
    'pagination' in response &&
    typeof (response).pagination === 'object'
  );
}

// ============================================================
// 工具类型
// ============================================================

/**
 * 从 API 响应中提取数据的工具类型
 */
export type ExtractData<T> = T extends ApiResponse<infer U> ? U : never;

/**
 * 从分页响应中提取数据项的工具类型
 */
export type ExtractItems<T> = T extends PaginatedResponse<infer U> ? U[] : never;

/**
 * 通用 API 响应类型
 * 支持普通响应和分页响应
 */
export type AnyApiResponse<T = unknown> = ApiResponse<T> | PaginatedResponse<T>;

/**
 * 空响应数据类型
 */
export type VoidData = null;

/**
 * 列表响应数据类型
 */
export type ListData<T> = T[];

// ============================================================
// 请求配置类型
// ============================================================

/**
 * 通用请求配置
 */
export interface RequestConfig {
  /** 请求超时时间 (毫秒) */
  timeout?: number;
  /** 是否需要认证 */
  requiresAuth?: boolean;
  /** 是否显示错误提示 */
  showErrorToast?: boolean;
  /** 是否显示成功提示 */
  showSuccessToast?: boolean;
  /** 自定义请求头 */
  headers?: Record<string, string>;
}

/**
 * 分页请求参数
 */
export interface PaginationParams {
  /** 页码 (从 1 开始) */
  page: number;
  /** 每页大小 */
  page_size: number;
}

/**
 * 通用列表请求参数
 */
export interface ListQueryParams extends PaginationParams {
  /** 搜索关键词 */
  keyword?: string;
  /** 排序字段 */
  sort_by?: string;
  /** 排序方向 */
  sort_order?: 'asc' | 'desc';
  /** 额外筛选条件 */
  filters?: Record<string, unknown>;
}

// ============================================================
// 上传相关类型
// ============================================================

/**
 * 文件上传响应
 */
export interface UploadResponse {
  /** 文件 ID */
  file_id: string;
  /** 文件 URL */
  file_url: string;
  /** 文件名 */
  file_name: string;
  /** 文件大小 (字节) */
  file_size: number;
  /** 文件类型 */
  file_type: string;
}

/**
 * 上传进度
 */
export interface UploadProgress {
  /** 已上传字节数 */
  loaded: number;
  /** 总字节数 */
  total: number;
  /** 上传百分比 (0-100) */
  percentage: number;
}

// ============================================================
// WebSocket 相关类型
// ============================================================

/**
 * WebSocket 消息类型
 */
export interface WebSocketMessage<T = unknown> {
  /** 消息类型 */
  type: string;
  /** 消息数据 */
  data: T;
  /** 消息时间戳 */
  timestamp: number;
}

/**
 * WebSocket 连接状态
 */
export type WebSocketState = 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED';