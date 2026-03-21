/**
 * 统一错误处理模块
 *
 * 功能：
 * - 错误类型定义（与后端 ErrorCode 保持一致）
 * - 错误分类处理（网络错误、业务错误、认证错误）
 * - 错误码到用户友好消息的映射
 * - 错误处理策略配置
 * - 统一错误提示组件
 * - 错误日志上报
 */

import { AxiosError } from 'axios';

import {
  BusinessErrorCode,
  getErrorMessage,
  getErrorCodeRange,
  ERROR_MESSAGES,
} from '../shared/lib/api/types';

// ============================================
// 重新导出 BusinessErrorCode 供外部使用
// ============================================
export { BusinessErrorCode, getErrorMessage, getErrorCodeRange, ERROR_MESSAGES };

// ============================================
// 错误类型定义
// ============================================

/**
 * 错误分类
 */
export enum ErrorCategory {
  /** 网络错误 */
  NETWORK = 'NETWORK',
  /** 认证错误 */
  AUTH = 'AUTH',
  /** 业务错误 */
  BUSINESS = 'BUSINESS',
  /** 验证错误 */
  VALIDATION = 'VALIDATION',
  /** 服务器错误 */
  SERVER = 'SERVER',
  /** 权限错误 */
  PERMISSION = 'PERMISSION',
  /** 未知错误 */
  UNKNOWN = 'UNKNOWN',
}

/**
 * 统一错误接口
 */
export interface ApiError {
  /** 错误码 */
  code: number;
  /** 错误消息 */
  message: string;
  /** 错误分类 */
  category?: ErrorCategory;
  /** 详细错误信息（字段级） */
  details?: Record<string, string[]>;
  /** 验证错误列表（FastAPI 格式） */
  validationErrors?: Array<{
    type: string;
    loc: string[];
    msg: string;
    input?: unknown;
  }>;
  /** 原始错误对象 */
  originalError?: unknown;
  /** 请求 URL */
  url?: string;
  /** 请求方法 */
  method?: string;
  /** 时间戳 */
  timestamp?: number;
  /** 后端返回的错误码 */
  error_code?: number;
}

/**
 * 错误提示配置
 */
export interface ErrorToastConfig {
  /** 是否显示 */
  enabled: boolean;
  /** 显示时长（毫秒） */
  duration: number;
  /** 是否显示详细错误 */
  showDetails: boolean;
}

// ============================================
// 扩展错误消息映射（包含标题和操作建议）
// ============================================

/**
 * 扩展错误消息接口
 */
export interface ExtendedErrorMessage {
  /** 错误标题（简短描述） */
  title: string;
  /** 操作建议（可选） */
  action?: string;
  /** 图标类型（可选） */
  icon?: 'error' | 'warning' | 'info' | 'success';
}

/**
 * 扩展错误消息映射表
 * 提供更友好的用户提示和操作建议
 */
