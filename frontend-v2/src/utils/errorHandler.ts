/**
 * 统一错误处理模块
 *
 * 本模块已拆分为多个子模块:
 * - types: 错误类型定义
 * - messages: 错误消息映射
 * - strategies: 错误处理策略
 * - utils: 错误工具函数
 * - logging: 错误日志
 * - handler: 错误处理器
 */

export * from './errors';

import {
  normalizeError as originalNormalizeError,
  formatErrorMessage as originalFormatErrorMessage,
  formatValidationErrors as originalFormatValidationErrors,
} from './errors/utils';

export {
  EXTENDED_ERROR_MESSAGES,
  getExtendedErrorMessage,
  getErrorStrategy,
  DEFAULT_STRATEGY,
  ERROR_STRATEGIES,
  categorizeErrorByStatus,
  categorizeByErrorCode,
  isNetworkError,
  isAuthError,
  isValidationError,
  formatErrorMessage,
  formatValidationErrors,
  getErrorSeverity,
  getErrorAutoCloseDuration,
  logError,
  reportErrors,
  ErrorHandler,
  handleError,
  withErrorHandling,
  initializeErrorHandler,
  normalizeError,
  isRetryableError,
  isApiError,
  ErrorCategory,
  type ApiError,
  type ExtendedErrorMessage,
  type ErrorHandlingStrategy,
  type ErrorToastConfig,
} from './errors';

export const normalizeError = originalNormalizeError;
export const formatErrorMessage = originalFormatErrorMessage;
export const formatValidationErrors = originalFormatValidationErrors;
