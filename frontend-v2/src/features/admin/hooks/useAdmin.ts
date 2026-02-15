/**
 * Admin（管理后台）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  UserListItem,
  GetUsersRequest,
  AdminStats,
  UserRole,
} from '../types';
import {
  apiGetUsers,
  apiToggleUserActive,
  apiUpdateUserRole,
  apiGetAdminStats,
  apiExportUsers,
  apiExportPosts,
  apiExportNews,
  apiExportLawfirms,
} from '../api';

// ==================== Query Keys ====================

const ADMIN_QUERY_KEYS = {
  users: (params?: GetUsersRequest) => ['admin', 'users', params] as const,
  stats: ['admin', 'stats'] as const,
} as const;

// ==================== Users Hooks ====================

/**
 * 获取用户列表 Hook
 */
export function useUsers(params: GetUsersRequest = {}) {
  return useQuery<{ users: UserListItem[]; total: number }>({
    queryKey: ADMIN_QUERY_KEYS.users(params),
    queryFn: async () => {
      const response = await apiGetUsers(params);
      return {
        users: response.items,
        total: response.total,
      };
    },
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 切换用户激活状态 Hook
 */
export function useToggleUserActive() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId }: { userId: number }) => apiToggleUserActive(userId),
    onSuccess: () => {
      // 更新成功后刷新用户列表
      void queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

/**
 * 更新用户角色 Hook
 */
export function useUpdateUserRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: UserRole }) => 
      apiUpdateUserRole(userId, { role }),
    onSuccess: () => {
      // 更新成功后刷新用户列表
      void queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

// ==================== Stats Hooks ====================

/**
 * 获取系统统计数据 Hook
 */
export function useAdminStats() {
  return useQuery<AdminStats>({
    queryKey: ADMIN_QUERY_KEYS.stats,
    queryFn: apiGetAdminStats,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== Export Hooks ====================

/**
 * 导出用户数据 Hook
 */
export function useExportUsers() {
  return useMutation({
    mutationFn: () => apiExportUsers('csv'),
    onSuccess: (blob) => {
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `users_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });
}

/**
 * 导出帖子数据 Hook
 */
export function useExportPosts() {
  return useMutation({
    mutationFn: () => apiExportPosts(),
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `posts_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });
}

/**
 * 导出新闻数据 Hook
 */
export function useExportNews() {
  return useMutation({
    mutationFn: () => apiExportNews(),
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `news_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });
}

/**
 * 导出律所数据 Hook
 */
export function useExportLawfirms() {
  return useMutation({
    mutationFn: () => apiExportLawfirms(),
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `lawfirms_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });
}