/**
 * Admin（管理后台）API 层
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  GetUsersRequest,
  GetUsersResponse,
  ToggleUserActiveResponse,
  UpdateUserRoleRequest,
  UpdateUserRoleResponse,
  AdminStats,
} from '../types';


// API 基础路径
const USER_API_BASE = '/user';
const ADMIN_API_BASE = '/admin';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
}

/**
 * 安全获取 JSON 响应
 */
function safeJson<T>(response: Response): Promise<T> {
  return response.json() as Promise<T>;
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
 * 获取用户列表
 */
export async function apiGetUsers(request: GetUsersRequest = {}): Promise<GetUsersResponse> {
  const searchParams = new URLSearchParams();
  if (request.page) searchParams.set('page', request.page.toString());
  if (request.pageSize) searchParams.set('page_size', request.pageSize.toString());
  if (request.keyword) searchParams.set('keyword', request.keyword);

  const url = `${USER_API_BASE}/admin/list${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取用户列表失败' }));
    throw new Error(getErrorMessage(error, '获取用户列表失败'));
  }

  return safeJson<GetUsersResponse>(response);
}

/**
 * 切换用户激活状态
 */
export async function apiToggleUserActive(userId: number): Promise<ToggleUserActiveResponse> {
  const response = await apiClient.put<ToggleUserActiveResponse>(`${USER_API_BASE}/admin/${userId}/toggle-active`);
  return response.data;
}

/**
 * 更新用户角色
 */
export async function apiUpdateUserRole(
  userId: number,
  request: UpdateUserRoleRequest
): Promise<UpdateUserRoleResponse> {
  const response = await apiClient.put<UpdateUserRoleResponse>(`${USER_API_BASE}/admin/${userId}/role`, request);
  return response.data;
}

/**
 * 获取系统统计数据
 */
export async function apiGetAdminStats(): Promise<AdminStats> {
  const response = await apiClient.get<AdminStats>(`${ADMIN_API_BASE}/stats`);
  return response.data;
}

/**
 * 导出用户数据
 */
export async function apiExportUsers(format: 'csv' = 'csv'): Promise<Blob> {
  const response = await fetch(`${ADMIN_API_BASE}/export/users?format=${format}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: '导出用户数据失败' })) as { detail?: string };
    throw new Error(errorData.detail || '导出用户数据失败');
  }

  return response.blob();
}

/**
 * 导出帖子数据
 */
export async function apiExportPosts(): Promise<Blob> {
  const response = await fetch(`${ADMIN_API_BASE}/export/posts`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '导出帖子数据失败' }));
    throw new Error(getErrorMessage(error, '导出帖子数据失败'));
  }

  return response.blob();
}

/**
 * 导出新闻数据
 */
export async function apiExportNews(): Promise<Blob> {
  const response = await fetch(`${ADMIN_API_BASE}/export/news`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '导出新闻数据失败' }));
    throw new Error(getErrorMessage(error, '导出新闻数据失败'));
  }

  return response.blob();
}

/**
 * 导出律所数据
 */
export async function apiExportLawfirms(): Promise<Blob> {
  const response = await fetch(`${ADMIN_API_BASE}/export/lawfirms`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '导出律所数据失败' }));
    throw new Error(getErrorMessage(error, '导出律所数据失败'));
  }

  return response.blob();
}