/**
 * 管理后台路由守卫组件
 * 检查用户角色是否有权限访问当前面板
 */

import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/features/auth/store/authStore';
import type { UserRole } from '@/features/auth/types';

const PUBLIC_ROLES: UserRole[] = ['admin', 'super_admin'];

const ROLE_PATH_MAP: Record<string, UserRole[]> = {
  '/admin/super': ['super_admin'],
  '/admin/general': ['admin', 'super_admin'],
  '/admin/forum': ['forum_admin', 'moderator', 'admin', 'super_admin'],
  '/admin/news': ['news_admin', 'admin', 'super_admin'],
  '/admin/ai': ['ai_admin', 'admin', 'super_admin'],
  '/admin/lawyer': ['lawyer_admin', 'admin', 'super_admin'],
  '/admin/cs': ['cs_agent', 'admin', 'super_admin'],
};

export interface AdminAuthGuardProps {
  children: React.ReactNode;
}

export function AdminAuthGuard({ children }: AdminAuthGuardProps): JSX.Element {
  const { user } = useAuthStore();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  const role = (user.role ?? 'user') as UserRole;

  if (!PUBLIC_ROLES.includes(role) && !Object.keys(ROLE_PATH_MAP).some(path =>
    ROLE_PATH_MAP[path].includes(role)
  )) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="text-center p-8 bg-white rounded-xl shadow-sm border border-slate-200 max-w-md">
          <div className="text-5xl mb-4">🚫</div>
          <h2 className="text-xl font-semibold text-slate-700 mb-2">无访问权限</h2>
          <p className="text-slate-400 mb-6">您没有权限访问管理后台，请联系超级管理员。</p>
          <a href="/" className="text-primary-600 hover:text-primary-700 font-medium">
            返回首页
          </a>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export function checkAccess(pathname: string, role: UserRole | undefined): boolean {
  if (!role) return false;
  if (role === 'super_admin') return true;

  const allowedRoles = ROLE_PATH_MAP[pathname];
  if (!allowedRoles) return role === 'admin';

  return allowedRoles.includes(role);
}