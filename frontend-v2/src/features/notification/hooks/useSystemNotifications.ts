/**
 * 系统通知管理 Hook（管理员用）
 * 使用 React Query 管理系统通知相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  GetSystemNotificationsRequest,
  GetSystemNotificationsResponse,
  CreateSystemNotificationRequest,
  UpdateSystemNotificationRequest,
} from '../types';
import {
  apiGetSystemNotifications,
  apiCreateSystemNotification,
  apiUpdateSystemNotification,
  apiDeleteSystemNotification,
  apiPublishSystemNotification,
  apiRevokeSystemNotification,
} from '../api';

// Query Keys
const SYSTEM_NOTIFICATION_KEYS = {
  all: ['notification', 'system', 'admin'] as const,
  list: (params: GetSystemNotificationsRequest) => [...SYSTEM_NOTIFICATION_KEYS.all, 'list', params] as const,
} as const;

/**
 * 获取系统通知列表（管理员用）
 */
export function useSystemNotifications(params: GetSystemNotificationsRequest = {}) {
  return useQuery<GetSystemNotificationsResponse, Error>({
    queryKey: SYSTEM_NOTIFICATION_KEYS.list(params),
    queryFn: () => apiGetSystemNotifications(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 创建系统通知（管理员用）
 */
export function useCreateSystemNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateSystemNotificationRequest) => apiCreateSystemNotification(request),
    onSuccess: () => {
      // 创建成功后刷新通知列表
      void queryClient.invalidateQueries({ queryKey: SYSTEM_NOTIFICATION_KEYS.all });
    },
  });
}

/**
 * 更新系统通知（管理员用）
 */
export function useUpdateSystemNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateSystemNotificationRequest }) =>
      apiUpdateSystemNotification(id, request),
    onSuccess: () => {
      // 更新成功后刷新通知列表
      void queryClient.invalidateQueries({ queryKey: SYSTEM_NOTIFICATION_KEYS.all });
    },
  });
}

/**
 * 删除系统通知（管理员用）
 */
export function useDeleteSystemNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiDeleteSystemNotification(id),
    onSuccess: () => {
      // 删除成功后刷新通知列表
      void queryClient.invalidateQueries({ queryKey: SYSTEM_NOTIFICATION_KEYS.all });
    },
  });
}

/**
 * 发布系统通知（管理员用）
 */
export function usePublishSystemNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiPublishSystemNotification(id),
    onSuccess: () => {
      // 发布成功后刷新通知列表
      void queryClient.invalidateQueries({ queryKey: SYSTEM_NOTIFICATION_KEYS.all });
    },
  });
}

/**
 * 撤销系统通知（管理员用）
 */
export function useRevokeSystemNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiRevokeSystemNotification(id),
    onSuccess: () => {
      // 撤销成功后刷新通知列表
      void queryClient.invalidateQueries({ queryKey: SYSTEM_NOTIFICATION_KEYS.all });
    },
  });
}
