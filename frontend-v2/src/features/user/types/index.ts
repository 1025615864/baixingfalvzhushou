/**
 * 用户模块类型定义
 *
 * 注意：此类型定义用于用户模块内部使用。
 * 对于认证相关的用户类型，请使用 @/features/auth/types 中的 User 类型。
 *
 * TODO: 后续迭代应统一两套User类型定义，避免不一致。
 */

export type UserRole = 'user' | 'lawyer' | 'admin' | 'super_admin';

/**
 * 用户对象（用户模块内部使用）
 *
 * 与后端 UserResponse 的字段映射：
 * - id: number (后端) -> string (前端)
 * - username: string (后端) -> name: string (前端)
 * - email_verified: boolean (后端) -> isVerified: boolean (前端)
 * - created_at: string (后端) -> createdAt: string (前端)
 */
export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string | null;
  avatar?: string | null;
  role: UserRole;
  isVerified: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface UserProfile extends User {
  bio?: string;
  location?: string;
  company?: string;
  title?: string;
  website?: string;
  socialLinks?: {
    weibo?: string;
    wechat?: string;
    linkedin?: string;
  };
}

export interface UserStats {
  consultationCount: number;
  documentCount: number;
  knowledgeCount: number;
  totalSpent: number;
}

export interface UserSettings {
  emailNotifications: boolean;
  smsNotifications: boolean;
  newsletter: boolean;
  language: 'zh-CN' | 'zh-TW' | 'en';
  theme: 'light' | 'dark' | 'auto';
}

export interface UpdateProfileDTO {
  nickname?: string;
  phone?: string;
  bio?: string;
  location?: string;
  company?: string;
  title?: string;
  website?: string;
}

export interface ChangePasswordDTO {
  currentPassword: string;
  newPassword: string;
}