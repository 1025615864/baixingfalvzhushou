/**
 * Security（安全中心）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/user/security 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  TwoFactorStatus,
  EnableTwoFactorResponse,
  VerifyTwoFactorRequest,
  DisableTwoFactorRequest,
  LoginAuditRecord,
  GetLoginAuditRequest,
  GetLoginAuditResponse,
  ActiveDevice,
  GetDevicesResponse,
  RevokeDeviceRequest,
  ChangePasswordRequest,
  ChangePasswordResponse,
  PasswordStrengthResponse,
  SecurityLevelAssessment,
  GetSecurityLevelResponse,
  RegenerateBackupCodesResponse,
  TwoFAVerifyRequest,
  BackupCodesRegenerateRequest,
} from '../types';


// API 基础路径
const API_BASE = '/user/security';

// ==================== 后端响应类型定义 ====================

/** 后端 2FA 状态响应 */
interface BackendTwoFAStatusResponse {
  is_enabled: boolean;
  is_setup: boolean;
}

/** 后端 2FA 设置响应 */
interface BackendTwoFASetupResponse {
  secret: string;
  uri: string;
  backup_codes: string[];
  qr_code_url?: string | null;
}

/** 后端设备信息 */
interface BackendDeviceInfo {
  device_id: string;
  device_name: string | null;
  device_type: string;
  user_agent: string | null;
  ip_address: string | null;
  location: string | null;
  first_login_at: string | null;
  last_login_at: string | null;
  is_current: boolean;
  is_revoked: boolean;
}

/** 后端设备列表响应 */
interface BackendDeviceListResponse {
  devices: BackendDeviceInfo[];
  total: number;
  current_device_id: string | null;
}

/** 后端登录记录 */
interface BackendLoginRecord {
  id: number;
  action: string;
  success: boolean;
  ip_address: string | null;
  user_agent: string | null;
  device_id: string | null;
  location: string | null;
  failure_reason: string | null;
  created_at: string;
}