export const EXTENDED_ERROR_MESSAGES: Record<number, ExtendedErrorMessage> = {
  // 通用错误 1000-1999
  [BusinessErrorCode.SUCCESS]: {
    title: '操作成功',
    icon: 'success',
  },
  [BusinessErrorCode.INVALID_PARAMS]: {
    title: '请求参数无效',
    action: '请检查输入内容后重试',
  },
  [BusinessErrorCode.UNAUTHORIZED]: {
    title: '未登录',
    action: '请先登录后再继续操作',
    icon: 'warning',
  },
  [BusinessErrorCode.FORBIDDEN]: {
    title: '禁止访问',
    action: '您没有权限执行此操作',
    icon: 'warning',
  },
  [BusinessErrorCode.NOT_FOUND]: {
    title: '资源不存在',
    action: '请检查请求的资源是否正确',
  },
  [BusinessErrorCode.INTERNAL_ERROR]: {
    title: '服务器错误',
    action: '请稍后重试，如问题持续请联系客服',
    icon: 'error',
  },
  [BusinessErrorCode.CONFLICT]: {
    title: '资源冲突',
    action: '该资源已被其他用户修改，请刷新后重试',
  },
  [BusinessErrorCode.VALIDATION_ERROR]: {
    title: '数据验证失败',
    action: '请检查输入内容是否符合要求',
  },
  [BusinessErrorCode.RATE_LIMIT_EXCEEDED]: {
    title: '请求过于频繁',
    action: '请稍后再试',
    icon: 'warning',
  },
  [BusinessErrorCode.SERVICE_UNAVAILABLE]: {
    title: '服务暂时不可用',
    action: '系统正在维护中，请稍后再试',
    icon: 'warning',
  },

  // 用户相关 2000-2999
  [BusinessErrorCode.USER_NOT_FOUND]: {
    title: '用户不存在',
    action: '请检查用户信息或联系客服',
  },
  [BusinessErrorCode.USER_ALREADY_EXISTS]: {
    title: '用户已存在',
    action: '该账号已被注册，请直接登录或使用其他账号',
  },
  [BusinessErrorCode.INVALID_CREDENTIALS]: {
    title: '登录失败',
    action: '用户名或密码错误，请检查后重试',
    icon: 'warning',
  },
  [BusinessErrorCode.TOKEN_EXPIRED]: {
    title: '登录已过期',
    action: '请重新登录',
    icon: 'warning',
  },
  [BusinessErrorCode.TOKEN_INVALID]: {
    title: '无效的登录状态',
    action: '请重新登录',
    icon: 'warning',
  },
  [BusinessErrorCode.EMAIL_VERIFICATION_REQUIRED]: {
    title: '需要验证邮箱',
    action: '请前往邮箱完成验证',
    icon: 'info',
  },
  [BusinessErrorCode.PHONE_VERIFICATION_REQUIRED]: {
    title: '需要验证手机号',
    action: '请完成手机号验证',
    icon: 'info',
  },

  // 支付相关 3000-3999
  [BusinessErrorCode.PAYMENT_FAILED]: {
    title: '支付失败',
    action: '请检查支付信息后重试',
    icon: 'error',
  },
  [BusinessErrorCode.PAYMENT_AMOUNT_MISMATCH]: {
    title: '支付金额不匹配',
    action: '订单金额已变更，请刷新页面后重试',
    icon: 'warning',
  },
  [BusinessErrorCode.PAYMENT_ORDER_NOT_FOUND]: {
    title: '订单不存在',
    action: '请检查订单号是否正确',
  },
  [BusinessErrorCode.PAYMENT_ORDER_ALREADY_PAID]: {
    title: '订单已支付',
    action: '无需重复支付',
    icon: 'info',
  },
  [BusinessErrorCode.PAYMENT_ORDER_CANCELLED]: {
    title: '订单已取消',
    action: '如需购买请重新下单',
    icon: 'warning',
  },
  [BusinessErrorCode.PAYMENT_CALLBACK_INVALID]: {
    title: '支付回调无效',
    action: '请联系客服处理',
    icon: 'error',
  },
  [BusinessErrorCode.PAYMENT_CALLBACK_DUPLICATE]: {
    title: '重复的支付回调',
    action: '订单已处理，请勿重复操作',
    icon: 'warning',
  },
  [BusinessErrorCode.PAYMENT_METHOD_NOT_SUPPORTED]: {
    title: '不支持的支付方式',
    action: '请选择其他支付方式',
  },
  [BusinessErrorCode.PAYMENT_PROCESSING_ERROR]: {
    title: '支付处理错误',
    action: '请稍后重试或联系客服',
    icon: 'error',
  },
  [BusinessErrorCode.PAYMENT_TIMEOUT]: {
    title: '支付超时',
    action: '请重新发起支付',
    icon: 'warning',
  },
  [BusinessErrorCode.INSUFFICIENT_BALANCE]: {
    title: '余额不足',
    action: '请先充值或选择其他支付方式',
    icon: 'warning',
  },

  // AI 相关 4000-4999
  [BusinessErrorCode.AI_SERVICE_UNAVAILABLE]: {
    title: 'AI 服务暂时不可用',
    action: '请稍后重试',
    icon: 'warning',
  },
  [BusinessErrorCode.AI_QUOTA_EXCEEDED]: {
    title: 'AI 配额已用完',
    action: '请升级会员或等待配额重置',
    icon: 'warning',
  },
  [BusinessErrorCode.AI_REQUEST_TOO_LONG]: {
    title: '请求内容过长',
    action: '请精简内容后重试',
  },
  [BusinessErrorCode.AI_RESPONSE_INVALID]: {
    title: 'AI 响应异常',
    action: '请重新提问',
    icon: 'warning',
  },
  [BusinessErrorCode.AI_TIMEOUT]: {
    title: 'AI 服务响应超时',
    action: '请稍后重试',
    icon: 'warning',
  },
  [BusinessErrorCode.AI_RATE_LIMIT_EXCEEDED]: {
    title: 'AI 请求过于频繁',
    action: '请稍后再试',
    icon: 'warning',
  },

  // 业务相关 5000-5999
  [BusinessErrorCode.INVALID_ORDER_TYPE]: {
    title: '无效的订单类型',
    action: '请选择正确的订单类型',
  },
  [BusinessErrorCode.ORDER_EXPIRED]: {
    title: '订单已过期',
    action: '请重新下单',
    icon: 'warning',
  },
  [BusinessErrorCode.RESOURCE_NOT_FOUND]: {
    title: '资源不存在',
    action: '请检查资源是否已被删除',
  },
  [BusinessErrorCode.RESOURCE_ALREADY_EXISTS]: {
    title: '资源已存在',
    action: '请勿重复创建',
    icon: 'info',
  },
  [BusinessErrorCode.OPERATION_NOT_ALLOWED]: {
    title: '操作不被允许',
    action: '您没有权限执行此操作',
    icon: 'warning',
  },

  // 内容相关 6000-6999
  [BusinessErrorCode.CONTENT_NOT_FOUND]: {
    title: '内容不存在',
    action: '该内容可能已被删除',
  },
  [BusinessErrorCode.CONTENT_ALREADY_PUBLISHED]: {
    title: '内容已发布',
    action: '请勿重复发布',
    icon: 'info',
  },
  [BusinessErrorCode.CONTENT_MODIFICATION_NOT_ALLOWED]: {
    title: '不允许修改内容',
    action: '该内容已锁定或无权限修改',
    icon: 'warning',
  },
  [BusinessErrorCode.CONTENT_VALIDATION_FAILED]: {
    title: '内容验证失败',
    action: '请检查内容是否符合规范',
  },

  // 论坛相关 7000-7999
  [BusinessErrorCode.FORUM_POST_NOT_FOUND]: {
    title: '帖子不存在',
    action: '该帖子可能已被删除或下架',
  },
  [BusinessErrorCode.FORUM_COMMENT_NOT_FOUND]: {
    title: '评论不存在',
    action: '该评论可能已被删除',
  },
  [BusinessErrorCode.FORUM_POST_LOCKED]: {
    title: '帖子已锁定',
    action: '该帖子无法回复',
    icon: 'warning',
  },
  [BusinessErrorCode.FORUM_COMMENT_NOT_ALLOWED]: {
    title: '不允许评论',
    action: '您没有权限在此帖子下评论',
    icon: 'warning',
  },

  // 系统相关 8000-8999
  [BusinessErrorCode.SYSTEM_MAINTENANCE]: {
    title: '系统维护中',
    action: '系统正在进行维护，请稍后再试',
    icon: 'warning',
  },
  [BusinessErrorCode.SYSTEM_OVERLOADED]: {
    title: '系统繁忙',
    action: '当前访问量较大，请稍后再试',
    icon: 'warning',
  },
  [BusinessErrorCode.DATABASE_ERROR]: {
    title: '数据库错误',
    action: '请稍后重试，如问题持续请联系客服',
    icon: 'error',
  },
  [BusinessErrorCode.CACHE_ERROR]: {
    title: '缓存服务异常',
    action: '请稍后重试',
    icon: 'warning',
  },
  [BusinessErrorCode.EXTERNAL_SERVICE_ERROR]: {
    title: '外部服务异常',
    action: '请稍后重试',
    icon: 'warning',
  },
};

