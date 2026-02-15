/**
 * Forum-Admin（论坛管理）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  ForumCategory,
  CreateCategoryRequest,
  UpdateCategoryRequest,
  GetCategoriesRequest,
  ModerationItem,
  ModerationRecord,
  GetModerationQueueRequest,
  GetModerationRecordsRequest,
  ModerateContentRequest,
  BatchModerateRequest,
  ForumUser,
  GetForumUsersRequest,
  UpdateUserStatusRequest,
  SetModeratorRequest,
  ForumStatsOverview,
  GetTrendDataRequest,
  TrendDataPoint,
  HotContent,
  ForumConfig,
} from '../types';
import {
  apiGetCategories,
  apiCreateCategory,
  apiUpdateCategory,
  apiDeleteCategory,
  apiGetModerationQueue,
  apiModerateContent,
  apiBatchModerate,
  apiGetModerationRecords,
  apiGetForumUsers,
  apiUpdateUserStatus,
  apiSetModerator,
  apiGetUserActionRecords,
  apiGetForumStats,
  apiGetTrendData,
  apiGetHotContent,
  apiGetForumConfig,
  apiUpdateForumConfig,
} from '../api';

// ==================== Query Keys ====================

const FORUM_ADMIN_QUERY_KEYS = {
  categories: (params?: GetCategoriesRequest) => ['forum-admin', 'categories', params] as const,
  moderationQueue: (params?: GetModerationQueueRequest) => ['forum-admin', 'moderation-queue', params] as const,
  moderationRecords: (params?: GetModerationRecordsRequest) => ['forum-admin', 'moderation-records', params] as const,
  users: (params?: GetForumUsersRequest) => ['forum-admin', 'users', params] as const,
  userRecords: (userId: number) => ['forum-admin', 'user-records', userId] as const,
  stats: ['forum-admin', 'stats'] as const,
  trendData: (params: GetTrendDataRequest) => ['forum-admin', 'trend', params] as const,
  hotContent: ['forum-admin', 'hot-content'] as const,
  config: ['forum-admin', 'config'] as const,
} as const;

// ==================== 板块管理 Hooks ====================

/**
 * 获取板块列表 Hook
 */
export function useForumCategories(params: GetCategoriesRequest = {}) {
  return useQuery<ForumCategory[]>({
    queryKey: FORUM_ADMIN_QUERY_KEYS.categories(params),
    queryFn: async () => {
      const response = await apiGetCategories(params);
      return response.categories;
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 创建板块 Hook
 */
export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateCategoryRequest) => apiCreateCategory(request),
    onSuccess: () => {
      // 创建成功后刷新板块列表
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'categories'] });
    },
  });
}

/**
 * 更新板块 Hook
 */
export function useUpdateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ categoryId, request }: { categoryId: number; request: UpdateCategoryRequest }) =>
      apiUpdateCategory(categoryId, request),
    onSuccess: () => {
      // 更新成功后刷新板块列表
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'categories'] });
    },
  });
}

/**
 * 删除板块 Hook
 */
export function useDeleteCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (categoryId: number) => apiDeleteCategory(categoryId),
    onSuccess: () => {
      // 删除成功后刷新板块列表
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'categories'] });
    },
  });
}

// ==================== 内容审核 Hooks ====================

/**
 * 获取审核队列 Hook
 */
export function useModerationQueue(params: GetModerationQueueRequest = {}) {
  return useQuery<{ items: ModerationItem[]; total: number; pendingCount: number }>({
    queryKey: FORUM_ADMIN_QUERY_KEYS.moderationQueue(params),
    queryFn: async () => apiGetModerationQueue(params),
    staleTime: 30 * 1000, // 30秒缓存，审核队列变化频繁
  });
}

/**
 * 审核内容 Hook
 */
export function useModerateContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ModerateContentRequest) => apiModerateContent(request),
    onSuccess: () => {
      // 审核成功后刷新审核队列和记录
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'moderation-queue'] });
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'moderation-records'] });
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'stats'] });
    },
  });
}

