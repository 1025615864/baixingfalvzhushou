/**
 * Security（安全中心）Query Keys
 * 统一管理 React Query 的缓存键
 */

export const securityKeys = {
  all: ['security'] as const,

  // 2FA 相关
  twoFA: () => [...securityKeys.all, '2fa'] as const,
  twoFAStatus: () => [...securityKeys.twoFA(), 'status'] as const,

  // 设备管理相关
  devices: () => [...securityKeys.all, 'devices'] as const,

  // 登录审计相关
  audit: () => [...securityKeys.all, 'audit'] as const,
  auditLogins: (params?: { page?: number; pageSize?: number; action?: string }) =>
    [...securityKeys.audit(), 'logins', params] as const,

  // 安全等级相关
  level: () => [...securityKeys.all, 'level'] as const,
};