/**
 * 通知模块React Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import {
  Notification,
  GetNotificationsParams,
} from '../types';
import { notificationApi } from '../api';

/** 查询键常量 */
export const notificationQueryKeys = {
  all: ['notifications'] as const,
  lists: () => [...notificationQueryKeys.all, 'list'] as const,
  list: (params: GetNotificationsParams) =>
    [...notificationQueryKeys.lists(), params] as const,
  unreadCount: () => [...notificationQueryKeys.all, 'unread-count'] as const,
  types: () => [...notificationQueryKeys.all, 'types'] as const,
  details: () => [...notificationQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...notificationQueryKeys.details(), id] as const,
};

/**
 * 获取通知列表
 * @param params 查询参数
 */
export function useNotifications(params: GetNotificationsParams = {}) {
  return useQuery({
    queryKey: notificationQueryKeys.list(params),
    queryFn: () => notificationApi.getNotifications(params),
    staleTime: 1000 * 30, // 30秒
  });
}

/**
 * 获取未读通知数量
 * @param enabled 是否启用查询（用于控制只在登录后查询）
 */
export function useUnreadCount(enabled: boolean = true) {
  return useQuery({
    queryKey: notificationQueryKeys.unreadCount(),
    queryFn: () => notificationApi.getUnreadCount(),
    staleTime: 1000 * 10, // 10秒
    refetchInterval: enabled ? 1000 * 60 : false, // 每分钟自动刷新（仅在启用时）
    enabled, // 控制是否启用查询
  });
}

/**
 * 标记通知为已读
 */
export function useMarkAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: number) =>
      notificationApi.markAsRead(notificationId),
    onSuccess: () => {
      // 使相关查询失效
      void queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.lists(),
      });
      void queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.unreadCount(),
      });
    },
  });
}

/**
 * 标记所有通知为已读
 */
export function useMarkAllAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => notificationApi.markAllAsRead(),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.lists(),
      });
      void queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.unreadCount(),
      });
    },
  });
}

/**
 * 删除通知
 */
export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: number) =>
      notificationApi.deleteNotification(notificationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.lists(),
      });
      void queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.unreadCount(),
      });
    },
  });
}

/**
 * 批量标记通知为已读
 */
export function useBatchMarkAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => notificationApi.batchMarkAsRead({ ids }),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.lists(),
      });
      void queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.unreadCount(),
      });
    },
  });
}

/**
 * 批量删除通知
 */
export function useBatchDeleteNotifications() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) =>
      notificationApi.batchDeleteNotifications({ ids }),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.lists(),
      });
      void queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.unreadCount(),
      });
    },
  });
}

/**
 * 获取通知类型统计
 */
export function useNotificationTypesStats() {
  return useQuery({
    queryKey: notificationQueryKeys.types(),
    queryFn: () => notificationApi.getNotificationTypesStats(),
    staleTime: 1000 * 60, // 1分钟
  });
}

/**
 * 通知Hook整合
 * 提供所有通知相关操作
 */
export function useNotificationActions() {
  const queryClient = useQueryClient();
  const { mutateAsync: markAsRead } = useMarkAsRead();
  const { mutateAsync: markAllAsRead } = useMarkAllAsRead();
  const { mutateAsync: deleteNotification } = useDeleteNotification();
  const { mutateAsync: batchMarkAsRead } = useBatchMarkAsRead();
  const { mutateAsync: batchDelete } = useBatchDeleteNotifications();

  /** 处理通知点击 */
  const handleNotificationClick = useCallback(
    async (notification: Notification) => {
      // 如果未读，先标记为已读
      if (!notification.is_read) {
        await markAsRead(notification.id);
      }

      // 返回链接用于跳转
      return notification.link;
    },
    [markAsRead]
  );

  /** 刷新通知数据 */
  const refreshNotifications = useCallback(() => {
    void queryClient.invalidateQueries({
      queryKey: notificationQueryKeys.lists(),
    });
    void queryClient.invalidateQueries({
      queryKey: notificationQueryKeys.unreadCount(),
    });
  }, [queryClient]);

  return {
    markAsRead,
    markAllAsRead,
    deleteNotification,
    batchMarkAsRead,
    batchDelete,
    handleNotificationClick,
    refreshNotifications,
  };
}