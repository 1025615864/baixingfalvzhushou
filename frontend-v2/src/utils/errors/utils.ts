import { AxiosError } from 'axios';
import {
  ErrorCategory,
  BusinessErrorCode,
  getErrorCodeRange,
  isApiError,
  type ApiError,
} from './types';
import { getErrorMessage } from './types';

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

export function isNetworkError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return !error.response && error.code !== 'ECONNABORTED';
  }
  return false;
}

export function isAuthError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 401;
  }
  if (isApiError(error)) {
    if (error.code === 401 || error.category === ErrorCategory.AUTH) {
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

export function isValidationError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 422;
  }
  if (isApiError(error)) {
    if (error.code === 422 || error.category === ErrorCategory.VALIDATION) {
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

export function formatErrorMessage(error: unknown): string {
  if (isApiError(error) && error.error_code !== undefined) {
    return getErrorMessage(error.error_code, error.message);
  }

  if (isApiError(error)) {
    return error.message;
  }

  if (error instanceof AxiosError) {
    const responseData = error.response?.data as {
      error_code?: number;
      message?: string;
      msg?: string;
      detail?: string | Array<{ loc: string[]; msg: string }>;
    };

    if (responseData?.error_code !== undefined) {
      return getErrorMessage(responseData.error_code, responseData.message || '未知错误');
    }

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

    if (responseData) {
      const detail = responseData.detail;
      if (typeof detail === 'string') {
        return detail;
      }
      return responseData.message || responseData.msg || error.message;
    }

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
