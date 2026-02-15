/**
 * Consultation（咨询预约）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/lawfirm/consultations 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  Consultation,
  ConsultationStatus,
  ConsultationMessage,
  CreateConsultationRequest,
  SendMessageRequest,
  ConsultationListResponse,
  ConsultationMessageListResponse,
  CancelConsultationResponse,
  // 咨询模板管理类型
  ConsultationTemplate,
  ConsultationQuestion,
  GetConsultationTemplatesRequest,
  GetConsultationTemplatesResponse,
  CreateConsultationTemplateRequest,
  UpdateConsultationTemplateRequest,
} from '../types';


// API 基础路径
const API_BASE = '/lawfirm/consultations';

// ==================== 后端响应类型定义 ====================

/** 后端咨询响应 */
interface BackendConsultationResponse {
  id: number;
  user_id: number;
  lawyer_id: number;
  subject: string;
  description: string | null;
  category: string | null;
  contact_phone: string | null;
  preferred_time: string | null;
  status: string;
  admin_note: string | null;
  created_at: string;
  updated_at: string;
  lawyer_name: string | null;
  payment_order_no: string | null;
  payment_status: string | null;
  payment_amount: number | null;
  review_id: number | null;
  can_review: boolean;
}

/** 后端咨询列表响应 */
interface BackendConsultationListResponse {
  items: BackendConsultationResponse[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端消息响应 */
interface BackendMessageResponse {
  id: number;
  consultation_id: number;
  sender_user_id: number;
  sender_role: string;
  content: string;
  created_at: string;
  sender_name: string | null;
}

/** 后端消息列表响应 */
interface BackendMessageListResponse {
  items: BackendMessageResponse[];
  total: number;
  page: number;
  page_size: number;
}

// ==================== 转换函数 ====================

/**
 * 转换后端咨询到前端格式
 */
function mapBackendToConsultation(backend: BackendConsultationResponse): Consultation {
  return {
    id: String(backend.id),
    userId: String(backend.user_id),
    lawyerId: String(backend.lawyer_id),
    subject: backend.subject,
    description: backend.description ?? undefined,
    category: backend.category ?? undefined,
    contactPhone: backend.contact_phone ?? undefined,
    preferredTime: backend.preferred_time ?? undefined,
    status: backend.status as ConsultationStatus,
    adminNote: backend.admin_note ?? undefined,
    createdAt: backend.created_at,
    updatedAt: backend.updated_at,
    lawyerName: backend.lawyer_name ?? undefined,
    paymentOrderNo: backend.payment_order_no ?? undefined,
    paymentStatus: backend.payment_status ?? undefined,
    paymentAmount: backend.payment_amount ?? undefined,
    reviewId: backend.review_id ?? undefined,
    canReview: backend.can_review,
  };
}

/**
 * 转换后端消息到前端格式
 */
function mapBackendToMessage(backend: BackendMessageResponse): ConsultationMessage {
  return {
    id: String(backend.id),
    consultationId: String(backend.consultation_id),
    senderId: String(backend.sender_user_id),
    senderRole: backend.sender_role as 'user' | 'lawyer' | 'system',
    content: backend.content,
    createdAt: backend.created_at,
    senderName: backend.sender_name ?? undefined,
  };
}

/**
 * 转换前端创建请求到后端格式
 */
function mapCreateRequestToBackend(request: CreateConsultationRequest): Record<string, unknown> {
  return {
    lawyer_id: Number(request.lawyerId),
    subject: request.subject,
    description: request.description,
    category: request.category,
    contact_phone: request.contactPhone,
    preferred_time: request.preferredTime,
  };
}

// ==================== API 方法 ====================

/**
 * 创建咨询预约
 */
export async function createConsultation(request: CreateConsultationRequest): Promise<Consultation> {
  const backendData = mapCreateRequestToBackend(request);
  const response = await apiClient.post<BackendConsultationResponse>(API_BASE, backendData);
  return mapBackendToConsultation(response.data);
}

/**
 * 获取咨询列表
 */
export async function getConsultations(params?: {
  status?: ConsultationStatus;
  page?: number;
  pageSize?: number;
}): Promise<ConsultationListResponse> {
  const queryParams = new URLSearchParams();
  
  if (params?.status) queryParams.append('status_filter', params.status);
  if (params?.page) queryParams.append('page', String(params.page));
  if (params?.pageSize) queryParams.append('page_size', String(params.pageSize));
  
  const queryString = queryParams.toString();
  const url = `${API_BASE}${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get<BackendConsultationListResponse>(url);
  const backendData = response.data;
  
  return {
    items: backendData.items.map(mapBackendToConsultation),
    total: backendData.total,
    page: backendData.page,
    pageSize: backendData.page_size,
  };
}

/**
 * 获取单个咨询详情
 */
export async function getConsultation(id: string | number): Promise<Consultation> {
  const response = await apiClient.get<BackendConsultationResponse>(`${API_BASE}/${id}`);
  return mapBackendToConsultation(response.data);
}

/**
 * 取消咨询预约
 */
export async function cancelConsultation(id: string | number): Promise<CancelConsultationResponse> {
  const response = await apiClient.post<{ message: string }>(`${API_BASE}/${id}/cancel`);
  return {
    success: true,
    message: response.data.message,
  };
}

/**
 * 获取咨询消息列表
 */
export async function getMessages(
  consultationId: string | number,
  params?: { page?: number; pageSize?: number }
): Promise<ConsultationMessageListResponse> {
  const queryParams = new URLSearchParams();
  
  if (params?.page) queryParams.append('page', String(params.page));
  if (params?.pageSize) queryParams.append('page_size', String(params.pageSize));
  
  const queryString = queryParams.toString();
  const url = `${API_BASE}/${consultationId}/messages${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get<BackendMessageListResponse>(url);
  const backendData = response.data;
  
  return {
    items: backendData.items.map(mapBackendToMessage),
    total: backendData.total,
    page: backendData.page,
    pageSize: backendData.page_size,
  };
}

/**
 * 发送咨询消息
 */
export async function sendMessage(
  consultationId: string | number,
  request: SendMessageRequest
): Promise<ConsultationMessage> {
  const response = await apiClient.post<BackendMessageResponse>(
    `${API_BASE}/${consultationId}/messages`,
    { content: request.content }
  );
  return mapBackendToMessage(response.data);
}

/**
 * 接受咨询（律师端）
 */
export async function acceptConsultation(id: string | number): Promise<Consultation> {
  const response = await apiClient.post<BackendConsultationResponse>(`${API_BASE}/${id}/accept`);
  return mapBackendToConsultation(response.data);
}

/**
 * 拒绝咨询（律师端）
 */
export async function rejectConsultation(
  id: string | number,
  reason?: string
): Promise<Consultation> {
  const response = await apiClient.post<BackendConsultationResponse>(
    `${API_BASE}/${id}/reject`,
    { reason }
  );
  return mapBackendToConsultation(response.data);
}

/**
 * 完成咨询
 */
export async function completeConsultation(id: string | number): Promise<Consultation> {
  const response = await apiClient.post<BackendConsultationResponse>(`${API_BASE}/${id}/complete`);
  return mapBackendToConsultation(response.data);
}

// ==================== 咨询模板管理API（管理员用） ====================

const ADMIN_API_BASE = '/v1/admin';

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
 * 转换后端模板数据到前端格式
 */
function mapBackendToTemplate(data: {
  id: number;
  key: string;
  name: string;
  description: string;
  category: string;
  questions: Array<{
    id: string;
    type: string;
    label: string;
    placeholder?: string;
    required: boolean;
    options?: string[];
    validation?: {
      min?: number;
      max?: number;
      pattern?: string;
      message?: string;
    };
  }>;
  status: string;
  is_default: boolean;
  usage_count: number;
  created_by: string;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}): ConsultationTemplate {
  return {
    id: String(data.id),
    key: data.key,
    name: data.name,
    description: data.description,
    category: data.category as ConsultationTemplate['category'],
    questions: (data.questions ?? []).map((q) => ({
      id: q.id,
      type: q.type as ConsultationQuestion['type'],
      label: q.label,
      placeholder: q.placeholder,
      required: q.required,
      options: q.options,
      validation: q.validation,
    })),
    status: data.status as ConsultationTemplate['status'],
    isDefault: data.is_default,
    usageCount: data.usage_count,
    createdBy: data.created_by,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    publishedAt: data.published_at,
  };
}

/**
 * 获取咨询模板列表（管理员用）
 */
export async function apiGetConsultationTemplates(
  params: GetConsultationTemplatesRequest = {}
): Promise<GetConsultationTemplatesResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));
  if (params.category) searchParams.set('category', params.category);
  if (params.status) searchParams.set('status', params.status);
  if (params.keyword) searchParams.set('keyword', params.keyword);

