/**
 * 用户反馈功能 API 层
 * 基于统一的 apiClient，对接后端 /api/v1/feedback 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  Feedback,
  CreateFeedbackDTO,
  UpdateFeedbackDTO,
  FeedbackListResponse,
  FeedbackStatsResponse,
  FeedbackQueryParams,
} from '../types';


// API 基础路径
const API_BASE = '/feedback';

// ==================== 后端响应类型定义 ====================

/** 后端反馈工单响应 */
interface BackendFeedbackTicketResponse {
  id: number;
  user_id: number;
  subject: string;
  content: string;
  status: string;
  admin_reply: string | null;
  admin_id: number | null;
  created_at: string;
  updated_at: string;
}

/** 后端反馈列表响应 */
interface BackendFeedbackListResponse {
  items: BackendFeedbackTicketResponse[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端反馈统计响应 */
interface BackendFeedbackStatsResponse {
  total: number;
  open: number;
  processing: number;
  closed: number;
  unassigned: number;
}

// ==================== 转换函数 ====================

/**
 * 转换后端反馈工单到前端格式
 */
function mapBackendToFeedback(data: BackendFeedbackTicketResponse): Feedback {
  return {
    id: data.id,
    userId: data.user_id,
    type: 'other', // 后端目前不支持类型，默认为other
    subject: data.subject,
    content: data.content,
    status: data.status as Feedback['status'],
    adminReply: data.admin_reply,
    adminId: data.admin_id,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

// ==================== 用户反馈 API ====================

/**
 * 提交反馈工单
 */
export async function apiCreateFeedback(data: CreateFeedbackDTO): Promise<Feedback> {
  const response = await apiClient.post<BackendFeedbackTicketResponse>(API_BASE, {
    subject: data.subject,
    content: data.content,
    // 注意：后端目前只支持subject和content，其他字段（type、images、contact）暂不发送
  });

  return mapBackendToFeedback(response.data);
}

/**
 * 获取我的反馈列表
 */
export async function apiGetMyFeedbackList(
  params?: FeedbackQueryParams
): Promise<FeedbackListResponse> {
  const response = await apiClient.get<BackendFeedbackListResponse>(API_BASE, {
    params: {
      page: params?.page || 1,
      page_size: params?.pageSize || 20,
    },
  });

  return {
    items: response.data.items.map(mapBackendToFeedback),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

// ==================== 管理员反馈 API ====================

/**
 * 获取反馈工单统计（管理员）
 */
export async function apiGetFeedbackStats(): Promise<FeedbackStatsResponse> {
  const response = await apiClient.get<BackendFeedbackStatsResponse>(
    `${API_BASE}/admin/tickets/stats`
  );

  return {
    total: response.data.total,
    open: response.data.open,
    processing: response.data.processing,
    closed: response.data.closed,
    unassigned: response.data.unassigned,
  };
}

/**
 * 获取反馈工单列表（管理员）
 */
export async function apiGetAdminFeedbackList(
  params?: FeedbackQueryParams
): Promise<FeedbackListResponse> {
  const response = await apiClient.get<BackendFeedbackListResponse>(
    `${API_BASE}/admin/tickets`,
    {
      params: {
        page: params?.page || 1,
        page_size: params?.pageSize || 20,
        status: params?.status,
        keyword: params?.keyword,
      },
    }
  );

  return {
    items: response.data.items.map(mapBackendToFeedback),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

/**
 * 更新反馈工单（管理员）
 */
export async function apiUpdateFeedback(
  ticketId: number,
  data: UpdateFeedbackDTO
): Promise<Feedback> {
  const response = await apiClient.put<BackendFeedbackTicketResponse>(
    `${API_BASE}/admin/tickets/${ticketId}`,
    {
      status: data.status,
      admin_reply: data.adminReply,
      admin_id: data.adminId,
    }
  );

  return mapBackendToFeedback(response.data);
}