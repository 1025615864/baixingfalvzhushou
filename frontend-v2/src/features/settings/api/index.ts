/**
 * Settings（系统设置）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/admin/settings 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  SystemConfig,
  GetSystemConfigResponse,
  UpdateSystemConfigRequest,
  SystemLog,
  GetSystemLogsRequest,
  GetSystemLogsResponse,
  SystemStatus,
  BackupInfo,
  GetBackupsResponse,
} from '../types';

// API 基础路径
const API_BASE = '/admin/settings';

// ==================== 后端响应类型定义 ====================

/** 后端系统配置响应 */
interface BackendSystemConfigResponse {
  site: {
    site_name: string;
    site_description: string;
    site_logo: string | null;
    site_favicon: string | null;
    contact_email: string;
    contact_phone: string;
    icp: string;
    copyright: string;
  };
  user: {
    default_user_role: string;
    require_email_verification: boolean;
    require_phone_verification: boolean;
    allow_registration: boolean;
    password_min_length: number;
    password_require_uppercase: boolean;
    password_require_number: boolean;
    password_require_special: boolean;
    session_timeout: number;
  };
  consultation: {
    enable_consultation: boolean;
    require_payment: boolean;
    default_price: number;
    min_price: number;
    max_price: number;
    lawyer_commission_rate: number;
    platform_commission_rate: number;
    auto_complete_hours: number;
    max_consultation_duration: number;
  };
  document: {
    enable_document_generation: boolean;
    max_documents_per_day: number;
    max_upload_size: number;
    allowed_file_types: string[];
    storage_provider: string;
  };
  payment: {
    enable_alipay: boolean;
    enable_wechat_pay: boolean;
    enable_balance: boolean;
    min_withdrawal_amount: number;
    withdrawal_fee_rate: number;
    withdrawal_processing_days: number;
  };
  notification: {
    enable_email_notification: boolean;
    enable_sms_notification: boolean;
    enable_push_notification: boolean;
    email_from: string;
    sms_provider: string;
  };
  security: {
    enable_captcha: boolean;
    max_login_attempts: number;
    lockout_duration: number;
    enable_ip_whitelist: boolean;
    ip_whitelist: string[];
    enable_audit_log: boolean;
  };
}

