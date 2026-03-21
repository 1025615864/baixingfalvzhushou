import { AxiosError } from 'axios';

export {
  BusinessErrorCode,
  getErrorMessage,
  getErrorCodeRange,
  ERROR_MESSAGES,
} from '@/shared/lib/api/types';

import {
  BusinessErrorCode,
  getErrorMessage,
  getErrorCodeRange,
} from '@/shared/lib/api/types';

export { BusinessErrorCode, getErrorMessage, getErrorCodeRange };

export enum ErrorCategory {
  NETWORK = 'NETWORK',
  AUTH = 'AUTH',
  BUSINESS = 'BUSINESS',
  VALIDATION = 'VALIDATION',
  SERVER = 'SERVER',
  PERMISSION = 'PERMISSION',
  UNKNOWN = 'UNKNOWN',
}

export interface ApiError {
  code: number;
  message: string;
  category?: ErrorCategory;
  details?: Record<string, string[]>;
  validationErrors?: Array<{
    type: string;
    loc: string[];
    msg: string;
    input?: unknown;
  }>;
  originalError?: unknown;
  url?: string;
  method?: string;
  timestamp?: number;
  error_code?: number;
}

export interface ErrorToastConfig {
  enabled: boolean;
  duration: number;
  showDetails: boolean;
}

export interface ExtendedErrorMessage {
  title: string;
  action?: string;
  icon?: 'error' | 'warning' | 'info' | 'success';
}

export interface ErrorHandlingStrategy {
  shouldShowToast: boolean;
  shouldLog: boolean;
  shouldReport: boolean;
  redirectUrl?: string;
  retryable: boolean;
  toastDuration?: number;
}

export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error
  );
}
