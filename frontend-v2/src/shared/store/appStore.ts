/**
 * 全局应用状态管理 Store
 * 整合用户、UI、会员、通知等全局状态
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import type { User } from '@/features/auth/types';
import type { MembershipTier } from '@/features/membership/types';

// ==================== 类型定义 ====================

/** 主题类型 */
export type Theme = 'light' | 'dark' | 'system';

/** 侧边栏状态 */
export type SidebarState = 'expanded' | 'collapsed';

/** 用户偏好设置 */
export interface UserPreferences {
  /** 主题 */
  theme: Theme;
  /** 语言 */
  language: 'zh-CN' | 'en-US';
  /** 通知开关 */
  notificationsEnabled: boolean;
  /** 邮件通知 */
  emailNotifications: boolean;
  /** 声音提醒 */
  soundEnabled: boolean;
  /** 自动播放视频 */
  autoPlayVideo: boolean;
  /** 每页显示数量 */
  pageSize: number;
}

/** 会员信息摘要（用于全局状态） */
export interface MembershipInfo {
  tier: MembershipTier;
  isVip: boolean;
  levelName: string;
  endDate: string | null;
  freeVideoConsultations: number;
  freeDocumentReviews: number;
}

/** 应用状态 */
export interface AppState {
  // ========== 用户相关 ==========
  /** 当前用户 */
  user: User | null;
  /** 是否已认证 */
  isAuthenticated: boolean;
  /** 是否加载中 */
  isLoading: boolean;

  // ========== UI 状态 ==========
  /** 主题 */
  theme: Theme;
  /** 侧边栏是否折叠 */
  sidebarCollapsed: boolean;
  /** 是否移动端视图 */
  isMobileView: boolean;
  /** 全局加载状态 */
  globalLoading: boolean;
  /** 全局错误信息 */
  globalError: string | null;

  // ========== 会员状态 ==========
  /** 会员信息 */
  membership: MembershipInfo | null;

  // ========== 通知状态 ==========
  /** 未读通知数量 */
  unreadCount: number;
  /** 未读消息数量 */
  unreadMessageCount: number;

  // ========== 用户偏好 ==========
  /** 用户偏好设置 */
  preferences: UserPreferences;

  // ========== Actions ==========
  /** 设置用户信息 */
  setUser: (user: User | null) => void;
  /** 设置认证状态 */
  setAuthenticated: (isAuthenticated: boolean) => void;
  /** 设置加载状态 */
  setLoading: (isLoading: boolean) => void;
  /** 更新用户信息（部分更新） */
  updateUser: (updates: Partial<User>) => void;
  /** 清除用户信息 */
  clearUser: () => void;

  /** 设置主题 */
  setTheme: (theme: Theme) => void;
  /** 切换侧边栏 */
  toggleSidebar: () => void;
  /** 设置侧边栏状态 */
  setSidebarCollapsed: (collapsed: boolean) => void;
  /** 设置移动端视图 */
  setMobileView: (isMobile: boolean) => void;
  /** 设置全局加载 */
  setGlobalLoading: (loading: boolean) => void;
  /** 设置全局错误 */
  setGlobalError: (error: string | null) => void;
  /** 清除全局错误 */
  clearGlobalError: () => void;

  /** 设置会员信息 */
  setMembership: (membership: MembershipInfo | null) => void;
  /** 更新免费咨询次数 */
  updateFreeConsultations: (count: number) => void;
  /** 更新免费文档审核次数 */
  updateFreeDocumentReviews: (count: number) => void;

  /** 设置未读通知数 */
  setUnreadCount: (count: number) => void;
  /** 增加未读通知 */
  incrementUnreadCount: () => void;
  /** 减少未读通知 */
  decrementUnreadCount: () => void;
  /** 设置未读消息数 */
  setUnreadMessageCount: (count: number) => void;

  /** 更新用户偏好 */
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  /** 重置用户偏好为默认值 */
  resetPreferences: () => void;

  /** 重置所有状态 */
  resetAll: () => void;
}

// ==================== 默认值 ====================

/** 默认用户偏好设置 */
const defaultPreferences: UserPreferences = {
  theme: 'system',
  language: 'zh-CN',
  notificationsEnabled: true,
  emailNotifications: true,
  soundEnabled: true,
  autoPlayVideo: false,
  pageSize: 20,
};

/** 初始状态 */
const initialState = {
  // 用户相关
  user: null,
  isAuthenticated: false,
  isLoading: false,

  // UI 状态
  theme: 'system' as Theme,
  sidebarCollapsed: false,
  isMobileView: false,
  globalLoading: false,
  globalError: null,

  // 会员状态
  membership: null,

  // 通知状态
  unreadCount: 0,
  unreadMessageCount: 0,

  // 用户偏好
  preferences: defaultPreferences,
};

