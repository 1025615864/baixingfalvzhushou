/**
 * User（用户管理）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/user 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  User,
  UserStats,
  UpdateProfileDTO,
  ChangePasswordDTO,
} from '../types';


// API 基础路径
const API_BASE = '/user';

// ==================== 后端响应类型定义 ====================

/** 后端用户响应 */
interface BackendUserResponse {
  id: string;
  username: string;
  email: string;
  phone?: string;
  avatar?: string;
  nickname?: string;
  role: 'user' | 'lawyer' | 'admin';
  is_active: boolean;
  email_verified?: boolean;
  phone_verified?: boolean;
  created_at: string;
  updated_at: string;
}

/** 后端登录响应 */
interface BackendLoginResponse {
  user: BackendUserResponse;
  message: string;
}

/** 后端注册响应 */
interface BackendRegisterResponse {
  user: BackendUserResponse;
  message: string;
}

/** 后端用户配额响应 */
interface BackendQuotaResponse {
  consultation: number;
  document_review: number;
  ai_chat: number;
  knowledge: number;
  used_consultation: number;
  used_document_review: number;
  used_ai_chat: number;
  used_knowledge: number;
}

/** 后端配额使用项 */
interface BackendQuotaUsageItem {
  date: string;
  action: string;
  count: number;
}

