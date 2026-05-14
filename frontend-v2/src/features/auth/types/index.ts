// ============================================
// Auth Types - 与后端接口完全匹配
// ============================================

/** 用户角色 */
export type UserRole = 'user' | 'lawyer' | 'moderator' | 'forum_admin' | 'news_admin' | 'ai_admin' | 'lawyer_admin' | 'cs_agent' | 'admin' | 'super_admin';

export const ROLE_LABELS: Record<UserRole, string> = {
  user: '普通用户',
  lawyer: '律师',
  moderator: '审核员',
  forum_admin: '论坛服务管理员',
  news_admin: '新闻服务管理员',
  ai_admin: 'AI 服务管理员',
  lawyer_admin: '律师服务管理员',
  cs_agent: '客服',
  admin: '管理员',
  super_admin: '超级管理员',
};

export interface AccessibleDashboard {
  key: string;
  path: string;
  label: string;
  icon: string;
  description: string;
}

export interface DashboardsResponse {
  role: UserRole;
  role_label: string;
  panels: AccessibleDashboard[];
}

/** 用户对象 - 与后端返回格式一致 */
export interface User {
  id: number;
  username: string;
  email: string;
  nickname: string | null;
  avatar: string | null;
  phone: string | null;
  email_verified: boolean;
  email_verified_at: string | null;
  phone_verified: boolean;
  phone_verified_at: string | null;
  role: UserRole;
  is_active: boolean;
  vip_expires_at: string | null;
  created_at: string;
}

/** 认证状态 */
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

/** 登录请求 - 后端使用 username 字段，可以是用户名或邮箱 */
export interface LoginRequest {
  username: string;  // 后端支持用户名或邮箱登录
  password: string;
}

/** 注册请求 - 发送到后端的数据（不含协议同意字段） */
export interface RegisterRequest {
  username: string;
  password: string;
  email: string;
  nickname?: string;
}

/** 注册请求（含协议同意，仅前端验证用） */
export interface RegisterFormData extends RegisterRequest {
  agree_terms: boolean;
  agree_privacy: boolean;
  agree_ai_disclaimer: boolean;
}

/** JWT Token 信息 */
export interface Token {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

/** 登录响应 - 后端返回 {user, token: Token, message} */
export interface LoginResponse {
  user: User;
  token?: Token;
  message?: string;
}

/** 注册响应 - 后端返回 {user, token, message} */
export interface RegisterResponse {
  user: User;
  token?: Token;
  message?: string;
}

/** 更新用户信息请求 */
export interface UpdateProfileRequest {
  nickname?: string;
  avatar?: string;
  phone?: string;
}

/** 修改密码请求 */
export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}