/**
 * 获取扩展错误消息
 * @param code 错误码
 * @returns 扩展错误消息
 */
export function getExtendedErrorMessage(code: number): ExtendedErrorMessage {
  return (
    EXTENDED_ERROR_MESSAGES[code] || {
      title: getErrorMessage(code),
      action: '请稍后重试',
    }
  );
}

// ============================================
// 错误处理策略配置
// ============================================

/**
 * 错误处理策略接口
 */
export interface ErrorHandlingStrategy {
  /** 是否显示 Toast 提示 */
  shouldShowToast: boolean;
  /** 是否记录日志 */
  shouldLog: boolean;
  /** 是否上报到监控 */
  shouldReport: boolean;
  /** 重定向 URL（可选） */
  redirectUrl?: string;
  /** 是否可重试 */
  retryable: boolean;
  /** Toast 显示时长（毫秒，可选） */
  toastDuration?: number;
}

/**
 * 默认错误处理策略
 */
const DEFAULT_STRATEGY: ErrorHandlingStrategy = {
  shouldShowToast: true,
  shouldLog: true,
  shouldReport: false,
  retryable: true,
};

/**
 * 错误处理策略映射表
 */
const ERROR_STRATEGIES: Record<number, ErrorHandlingStrategy> = {
  // 认证相关错误 - 重定向到登录页
  [BusinessErrorCode.UNAUTHORIZED]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: false,
    redirectUrl: '/login',
    retryable: false,
  },
  [BusinessErrorCode.TOKEN_EXPIRED]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: false,
    redirectUrl: '/login',
    retryable: false,
  },
  [BusinessErrorCode.TOKEN_INVALID]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: false,
    redirectUrl: '/login',
    retryable: false,
  },

  // 权限相关错误
  [BusinessErrorCode.FORBIDDEN]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: false,
    redirectUrl: '/',
    retryable: false,
  },
  [BusinessErrorCode.OPERATION_NOT_ALLOWED]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: false,
    retryable: false,
  },

  // 限流错误 - 不重试
  [BusinessErrorCode.RATE_LIMIT_EXCEEDED]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: false,
    retryable: false,
    toastDuration: 5000,
  },
  [BusinessErrorCode.AI_RATE_LIMIT_EXCEEDED]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: false,
    retryable: false,
    toastDuration: 5000,
  },

  // 系统错误 - 上报
  [BusinessErrorCode.INTERNAL_ERROR]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: true,
    retryable: true,
  },
  [BusinessErrorCode.DATABASE_ERROR]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: true,
    retryable: true,
  },
  [BusinessErrorCode.SYSTEM_MAINTENANCE]: {
    shouldShowToast: true,
    shouldLog: false,
    shouldReport: false,
    retryable: false,
  },
  [BusinessErrorCode.SYSTEM_OVERLOADED]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: true,
    retryable: true,
  },

  // 支付错误
  [BusinessErrorCode.PAYMENT_FAILED]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: true,
    retryable: true,
  },
  [BusinessErrorCode.INSUFFICIENT_BALANCE]: {
    shouldShowToast: true,
    shouldLog: false,
    shouldReport: false,
    retryable: false,
  },

  // AI 相关错误
  [BusinessErrorCode.AI_SERVICE_UNAVAILABLE]: {
    shouldShowToast: true,
    shouldLog: true,
    shouldReport: true,
    retryable: true,
  },
  [BusinessErrorCode.AI_QUOTA_EXCEEDED]: {
    shouldShowToast: true,
    shouldLog: false,
    shouldReport: false,
    retryable: false,
  },

  // 验证错误 - 不显示 Toast（通常在表单中显示）
  [BusinessErrorCode.VALIDATION_ERROR]: {
    shouldShowToast: false,
    shouldLog: false,
    shouldReport: false,
    retryable: false,
  },
  [BusinessErrorCode.INVALID_PARAMS]: {
    shouldShowToast: false,
    shouldLog: false,
    shouldReport: false,
    retryable: false,
  },
};

