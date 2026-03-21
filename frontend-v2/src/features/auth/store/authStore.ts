/**
 * 认证状态管理 Store
 * 管理用户认证、登录状态、用户偏好设置等
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import type { User } from '@/features/auth/types';

// ==================== 类型定义 ====================

/** 登录方式 */
export type LoginMethod = 'password' | 'wechat' | 'phone' | 'email';

/** 用户偏好设置 */
export interface AuthPreferences {
  /** 记住我 */
  rememberMe: boolean;
  /** 上次登录方式 */
  lastLoginMethod: LoginMethod;
  /** 上次登录账号（脱敏） */
  lastLoginAccount: string | null;
  /** 自动登录 */
  autoLogin: boolean;
  /** 双因素认证启用 */
  twoFactorEnabled: boolean;
  /** 会话超时时间（分钟） */
  sessionTimeout: number;
  /** 安全提醒 */
  securityReminder: boolean;
}

/** 登录状态 */
export interface LoginStatus {
  /** 是否正在登录 */
  isLoggingIn: boolean;
  /** 登录错误信息 */
  loginError: string | null;
  /** 登录尝试次数 */
  loginAttempts: number;
  /** 是否被锁定 */
  isLocked: boolean;
  /** 锁定截止时间 */
  lockedUntil: string | null;
}

/** 认证状态 */
export interface AuthState {
  // ========== 用户信息 ==========
  /** 当前用户 */
  user: User | null;
  /** 是否已认证 */
  isAuthenticated: boolean;
  /** Token 过期时间 */
  tokenExpiresAt: string | null;

  // ========== 登录状态 ==========
  /** 登录状态 */
  loginStatus: LoginStatus;

  // ========== 用户偏好 ==========
  /** 用户偏好设置 */
  preferences: AuthPreferences;

  // ========== 加载状态 ==========
  /** 是否加载中 */
  isLoading: boolean;
  /** 错误信息 */
  error: string | null;

  // ========== Actions ==========
  /** 设置认证（登录成功后调用） */
  setAuth: (user: User) => void;
  /** 更新用户信息 */
  updateUser: (updates: Partial<User>) => void;
  /** 清除认证（登出时调用） */
  clearAuth: () => void;

  /** 设置 Token 过期时间 */
  setTokenExpiresAt: (expiresAt: string | null) => void;
  /** 检查 Token 是否过期 */
  isTokenExpired: () => boolean;

  /** 设置登录中状态 */
  setLoggingIn: (isLoggingIn: boolean) => void;
  /** 设置登录错误 */
  setLoginError: (error: string | null) => void;
  /** 增加登录尝试次数 */
  incrementLoginAttempts: () => void;
  /** 重置登录尝试次数 */
  resetLoginAttempts: () => void;
  /** 设置锁定状态 */
  setLocked: (isLocked: boolean, lockedUntil?: string) => void;

  /** 更新用户偏好 */
  updatePreferences: (preferences: Partial<AuthPreferences>) => void;
  /** 设置上次登录方式 */
  setLastLoginMethod: (method: LoginMethod, account?: string) => void;
  /** 重置用户偏好 */
  resetPreferences: () => void;

  /** 设置加载状态 */
  setLoading: (isLoading: boolean) => void;
  /** 设置错误信息 */
  setError: (error: string | null) => void;
  /** 清除错误 */
  clearError: () => void;

  /** 重置所有状态 */
  reset: () => void;
}

// ==================== 默认值 ====================

/** 默认用户偏好设置 */
const defaultPreferences: AuthPreferences = {
  rememberMe: false,
  lastLoginMethod: 'password',
  lastLoginAccount: null,
  autoLogin: false,
  twoFactorEnabled: false,
  sessionTimeout: 30,
  securityReminder: true,
};

/** 默认登录状态 */
const defaultLoginStatus: LoginStatus = {
  isLoggingIn: false,
  loginError: null,
  loginAttempts: 0,
  isLocked: false,
  lockedUntil: null,
};

/** 初始状态 */
const initialState = {
  user: null,
  isAuthenticated: false,
  tokenExpiresAt: null,
  loginStatus: defaultLoginStatus,
  preferences: defaultPreferences,
  isLoading: false,
  error: null,
};

