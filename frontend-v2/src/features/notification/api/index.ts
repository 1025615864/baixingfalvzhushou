/**
 * 通知API封装
 */

import apiClient from "@/shared/lib/api/client";

import {
  NotificationListResponse,
  UnreadCountResponse,
  NotificationTypesStatsResponse,
  BatchOperationResponse,
  BatchIdsRequest,
  GetNotificationsParams,
  // 系统通知管理类型
  SystemNotification,
  GetSystemNotificationsRequest,
  GetSystemNotificationsResponse,
  CreateSystemNotificationRequest,
  UpdateSystemNotificationRequest,
} from '../types';


/**
 * 获取通知列表
 * @param params 查询参数
 * @returns 通知列表响应
 */
export async function getNotifications(
  params: GetNotificationsParams = {}
): Promise<NotificationListResponse> {
  const response = await apiClient.get<NotificationListResponse>('/notifications', {
    params: {
      page: params.page || 1,
      page_size: params.page_size || 20,
      unread_only: params.unread_only || false,
      notification_type: params.notification_type,
    },
  });
  return response.data;
}

/**
 * 获取未读通知数量
 * @returns 未读数量响应
 */
export async function getUnreadCount(): Promise<UnreadCountResponse> {
  const response = await apiClient.get<UnreadCountResponse>('/notifications/unread-count');
  return response.data;
}

/**
 * 标记通知为已读
 * @param notificationId 通知ID
 * @returns 操作结果
 */
export async function markAsRead(notificationId: number): Promise<{ message: string }> {
  const response = await apiClient.put<{ message: string }>(
    `/notifications/${notificationId}/read`
  );
  return response.data;
}

/**
 * 标记所有通知为已读
 * @returns 操作结果
 */
export async function markAllAsRead(): Promise<{ message: string }> {
  const response = await apiClient.put<{ message: string }>('/notifications/read-all');
  return response.data;
}

/**
 * 删除通知
 * @param notificationId 通知ID
 * @returns 操作结果
 */
export async function deleteNotification(notificationId: number): Promise<{ message: string }> {
  const response = await apiClient.delete<{ message: string }>(
    `/notifications/${notificationId}`
  );
  return response.data;
}

/**
 * 批量标记通知为已读
 * @param data 批量操作请求
 * @returns 批量操作响应
 */
export async function batchMarkAsRead(data: BatchIdsRequest): Promise<BatchOperationResponse> {
  const response = await apiClient.post<BatchOperationResponse>(
    '/notifications/batch-read',
    data
  );
  return response.data;
}

/**
 * 批量删除通知
 * @param data 批量操作请求
 * @returns 批量操作响应
 */
export async function batchDeleteNotifications(
  data: BatchIdsRequest
): Promise<BatchOperationResponse> {
  const response = await apiClient.post<BatchOperationResponse>(
    '/notifications/batch-delete',
    data
  );
  return response.data;
}

/**
 * 获取通知类型统计
 * @returns 通知类型统计响应
 */
export async function getNotificationTypesStats(): Promise<NotificationTypesStatsResponse> {
  const response = await apiClient.get<NotificationTypesStatsResponse>('/notifications/types');
  return response.data;
}

/**
 * 通知API对象
 */
export const notificationApi = {
  getNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  deleteNotification,
  batchMarkAsRead,
  batchDeleteNotifications,
  getNotificationTypesStats,
};

// ==================== 系统通知管理API（管理员用） ====================

const API_BASE = '/v1';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
}

/**
 * 安全获取 JSON 响应
 */
async function safeJson<T>(response: Response): Promise<T> {
  const data = await response.json() as T;
  return data;
}

/**
 * 获取 API 错误信息
 */
function getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiErrorResponse).detail || defaultMsg;
  }
  return defaultMsg;
}

/**
 * 转换系统通知数据 snake_case → camelCase
 */
