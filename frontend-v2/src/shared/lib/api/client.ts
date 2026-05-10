import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
  InternalAxiosRequestConfig
} from 'axios';

import { logger } from '../logger';
import { camelKeysToSnake, convertPaginationParams } from '@/utils/transformers';

import { clearAuthStorage, getToken } from '../security/tokenStorage';

import { handleRefreshFailure } from './auth';
import { getTokenManager } from './tokenManager';
import type { ApiResponse, PaginatedResponse, PaginationInfo } from './types';


// CSRF Token 缓存
let csrfTokenCache: string | null = null;
let csrfTokenFetchTime: number = 0;
const CSRF_TOKEN_CACHE_MS = 5 * 60 * 1000; // 5 分钟缓存

// API 错误类型
export interface ApiError {
  code: number;
  message: string;
  details?: Record<string, string[]>;
  // FastAPI 验证错误格式
  validationErrors?: Array<{
    type: string;
    loc: string[];
    msg: string;
    input?: unknown;
  }>;
}

/**
 * API 错误类
 */
export class ApiErrorClass extends Error {
  public readonly code: number;
  public readonly details?: Record<string, string[]>;
  public readonly validationErrors?: Array<{
    type: string;
    loc: string[];
    msg: string;
    input?: unknown;
  }>;

  constructor(message: string, code: number, details?: Record<string, string[]>, validationErrors?: Array<{
    type: string;
    loc: string[];
    msg: string;
    input?: unknown;
  }>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
    this.validationErrors = validationErrors;
  }
}

function normalizeApiError(error: AxiosError<ApiError>): ApiError {
  const responseData = error.response?.data;

  if (responseData && typeof responseData === 'object') {
    return {
      code: responseData.code ?? error.response?.status ?? 0,
      message: responseData.message || error.message || '请求失败',
      details: responseData.details,
      validationErrors: responseData.validationErrors,
    };
  }

  return {
    code: error.response?.status ?? 0,
    message: error.message || '请求失败',
  };
}

function logApiError(error: ApiError, method?: string, url?: string): void {
  logger.error('API Error Normalized', {
    code: error.code,
    message: error.message,
    details: error.details,
    validationErrors: error.validationErrors,
    action: `${method?.toUpperCase() || 'UNKNOWN'} ${url || ''}`.trim(),
  });
}

