import axios, { 
  AxiosInstance, 
  AxiosRequestConfig, 
  AxiosResponse, 
  AxiosError,
  InternalAxiosRequestConfig 
} from 'axios';

import { 
  getToken, 
  setToken, 
  getRefreshToken, 
  setRefreshToken,
  clearAuthStorage 
} from '../security/tokenStorage';

// CSRF Token 缓存
let csrfTokenCache: string | null = null;
let csrfTokenFetchTime: number = 0;
const CSRF_TOKEN_CACHE_MS = 5 * 60 * 1000; // 5分钟缓存

// API 响应类型
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

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

// 获取 CSRF Token（带缓存）
async function getCsrfToken(): Promise<string | null> {
  const now = Date.now();
  
  // 检查缓存是否有效
  if (csrfTokenCache && (now - csrfTokenFetchTime) < CSRF_TOKEN_CACHE_MS) {
    return csrfTokenCache;
  }
  
  // 检查用户是否已登录（通过检查localStorage中是否有token）
  const token = getToken();
  if (!token) {
    // 用户未登录，不需要获取CSRF Token
    return null;
  }
  
  try {
    const response = await axios.get<ApiResponse<{ csrf_token: string; expires_in_hours: number }>>(
      `${import.meta.env.VITE_API_BASE_URL || '/api'}/user/me/csrf-token`,
      { 
        withCredentials: true,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    // 后端返回的字段名是 csrf_token（下划线），不是 token
    if (response.data?.data?.csrf_token) {
      csrfTokenCache = response.data.data.csrf_token;
      csrfTokenFetchTime = now;
      return csrfTokenCache;
    }
  } catch (error) {
    // 记录 CSRF token 获取错误，但不阻断流程
    console.warn('获取 CSRF token 失败:', error instanceof Error ? error.message : '未知错误');
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

// 请求拦截器 - 添加认证 token 和 CSRF token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
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
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误和 token 刷新
apiClient.interceptors.response.use(
  (response: AxiosResponse<unknown>) => {
    // 返回完整响应对象，保持axios默认行为
    return response;
  },
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // 处理 401 错误 - 尝试刷新 token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        const response = await axios.post<ApiResponse<{ access_token: string; refresh_token: string }>>(
          `${import.meta.env.VITE_API_BASE_URL || '/api'}/user/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const { access_token, refresh_token } = response.data.data;
        setToken(access_token);
        setRefreshToken(refresh_token);

        // 重试原请求 - 使用 set 方法正确设置 headers
        originalRequest.headers.set('Authorization', `Bearer ${access_token}`);
        return apiClient(originalRequest);
      } catch (refreshError) {
        // 刷新失败，清除 token 并跳转登录
        clearAuthStorage();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // 统一错误处理
    const responseData = error.response?.data as ApiError & { detail?: unknown } | undefined;

    // 处理 FastAPI 422 验证错误
    if (error.response?.status === 422 && Array.isArray(responseData?.detail)) {
      const validationErrors = responseData.detail as Array<{
        type: string;
        loc: string[];
        msg: string;
        input?: unknown;
      }>;

      // 提取所有错误消息
      const errorMessages = validationErrors
        .map(err => {
          const field = err.loc?.join('.') || '';
          return field ? `${field}: ${err.msg}` : err.msg;
        })
        .join('; ');

      const apiError: ApiError = {
        code: 422,
        message: errorMessages || '数据验证失败',
        validationErrors,
      };

      return Promise.reject(apiError);
    }

    const apiError: ApiError = {
      code: responseData?.code || error.response?.status || 500,
      message: responseData?.message || '网络错误，请稍后重试',
      details: responseData?.details,
    };

    return Promise.reject(apiError);
  }
);

// 封装请求方法 - 后端直接返回数据，不使用包装格式
// 这些方法自动解包 response.data
export const api = {
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<T>(url, config).then(res => res.data),

  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.post<T>(url, data, config).then(res => res.data),

  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.put<T>(url, data, config).then(res => res.data),

  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.patch<T>(url, data, config).then(res => res.data),

  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.delete<T>(url, config).then(res => res.data),
};

// 同时提供命名导出和默认导出，兼容不同导入方式
export { apiClient };
export default apiClient;