/** 后端登录历史响应 */
interface BackendLoginHistoryResponse {
  records: BackendLoginRecord[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端消息响应 */
interface BackendMessageResponse {
  message: string;
  success: boolean;
}

/** 后端密码强度响应 */
interface BackendPasswordStrengthResponse {
  score: number;
  level: string;
  feedback: string[];
  is_acceptable: boolean;
}

/** 后端安全等级响应 */
interface BackendSecurityLevelResponse {
  score: number;
  level: string;
  factors: Record<string, unknown>;
  recommendations: string[];
}

/** 后端备用码重新生成响应 */
interface BackendBackupCodesRegenerateResponse {
  backup_codes: string[];
}

// ==================== 转换函数 ====================

/**
 * 转换后端 2FA 状态到前端格式
 */
function mapBackendToTwoFactorStatus(data: BackendTwoFAStatusResponse): TwoFactorStatus {
  return {
    enabled: data.is_enabled,
    method: data.is_enabled ? 'totp' : null,
    verifiedAt: null, // 后端不提供此字段，使用 null
    backupCodesRemaining: 0, // 后端不提供此字段，使用 0
  };
}

/**
 * 转换后端设备信息到前端格式
 */
function mapBackendToDeviceInfo(data: BackendDeviceInfo): ActiveDevice {
  return {
    id: data.device_id,
    deviceType: data.device_type as ActiveDevice['deviceType'],
    deviceName: data.device_name || '未知设备',
    browser: data.user_agent || '未知浏览器',
    os: '未知系统', // 后端不提供此字段，使用默认值
    ipAddress: data.ip_address || '',
    location: data.location,
    lastActiveAt: data.last_login_at || data.first_login_at || new Date().toISOString(),
    createdAt: data.first_login_at || new Date().toISOString(),
    isCurrentDevice: data.is_current,
  };
}

/**
 * 转换后端登录记录到前端格式
 */
function mapBackendToLoginRecord(data: BackendLoginRecord): LoginAuditRecord {
  const statusMap: Record<string, LoginAuditRecord['status']> = {
    'login': 'success',
    'failed': 'failed',
    'logout': 'success',
    '2fa_verify': 'success',
    'password_change': 'success',
  };

  return {
    id: data.id,
    userId: 0, // 后端不提供，使用默认值
    ipAddress: data.ip_address || '',
    userAgent: data.user_agent || '',
    deviceType: 'unknown',
    browser: '未知浏览器',
    os: '未知系统',
    location: data.location,
    status: statusMap[data.action] || (data.success ? 'success' : 'failed'),
    failureReason: data.failure_reason,
    createdAt: data.created_at,
  };
}

// ==================== 2FA 相关 API ====================

/**
 * 获取 2FA 状态
 */
export async function apiGetTwoFactorStatus(): Promise<TwoFactorStatus> {
  const response = await apiClient.get<BackendTwoFAStatusResponse>(`${API_BASE}/2fa/status`);
  return mapBackendToTwoFactorStatus(response.data);
}

/**
 * 初始化 2FA 设置
 */
export async function apiEnableTwoFactor(): Promise<EnableTwoFactorResponse> {
  const response = await apiClient.post<BackendTwoFASetupResponse>(`${API_BASE}/2fa/setup/init`);
  
  return {
    success: true,
    secret: response.data.secret,
    qrCodeUrl: response.data.qr_code_url || response.data.uri,
    backupCodes: response.data.backup_codes,
  };
}

/**
 * 验证并启用 2FA
 */
export async function apiVerifyTwoFactor(request: VerifyTwoFactorRequest): Promise<BackendMessageResponse> {
  const response = await apiClient.post<BackendMessageResponse>(`${API_BASE}/2fa/setup/verify`, {
    code: request.code,
  });
  return response.data;
}

/**
 * 禁用 2FA
 */
export async function apiDisableTwoFactor(request: DisableTwoFactorRequest): Promise<BackendMessageResponse> {
  const response = await apiClient.post<BackendMessageResponse>(`${API_BASE}/2fa/disable`, {
    code: request.code,
  });
  return response.data;
}

/**
 * 验证 2FA 码（用于登录验证）
 */
export async function apiVerifyTwoFactorCode(data: TwoFAVerifyRequest): Promise<BackendMessageResponse> {
  const response = await apiClient.post<BackendMessageResponse>(`${API_BASE}/2fa/verify`, {
    code: data.code,
  });
  return response.data;
}

/**
 * 重新生成备用码
 */
export async function apiRegenerateBackupCodes(data: BackupCodesRegenerateRequest): Promise<RegenerateBackupCodesResponse> {
  const response = await apiClient.post<BackendBackupCodesRegenerateResponse>(
    `${API_BASE}/2fa/backup-codes/regenerate`,
    {
      code: data.code,
    }
  );
  
  return {
    success: true,
    backupCodes: response.data.backup_codes,
  };
}

// ==================== 设备管理相关 API ====================

/**
 * 获取活跃设备列表
 */
export async function apiGetDevices(): Promise<GetDevicesResponse> {
  const response = await apiClient.get<BackendDeviceListResponse>(`${API_BASE}/devices`);
  
  return {
    devices: response.data.devices.map(mapBackendToDeviceInfo),
    total: response.data.total,
  };
}

/**
 * 踢出指定设备
 */
export async function apiRevokeDevice(request: RevokeDeviceRequest): Promise<BackendMessageResponse> {
  const response = await apiClient.delete<BackendMessageResponse>(
    `${API_BASE}/devices/${request.deviceId}`
  );
  return response.data;
}

/**
 * 踢出其他所有设备
 */
export async function apiRevokeOtherDevices(): Promise<BackendMessageResponse> {
  const response = await apiClient.delete<BackendMessageResponse>(`${API_BASE}/devices/others`);
  return response.data;
}

// ==================== 登录审计相关 API ====================

/**
 * 获取登录审计日志
 */
export async function apiGetLoginAudit(params: GetLoginAuditRequest = {}): Promise<GetLoginAuditResponse> {
  const response = await apiClient.get<BackendLoginHistoryResponse>(`${API_BASE}/audit/logins`, {
    params: {
      page: params.page || 1,
      page_size: params.pageSize || 20,
      action: params.status, // 使用 status 作为 action 筛选
      start_date: params.startDate,
      end_date: params.endDate,
    },
  });
  
  return {
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
    records: response.data.records.map(mapBackendToLoginRecord),
  };
}

// ==================== 密码安全相关 API ====================

/**
 * 修改密码（安全中心版本）
 * 注意: 后端端点是 PUT /user/me/password
 */
export async function apiChangePassword(request: ChangePasswordRequest): Promise<ChangePasswordResponse> {
  const response = await apiClient.put<BackendMessageResponse>('/user/me/password', {
    old_password: request.currentPassword,
    new_password: request.newPassword,
  });

  return {
    success: response.data.success,
    message: response.data.message,
    passwordStrength: {
      strength: 'good',
      score: 70,
      requirements: {
        minLength: true,
        hasUppercase: true,
        hasLowercase: true,
        hasNumbers: true,
        hasSpecialChars: true,
      },
      suggestions: [],
    },
  };
}

/**
 * 检查密码强度
 */
export async function apiCheckPasswordStrength(data: { password: string }): Promise<PasswordStrengthResponse> {
  const response = await apiClient.post<BackendPasswordStrengthResponse>(`${API_BASE}/password/check-strength`, {
    password: data.password,
  });
  
  const strengthMap: Record<string, PasswordStrengthResponse['strength']> = {
    'weak': 'weak',
    'medium': 'fair',
    'strong': 'strong',
  };
  
  return {
    strength: strengthMap[response.data.level] || 'weak',
    score: response.data.score,
    requirements: {
      minLength: response.data.score >= 20,
      hasUppercase: response.data.score >= 35,
      hasLowercase: response.data.score >= 50,
      hasNumbers: response.data.score >= 65,
      hasSpecialChars: response.data.score >= 80,
    },
    suggestions: response.data.feedback,
  };
}

// ==================== 安全等级相关 API ====================

/**
 * 获取安全等级评估
 */
export async function apiGetSecurityLevel(): Promise<GetSecurityLevelResponse> {
  const response = await apiClient.get<BackendSecurityLevelResponse>(`${API_BASE}/level`);
  
  const levelMap: Record<string, SecurityLevelAssessment['level']> = {
    'low': 'low',
    'medium': 'medium',
    'high': 'high',
  };
  
  return {
    assessment: {
      level: levelMap[response.data.level] || 'low',
      score: response.data.score,
      checks: [], // 后端不提供详细检查项，使用空数组
      lastAssessmentAt: new Date().toISOString(),
    },
  };
}

// ==================== 兼容性导出（旧 API 名称映射）=====================

/**
 * @deprecated 使用 apiGetDevices 替代
 */
export function apiGetSecuritySettings(): Promise<never> {
  return Promise.reject(new Error('apiGetSecuritySettings 已弃用，请使用新的 API'));
}

/**
 * @deprecated 使用 apiChangePassword 替代
 */
export function apiUpdateSecuritySettings(): Promise<never> {
  return Promise.reject(new Error('apiUpdateSecuritySettings 已弃用，请使用新的 API'));
}