function transformSystemNotification(data: {
  id: number;
  title: string;
  content: string;
  target_type: string;
  target_ids: string[] | null;
  sent_count: number;
  read_count: number;
  is_published: boolean;
  published_at: string | null;
  expires_at: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}): SystemNotification {
  return {
    id: String(data.id),
    title: data.title,
    content: data.content,
    targetType: data.target_type as 'all' | 'users' | 'lawyers' | 'admins' | 'specific',
    targetIds: data.target_ids,
    sentCount: data.sent_count,
    readCount: data.read_count,
    isPublished: data.is_published,
    publishedAt: data.published_at,
    expiresAt: data.expires_at,
    createdBy: data.created_by,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 获取系统通知列表（管理员用）
 */
export async function apiGetSystemNotifications(
  params: GetSystemNotificationsRequest = {}
): Promise<GetSystemNotificationsResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));
  if (params.isPublished !== undefined) searchParams.set('is_published', String(params.isPublished));
  if (params.keyword) searchParams.set('keyword', params.keyword);

  const response = await fetch(`${API_BASE}/admin/notifications?${searchParams.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取系统通知列表失败' }));
    throw new Error(getErrorMessage(error, '获取系统通知列表失败'));
  }

  const data = await safeJson<{
    items: Array<{
      id: number;
      title: string;
      content: string;
      target_type: string;
      target_ids: string[] | null;
      sent_count: number;
      read_count: number;
      is_published: boolean;
      published_at: string | null;
      expires_at: string | null;
      created_by: string;
      created_at: string;
      updated_at: string;
    }>;
    total: number;
    page: number;
    page_size: number;
  }>(response);

  return {
    items: (data.items ?? []).map(transformSystemNotification),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

/**
 * 创建系统通知（管理员用）
 */
export async function apiCreateSystemNotification(
  request: CreateSystemNotificationRequest
): Promise<SystemNotification> {
  const response = await apiClient.post<{
    id: number;
    title: string;
    content: string;
    target_type: string;
    target_ids: string[] | null;
    sent_count: number;
    read_count: number;
    is_published: boolean;
    published_at: string | null;
    expires_at: string | null;
    created_by: string;
    created_at: string;
    updated_at: string;
  }>(`${API_BASE}/admin/notifications`, {
    title: request.title,
    content: request.content,
    target_type: request.targetType,
    target_ids: request.targetIds,
    expires_at: request.expiresAt,
  });

  return transformSystemNotification(response.data);
}

/**
 * 更新系统通知（管理员用）
 */
export async function apiUpdateSystemNotification(
  id: string,
  request: UpdateSystemNotificationRequest
): Promise<SystemNotification> {
  const response = await apiClient.put<{
    id: number;
    title: string;
    content: string;
    target_type: string;
    target_ids: string[] | null;
    sent_count: number;
    read_count: number;
    is_published: boolean;
    published_at: string | null;
    expires_at: string | null;
    created_by: string;
    created_at: string;
    updated_at: string;
  }>(`${API_BASE}/admin/notifications/${id}`, {
    title: request.title,
    content: request.content,
    target_type: request.targetType,
    target_ids: request.targetIds,
    expires_at: request.expiresAt,
  });

  return transformSystemNotification(response.data);
}

/**
 * 删除系统通知（管理员用）
 */
export async function apiDeleteSystemNotification(id: string): Promise<void> {
  await apiClient.delete(`${API_BASE}/admin/notifications/${id}`);
}

/**
 * 发布系统通知（管理员用）
 */
export async function apiPublishSystemNotification(id: string): Promise<SystemNotification> {
  const response = await apiClient.post<{
    id: number;
    title: string;
    content: string;
    target_type: string;
    target_ids: string[] | null;
    sent_count: number;
    read_count: number;
    is_published: boolean;
    published_at: string | null;
    expires_at: string | null;
    created_by: string;
    created_at: string;
    updated_at: string;
  }>(`${API_BASE}/admin/notifications/${id}/publish`, {});

  return transformSystemNotification(response.data);
}

/**
 * 撤销系统通知（管理员用）
 */
export async function apiRevokeSystemNotification(id: string): Promise<SystemNotification> {
  const response = await apiClient.post<{
    id: number;
    title: string;
    content: string;
    target_type: string;
    target_ids: string[] | null;
    sent_count: number;
    read_count: number;
    is_published: boolean;
    published_at: string | null;
    expires_at: string | null;
    created_by: string;
    created_at: string;
    updated_at: string;
  }>(`${API_BASE}/admin/notifications/${id}/revoke`, {});

  return transformSystemNotification(response.data);
}