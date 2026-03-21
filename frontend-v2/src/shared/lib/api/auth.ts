/**
 * 认证失败处理模块
 *
 * 功能：
 * - 刷新失败后的处理逻辑
 * - 用户会话过期通知
 * - 自动登出流程
 * - 登录页跳转
 *
 * @see FR-011: Token 刷新失败处理
 */

import { clearAuthStorage } from '../security/tokenStorage';


// ============================================
// 类型定义
// ============================================

/** 会话过期回调函数 */
export type SessionExpiredCallback = () => void;

/** 登出选项 */
export interface LogoutOptions {
  /** 是否清除认证状态 */
  clearAuth?: boolean;
  /** 是否跳转登录页 */
  redirectToLogin?: boolean;
  /** 重定向 URL 参数 */
  redirectUrl?: string;
  /** 自定义回调函数 */
  onLogout?: () => void;
}

// ============================================
// 默认配置
// ============================================

const DEFAULT_OPTIONS: Required<LogoutOptions> = {
  clearAuth: true,
  redirectToLogin: true,
  redirectUrl: '/login',
  onLogout: () => {},
};

// ============================================
// 模块级回调
// ============================================

/** 全局会话过期回调 */
let globalSessionExpiredCallback: SessionExpiredCallback | null = null;

// ============================================
// 核心函数
// ============================================

/**
 * 处理刷新失败后的逻辑
 * 
 * 这是 TokenManager 刷新失败时的统一处理入口
 */
export function handleRefreshFailure(): void {
  // 清除所有认证存储
  clearAuthStorage();
  
  // 清除认证状态持久化缓存
  localStorage.removeItem('auth-storage');
  
  // 调用全局回调（如果存在）
  if (globalSessionExpiredCallback) {
    try {
      globalSessionExpiredCallback();
    } catch (e) {
      console.warn('Session expired callback failed:', e);
    }
  }
}

/**
 * 执行登出操作
 * 
 * @param options - 登出选项
 */
export function logout(options?: Partial<LogoutOptions>): void {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  // 清除认证状态
  if (opts.clearAuth) {
    clearAuthStorage();
    
    try {
      localStorage.removeItem('auth-storage');
    } catch {
      localStorage.removeItem('auth-storage');
    }
  }
  
  // 调用自定义回调
  if (opts.onLogout) {
    opts.onLogout();
  }
  
  // 跳转登录页
  if (opts.redirectToLogin) {
    if (opts.redirectUrl) {
      window.location.href = opts.redirectUrl;
    } else {
      window.location.href = '/login';
    }
  }
}

/**
 * 设置用户会话过期通知
 * 
 * @param callback - 会话过期时的回调函数
 */
export function setSessionExpiredCallback(callback: SessionExpiredCallback): void {
  globalSessionExpiredCallback = callback;
}

/**
 * 清除用户会话过期通知
 */
export function clearSessionExpiredCallback(): void {
  globalSessionExpiredCallback = null;
}

// ============================================
// 导出
// ============================================

export const authErrorHandler = {
  handleRefreshFailure,
  logout,
  setSessionExpiredCallback,
  clearSessionExpiredCallback,
};