import { AxiosError, AxiosRequestConfig } from 'axios';

export interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  retryCondition?: (error: AxiosError) => boolean;
  onRetry?: (attempt: number, error: AxiosError) => void;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  retryCondition: (error) => {
    if (error.response) {
      return error.response.status >= 500 || error.response.status === 429;
    }
    return !error.response && error.code !== 'ECONNABORTED';
  },
};

export async function withRetry<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const { maxRetries, retryDelay, retryCondition, onRetry } = {
    ...DEFAULT_RETRY_CONFIG,
    ...config,
  };

  let lastError: Error;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt === maxRetries) {
        throw error;
      }

      if (error instanceof AxiosError && retryCondition && !retryCondition(error)) {
        throw error;
      }

      if (onRetry && error instanceof AxiosError) {
        onRetry(attempt + 1, error);
      }

      await sleep(retryDelay * Math.pow(2, attempt));
    }
  }

  throw lastError!;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function createRetryInterceptor(config: Partial<RetryConfig> = {}) {
  const { maxRetries, retryDelay, retryCondition, onRetry } = {
    ...DEFAULT_RETRY_CONFIG,
    ...config,
  };

  return async (error: AxiosError, retryCount: number = 0): Promise<AxiosError> => {
    if (retryCount >= maxRetries) {
      return Promise.reject(error);
    }

    if (retryCondition && !retryCondition(error)) {
      return Promise.reject(error);
    }

    if (onRetry) {
      onRetry(retryCount + 1, error);
    }

    const delay = retryDelay * Math.pow(2, retryCount);
    await sleep(delay);

    const config: AxiosRequestConfig = {
      ...error.config,
      headers: {
        ...error.config?.headers,
        'X-Retry-Attempt': String(retryCount + 1),
      },
    };

    const axios = await import('axios');
    return axios.default.request(config);
  };
}

export class RetryManager {
  private retryCount = new Map<string, number>();

  recordRetry(requestId: string): void {
    const current = this.retryCount.get(requestId) || 0;
    this.retryCount.set(requestId, current + 1);
  }

  getRetryCount(requestId: string): number {
    return this.retryCount.get(requestId) || 0;
  }

  clearRetry(requestId: string): void {
    this.retryCount.delete(requestId);
  }

  clearAll(): void {
    this.retryCount.clear();
  }
}

export const retryManager = new RetryManager();