/**
 * 获取错误处理策略
 * @param errorCode 错误码
 * @returns 错误处理策略
 */
export function getErrorStrategy(errorCode: number): ErrorHandlingStrategy {
  return ERROR_STRATEGIES[errorCode] || DEFAULT_STRATEGY;
}

// ============================================
// 错误分类工具
// ============================================

/**
 * 根据 HTTP 状态码分类错误
 * @param status - HTTP 状态码
 * @returns 错误分类
 */
export function categorizeErrorByStatus(status: number): ErrorCategory {
  if (status >= 500) {
    return ErrorCategory.SERVER;
  }

  switch (status) {
    case 401:
      return ErrorCategory.AUTH;
    case 403:
      return ErrorCategory.PERMISSION;
    case 422:
      return ErrorCategory.VALIDATION;
    case 400:
    case 404:
    case 405:
    case 409:
    case 429:
      return ErrorCategory.BUSINESS;
    default:
      return ErrorCategory.UNKNOWN;
  }
}

/**
 * 根据业务错误码分类错误
 * @param errorCode 业务错误码
 * @returns 错误分类
 */
export function categorizeByErrorCode(errorCode: number): ErrorCategory {
  const range = getErrorCodeRange(errorCode);

  switch (range) {
    case 'USER': {
      const authCodes: number[] = [
        BusinessErrorCode.UNAUTHORIZED,
        BusinessErrorCode.TOKEN_EXPIRED,
        BusinessErrorCode.TOKEN_INVALID,
      ];
      if (authCodes.includes(errorCode)) {
        return ErrorCategory.AUTH;
      }
      return ErrorCategory.BUSINESS;
    }

    case 'PAYMENT':
    case 'BUSINESS':
    case 'CONTENT':
    case 'FORUM':
      return ErrorCategory.BUSINESS;

    case 'AI':
      return ErrorCategory.BUSINESS;

    case 'SYSTEM':
      return ErrorCategory.SERVER;

    case 'RATE_LIMIT':
      return ErrorCategory.BUSINESS;

    default:
      return ErrorCategory.UNKNOWN;
  }
}

