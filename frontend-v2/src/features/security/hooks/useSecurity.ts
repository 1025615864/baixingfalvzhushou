/**
 * Security（安全中心）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  TwoFactorStatus,
  EnableTwoFactorResponse,
  VerifyTwoFactorRequest,
  DisableTwoFactorRequest,
  LoginAuditRecord,
  GetLoginAuditRequest,
  ActiveDevice,
  RevokeDeviceRequest,
  ChangePasswordRequest,
  ChangePasswordResponse,
  SecurityLevelAssessment,
  RegenerateBackupCodesResponse,
  BackupCodesRegenerateRequest,
  TwoFAVerifyRequest,
  BackendMessageResponse,
} from '../types';
import {
  apiGetTwoFactorStatus,
  apiEnableTwoFactor,
  apiVerifyTwoFactor,
  apiDisableTwoFactor,
  apiRegenerateBackupCodes,
  apiGetLoginAudit,
  apiGetDevices,
  apiRevokeDevice,
  apiRevokeOtherDevices,
  apiChangePassword,
  apiGetSecurityLevel,
  apiVerifyTwoFactorCode,
  apiCheckPasswordStrength,
} from '../api';
import { securityKeys } from '../api/queryKeys';

// ==================== 2FA Hooks ====================

/**
 * 获取 2FA 状态 Hook
 */
