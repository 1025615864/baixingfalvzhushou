// ============================================
// 通知模块 API Hooks
// ============================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  getNotifications,
  getUnreadCount as getUnreadCountApi,
  markAsRead as markAsReadApi,
  markAllAsRead as markAllAsReadApi,
  deleteNotification as deleteNotificationApi,
  batchMarkAsRead as batchMarkAsReadApi,
  batchDeleteNotifications as batchDeleteNotificationsApi,
} from '../api';
import type {
  NotificationListResponse,
  GetNotificationsParams,
  NotificationType,
} from '../types';

// Re-export types for backward compatibility
export type { Notification, NotificationListResponse } from '../types';

const NOTIFICATION_KEYS = {
  all: ['notifications'] as const,
  list: (params?: unknown) => [...NOTIFICATION_KEYS.all, 'list', params] as const,
  unread: () => [...NOTIFICATION_KEYS.all, 'unread'] as const,
};

/**
 * 获取通知列表
 */
export function useNotificationList(params?: {
  page?: number;
  pageSize?: number;
  unreadOnly?: boolean;
  type?: string;
}) {
  // 转换参数格式以匹配 API 期望的格式
  const apiParams: GetNotificationsParams = {
    page: params?.page,
    page_size: params?.pageSize,
    unread_only: params?.unreadOnly,
    notification_type: params?.type as NotificationType | undefined,
  };
  return useQuery({
    queryKey: NOTIFICATION_KEYS.list(params),
    queryFn: async (): Promise<NotificationListResponse> => {
      return await getNotifications(apiParams);
    },
  });
}

/**
 * 获取未读通知数量
 */
export function useUnreadCount() {
  return useQuery({
    queryKey: NOTIFICATION_KEYS.unread(),
    queryFn: async () => {
      const response = await getUnreadCountApi();
      return response.unread_count;
    },
  });
}

/**
 * 标记通知为已读
 */
export function useMarkAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      return await markAsReadApi(id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });
}

/**
 * 标记所有通知为已读
 */
export function useMarkAllAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      return await markAllAsReadApi();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });
}

/**
 * 删除通知
 */
export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      return await deleteNotificationApi(id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });
}

/**
 * 批量标记已读
 */
export function useBatchMarkAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ids: number[]) => {
      return await batchMarkAsReadApi({ ids });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });
}

/**
 * 批量删除通知
 */
export function useBatchDeleteNotifications() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ids: number[]) => {
      return await batchDeleteNotificationsApi({ ids });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
  });
}