/**
 * 判断是否为网络错误
 * @param error - 错误对象
 * @returns 是否为网络错误
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return !error.response && error.code !== 'ECONNABORTED';
  }
  return false;
}

/**
 * 判断是否为认证错误
 * @param error - 错误对象
 * @returns 是否为认证错误
 */
export function isAuthError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 401;
  }
  if (isApiError(error)) {
    if (
      error.code === 401 ||
      error.category === ErrorCategory.AUTH
    ) {
      return true;
    }
    const errorCode = error.error_code;
    if (errorCode !== undefined) {
      const authErrorCodes: number[] = [
        BusinessErrorCode.UNAUTHORIZED,
        BusinessErrorCode.TOKEN_EXPIRED,
        BusinessErrorCode.TOKEN_INVALID,
      ];
      return authErrorCodes.includes(errorCode);
    }
    return false;
  }
  return false;
}

/**
 * 判断是否为验证错误
 * @param error - 错误对象
 * @returns 是否为验证错误
 */
export function isValidationError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 422;
  }
  if (isApiError(error)) {
    if (
      error.code === 422 ||
      error.category === ErrorCategory.VALIDATION
    ) {
      return true;
    }
    const errorCode = error.error_code;
    if (errorCode !== undefined) {
      const validationErrorCodes: number[] = [
        BusinessErrorCode.VALIDATION_ERROR,
        BusinessErrorCode.INVALID_PARAMS,
      ];
      return validationErrorCodes.includes(errorCode);
    }
    return false;
  }
  return false;
}

/**
 * 判断是否为可重试错误
 * @param error - 错误对象
 * @returns 是否可重试
 */
export function isRetryableError(error: unknown): boolean {
  if (isApiError(error) && error.error_code !== undefined) {
    const strategy = getErrorStrategy(error.error_code);
    return strategy.retryable;
  }
  // 网络错误通常可以重试
  if (isNetworkError(error)) {
    return true;
  }
  // 5xx 服务器错误可以重试
  if (error instanceof AxiosError && error.response?.status) {
    return error.response.status >= 500;
  }
  return false;
}

// ============================================
// 类型守卫
// ============================================

/**
 * 判断是否为 ApiError 类型
 * @param error - 错误对象
 * @returns 是否为 ApiError
 */
export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error
  );
}

// ============================================
// 错误格式化
// ============================================

/**
 * 格式化错误消息
 * @param error - 错误对象
 * @returns 格式化后的错误消息
 */