export function useTwoFactorStatus() {
  return useQuery<TwoFactorStatus>({
    queryKey: securityKeys.twoFAStatus(),
    queryFn: apiGetTwoFactorStatus,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 初始化 2FA 设置 Hook
 */
export function useTwoFactorSetup() {
  const queryClient = useQueryClient();

  return useMutation<EnableTwoFactorResponse, Error, void>({
    mutationFn: apiEnableTwoFactor,
    onSuccess: () => {
      // 启用后刷新 2FA 状态
      void queryClient.invalidateQueries({ queryKey: securityKeys.twoFAStatus() });
    },
  });
}

/**
 * 验证并启用 2FA Hook
 */
export function useTwoFactorVerify() {
  const queryClient = useQueryClient();

  return useMutation<BackendMessageResponse, Error, VerifyTwoFactorRequest>({
    mutationFn: apiVerifyTwoFactor,
    onSuccess: () => {
      // 验证成功后刷新 2FA 状态
      void queryClient.invalidateQueries({ queryKey: securityKeys.twoFAStatus() });
      // 刷新安全等级
      void queryClient.invalidateQueries({ queryKey: securityKeys.level() });
    },
  });
}

/**
 * 禁用 2FA Hook
 */
export function useDisableTwoFactor() {
  const queryClient = useQueryClient();

  return useMutation<BackendMessageResponse, Error, DisableTwoFactorRequest>({
    mutationFn: apiDisableTwoFactor,
    onSuccess: () => {
      // 禁用后刷新 2FA 状态
      void queryClient.invalidateQueries({ queryKey: securityKeys.twoFAStatus() });
      // 刷新安全等级
      void queryClient.invalidateQueries({ queryKey: securityKeys.level() });
    },
  });
}

/**
 * 验证 2FA 码 Hook（用于登录验证）
 */
export function useVerifyTwoFactorCode() {
  return useMutation<BackendMessageResponse, Error, TwoFAVerifyRequest>({
    mutationFn: apiVerifyTwoFactorCode,
  });
}

/**
 * 重新生成备用码 Hook
 */
export function useRegenerateBackupCodes() {
  return useMutation<RegenerateBackupCodesResponse, Error, BackupCodesRegenerateRequest>({
    mutationFn: apiRegenerateBackupCodes,
  });
}

// ==================== 登录审计 Hooks ====================

/**
 * 获取登录审计日志 Hook
 */
export function useLoginAudit(params: GetLoginAuditRequest = {}) {
  return useQuery<{ records: LoginAuditRecord[]; total: number; page: number; pageSize: number }>({
    queryKey: securityKeys.auditLogins(params),
    queryFn: async () => {
      const response = await apiGetLoginAudit(params);
      return {
        records: response.records,
        total: response.total,
        page: response.page,
        pageSize: response.pageSize,
      };
    },
    staleTime: 30 * 1000, // 30秒缓存
  });
}

// ==================== 设备管理 Hooks ====================

/**
 * 获取活跃设备列表 Hook
 */
export function useDeviceList() {
  return useQuery<ActiveDevice[]>({
    queryKey: securityKeys.devices(),
    queryFn: async () => {
      const response = await apiGetDevices();
      return response.devices;
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 踢出指定设备 Hook
 */
export function useRevokeDevice() {
  const queryClient = useQueryClient();

  return useMutation<BackendMessageResponse, Error, RevokeDeviceRequest>({
    mutationFn: apiRevokeDevice,
    onSuccess: () => {
      // 踢出成功后刷新设备列表
      void queryClient.invalidateQueries({ queryKey: securityKeys.devices() });
    },
  });
}

/**
 * 踢出其他所有设备 Hook
 */
export function useRevokeOtherDevices() {
  const queryClient = useQueryClient();

  return useMutation<BackendMessageResponse, Error, void>({
    mutationFn: apiRevokeOtherDevices,
    onSuccess: () => {
      // 踢出成功后刷新设备列表
      void queryClient.invalidateQueries({ queryKey: securityKeys.devices() });
    },
  });
}

// ==================== 密码安全 Hooks ====================

/**
 * 修改密码 Hook
 */
export function useChangePassword() {
  const queryClient = useQueryClient();

  return useMutation<ChangePasswordResponse, Error, ChangePasswordRequest>({
    mutationFn: apiChangePassword,
    onSuccess: () => {
      // 修改密码后刷新安全等级
      void queryClient.invalidateQueries({ queryKey: securityKeys.level() });
    },
  });
}

/**
 * 检查密码强度 Hook
 */
export function useCheckPasswordStrength() {
  return useMutation<
    { strength: 'weak' | 'fair' | 'good' | 'strong'; score: number; requirements: Record<string, boolean>; suggestions: string[] },
    Error,
    { password: string }
  >({
    mutationFn: apiCheckPasswordStrength,
  });
}

// ==================== 安全等级 Hooks ====================

/**
 * 获取安全等级评估 Hook
 */
export function useSecurityLevel() {
  return useQuery<SecurityLevelAssessment>({
    queryKey: securityKeys.level(),
    queryFn: async () => {
      const response = await apiGetSecurityLevel();
      return response.assessment;
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== 辅助函数 ====================

/**
 * 密码强度检测函数（本地计算）
 */
export function checkPasswordStrength(password: string): {
  strength: 'weak' | 'fair' | 'good' | 'strong';
  score: number;
  requirements: {
    minLength: boolean;
    hasUppercase: boolean;
    hasLowercase: boolean;
    hasNumbers: boolean;
    hasSpecialChars: boolean;
  };
  suggestions: string[];
} {
  const requirements = {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumbers: /\d/.test(password),
    hasSpecialChars: /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password),
  };

  let score = 0;
  const suggestions: string[] = [];

  if (requirements.minLength) {
    score += 20;
  } else {
    suggestions.push('密码长度至少需要8个字符');
  }

  if (requirements.hasUppercase) {
    score += 20;
  } else {
    suggestions.push('建议包含大写字母');
  }

  if (requirements.hasLowercase) {
    score += 20;
  } else {
    suggestions.push('建议包含小写字母');
  }

  if (requirements.hasNumbers) {
    score += 20;
  } else {
    suggestions.push('建议包含数字');
  }

  if (requirements.hasSpecialChars) {
    score += 20;
  } else {
    suggestions.push('建议包含特殊字符');
  }

  let strength: 'weak' | 'fair' | 'good' | 'strong' = 'weak';
  if (score >= 80) {
    strength = 'strong';
  } else if (score >= 60) {
    strength = 'good';
  } else if (score >= 40) {
    strength = 'fair';
  }

  return {
    strength,
    score,
    requirements,
    suggestions,
  };
}

/**
 * 格式化设备类型
 */
export function formatDeviceType(deviceType: string): string {
  const typeMap: Record<string, string> = {
    desktop: '桌面端',
    mobile: '移动端',
    tablet: '平板',
    unknown: '未知设备',
  };
  return typeMap[deviceType] || '未知设备';
}

/**
 * 格式化登录状态
 */
export function formatLoginStatus(status: string): { text: string; color: string } {
  const statusMap: Record<string, { text: string; color: string }> = {
    success: { text: '成功', color: 'text-green-600' },
    failed: { text: '失败', color: 'text-red-600' },
    blocked: { text: '被阻止', color: 'text-orange-600' },
    expired: { text: '已过期', color: 'text-gray-600' },
  };
  return statusMap[status] || { text: status, color: 'text-gray-600' };
}

/**
 * 格式化日期时间
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 30) return `${days}天前`;
  
  return formatDateTime(dateString);
}

// ==================== 兼容性导出（已弃用）====================

/**
 * @deprecated 使用 useTwoFactorSetup 替代
 */
export function useTwoFactorEnable() {
  return useTwoFactorSetup();
}

/**
 * @deprecated 使用 useSecurityLevel 替代
 */
export function useSecuritySettings() {
  return useSecurityLevel();
}

/**
 * @deprecated 此功能已移除
 */
export function useUpdateSecuritySettings() {
  throw new Error('useUpdateSecuritySettings 已弃用');
}