  const response = await fetch(`${ADMIN_API_BASE}/consultation-templates?${searchParams.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取咨询模板列表失败' }));
    throw new Error(getErrorMessage(error, '获取咨询模板列表失败'));
  }

  const data = await safeJson<{
    items: Array<{
      id: number;
      key: string;
      name: string;
      description: string;
      category: string;
      questions: Array<{
        id: string;
        type: string;
        label: string;
        placeholder?: string;
        required: boolean;
        options?: string[];
        validation?: {
          min?: number;
          max?: number;
          pattern?: string;
          message?: string;
        };
      }>;
      status: string;
      is_default: boolean;
      usage_count: number;
      created_by: string;
      created_at: string;
      updated_at: string;
      published_at: string | null;
    }>;
    total: number;
    page: number;
    page_size: number;
  }>(response);

  return {
    items: (data.items ?? []).map(mapBackendToTemplate),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

/**
 * 获取咨询模板详情（管理员用）
 */
export async function apiGetConsultationTemplate(id: string): Promise<ConsultationTemplate> {
  const response = await fetch(`${ADMIN_API_BASE}/consultation-templates/${id}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取咨询模板详情失败' }));
    throw new Error(getErrorMessage(error, '获取咨询模板详情失败'));
  }

  const data = await safeJson<{
    id: number;
    key: string;
    name: string;
    description: string;
    category: string;
    questions: Array<{
      id: string;
      type: string;
      label: string;
      placeholder?: string;
      required: boolean;
      options?: string[];
      validation?: {
        min?: number;
        max?: number;
        pattern?: string;
        message?: string;
      };
    }>;
    status: string;
    is_default: boolean;
    usage_count: number;
    created_by: string;
    created_at: string;
    updated_at: string;
    published_at: string | null;
  }>(response);