export function formatErrorMessage(error: unknown): string {
  // 处理后端返回的业务错误码
  if (isApiError(error) && error.error_code !== undefined) {
    return getErrorMessage(error.error_code, error.message);
  }

  if (isApiError(error)) {
    return error.message;
  }

  if (error instanceof AxiosError) {
    // 处理后端统一响应格式中的 error_code
    const responseData = error.response?.data as {
      error_code?: number;
      message?: string;
      msg?: string;
      detail?: string | Array<{ loc: string[]; msg: string }>;
    };

    if (responseData?.error_code !== undefined) {
      return getErrorMessage(responseData.error_code, responseData.message || '未知错误');
    }

    // 处理 FastAPI 422 验证错误
    if (error.response?.status === 422) {
      if (Array.isArray(responseData?.detail)) {
        return responseData.detail
          .map((err) => {
            const field = err.loc?.join('.') || '';
            return field ? `${field}: ${err.msg}` : err.msg;
          })
          .join('; ');
      }
    }

    // 处理一般错误
    if (responseData) {
      const detail = responseData.detail;
      if (typeof detail === 'string') {
        return detail;
      }
      return responseData.message || responseData.msg || error.message;
    }

    // 网络错误
    if (!error.response) {
      return '网络连接失败，请检查网络设置';
    }

    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  return '未知错误，请稍后重试';
}

/**
 * 格式化验证错误
 * @param error - 错误对象
 * @returns 字段级错误映射
 */
export function formatValidationErrors(error: unknown): Record<string, string[]> {
  if (isApiError(error) && error.details) {
    return error.details;
  }

  if (error instanceof AxiosError && error.response?.status === 422) {
    const data = error.response.data as { detail?: Array<{ loc: string[]; msg: string }> };
    if (Array.isArray(data?.detail)) {
      const errors: Record<string, string[]> = {};
      for (const err of data.detail) {
        const field = err.loc?.length > 1 ? err.loc.slice(1).join('.') : 'form';
        if (!errors[field]) {
          errors[field] = [];
        }
        errors[field].push(err.msg);
      }
      return errors;
    }
  }

  return {};
}

// ============================================
// 错误日志上报
// ============================================

/**
 * 错误日志配置
 */
interface ErrorLogConfig {
  /** 是否启用日志 */
  enabled: boolean;
  /** 是否上报到服务端 */
  reportToServer: boolean;
  /** 是否记录到控制台 */
  logToConsole: boolean;
  /** 错误上报端点 */
  reportUrl: string;
}

const DEFAULT_LOG_CONFIG: ErrorLogConfig = {
  enabled: true,
  reportToServer: false,
  logToConsole: true,
  reportUrl: '/api/logs/error',
};

/**
 * 记录错误日志
 * @param error - 错误对象
 * @param context - 上下文信息
 */
export function logError(
  error: ApiError,
  context?: {
    component?: string;
    action?: string;
    userId?: string;
    extra?: Record<string, unknown>;
  }
): void {
  const apiError = normalizeError(error);
  const errorLog = {
    ...apiError,
    timestamp: Date.now(),
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
    url: typeof window !== 'undefined' ? window.location.href : 'unknown',
    context,
  };

  // 记录到控制台
  if (DEFAULT_LOG_CONFIG.logToConsole) {
    console.error('[Error Log]', JSON.stringify(errorLog, null, 2));
  }

  // 上报到服务端（如果启用）
  if (DEFAULT_LOG_CONFIG.reportToServer) {
    // 使用 sendBeacon 发送错误日志，不会阻塞页面
    if (typeof navigator !== 'undefined' && 'sendBeacon' in navigator) {
      navigator.sendBeacon(DEFAULT_LOG_CONFIG.reportUrl, JSON.stringify(errorLog));
    }
  }
}

/**
 * 批量上报错误日志
 * @param errors - 错误列表
 */
export async function reportErrors(errors: ApiError[]): Promise<void> {
  if (!DEFAULT_LOG_CONFIG.reportToServer || errors.length === 0) {
    return;
  }

  try {
    // 使用 fetch 发送错误日志
    await fetch(DEFAULT_LOG_CONFIG.reportUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        errors: errors.map((err) => ({
          ...err,
          timestamp: err.timestamp || Date.now(),
        })),
        reportedAt: new Date().toISOString(),
      }),
    });
  } catch (reportError) {
    // 上报失败时记录到控制台
    console.error('[Error Report Failed]', reportError);
  }
}

// ============================================
// 错误标准化
// ============================================

/**
 * 将未知错误转换为标准 ApiError 格式
 * @param error - 未知错误
 * @returns 标准化的 ApiError
 */