// 获取 CSRF Token（带缓存）
async function getCsrfToken(): Promise<string | null> {
  const now = Date.now();
  
  // 检查缓存是否有效
  if (csrfTokenCache && (now - csrfTokenFetchTime) < CSRF_TOKEN_CACHE_MS) {
    return csrfTokenCache;
  }
  
  // 检查用户是否已登录（通过检查 localStorage 中是否有 token）
  const token = getToken();
  if (!token) {
    // 用户未登录，不需要获取 CSRF Token
    return null;
  }
  
  try {
    const response = await axios.get<{ csrf_token: string; expires_in_hours: number }>(
      `${import.meta.env.VITE_API_BASE_URL || '/api'}/user/me/csrf-token`,
      { 
        withCredentials: true,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    // 后端直接返回 { csrf_token: "...", expires_in_hours: 1 }
    if (response.data?.csrf_token) {
      csrfTokenCache = response.data.csrf_token;
      csrfTokenFetchTime = now;
      return csrfTokenCache;
    }
  } catch (error) {
    // 记录 CSRF token 获取错误，但不阻断流程
    logger.warn('获取 CSRF token 失败:', error instanceof Error ? error.message : '未知错误');
  }
  
  return null;
}

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// 请求拦截器 - 添加认证 token、CSRF token 和参数转换
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // 开发环境调试日志
    if (import.meta.env.DEV) {
      logger.debug(`API Request ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, {
        params: config.params as unknown,
        data: config.data as unknown,
      });
    }

    const token = getToken();
    if (token) {
      config.headers.set('Authorization', `Bearer ${token}`);
    }
    
    // 添加 CSRF token（对于非安全方法）
    const needsCsrf = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(config.method?.toUpperCase() || '');
    if (needsCsrf) {
      const csrfToken = await getCsrfToken();
      if (csrfToken) {
        config.headers.set('X-CSRF-Token', csrfToken);
      }
    }
    
    // FR-015: 分页参数转换（前端 → 后端）
    if (config.params) {
      const paginationKeys = ['pageSize', 'sortBy', 'sortOrder'];
      const hasPagination = paginationKeys.some((key) => key in config.params);
      if (hasPagination) {
        const convertedParams = convertPaginationParams(config.params as {
          page?: number;
          pageSize?: number;
          sortBy?: string;
          sortOrder?: 'asc' | 'desc';
        });
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        config.params = { ...config.params, ...convertedParams };
      }
    }
    
    // FR-015: 请求体参数转换（驼峰 → 蛇形）
    if (config.data && typeof config.data === 'object') {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
      config.data = camelKeysToSnake(config.data);
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 统一处理 ApiResponse 格式和错误
apiClient.interceptors.response.use(
  (response: AxiosResponse<unknown>) => {
    // 开发环境日志
    if (import.meta.env.DEV) {
      // 开发环境保留分支，避免影响响应处理流程
    }
    return response;
  },
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // 开发环境错误日志
    if (import.meta.env.DEV) {
      logger.error(`API Error ${error.response?.status} ${error.config?.url}`, {
        message: error.message,
        response: error.response?.data,
      });
    }

    // 处理 401 错误 - 使用 TokenManager 进行并发控制的刷新
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // 使用 TokenManager 进行刷新（带并发控制）
        const tokenManager = getTokenManager();
        const refreshResult = await tokenManager.refreshToken();

        if (!refreshResult.success || !refreshResult.accessToken) {
          throw new Error('Token refresh failed');
        }

        // 重试原请求 - 使用 set 方法正确设置 headers
        originalRequest.headers.set('Authorization', `Bearer ${refreshResult.accessToken}`);
        return apiClient(originalRequest);
      } catch (refreshError) {
        try {
          handleRefreshFailure();
        } catch {
          clearAuthStorage();
          try {
            localStorage.removeItem('auth-storage');
          } catch {
            localStorage.removeItem('auth-storage');
          }
        }

        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // 标准化错误对象
    const apiError = normalizeApiError(error);

    // 记录错误日志（仅开发环境）
    logApiError(apiError, error.config?.method, error.config?.url);

    return Promise.reject(apiError);
  }
);

// ============================================================
// 响应解包函数
// ============================================================

type LegacyResponse<T> = {
  ok?: boolean;
  data?: T;
  message?: string;
  error?: {
    message?: string;
    code?: string;
    details?: Record<string, string[]>;
  };
};

type LegacyListResponse<T> = {
  items?: T[];
  total?: number;
  page?: number;
  page_size?: number;
  pageSize?: number;
};

function isLegacySuccessResponse<T>(response: unknown): response is LegacyResponse<T> {
  return typeof response === 'object' && response !== null && 'ok' in response;
}

function isLegacyListResponse<T>(response: unknown): response is LegacyListResponse<T> {
  return typeof response === 'object' && response !== null && 'items' in response;
}

/**
 * 解包普通 API 响应
 * 兼容 success/message/data 与旧版 ok/data/ts
 */
export function unwrapResponse<T>(response: ApiResponse<T> | LegacyResponse<T> | T): T {
  if (isLegacySuccessResponse<T>(response)) {
    if (response.ok === false) {
      throw new ApiErrorClass(
        response.error?.message || response.message || '请求失败',
        1005,
        response.error?.details
      );
    }

    if (response.data === null || response.data === undefined) {
      throw new ApiErrorClass('响应数据为空', 1005);
    }

    return response.data;
  }

  if (typeof response === 'object' && response !== null && 'success' in response) {
    const standardResponse = response as ApiResponse<T> & { details?: Record<string, string[]> };

    if (!standardResponse.success) {
      throw new ApiErrorClass(
        standardResponse.message || '请求失败',
        standardResponse.error_code || 1005,
        standardResponse.details
      );
    }

    if (standardResponse.data === null || standardResponse.data === undefined) {
      throw new ApiErrorClass('响应数据为空', 1005);
    }

    return standardResponse.data;
  }

  return response;
}

/**
 * 解包分页 API 响应
 * 兼容新版分页格式和旧版 items/total/page/page_size 格式
 */
export function unwrapPaginatedResponse<T>(
  response: PaginatedResponse<T> | LegacyListResponse<T>
): { data: T[]; pagination: PaginationInfo } {
  if (isLegacyListResponse<T>(response)) {
    const page = response.page ?? 1;
    const pageSize = response.page_size ?? response.pageSize ?? 20;
    const total = response.total ?? response.items?.length ?? 0;

    return {
      data: response.items ?? [],
      pagination: {
        page,
        page_size: pageSize,
        total,
        total_pages: pageSize > 0 ? Math.ceil(total / pageSize) : 0,
      },
    };
  }

  if (!response.success) {
    throw new ApiErrorClass(
      response.message || '请求失败',
      (response as PaginatedResponse<T> & { error_code?: number }).error_code || 1005,
      (response as PaginatedResponse<T> & { details?: Record<string, string[]> }).details
    );
  }

  return {
    data: response.data,
    pagination: response.pagination,
  };
}

// ============================================================
// 封装的 API 客户端类
// ============================================================

/**
 * API 客户端类
 * 提供类型安全的 HTTP 请求方法，自动解包 ApiResponse 响应
 */
export class ApiClient {
  private client: AxiosInstance;

  constructor(client: AxiosInstance) {
    this.client = client;
  }

  /**
   * GET 请求
   * 自动解包 ApiResponse<T> 返回 T
   */
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<ApiResponse<T>>(url, config);
    return unwrapResponse(response.data);
  }

  /**
   * POST 请求
   * 自动解包 ApiResponse<T> 返回 T
   */
  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config);
    return unwrapResponse(response.data);
  }

  /**
   * PUT 请求
   * 自动解包 ApiResponse<T> 返回 T
   */
  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config);
    return unwrapResponse(response.data);
  }

  /**
   * PATCH 请求
   * 自动解包 ApiResponse<T> 返回 T
   */
  async patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<ApiResponse<T>>(url, data, config);
    return unwrapResponse(response.data);
  }

  /**
   * DELETE 请求
   * 自动解包 ApiResponse<T> 返回 T
   */
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<ApiResponse<T>>(url, config);
    return unwrapResponse(response.data);
  }

  /**
   * GET 列表请求（分页）
   * 自动解包 PaginatedResponse<T> 返回 { data: T[]; pagination: PaginationInfo }
   */
  async getList<T>(url: string, config?: AxiosRequestConfig): Promise<{ data: T[]; pagination: PaginationInfo }> {
    const response = await this.client.get<PaginatedResponse<T>>(url, config);
    return unwrapPaginatedResponse(response.data);
  }

  /**
   * POST 列表请求（分页）
   * 自动解包 PaginatedResponse<T> 返回 { data: T[]; pagination: PaginationInfo }
   */
  async postList<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<{ data: T[]; pagination: PaginationInfo }> {
    const response = await this.client.post<PaginatedResponse<T>>(url, data, config);
    return unwrapPaginatedResponse(response.data);
  }
}

// 创建 API 客户端实例
export const apiClientInstance = new ApiClient(apiClient);

// 导出便捷的 API 方法（保持向后兼容）
export const api = {
  /**
   * GET 请求 - 自动解包 ApiResponse
   */
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<ApiResponse<T>>(url, config).then(res => unwrapResponse(res.data)),

  /**
   * POST 请求 - 自动解包 ApiResponse
   */
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.post<ApiResponse<T>>(url, data, config).then(res => unwrapResponse(res.data)),

  /**
   * PUT 请求 - 自动解包 ApiResponse
   */
  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.put<ApiResponse<T>>(url, data, config).then(res => unwrapResponse(res.data)),

  /**
   * PATCH 请求 - 自动解包 ApiResponse
   */
  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.patch<ApiResponse<T>>(url, data, config).then(res => unwrapResponse(res.data)),

  /**
   * DELETE 请求 - 自动解包 ApiResponse
   */
  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.delete<ApiResponse<T>>(url, config).then(res => unwrapResponse(res.data)),

  /**
   * GET 列表请求（分页） - 自动解包 PaginatedResponse
   */
  getList: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<PaginatedResponse<T>>(url, config).then(res => unwrapPaginatedResponse(res.data)),

  /**
   * POST 列表请求（分页） - 自动解包 PaginatedResponse
   */
  postList: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.post<PaginatedResponse<T>>(url, data, config).then(res => unwrapPaginatedResponse(res.data)),
};

// 同时提供命名导出和默认导出，兼容不同导入方式
export { apiClient };
export default apiClient;