  return mapBackendToTemplate(data);
}

/**
 * 创建咨询模板（管理员用）
 */
export async function apiCreateConsultationTemplate(
  request: CreateConsultationTemplateRequest
): Promise<ConsultationTemplate> {
  const response = await apiClient.post<{
    id: number;
    key: string;
    name: string;
    description: string;
    category: string;
    questions: Array<{
      id: string;
      type: string;
      label: string;
      placeholder?: string;
      required: boolean;
      options?: string[];
      validation?: {
        min?: number;
        max?: number;
        pattern?: string;
        message?: string;
      };
    }>;
    status: string;
    is_default: boolean;
    usage_count: number;
    created_by: string;
    created_at: string;
    updated_at: string;
    published_at: string | null;
  }>(`${ADMIN_API_BASE}/consultation-templates`, {
    key: request.key,
    name: request.name,
    description: request.description,
    category: request.category,
    questions: request.questions,
    is_default: request.isDefault,
  });

  return mapBackendToTemplate(response.data);
}

/**
 * 更新咨询模板（管理员用）
 */
export async function apiUpdateConsultationTemplate(
  id: string,
  request: UpdateConsultationTemplateRequest
): Promise<ConsultationTemplate> {
  const response = await apiClient.put<{
    id: number;
    key: string;
    name: string;
    description: string;
    category: string;
    questions: Array<{
      id: string;
      type: string;
      label: string;
      placeholder?: string;
      required: boolean;
      options?: string[];
      validation?: {
        min?: number;
        max?: number;
        pattern?: string;
        message?: string;
      };
    }>;
    status: string;
    is_default: boolean;
    usage_count: number;
    created_by: string;
    created_at: string;
    updated_at: string;
    published_at: string | null;
  }>(`${ADMIN_API_BASE}/consultation-templates/${id}`, {
    name: request.name,
    description: request.description,
    category: request.category,
    questions: request.questions,
    is_default: request.isDefault,
  });

  return mapBackendToTemplate(response.data);
}

/**
 * 删除咨询模板（管理员用）
 */
export async function apiDeleteConsultationTemplate(id: string): Promise<void> {
  await apiClient.delete(`${ADMIN_API_BASE}/consultation-templates/${id}`);
}

/**
 * 发布咨询模板（管理员用）
 */
export async function apiPublishConsultationTemplate(id: string): Promise<ConsultationTemplate> {
  const response = await apiClient.post<{
    id: number;
    key: string;
    name: string;
    description: string;
    category: string;
    questions: Array<{
      id: string;
      type: string;
      label: string;
      placeholder?: string;
      required: boolean;
      options?: string[];
      validation?: {
        min?: number;
        max?: number;
        pattern?: string;
        message?: string;
      };
    }>;
    status: string;
    is_default: boolean;
    usage_count: number;
    created_by: string;
    created_at: string;
    updated_at: string;
    published_at: string | null;
  }>(`${ADMIN_API_BASE}/consultation-templates/${id}/publish`, {});

  return mapBackendToTemplate(response.data);
}