export function normalizeError(error: unknown): ApiError {
  if (isApiError(error)) {
    return {
      ...error,
      timestamp: error.timestamp || Date.now(),
    };
  }

  if (error instanceof AxiosError) {
    const responseData = error.response?.data as {
      error_code?: number;
      message?: string;
    };
    const errorCode = responseData?.error_code;
    const category = errorCode
      ? categorizeByErrorCode(errorCode)
      : error.response
        ? categorizeErrorByStatus(error.response.status)
        : ErrorCategory.NETWORK;

    return {
      code: error.response?.status || 0,
      message: formatErrorMessage(error),
      category,
      details: formatValidationErrors(error),
      validationErrors: (error.response?.data as Record<string, unknown>)?.detail as Array<{
        type: string;
        loc: string[];
        msg: string;
        input?: unknown;
      }>,
      url: error.config?.url,
      method: error.config?.method?.toUpperCase(),
      originalError: error,
      timestamp: Date.now(),
      error_code: errorCode,
    };
  }

  if (error instanceof Error) {
    return {
      code: 0,
      message: error.message,
      category: ErrorCategory.UNKNOWN,
      originalError: error,
      timestamp: Date.now(),
    };
  }

  return {
    code: 0,
    message: typeof error === 'string' ? error : '未知错误',
    category: ErrorCategory.UNKNOWN,
    timestamp: Date.now(),
  };
}

// ============================================
// 错误提示组件辅助
// ============================================

/**
 * 获取错误提示的严重程度
 * @param category - 错误分类
 * @returns 严重程度
 */
export function getErrorSeverity(category: ErrorCategory): 'info' | 'warning' | 'error' {
  switch (category) {
    case ErrorCategory.NETWORK:
    case ErrorCategory.SERVER:
      return 'error';
    case ErrorCategory.AUTH:
    case ErrorCategory.PERMISSION:
      return 'warning';
    case ErrorCategory.VALIDATION:
    case ErrorCategory.BUSINESS:
      return 'info';
    default:
      return 'error';
  }
}

/**
 * 获取错误提示的自动关闭时间
 * @param category - 错误分类
 * @returns 关闭时间（毫秒）
 */
export function getErrorAutoCloseDuration(category: ErrorCategory): number {
  switch (category) {
    case ErrorCategory.VALIDATION:
      return 5000;
    case ErrorCategory.BUSINESS:
      return 3000;
    case ErrorCategory.NETWORK:
    case ErrorCategory.SERVER:
      return 8000;
    default:
      return 4000;
  }
}

// ============================================
// Toast 接口定义
// ============================================

/**
 * Toast 显示函数类型
 */
export type ToastFunction = (
  message: string,
  options?: {
    type?: 'success' | 'error' | 'warning' | 'info';
    duration?: number;
    action?: string;
  }
) => void;

/**
 * 导航函数类型
 */
export type NavigateFunction = (url: string) => void;

// ============================================
// 错误处理类
// ============================================

/**
 * 统一错误处理器
 */
