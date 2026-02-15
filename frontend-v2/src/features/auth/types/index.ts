// ============================================
// Auth Types - 与后端接口完全匹配
// ============================================

/** 用户角色 */
export type UserRole = 'user' | 'lawyer' | 'admin' | 'super_admin';

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

/** 注册请求 - 与后端 UserCreate 模式完全匹配 */
export interface RegisterRequest {
  username: string;
  password: string;
  email: string;
  nickname?: string;  // 可选，如果不提供，后端会默认使用 username
  agree_terms: boolean;
  agree_privacy: boolean;
  agree_ai_disclaimer: boolean;
}

/** 登录响应 - 后端直接返回 {user, token?, message} */
export interface LoginResponse {
  user: User;
  token?: string;
  message?: string;
}

/** 注册响应 - 后端直接返回 {user, message} */
export interface RegisterResponse {
  user: User;
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