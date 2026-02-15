/**
 * Security（安全中心）模块统一导出
 * 
 * 使用方式:
 * import { SecurityPage, TwoFactorSetup, useSecurity } from '@/features/security';
 */

// ==================== 页面组件 ====================

export { SecurityPage } from './pages/SecurityPage';

// ==================== UI 组件 ====================

export { TwoFactorSetup } from './components/TwoFactorSetup';
export { TwoFactorVerify } from './components/TwoFactorVerify';
export { LoginAuditTable } from './components/LoginAuditTable';
export { DeviceList } from './components/DeviceList';
export { SecurityLevel } from './components/SecurityLevel';
export { PasswordChange } from './components/PasswordChange';

// ==================== Hooks ====================

export {
  // 2FA 相关 Hooks
  useTwoFactorStatus,
  useTwoFactorSetup,
  useTwoFactorVerify,
  useDisableTwoFactor,
  useRegenerateBackupCodes,
  // 登录审计 Hooks
  useLoginAudit,
  // 设备管理 Hooks
  useDeviceList,
  useRevokeDevice,
  // 安全设置 Hooks
  useSecuritySettings,
  useChangePassword,
  useUpdateSecuritySettings,
  // 安全等级 Hooks
  useSecurityLevel,
  // 辅助函数
  checkPasswordStrength,
  formatLoginStatus,
  formatRelativeTime,
  formatDateTime,
} from './hooks/useSecurity';

// ==================== 类型定义 ====================

export type {
  // 2FA 相关类型
  TwoFactorMethod,
  TwoFactorStatus,
  TwoFactorSetupStep,
  EnableTwoFactorRequest,
  EnableTwoFactorResponse,
  VerifyTwoFactorRequest,
  VerifyTwoFactorResponse,
  DisableTwoFactorRequest,
  DisableTwoFactorResponse,
  // 登录审计相关类型
  LoginStatus,
  LoginAuditRecord,
  GetLoginAuditRequest,
  GetLoginAuditResponse,
  // 设备管理相关类型
  DeviceType,
  ActiveDevice,
  GetDevicesResponse,
  RevokeDeviceRequest,
  RevokeDeviceResponse,
  // 安全设置相关类型
  PasswordStrength,
  PasswordStrengthResult,
  SecuritySettings,
  ChangePasswordRequest,
  ChangePasswordResponse,
  UpdateSecuritySettingsRequest,
  UpdateSecuritySettingsResponse,
  // 安全等级相关类型
  SecurityCheckItem,
  SecurityLevelAssessment,
  GetSecurityLevelResponse,
  // 备份码相关类型
  BackupCode,
  RegenerateBackupCodesResponse,
} from './types';

// ==================== API 服务 ====================

export {
  // 2FA 相关 API
  apiGetTwoFactorStatus,
  apiEnableTwoFactor,
  apiVerifyTwoFactor,
  apiDisableTwoFactor,
  apiRegenerateBackupCodes,
  // 登录审计相关 API
  apiGetLoginAudit,
  // 设备管理相关 API
  apiGetDevices,
  apiRevokeDevice,
  // 安全设置相关 API
  apiGetSecuritySettings,
  apiChangePassword,
  apiUpdateSecuritySettings,
  // 安全等级相关 API
  apiGetSecurityLevel,
} from './api';