// ==================== Store 实现 ====================

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // ========== 用户 Actions ==========
      setAuth: (user) =>
        set({
          user,
          isAuthenticated: true,
          loginStatus: defaultLoginStatus,
          error: null,
        }),

      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      clearAuth: () =>
        set({
          user: null,
          isAuthenticated: false,
          tokenExpiresAt: null,
          loginStatus: defaultLoginStatus,
          error: null,
        }),

      // ========== Token Actions ==========
      setTokenExpiresAt: (expiresAt) =>
        set({ tokenExpiresAt: expiresAt }),

      isTokenExpired: () => {
        const { tokenExpiresAt } = get();
        if (!tokenExpiresAt) return true;
        return new Date(tokenExpiresAt) < new Date();
      },

      // ========== 登录状态 Actions ==========
      setLoggingIn: (isLoggingIn) =>
        set((state) => ({
          loginStatus: { ...state.loginStatus, isLoggingIn, loginError: null },
        })),

      setLoginError: (error) =>
        set((state) => ({
          loginStatus: {
            ...state.loginStatus,
            isLoggingIn: false,
            loginError: error,
          },
        })),

      incrementLoginAttempts: () =>
        set((state) => {
          const newAttempts = state.loginStatus.loginAttempts + 1;
          // 超过 5 次尝试则锁定 30 分钟
          const shouldLock = newAttempts >= 5;
          return {
            loginStatus: {
              ...state.loginStatus,
              loginAttempts: newAttempts,
              isLocked: shouldLock,
              lockedUntil: shouldLock
                ? new Date(Date.now() + 30 * 60 * 1000).toISOString()
                : null,
            },
          };
        }),

      resetLoginAttempts: () =>
        set((state) => ({
          loginStatus: {
            ...state.loginStatus,
            loginAttempts: 0,
            isLocked: false,
            lockedUntil: null,
          },
        })),

      setLocked: (isLocked, lockedUntil) =>
        set((state) => ({
          loginStatus: {
            ...state.loginStatus,
            isLocked,
            lockedUntil: lockedUntil ?? null,
          },
        })),

      // ========== 偏好设置 Actions ==========
      updatePreferences: (newPreferences) =>
        set((state) => ({
          preferences: { ...state.preferences, ...newPreferences },
        })),

      setLastLoginMethod: (method, account) =>
        set((state) => ({
          preferences: {
            ...state.preferences,
            lastLoginMethod: method,
            lastLoginAccount: account ?? state.preferences.lastLoginAccount,
          },
        })),

      resetPreferences: () =>
        set({ preferences: defaultPreferences }),

      // ========== 状态管理 Actions ==========
      setLoading: (isLoading) =>
        set({ isLoading }),

      setError: (error) =>
        set({ error }),

      clearError: () =>
        set({ error: null }),

      reset: () =>
        set({
          ...initialState,
          preferences: defaultPreferences,
        }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // 只持久化必要的字段
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        tokenExpiresAt: state.tokenExpiresAt,
        preferences: state.preferences,
      }),
    }
  )
);

// ==================== 选择器 ====================

/** 用户选择器 */
export const selectUser = (state: AuthState) => state.user;

/** 认证状态选择器 */
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated;

/** Token 过期时间选择器 */
export const selectTokenExpiresAt = (state: AuthState) => state.tokenExpiresAt;

/** 登录状态选择器 */
export const selectLoginStatus = (state: AuthState) => state.loginStatus;

/** 是否正在登录选择器 */
export const selectIsLoggingIn = (state: AuthState) => state.loginStatus.isLoggingIn;

/** 登录错误选择器 */
export const selectLoginError = (state: AuthState) => state.loginStatus.loginError;

/** 是否被锁定选择器 */
export const selectIsLocked = (state: AuthState) => state.loginStatus.isLocked;

/** 用户偏好选择器 */
export const selectPreferences = (state: AuthState) => state.preferences;

/** 上次登录方式选择器 */
export const selectLastLoginMethod = (state: AuthState) =>
  state.preferences.lastLoginMethod;

/** 加载状态选择器 */
export const selectIsLoading = (state: AuthState) => state.isLoading;

/** 错误选择器 */
export const selectError = (state: AuthState) => state.error;

// ==================== Hooks ====================

/** 获取当前用户 */
export const useUser = () => useAuthStore(selectUser);

/** 获取认证状态 */
export const useIsAuthenticated = () => useAuthStore(selectIsAuthenticated);

/** 获取登录状态 */
export const useLoginStatus = () => useAuthStore(selectLoginStatus);

/** 获取是否正在登录 */
export const useIsLoggingIn = () => useAuthStore(selectIsLoggingIn);

/** 获取登录错误 */
export const useLoginError = () => useAuthStore(selectLoginError);

/** 获取是否被锁定 */
export const useIsLocked = () => useAuthStore(selectIsLocked);

/** 获取用户偏好 */
export const useAuthPreferences = () => useAuthStore(selectPreferences);

/** 获取上次登录方式 */
export const useLastLoginMethod = () => useAuthStore(selectLastLoginMethod);

/** 获取加载状态 */
export const useAuthLoading = () => useAuthStore(selectIsLoading);

/** 获取错误信息 */
export const useAuthError = () => useAuthStore(selectError);

export default useAuthStore;