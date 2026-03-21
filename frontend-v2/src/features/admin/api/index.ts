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

/**
 * 获取用户列表
 */
export async function apiGetUsers(request: GetUsersRequest = {}): Promise<GetUsersResponse> {
  const { data } = await apiClient.get<{
    items: Array<{
      id: number;
      username: string;
      email: string;
      nickname: string | null;
      phone: string | null;
      avatar: string | null;
      role: string;
      is_active: boolean;
      email_verified: boolean;
      created_at: string;
      updated_at: string | null;
    }>;
    total: number;
    page: number;
    page_size: number;
  }>(`${USER_API_BASE}/admin/list`, {
    params: {
      ...(request.page && { page: request.page }),
      ...(request.pageSize && { page_size: request.pageSize }),
      ...(request.keyword && { keyword: request.keyword }),
    },
  });

  return {
    items: data.items.map(item => ({
      id: item.id,
      username: item.username,
      email: item.email,
      nickname: item.nickname,
      phone: item.phone,
      avatar: item.avatar,
      role: item.role as 'user' | 'lawyer' | 'admin',
      is_active: item.is_active,
      email_verified: item.email_verified,
      created_at: item.created_at,
      updated_at: item.updated_at,
    })),
    total: data.total,
    page: data.page,
    page_size: data.page_size,
  };
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
  const response = await apiClient.get<Blob>(`${ADMIN_API_BASE}/export/users`, {
    params: { format },
    responseType: 'blob',
  });
  return response.data;
}

/**
 * 导出帖子数据
 */
export async function apiExportPosts(): Promise<Blob> {
  const response = await apiClient.get<Blob>(`${ADMIN_API_BASE}/export/posts`, {
    responseType: 'blob',
  });
  return response.data;
}

/**
 * 导出新闻数据
 */
export async function apiExportNews(): Promise<Blob> {
  const response = await apiClient.get<Blob>(`${ADMIN_API_BASE}/export/news`, {
    responseType: 'blob',
  });
  return response.data;
}

/**
 * 导出律所数据
 */
export async function apiExportLawfirms(): Promise<Blob> {
  const response = await apiClient.get<Blob>(`${ADMIN_API_BASE}/export/lawfirms`, {
    responseType: 'blob',
  });
  return response.data;
}