// ==================== Store 实现 ====================

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      ...initialState,

      // ========== 用户 Actions ==========
      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
        }),

      setAuthenticated: (isAuthenticated) =>
        set({ isAuthenticated }),

      setLoading: (isLoading) =>
        set({ isLoading }),

      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      clearUser: () =>
        set({
          user: null,
          isAuthenticated: false,
          membership: null,
          unreadCount: 0,
          unreadMessageCount: 0,
        }),

      // ========== UI Actions ==========
      setTheme: (theme) => {
        set({ theme });
        // 应用主题到 DOM
        const root = document.documentElement;
        const isDark =
          theme === 'dark' ||
          (theme === 'system' &&
            window.matchMedia('(prefers-color-scheme: dark)').matches);
        root.classList.toggle('dark', isDark);
      },

      toggleSidebar: () =>
        set((state) => ({
          sidebarCollapsed: !state.sidebarCollapsed,
        })),

      setSidebarCollapsed: (sidebarCollapsed) =>
        set({ sidebarCollapsed }),

      setMobileView: (isMobileView) =>
        set({ isMobileView }),

      setGlobalLoading: (globalLoading) =>
        set({ globalLoading }),

      setGlobalError: (globalError) =>
        set({ globalError }),

      clearGlobalError: () =>
        set({ globalError: null }),

      // ========== 会员 Actions ==========
      setMembership: (membership) =>
        set({ membership }),

      updateFreeConsultations: (count) =>
        set((state) => ({
          membership: state.membership
            ? { ...state.membership, freeVideoConsultations: count }
            : null,
        })),

      updateFreeDocumentReviews: (count) =>
        set((state) => ({
          membership: state.membership
            ? { ...state.membership, freeDocumentReviews: count }
            : null,
        })),

      // ========== 通知 Actions ==========
      setUnreadCount: (unreadCount) =>
        set({ unreadCount }),

      incrementUnreadCount: () =>
        set((state) => ({
          unreadCount: state.unreadCount + 1,
        })),

      decrementUnreadCount: () =>
        set((state) => ({
          unreadCount: Math.max(0, state.unreadCount - 1),
        })),

      setUnreadMessageCount: (unreadMessageCount) =>
        set({ unreadMessageCount }),

      // ========== 偏好设置 Actions ==========
      updatePreferences: (newPreferences) =>
        set((state) => ({
          preferences: { ...state.preferences, ...newPreferences },
        })),

      resetPreferences: () =>
        set({ preferences: defaultPreferences }),

      // ========== 重置 Actions ==========
      resetAll: () =>
        set({
          ...initialState,
          preferences: defaultPreferences,
        }),
    }),
    {
      name: 'app-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // 只持久化必要的字段
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        membership: state.membership,
        preferences: state.preferences,
      }),
    }
  )
);

// ==================== 选择器 ====================

/** 用户选择器 */
export const selectUser = (state: AppState) => state.user;

/** 认证状态选择器 */
export const selectIsAuthenticated = (state: AppState) => state.isAuthenticated;

/** 主题选择器 */
export const selectTheme = (state: AppState) => state.theme;

/** 会员信息选择器 */
export const selectMembership = (state: AppState) => state.membership;

/** 是否 VIP 选择器 */
export const selectIsVip = (state: AppState) => state.membership?.isVip ?? false;

/** 未读数选择器 */
export const selectUnreadCount = (state: AppState) => state.unreadCount;

/** 用户偏好选择器 */
export const selectPreferences = (state: AppState) => state.preferences;

/** 侧边栏折叠状态选择器 */
export const selectSidebarCollapsed = (state: AppState) => state.sidebarCollapsed;

/** 全局加载状态选择器 */
export const selectGlobalLoading = (state: AppState) => state.globalLoading;

/** 全局错误选择器 */
export const selectGlobalError = (state: AppState) => state.globalError;

// ==================== Hooks ====================

/** 获取当前用户 */
export const useUser = () => useAppStore(selectUser);

/** 获取认证状态 */
export const useIsAuthenticated = () => useAppStore(selectIsAuthenticated);

/** 获取主题 */
export const useTheme = () => useAppStore(selectTheme);

/** 获取会员信息 */
export const useMembershipInfo = () => useAppStore(selectMembership);

/** 获取是否 VIP */
export const useIsVip = () => useAppStore(selectIsVip);

/** 获取未读通知数 */
export const useUnreadCount = () => useAppStore(selectUnreadCount);

/** 获取用户偏好 */
export const usePreferences = () => useAppStore(selectPreferences);

/** 获取侧边栏状态 */
export const useSidebarCollapsed = () => useAppStore(selectSidebarCollapsed);

/** 获取全局加载状态 */
export const useGlobalLoading = () => useAppStore(selectGlobalLoading);

/** 获取全局错误 */
export const useGlobalError = () => useAppStore(selectGlobalError);

export default useAppStore;