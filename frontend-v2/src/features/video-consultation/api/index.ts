/**
 * Video Consultation API 层
 * 对接后端 /api/v1/video-consultations 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  VideoConsultation,
  VideoConsultationListResponse,
  CreateVideoConsultationRequest,
  VideoAvailableSlotsResponse,
  VideoConsultationFee,
  MemberDiscount,
  UserUsage,
} from '../types';


const API_BASE = '/video-consultations';


/**
 * 转换后端咨询到前端格式
 */
function mapBackendToConsultation(backend: {
  id: number;
  user_id: number;
  lawyer_id: number;
  subject: string;
  description?: string;
  category?: string;
  scheduled_time: string;
  duration_minutes: number;
  meeting_room_id?: string;
  meeting_password?: string;
  meeting_url?: string;
  status: string;
  payment_status: string;
  payment_amount: number;
  is_free: boolean;
  discount_rate: number;
  started_at?: string;
  ended_at?: string;
  completed_at?: string;
  cancelled_at?: string;
  created_at: string;
  updated_at: string;
  lawyer_name?: string;
}): VideoConsultation {
  return {
    id: String(backend.id),
    userId: String(backend.user_id),
    lawyerId: String(backend.lawyer_id),
    subject: backend.subject,
    description: backend.description ?? undefined,
    category: backend.category ?? undefined,
    scheduledTime: backend.scheduled_time,
    durationMinutes: backend.duration_minutes,
    meetingRoomId: backend.meeting_room_id ?? undefined,
    meetingPassword: backend.meeting_password ?? undefined,
    meetingUrl: backend.meeting_url ?? undefined,
    status: backend.status as VideoConsultation['status'],
    paymentStatus: backend.payment_status as VideoConsultation['paymentStatus'],
    paymentAmount: backend.payment_amount,
    isFree: backend.is_free,
    discountRate: backend.discount_rate,
    startedAt: backend.started_at ?? undefined,
    endedAt: backend.ended_at ?? undefined,
    completedAt: backend.completed_at ?? undefined,
    cancelledAt: backend.cancelled_at ?? undefined,
    createdAt: backend.created_at,
    updatedAt: backend.updated_at,
    lawyerName: backend.lawyer_name ?? undefined,
  };
}


/**
 * 转换前端创建请求到后端格式
 */
function mapCreateRequestToBackend(request: CreateVideoConsultationRequest): Record<string, unknown> {
  return {
    lawyer_id: request.lawyerId,
    subject: request.subject,
    description: request.description,
    category: request.category,
    scheduled_time: request.scheduledTime,
  };
}


/**
 * 创建视频咨询预约
 */
export async function createVideoConsultation(
  request: CreateVideoConsultationRequest
): Promise<VideoConsultation> {
  const backendData = mapCreateRequestToBackend(request);
  const response = await apiClient.post<{
    id: number;
    user_id: number;
    lawyer_id: number;
    subject: string;
    description?: string;
    category?: string;
    scheduled_time: string;
    duration_minutes: number;
    meeting_room_id?: string;
    meeting_password?: string;
    meeting_url?: string;
    status: string;
    payment_status: string;
    payment_amount: number;
    is_free: boolean;
    discount_rate: number;
    started_at?: string;
    ended_at?: string;
    completed_at?: string;
    cancelled_at?: string;
    created_at: string;
    updated_at: string;
    lawyer_name?: string;
  }>(API_BASE, backendData);
  return mapBackendToConsultation(response.data);
}


/**
 * 获取视频咨询列表
 */
