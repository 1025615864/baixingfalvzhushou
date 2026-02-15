// ============================================
// Auth API - 基于后端实际接口的 API 层
// ============================================

import { api } from '@/shared/lib/api/client';
import type {
  LoginRequest,
  RegisterRequest,
  LoginResponse,
  RegisterResponse,
  User,
} from '@/features/auth/types';

// API 端点 - 与后端路由匹配
const ENDPOINTS = {
  REGISTER: '/user/register',
  LOGIN: '/user/login',
  LOGOUT: '/user/logout',
  PROFILE: '/user/me',          // 后端使用 /user/me
  PASSWORD: '/user/me/password', // 后端使用 /user/me/password
  CSRF_TOKEN: '/user/me/csrf-token', // CSRF Token 端点
  REFRESH: '/user/auth/refresh',  // Token 刷新端点
} as const;

/**
 * 用户注册
 */
export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  // api.post 已经返回了 res.data
  return await api.post<RegisterResponse>(ENDPOINTS.REGISTER, data);
}

/**
 * 用户登录
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  // api.post 已经返回了 res.data
  return await api.post<LoginResponse>(ENDPOINTS.LOGIN, data);
}

/**
 * 用户登出
 */
export async function logout(): Promise<void> {
  await api.post<void>(ENDPOINTS.LOGOUT);
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser(): Promise<User> {
  // api.get 已经返回了 res.data
  return await api.get<User>(ENDPOINTS.PROFILE);
}

/**
 * 更新用户信息
 */
export async function updateProfile(data: Partial<User>): Promise<User> {
  // api.put 已经返回了 res.data
  return await api.put<User>(ENDPOINTS.PROFILE, data);
}