/** 后端系统日志响应 */
interface BackendSystemLogResponse {
  id: number;
  level: string;
  module: string;
  message: string;
  details?: Record<string, unknown>;
  user_id?: number;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

/** 后端系统状态响应 */
interface BackendSystemStatusResponse {
  version: string;
  uptime: number;
  environment: string;
  database: {
    connected: boolean;
    latency: number;
  };
  cache: {
    connected: boolean;
    latency: number;
  };
  storage: {
    connected: boolean;
    used: number;
    total: number;
  };
  memory: {
    used: number;
    total: number;
  };
  cpu: {
    usage: number;
    cores: number;
  };
}

/** 后端备份响应 */
interface BackendBackupResponse {
  id: number;
  name: string;
  size: number;
  type: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  download_url?: string;
}

// ==================== 转换函数 ====================

/**
 * 转换后端配置到前端格式
 */
function mapBackendToConfig(backend: BackendSystemConfigResponse): SystemConfig {
  return {
    site: {
      siteName: backend.site.site_name,
      siteDescription: backend.site.site_description,
      siteLogo: backend.site.site_logo,
      siteFavicon: backend.site.site_favicon,
      contactEmail: backend.site.contact_email,
      contactPhone: backend.site.contact_phone,
      icp: backend.site.icp,
      copyright: backend.site.copyright,
    },
    user: {
      defaultUserRole: backend.user.default_user_role as 'user' | 'lawyer',
      requireEmailVerification: backend.user.require_email_verification,
      requirePhoneVerification: backend.user.require_phone_verification,
      allowRegistration: backend.user.allow_registration,
      passwordMinLength: backend.user.password_min_length,
      passwordRequireUppercase: backend.user.password_require_uppercase,
      passwordRequireNumber: backend.user.password_require_number,
      passwordRequireSpecial: backend.user.password_require_special,
      sessionTimeout: backend.user.session_timeout,
    },
    consultation: {
      enableConsultation: backend.consultation.enable_consultation,
      requirePayment: backend.consultation.require_payment,
      defaultPrice: backend.consultation.default_price,
      minPrice: backend.consultation.min_price,
      maxPrice: backend.consultation.max_price,
      lawyerCommissionRate: backend.consultation.lawyer_commission_rate,
      platformCommissionRate: backend.consultation.platform_commission_rate,
      autoCompleteHours: backend.consultation.auto_complete_hours,
      maxConsultationDuration: backend.consultation.max_consultation_duration,
    },
    document: {
      enableDocumentGeneration: backend.document.enable_document_generation,
      maxDocumentsPerDay: backend.document.max_documents_per_day,
      maxUploadSize: backend.document.max_upload_size,
      allowedFileTypes: backend.document.allowed_file_types,
      storageProvider: backend.document.storage_provider as 'local' | 'oss' | 's3',
    },
    payment: {
      enableAlipay: backend.payment.enable_alipay,
      enableWechatPay: backend.payment.enable_wechat_pay,
      enableBalance: backend.payment.enable_balance,
      minWithdrawalAmount: backend.payment.min_withdrawal_amount,
      withdrawalFeeRate: backend.payment.withdrawal_fee_rate,
      withdrawalProcessingDays: backend.payment.withdrawal_processing_days,
    },
    notification: {
      enableEmailNotification: backend.notification.enable_email_notification,
      enableSmsNotification: backend.notification.enable_sms_notification,
      enablePushNotification: backend.notification.enable_push_notification,
      emailFrom: backend.notification.email_from,
      smsProvider: backend.notification.sms_provider,
    },
    security: {
      enableCaptcha: backend.security.enable_captcha,
      maxLoginAttempts: backend.security.max_login_attempts,
      lockoutDuration: backend.security.lockout_duration,
      enableIpWhitelist: backend.security.enable_ip_whitelist,
      ipWhitelist: backend.security.ip_whitelist,
      enableAuditLog: backend.security.enable_audit_log,
    },
  };
}

/**
 * 转换后端日志到前端格式
 */
function mapBackendToLog(backend: BackendSystemLogResponse): SystemLog {
  return {
    id: String(backend.id),
    level: backend.level as SystemLog['level'],
    module: backend.module,
    message: backend.message,
    details: backend.details,
    userId: backend.user_id ? String(backend.user_id) : undefined,
    ipAddress: backend.ip_address,
    userAgent: backend.user_agent,
    createdAt: backend.created_at,
  };
}

/**
 * 转换后端备份到前端格式
 */
function mapBackendToBackup(backend: BackendBackupResponse): BackupInfo {
  return {
    id: String(backend.id),
    name: backend.name,
    size: backend.size,
    type: backend.type as 'full' | 'incremental',
    status: backend.status as 'pending' | 'running' | 'completed' | 'failed',
    createdAt: backend.created_at,
    completedAt: backend.completed_at,
    downloadUrl: backend.download_url,
  };
}

// ==================== API 方法 ====================

/**
 * 获取系统配置
 */
export async function apiGetSystemConfig(): Promise<GetSystemConfigResponse> {
  const response = await apiClient.get<{
    config: BackendSystemConfigResponse;
    updated_at: string;
    updated_by: string;
  }>(`${API_BASE}/settings`);
  return {
    config: mapBackendToConfig(response.data.config),
    updatedAt: response.data.updated_at,
    updatedBy: response.data.updated_by,
  };
}

/**
 * 更新系统配置
 */
export async function apiUpdateSystemConfig(
  request: UpdateSystemConfigRequest
): Promise<GetSystemConfigResponse> {
  const response = await apiClient.put<{
    config: BackendSystemConfigResponse;
    updated_at: string;
    updated_by: string;
  }>(`${API_BASE}/settings`, {
    site: request.site,
    user: request.user,
    consultation: request.consultation,
    document: request.document,
    payment: request.payment,
    notification: request.notification,
    security: request.security,
  });
  return {
    config: mapBackendToConfig(response.data.config),
    updatedAt: response.data.updated_at,
    updatedBy: response.data.updated_by,
  };
}

/**
 * 获取系统日志
 */
export async function apiGetSystemLogs(
  params: GetSystemLogsRequest = {}
): Promise<GetSystemLogsResponse> {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', String(params.page));
  if (params.pageSize) queryParams.append('page_size', String(params.pageSize));
  if (params.level) queryParams.append('level', params.level);
  if (params.module) queryParams.append('module', params.module);
  if (params.startDate) queryParams.append('start_date', params.startDate);
  if (params.endDate) queryParams.append('end_date', params.endDate);
  if (params.keyword) queryParams.append('keyword', params.keyword);

  const queryString = queryParams.toString();
  const url = `${API_BASE}/logs${queryString ? `?${queryString}` : ''}`;

  const response = await apiClient.get<{
    items: BackendSystemLogResponse[];
    total: number;
    page: number;
    page_size: number;
  }>(url);

  return {
    items: response.data.items.map(mapBackendToLog),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

/**
 * 获取系统状态
 */
export async function apiGetSystemStatus(): Promise<SystemStatus> {
  const response = await apiClient.get<BackendSystemStatusResponse>(`${API_BASE}/status`);
  const backend = response.data;
  return {
    version: backend.version,
    uptime: backend.uptime,
    environment: backend.environment as 'development' | 'staging' | 'production',
    database: backend.database,
    cache: backend.cache,
    storage: backend.storage,
    memory: backend.memory,
    cpu: backend.cpu,
  };
}

/**
 * 获取备份列表
 */
export async function apiGetBackups(params?: {
  page?: number;
  pageSize?: number;
}): Promise<GetBackupsResponse> {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append('page', String(params.page));
  if (params?.pageSize) queryParams.append('page_size', String(params.pageSize));

  const queryString = queryParams.toString();
  const url = `${API_BASE}/backups${queryString ? `?${queryString}` : ''}`;

  const response = await apiClient.get<{
    items: BackendBackupResponse[];
    total: number;
    page: number;
    page_size: number;
  }>(url);

  return {
    items: response.data.items.map(mapBackendToBackup),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

/**
 * 创建备份
 */
export async function apiCreateBackup(type: 'full' | 'incremental' = 'full'): Promise<BackupInfo> {
  const response = await apiClient.post<BackendBackupResponse>(`${API_BASE}/backups`, { type });
  return mapBackendToBackup(response.data);
}

/**
 * 删除备份
 */
export async function apiDeleteBackup(id: string): Promise<void> {
  await apiClient.delete(`${API_BASE}/backups/${id}`);
}

/**
 * 下载备份
 */
export async function apiDownloadBackup(id: string): Promise<Blob> {
  const response = await apiClient.get(`${API_BASE}/backups/${id}/download`, {
    responseType: 'blob',
  });
  return response.data as Blob;
}
