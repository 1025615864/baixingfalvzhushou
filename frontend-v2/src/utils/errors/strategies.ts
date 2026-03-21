import { BusinessErrorCode } from './types';
import type { ErrorHandlingStrategy } from './types';

const DEFAULT_STRATEGY: ErrorHandlingStrategy = {
  shouldShowToast: true,
  shouldLog: true,
  shouldReport: false,
  retryable: true,
};

const ERROR_STRATEGIES: Record<number, ErrorHandlingStrategy> = {
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

export function getErrorStrategy(errorCode: number): ErrorHandlingStrategy {
  return ERROR_STRATEGIES[errorCode] || DEFAULT_STRATEGY;
}

export { DEFAULT_STRATEGY, ERROR_STRATEGIES };