/**
 * 批量审核 Hook
 */
export function useBatchModerate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: BatchModerateRequest) => apiBatchModerate(request),
    onSuccess: () => {
      // 批量审核成功后刷新审核队列和记录
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'moderation-queue'] });
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'moderation-records'] });
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'stats'] });
    },
  });
}

/**
 * 获取审核记录 Hook
 */
export function useModerationRecords(params: GetModerationRecordsRequest = {}) {
  return useQuery<ModerationRecord[]>({
    queryKey: FORUM_ADMIN_QUERY_KEYS.moderationRecords(params),
    queryFn: async () => {
      const response = await apiGetModerationRecords(params);
      return response.records;
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== 用户管理 Hooks ====================

/**
 * 获取论坛用户列表 Hook
 */
export function useForumUsers(params: GetForumUsersRequest = {}) {
  return useQuery<{ users: ForumUser[]; total: number }>({
    queryKey: FORUM_ADMIN_QUERY_KEYS.users(params),
    queryFn: async () => apiGetForumUsers(params),
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 更新用户状态 Hook
 */
export function useUpdateUserStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateUserStatusRequest) => apiUpdateUserStatus(request),
    onSuccess: (_data, variables) => {
      // 更新成功后刷新用户列表和该用户的操作记录
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'users'] });
      void queryClient.invalidateQueries({ queryKey: FORUM_ADMIN_QUERY_KEYS.userRecords(variables.userId) });
    },
  });
}

/**
 * 设置版主 Hook
 */
export function useSetModerator() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SetModeratorRequest) => apiSetModerator(request),
    onSuccess: () => {
      // 设置成功后刷新用户列表
      void queryClient.invalidateQueries({ queryKey: ['forum-admin', 'users'] });
    },
  });
}

/**
 * 获取用户操作记录 Hook
 */
export function useUserActionRecords(userId: number) {
  return useQuery({
    queryKey: FORUM_ADMIN_QUERY_KEYS.userRecords(userId),
    queryFn: () => apiGetUserActionRecords(userId),
    staleTime: 60 * 1000, // 1分钟缓存
    enabled: userId > 0,
  });
}

// ==================== 统计 Hooks ====================

/**
 * 获取论坛统计概览 Hook
 */
export function useForumStats() {
  return useQuery<ForumStatsOverview>({
    queryKey: FORUM_ADMIN_QUERY_KEYS.stats,
    queryFn: apiGetForumStats,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 获取趋势数据 Hook
 */
export function useTrendData(params: GetTrendDataRequest) {
  return useQuery<TrendDataPoint[]>({
    queryKey: FORUM_ADMIN_QUERY_KEYS.trendData(params),
    queryFn: async () => {
      const response = await apiGetTrendData(params);
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存，趋势数据变化较慢
  });
}

/**
 * 获取热门内容 Hook
 */
export function useHotContent() {
  return useQuery<{ posts: HotContent[]; comments: HotContent[] }>({
    queryKey: FORUM_ADMIN_QUERY_KEYS.hotContent,
    queryFn: apiGetHotContent,
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

// ==================== 配置 Hooks ====================

/**
 * 获取论坛配置 Hook
 */
export function useForumConfig() {
  return useQuery<ForumConfig>({
    queryKey: FORUM_ADMIN_QUERY_KEYS.config,
    queryFn: apiGetForumConfig,
    staleTime: 30 * 60 * 1000, // 30分钟缓存，配置不常变化
  });
}

/**
 * 更新论坛配置 Hook
 */
export function useUpdateForumConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: Partial<ForumConfig>) => apiUpdateForumConfig(config),
    onSuccess: () => {
      // 更新成功后刷新配置
      void queryClient.invalidateQueries({ queryKey: FORUM_ADMIN_QUERY_KEYS.config });
    },
  });
}