import { AxiosError } from 'axios';
import {
  ErrorCategory,
  type ApiError,
  type ErrorHandlingStrategy,
  type ErrorToastConfig,
} from './types';
import { getErrorStrategy, DEFAULT_STRATEGY } from './strategies';
import { getExtendedErrorMessage } from './messages';
import {
  normalizeError,
  formatErrorMessage,
  getErrorSeverity,
  getErrorAutoCloseDuration,
} from './utils';
import { logError } from './logging';

export type ToastFunction = (
  message: string,
  options?: {
    type?: 'success' | 'error' | 'warning' | 'info';
    duration?: number;
    action?: string;
  }
) => void;

export type NavigateFunction = (url: string) => void;

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

  setToastFunction(fn: ToastFunction): void {
    this.toastFn = fn;
  }

  setNavigateFunction(fn: NavigateFunction): void {
    this.navigateFn = fn;
  }

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

    if (mergedStrategy.shouldLog && options?.logError !== false) {
      logError(apiError, options?.context);
    }

    if (mergedStrategy.shouldReport) {
      this.reportError(apiError);
    }

    this.errorQueue.push(apiError);

    if (mergedStrategy.shouldShowToast && options?.showToast !== false && this.config.enabled) {
      this.showToast(apiError, mergedStrategy);
    }

    if (mergedStrategy.redirectUrl && this.navigateFn) {
      this.navigateFn(mergedStrategy.redirectUrl);
    }

    return apiError;
  }

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
      if (import.meta.env.DEV) {
        console.log(`[${severity.toUpperCase()}] ${message}${extendedMessage?.action ? ` - ${extendedMessage.action}` : ''}`);
      }
    }
  }

  private reportError(error: ApiError): void {
    if (typeof navigator !== 'undefined' && 'sendBeacon' in navigator) {
      navigator.sendBeacon(
        '/api/logs/error',
        JSON.stringify({
          ...error,
          reportedAt: new Date().toISOString(),
        })
      );
    }
  }

  getErrorQueue(): ApiError[] {
    return [...this.errorQueue];
  }

  clearQueue(): void {
    this.errorQueue = [];
  }

  configure(config: Partial<ErrorToastConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

export function handleError(
  error: unknown,
  options?: Parameters<typeof ErrorHandler.prototype.handle>[1]
): ApiError {
  return ErrorHandler.getInstance().handle(error, options);
}

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

export function normalizeError(error: unknown): ApiError {
  if (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error
  ) {
    return {
      ...(error as ApiError),
      timestamp: (error as ApiError).timestamp || Date.now(),
    };
  }

  if (error instanceof AxiosError) {
    const responseData = error.response?.data as {
      error_code?: number;
      message?: string;
    };
    const errorCode = responseData?.error_code;
    const { categorizeByErrorCode, categorizeErrorByStatus } = require('./utils');

    return {
      code: error.response?.status || 0,
      message: formatErrorMessage(error),
      category: errorCode
        ? categorizeByErrorCode(errorCode)
        : error.response
          ? categorizeErrorByStatus(error.response.status)
          : ErrorCategory.NETWORK,
      details: {},
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

export function isRetryableError(error: unknown): boolean {
  if (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error
  ) {
    const apiError = error as ApiError;
    if (apiError.error_code !== undefined) {
      const strategy = getErrorStrategy(apiError.error_code);
      return strategy.retryable;
    }
  }

  if (error instanceof AxiosError) {
    if (!error.response && error.code !== 'ECONNABORTED') {
      return true;
    }
    if (error.response?.status && error.response.status >= 500) {
      return true;
    }
  }

  return false;
}
