/**
 * Calendar（法律日历）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/calendar 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  CalendarReminder,
  CreateReminderRequest,
  CreateReminderResponse,
  UpdateReminderRequest,
  UpdateReminderResponse,
  GetReminderListRequest,
  GetReminderListResponse,
  DeleteReminderResponse,
} from '../types';


// API 基础路径
const API_BASE = '/calendar';

// ==================== 后端响应类型定义 ====================

/** 后端提醒响应 */
interface BackendReminderResponse {
  id: number;
  user_id: number;
  title: string;
  note: string | null;
  due_at: string;
  remind_at: string | null;
  is_done: boolean;
  done_at: string | null;
  created_at: string;
  updated_at: string;
}

/** 后端提醒列表响应 */
interface BackendReminderListResponse {
  items: BackendReminderResponse[];
  total: number;
}

// ==================== 转换函数 ====================

/**
 * 转换后端提醒到前端格式
 */
function mapBackendToReminder(backend: BackendReminderResponse): CalendarReminder {
  return {
    id: backend.id,
    userId: backend.user_id,
    title: backend.title,
    note: backend.note ?? undefined,
    dueAt: backend.due_at,
    remindAt: backend.remind_at ?? undefined,
    isDone: backend.is_done,
    doneAt: backend.done_at ?? undefined,
    createdAt: backend.created_at,
    updatedAt: backend.updated_at,
  };
}

/**
 * 转换前端创建请求到后端格式
 */
function mapCreateRequestToBackend(request: CreateReminderRequest): Record<string, unknown> {
  return {
    title: request.title,
    note: request.note,
    due_at: request.dueAt,
    remind_at: request.remindAt,
  };
}

/**
 * 转换前端更新请求到后端格式
 */
function mapUpdateRequestToBackend(request: UpdateReminderRequest): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  
  if (request.title !== undefined) result.title = request.title;
  if (request.note !== undefined) result.note = request.note;
  if (request.dueAt !== undefined) result.due_at = request.dueAt;
  if (request.remindAt !== undefined) result.remind_at = request.remindAt;
  if (request.isDone !== undefined) result.is_done = request.isDone;
  
  return result;
}

// ==================== API 方法 ====================

/**
 * 创建提醒
 */
export async function createReminder(request: CreateReminderRequest): Promise<CreateReminderResponse> {
  const backendData = mapCreateRequestToBackend(request);
  const response = await apiClient.post<BackendReminderResponse>(`${API_BASE}/reminders`, backendData);
  return mapBackendToReminder(response.data);
}

/**
 * 获取提醒列表
 */
export async function getReminders(params: GetReminderListRequest = {}): Promise<GetReminderListResponse> {
  const queryParams = new URLSearchParams();
  
  if (params.page) queryParams.append('page', String(params.page));
  if (params.pageSize) queryParams.append('page_size', String(params.pageSize));
  if (params.done !== undefined && params.done !== null) queryParams.append('done', String(params.done));
  if (params.fromAt) queryParams.append('from_at', params.fromAt);
  if (params.toAt) queryParams.append('to_at', params.toAt);
  
  const queryString = queryParams.toString();
  const url = `${API_BASE}/reminders${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get<BackendReminderListResponse>(url);
  const backendData = response.data;
  
  return {
    items: backendData.items.map(mapBackendToReminder),
    total: backendData.total,
  };
}

/**
 * 获取单个提醒
 */
export async function getReminder(id: number): Promise<CalendarReminder> {
  const response = await apiClient.get<BackendReminderResponse>(`${API_BASE}/reminders/${id}`);
  return mapBackendToReminder(response.data);
}

/**
 * 更新提醒
 */
export async function updateReminder(
  id: number, 
  request: UpdateReminderRequest
): Promise<UpdateReminderResponse> {
  const backendData = mapUpdateRequestToBackend(request);
  const response = await apiClient.put<BackendReminderResponse>(`${API_BASE}/reminders/${id}`, backendData);
  return mapBackendToReminder(response.data);
}

/**
 * 删除提醒
 */
export async function deleteReminder(id: number): Promise<DeleteReminderResponse> {
  const response = await apiClient.delete<DeleteReminderResponse>(`${API_BASE}/reminders/${id}`);
  return response.data;
}

/**
 * 切换提醒状态
 */
export async function toggleReminderStatus(id: number, isDone: boolean): Promise<UpdateReminderResponse> {
  const response = await updateReminder(id, { isDone });
  return response;
}