export async function getVideoConsultations(params?: {
  status?: string;
  page?: number;
  pageSize?: number;
}): Promise<VideoConsultationListResponse> {
  const queryParams = new URLSearchParams();
  
  if (params?.status) queryParams.append('status_filter', params.status);
  if (params?.page) queryParams.append('page', String(params.page));
  if (params?.pageSize) queryParams.append('page_size', String(params.pageSize));
  
  const queryString = queryParams.toString();
  const url = `${API_BASE}${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get<{
    items: Array<{
      id: number;
      user_id: number;
      lawyer_id: number;
      subject: string;
      description?: string;
      category?: string;
      scheduled_time: string;
      duration_minutes: number;
      meeting_room_id?: string;
      meeting_password?: string;
      meeting_url?: string;
      status: string;
      payment_status: string;
      payment_amount: number;
      is_free: boolean;
      discount_rate: number;
      started_at?: string;
      ended_at?: string;
      completed_at?: string;
      cancelled_at?: string;
      created_at: string;
      updated_at: string;
      lawyer_name?: string;
    }>;
    total: number;
    page: number;
    page_size: number;
  }>(url);
  const backendData = response.data;
  
  return {
    items: backendData.items.map(mapBackendToConsultation),
    total: backendData.total,
    page: backendData.page,
    pageSize: backendData.page_size,
  };
}


/**
 * 获取视频咨询详情
 */
export async function getVideoConsultation(id: string | number): Promise<VideoConsultation> {
  const response = await apiClient.get<{
    id: number;
    user_id: number;
    lawyer_id: number;
    subject: string;
    description?: string;
    category?: string;
    scheduled_time: string;
    duration_minutes: number;
    meeting_room_id?: string;
    meeting_password?: string;
    meeting_url?: string;
    status: string;
    payment_status: string;
    payment_amount: number;
    is_free: boolean;
    discount_rate: number;
    started_at?: string;
    ended_at?: string;
    completed_at?: string;
    cancelled_at?: string;
    created_at: string;
    updated_at: string;
    lawyer_name?: string;
  }>(`${API_BASE}/${id}`);
  return mapBackendToConsultation(response.data);
}


/**
 * 确认视频咨询（律师端）
 */
export async function confirmVideoConsultation(id: string | number): Promise<{ id: number; status: string }> {
  const response = await apiClient.post<{ id: number; status: string }>(`${API_BASE}/${id}/confirm`);
  return response.data;
}


/**
 * 开始视频咨询
 */
export async function startVideoConsultation(id: string | number): Promise<{ id: number; status: string; meeting_url?: string }> {
  const response = await apiClient.post<{ id: number; status: string; meeting_url?: string }>(`${API_BASE}/${id}/start`);
  return response.data;
}


/**
 * 结束视频咨询
 */
export async function endVideoConsultation(id: string | number): Promise<{ id: number; status: string; duration_minutes: number }> {
  const response = await apiClient.post<{ id: number; status: string; duration_minutes: number }>(`${API_BASE}/${id}/end`);
  return response.data;
}


/**
 * 取消视频咨询
 */
export async function cancelVideoConsultation(id: string | number): Promise<{ id: number; status: string }> {
  const response = await apiClient.post<{ id: number; status: string }>(`${API_BASE}/${id}/cancel`);
  return response.data;
}


/**
 * 获取律师可用视频时段
 */
export async function getLawyerVideoSlots(
  lawyerId: number | string,
  date: string
): Promise<VideoAvailableSlotsResponse> {
  const params = new URLSearchParams({ date });
  const response = await apiClient.get<VideoAvailableSlotsResponse>(
    `/v1/video-consultations/lawyers/${String(lawyerId)}/available-slots?${params.toString()}`
  );
  return response.data;
}


/**
 * 获取律师视频咨询费用
 */
export async function getLawyerVideoFee(lawyerId: number | string): Promise<VideoConsultationFee> {
  const response = await apiClient.get<VideoConsultationFee>(
    `/v1/video-consultations/lawyers/${String(lawyerId)}/fee`
  );
  return response.data;
}


/**
 * 获取我的会员折扣
 */
export async function getMemberDiscount(): Promise<MemberDiscount> {
  const response = await apiClient.get<MemberDiscount>(`${API_BASE}/member-discount`);
  return response.data;
}


/**
 * 获取我的使用情况
 */
export async function getMyUsage(): Promise<UserUsage> {
  const response = await apiClient.get<UserUsage>(`${API_BASE}/usage`);
  return response.data;
}