export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorQueue: ApiError[] = [];
  private config: ErrorToastConfig = {
    enabled: true,
    duration: 4000,
    showDetails: false,
  };
  private toastFn: ToastFunction | null = null;
  private navigateFn: NavigateFunction | null = null;

  private constructor() {}

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  /**
   * 设置 Toast 显示函数
   * @param fn Toast 显示函数
   */
  setToastFunction(fn: ToastFunction): void {
    this.toastFn = fn;
  }

  /**
   * 设置导航函数
   * @param fn 导航函数
   */
  setNavigateFunction(fn: NavigateFunction): void {
    this.navigateFn = fn;
  }

  /**
   * 处理错误
   * @param error - 错误对象
   * @param options - 处理选项
   */
  handle(
    error: unknown,
    options?: {
      showToast?: boolean;
      logError?: boolean;
      context?: { component?: string; action?: string };
      overrideStrategy?: Partial<ErrorHandlingStrategy>;
    }
  ): ApiError {
    const apiError = normalizeError(error);
    const errorCode = apiError.error_code;
    const strategy = errorCode !== undefined ? getErrorStrategy(errorCode) : DEFAULT_STRATEGY;
    const mergedStrategy = { ...strategy, ...options?.overrideStrategy };

    // 记录错误日志
    if (mergedStrategy.shouldLog && options?.logError !== false) {
      logError(apiError, options?.context);
    }

    // 上报错误
    if (mergedStrategy.shouldReport) {
      this.reportError(apiError);
    }

    // 加入错误队列
    this.errorQueue.push(apiError);

    // 显示错误提示
    if (mergedStrategy.shouldShowToast && options?.showToast !== false && this.config.enabled) {
      this.showToast(apiError, mergedStrategy);
    }

    // 处理重定向
    if (mergedStrategy.redirectUrl && this.navigateFn) {
      this.navigateFn(mergedStrategy.redirectUrl);
    }

    return apiError;
  }

  /**
   * 显示错误提示
   * @param error - 错误对象
   * @param strategy - 处理策略
   */
  private showToast(error: ApiError, strategy: ErrorHandlingStrategy): void {
    const errorCode = error.error_code;
    const extendedMessage = errorCode !== undefined ? getExtendedErrorMessage(errorCode) : null;
    const message = extendedMessage?.title || formatErrorMessage(error);
    const severity = getErrorSeverity(error.category || ErrorCategory.UNKNOWN);
    const duration = strategy.toastDuration || getErrorAutoCloseDuration(error.category || ErrorCategory.UNKNOWN);

    if (this.toastFn) {
      this.toastFn(message, {
        type: severity === 'info' ? 'info' : severity === 'warning' ? 'warning' : 'error',
        duration,
        action: extendedMessage?.action,
      });
    } else {
      // 临时实现：使用 console 输出
      if (import.meta.env.DEV) {
        // eslint-disable-next-line no-console
        console.log(`[${severity.toUpperCase()}] ${message}${extendedMessage?.action ? ` - ${extendedMessage.action}` : ''}`);
      }
    }
  }

  /**
   * 上报单个错误
   * @param error - 错误对象
   */
  private reportError(error: ApiError): void {
    if (typeof navigator !== 'undefined' && 'sendBeacon' in navigator) {
      navigator.sendBeacon(
        DEFAULT_LOG_CONFIG.reportUrl,
        JSON.stringify({
          ...error,
          reportedAt: new Date().toISOString(),
        })
      );
    }
  }

  /**
   * 获取错误队列
   */
  getErrorQueue(): ApiError[] {
    return [...this.errorQueue];
  }

  /**
   * 清除错误队列
   */
  clearQueue(): void {
    this.errorQueue = [];
  }

  /**
   * 配置处理器
   */
  configure(config: Partial<ErrorToastConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

// ============================================
// 便捷函数
// ============================================

/**
 * 处理错误的便捷函数
 * @param error - 错误对象
 * @param options - 处理选项
 */
export function handleError(
  error: unknown,
  options?: Parameters<typeof ErrorHandler.prototype.handle>[1]
): ApiError {
  return ErrorHandler.getInstance().handle(error, options);
}

/**
 * 创建安全的异步调用包装器
 * @param fn - 异步函数
 * @param errorHandler - 错误处理函数
 * @returns 包装后的函数
 */
export function withErrorHandling<TArgs extends unknown[], TReturn>(
  fn: (...args: TArgs) => Promise<TReturn>,
  errorHandler?: (error: unknown) => void
): (...args: TArgs) => Promise<TReturn> {
  return async (...args: TArgs): Promise<TReturn> => {
    try {
      return await fn(...args);
    } catch (error) {
      if (errorHandler) {
        errorHandler(error);
      } else {
        handleError(error);
      }
      throw error;
    }
  };
}

/**
 * 初始化错误处理器
 * @param options 初始化选项
 */
export function initializeErrorHandler(options?: {
  toastFn?: ToastFunction;
  navigateFn?: NavigateFunction;
  config?: Partial<ErrorToastConfig>;
}): void {
  const handler = ErrorHandler.getInstance();
  if (options?.toastFn) {
    handler.setToastFunction(options.toastFn);
  }
  if (options?.navigateFn) {
    handler.setNavigateFunction(options.navigateFn);
  }
  if (options?.config) {
    handler.configure(options.config);
  }
}

// ============================================
// 导出
// ============================================
export default {
  // 类型
  ErrorCategory,
  // 核心函数
  normalizeError,
  formatErrorMessage,
  formatValidationErrors,
  categorizeErrorByStatus,
  categorizeByErrorCode,
  // 类型判断
  isNetworkError,
  isAuthError,
  isValidationError,
  isRetryableError,
  isApiError,
  // 日志
  logError,
  reportErrors,
  // 错误处理
  handleError,
  withErrorHandling,
  ErrorHandler,
  initializeErrorHandler,
  // 辅助函数
  getErrorSeverity,
  getErrorAutoCloseDuration,
  getErrorStrategy,
  getExtendedErrorMessage,
  // 映射表
  EXTENDED_ERROR_MESSAGES,
  ERROR_STRATEGIES,
};