/** 后端配额使用响应 */
interface BackendQuotaUsageResponse {
  usage: BackendQuotaUsageItem[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端用户统计响应 */
interface BackendUserStatsResponse {
  post_count: number;
  favorite_count: number;
  comment_count: number;
}

/** 后端消息响应 */
interface BackendMessageResponse {
  message: string;
  success: boolean;
}

/** 后端邮箱验证响应 */
interface BackendEmailVerificationResponse {
  message: string;
  success: boolean;
  token?: string;
  verify_url?: string;
}

/** 后端短信发送响应 */
interface BackendSmsSendResponse {
  message: string;
  success: boolean;
  code?: string;
}

/** 后端活跃用户列表项 */
interface BackendActiveTokenItem {
  jti: string;
  device_info?: string;
  ip_address?: string;
  created_at: string;
  rotated_at?: string;
  family_id?: string;
}

/** 后端活跃用户Token响应 */
interface BackendActiveTokensResponse {
  tokens: BackendActiveTokenItem[];
  total: number;
}

/** 后端Token刷新响应 */
interface BackendTokenRefreshResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  rotated: boolean;
  message: string;
}

/** 后端用户列表项 */
interface BackendUserListItem {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

/** 后端用户列表响应 */
interface BackendUserListResponse {
  items: BackendUserListItem[];
  total: number;
  page: number;
  page_size: number;
}

// ==================== 转换函数 ====================

/**
 * 转换后端用户到前端格式
 */
function mapBackendToUser(data: BackendUserResponse): User {
  return {
    id: String(data.id),
    name: data.nickname || data.username,
    email: data.email,
    phone: data.phone,
    avatar: data.avatar,
    role: data.role,
    isVerified: data.email_verified || false,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

// ==================== 认证 API ====================

/**
 * 用户注册
 */
export async function apiRegister(
  username: string,
  email: string,
  password: string,
  agreeTerms: boolean,
  agreePrivacy: boolean,
  agreeAiDisclaimer: boolean
): Promise<{ user: User; message: string }> {
  const response = await apiClient.post<BackendRegisterResponse>(`${API_BASE}/register`, {
    username,
    email,
    password,
    agree_terms: agreeTerms,
    agree_privacy: agreePrivacy,
    agree_ai_disclaimer: agreeAiDisclaimer,
  });

  return {
    user: mapBackendToUser(response.data.user),
    message: response.data.message,
  };
}

/**
 * 用户登录
 */
export async function apiLogin(
  username: string,
  password: string
): Promise<{ user: User; message: string }> {
  const response = await apiClient.post<BackendLoginResponse>(`${API_BASE}/login`, {
    username,
    password,
  });

  return {
    user: mapBackendToUser(response.data.user),
    message: response.data.message,
  };
}

/**
 * 用户登出
 */
export async function apiLogout(): Promise<{ message: string; success: boolean }> {
  const response = await apiClient.post<BackendMessageResponse>(`${API_BASE}/logout`);
  return response.data;
}

// ==================== 用户信息 API ====================

/**
 * 获取当前用户信息
 */
export async function apiGetCurrentUser(): Promise<User> {
  const response = await apiClient.get<BackendUserResponse>(`${API_BASE}/me`);
  return mapBackendToUser(response.data);
}

/**
 * 获取指定用户信息
 */
export async function apiGetUser(userId: string): Promise<User> {
  const response = await apiClient.get<BackendUserResponse>(`${API_BASE}/${userId}`);
  return mapBackendToUser(response.data);
}

/**
 * 更新当前用户信息
 */
export async function apiUpdateCurrentUser(
  data: UpdateProfileDTO
): Promise<User> {
  const response = await apiClient.put<BackendUserResponse>(`${API_BASE}/me`, {
    nickname: data.name,
    avatar: data.bio, // 如果avatar与bio不同，需调整
    phone: data.phone,
  });

  return mapBackendToUser(response.data);
}

// ==================== 配额 API ====================

/**
 * 获取当前用户配额
 */
export async function apiGetUserQuotas(): Promise<{
  consultation: number;
  documentReview: number;
  aiChat: number;
  knowledge: number;
  usedConsultation: number;
  usedDocumentReview: number;
  usedAiChat: number;
  usedKnowledge: number;
}> {
  const response = await apiClient.get<BackendQuotaResponse>(`${API_BASE}/me/quotas`);

  return {
    consultation: response.data.consultation,
    documentReview: response.data.document_review,
    aiChat: response.data.ai_chat,
    knowledge: response.data.knowledge,
    usedConsultation: response.data.used_consultation,
    usedDocumentReview: response.data.used_document_review,
    usedAiChat: response.data.used_ai_chat,
    usedKnowledge: response.data.used_knowledge,
  };
}

/**
 * 获取配额使用记录
 */
export async function apiGetQuotaUsage(
  days: number = 30,
  page: number = 1,
  pageSize: number = 20
): Promise<{
  usage: Array<{ date: string; action: string; count: number }>;
  total: number;
  page: number;
  pageSize: number;
}> {
  const response = await apiClient.get<BackendQuotaUsageResponse>(
    `${API_BASE}/me/quota-usage`,
    {
      params: {
        days,
        page,
        page_size: pageSize,
      },
    }
  );

  return {
    usage: response.data.usage.map(item => ({
      date: item.date,
      action: item.action,
      count: item.count,
    })),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

// ==================== 统计 API ====================

/**
 * 获取用户统计数据
 */
export async function apiGetUserStats(): Promise<UserStats> {
  const response = await apiClient.get<BackendUserStatsResponse>(`${API_BASE}/me/stats`);

  return {
    consultationCount: response.data.post_count || 0,
    documentCount: response.data.favorite_count || 0,
    knowledgeCount: response.data.comment_count || 0,
    totalSpent: 0,
  };
}

// ==================== 安全设置 API ====================

/**
 * 修改密码
 */
export async function apiChangePassword(
  data: ChangePasswordDTO
): Promise<{ message: string; success: boolean }> {
  const response = await apiClient.put<BackendMessageResponse>(
    `${API_BASE}/me/password`,
    {
      old_password: data.currentPassword,
      new_password: data.newPassword,
    }
  );
  return response.data;
}

/**
 * 请求邮箱验证邮件
 */
export async function apiRequestEmailVerification(): Promise<{
  message: string;
  success: boolean;
}> {
  const response = await apiClient.post<BackendEmailVerificationResponse>(
    `${API_BASE}/email-verification/request`
  );
  return {
    message: response.data.message,
    success: response.data.success,
  };
}

/**
 * 验证邮箱
 */
export async function apiVerifyEmail(token: string): Promise<{
  message: string;
  success: boolean;
}> {
  const response = await apiClient.get<BackendMessageResponse>(
    `${API_BASE}/email-verification/verify`,
    {
      params: { token },
    }
  );
  return response.data;
}

/**
 * 发送短信验证码
 */
export async function apiSendSmsCode(
  phone: string,
  scene: string = 'bind_phone'
): Promise<{ message: string; success: boolean }> {
  const response = await apiClient.post<BackendSmsSendResponse>(
    `${API_BASE}/sms/send`,
    {
      phone,
      scene,
    }
  );
  return {
    message: response.data.message,
    success: response.data.success,
  };
}

/**
 * 校验短信验证码并绑定手机
 */
export async function apiVerifySmsCode(
  phone: string,
  code: string,
  scene: string = 'bind_phone'
): Promise<{ message: string; success: boolean }> {
  const response = await apiClient.post<BackendMessageResponse>(
    `${API_BASE}/sms/verify`,
    {
      phone,
      code,
      scene,
    }
  );
  return response.data;
}

/**
 * 请求密码重置
 */
export async function apiRequestPasswordReset(email: string): Promise<{
  message: string;
}> {
  const response = await apiClient.post<{ message: string }>(
    `${API_BASE}/password-reset/request`,
    {
      email,
    }
  );
  return response.data;
}

/**
 * 确认密码重置
 */
export async function apiConfirmPasswordReset(
  token: string,
  newPassword: string
): Promise<{ message: string; success: boolean }> {
  const response = await apiClient.post<BackendMessageResponse>(
    `${API_BASE}/password-reset/confirm`,
    {
      token,
      new_password: newPassword,
    }
  );
  return response.data;
}

// ==================== Token 管理 API ====================

/**
 * 刷新访问令牌
 */
export async function apiRefreshToken(): Promise<{
  accessToken: string;
  refreshToken?: string;
  expiresIn: number;
  rotated: boolean;
  message: string;
}> {
  const response = await apiClient.post<BackendTokenRefreshResponse>(
    `${API_BASE}/auth/refresh`
  );

  return {
    accessToken: response.data.access_token,
    refreshToken: response.data.refresh_token,
    expiresIn: response.data.expires_in,
    rotated: response.data.rotated,
    message: response.data.message,
  };
}

/**
 * 撤销Token
 */
export async function apiRevokeToken(token?: string): Promise<{
  message: string;
  success: boolean;
}> {
  const response = await apiClient.post<BackendMessageResponse>(
    `${API_BASE}/auth/revoke`,
    token ? { token } : undefined
  );
  return response.data;
}

/**
 * 获取活跃Token列表
 */
export async function apiGetActiveTokens(): Promise<{
  tokens: Array<{
    jti: string;
    deviceInfo?: string;
    ipAddress?: string;
    createdAt: string;
    rotatedAt?: string;
    familyId?: string;
  }>;
  total: number;
}> {
  const response = await apiClient.get<BackendActiveTokensResponse>(
    `${API_BASE}/auth/active-tokens`
  );

  return {
    tokens: response.data.tokens.map(t => ({
      jti: t.jti,
      deviceInfo: t.device_info,
      ipAddress: t.ip_address,
      createdAt: t.created_at,
      rotatedAt: t.rotated_at,
      familyId: t.family_id,
    })),
    total: response.data.total,
  };
}

/**
 * 获取CSRF Token
 */
export async function apiGetCsrfToken(): Promise<{
  csrfToken: string;
  expiresInHours: number;
}> {
  const response = await apiClient.get<{
    csrf_token: string;
    expires_in_hours: number;
  }>(`${API_BASE}/me/csrf-token`);

  return {
    csrfToken: response.data.csrf_token,
    expiresInHours: response.data.expires_in_hours,
  };
}

// ==================== 管理员 API ====================

/**
 * 获取用户列表（管理员）
 */
export async function apiGetUserList(
  page: number = 1,
  pageSize: number = 20,
  keyword?: string
): Promise<{
  items: User[];
  total: number;
  page: number;
  pageSize: number;
}> {
  const response = await apiClient.get<BackendUserListResponse>(
    `${API_BASE}/admin/list`,
    {
      params: {
        page,
        page_size: pageSize,
        keyword,
      },
    }
  );

  return {
    items: response.data.items.map(item => ({
      id: String(item.id),
      name: item.username,
      email: item.email,
      role: item.role as 'user' | 'lawyer' | 'admin',
      isVerified: false,
      createdAt: item.created_at,
      updatedAt: '',
    })),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

/**
 * 切换用户激活状态（管理员）
 */
export async function apiToggleUserActive(
  userId: string
): Promise<User> {
  const response = await apiClient.put<BackendUserResponse>(
    `${API_BASE}/admin/${userId}/toggle-active`
  );
  return mapBackendToUser(response.data);
}

/**
 * 修改用户角色（管理员）
 */
export async function apiUpdateUserRole(
  userId: string,
  role: 'user' | 'lawyer' | 'admin'
): Promise<User> {
  const response = await apiClient.put<BackendUserResponse>(
    `${API_BASE}/admin/${userId}/role`,
    undefined,
    {
      params: { role },
    }
  );
  return mapBackendToUser(response.data);
}

/**
 * 获取用户统计数据（管理员）
 */
export async function apiGetUserStatsAdmin(userId: string): Promise<UserStats> {
  const response = await apiClient.get<BackendUserStatsResponse>(
    `${API_BASE}/${userId}/stats`
  );

  return {
    consultationCount: response.data.post_count || 0,
    documentCount: response.data.favorite_count || 0,
    knowledgeCount: response.data.comment_count || 0,
    totalSpent: 0,
  };
}

// ==================== 统一导出 ====================

/**
 * User API 统一导出对象
 */
export const userApi = {
  // 认证
  register: apiRegister,
  login: apiLogin,
  logout: apiLogout,

  // 用户信息
  getCurrentUser: apiGetCurrentUser,
  getUser: apiGetUser,
  updateCurrentUser: apiUpdateCurrentUser,

  // 配额
  getUserQuotas: apiGetUserQuotas,
  getQuotaUsage: apiGetQuotaUsage,

  // 统计
  getUserStats: apiGetUserStats,

  // 安全设置
  changePassword: apiChangePassword,
  requestEmailVerification: apiRequestEmailVerification,
  verifyEmail: apiVerifyEmail,
  sendSmsCode: apiSendSmsCode,
  verifySmsCode: apiVerifySmsCode,
  requestPasswordReset: apiRequestPasswordReset,
  confirmPasswordReset: apiConfirmPasswordReset,

  // Token管理
  refreshToken: apiRefreshToken,
  revokeToken: apiRevokeToken,
  getActiveTokens: apiGetActiveTokens,
  getCsrfToken: apiGetCsrfToken,

  // 管理员
  getUserList: apiGetUserList,
  toggleUserActive: apiToggleUserActive,
  updateUserRole: apiUpdateUserRole,
  getUserStatsAdmin: apiGetUserStatsAdmin,
} as const;

export default userApi;