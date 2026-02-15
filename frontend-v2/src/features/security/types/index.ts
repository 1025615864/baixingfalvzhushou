/**
 * Security（安全中心）类型定义
 * 与后端 Schema 保持一致
 */

// ==================== 双因素认证（2FA）相关类型 ====================

/** 2FA 认证方式 */
export type TwoFactorMethod = 'totp' | 'sms' | 'email';

/** 2FA 状态 */
export interface TwoFactorStatus {
  enabled: boolean;
  method: TwoFactorMethod | null;
  verifiedAt: string | null;
  backupCodesRemaining: number;
}

/** 2FA 设置请求（初始化） */
export interface EnableTwoFactorRequest {
  // 初始化设置不需要参数，由后端生成
}

/** 2FA 设置响应 */
export interface EnableTwoFactorResponse {
  success: boolean;
  secret: string;
  qrCodeUrl: string;
  backupCodes: string[];
}

/** 2FA 验证请求 */
export interface VerifyTwoFactorRequest {
  code: string;
  method?: TwoFactorMethod;
}

/** 2FA 验证响应 */
export interface VerifyTwoFactorResponse {
  success: boolean;
  message: string;
}

/** 2FA 禁用请求 */
export interface DisableTwoFactorRequest {
  code: string;
  password?: string;
}

/** 2FA 禁用响应 */
export interface DisableTwoFactorResponse {
  success: boolean;
  message: string;
}

/** 2FA 验证请求（用于登录验证） */
export interface TwoFAVerifyRequest {
  code: string;
}

/** 2FA 禁用请求（用于安全中心） */
export interface TwoFADisableRequest {
  code: string;
}

/** 备用码重新生成请求 */
export interface BackupCodesRegenerateRequest {
  code: string;
}

/** 2FA 设置步骤 */
export type TwoFactorSetupStep = 'select-method' | 'show-qr' | 'verify-code' | 'backup-codes' | 'complete';

// ==================== 登录审计相关类型 ====================

/** 登录状态 */
export type LoginStatus = 'success' | 'failed' | 'blocked' | 'expired';

/** 登录审计记录 */
export interface LoginAuditRecord {
  id: number;
  userId: number;
  ipAddress: string;
  userAgent: string;
  deviceType: string;
  browser: string;
  os: string;
  location: string | null;
  status: LoginStatus;
  failureReason: string | null;
  createdAt: string;
}

/** 登录审计查询请求 */
export interface GetLoginAuditRequest {
  startDate?: string;
  endDate?: string;
  status?: LoginStatus;
  page?: number;
  pageSize?: number;
  action?: string; // 用于后端筛选：login, logout, 2fa_verify, failed, password_change
}

/** 登录审计查询响应 */
export interface GetLoginAuditResponse {
  total: number;
  page: number;
  pageSize: number;
  records: LoginAuditRecord[];
}

// ==================== 设备管理相关类型 ====================

/** 设备类型 */
export type DeviceType = 'desktop' | 'mobile' | 'tablet' | 'unknown';

/** 活跃设备 */
export interface ActiveDevice {
  id: string;
  deviceType: DeviceType;
  deviceName: string;
  browser: string;
  os: string;
  ipAddress: string;
  location: string | null;
  lastActiveAt: string;
  createdAt: string;
  isCurrentDevice: boolean;
}

/** 获取设备列表响应 */
export interface GetDevicesResponse {
  devices: ActiveDevice[];
  total: number;
  currentDeviceId?: string | null;
}

/** 踢出设备请求 */
export interface RevokeDeviceRequest {
  deviceId: string;
  reason?: string;
}

/** 踢出设备响应 */
export interface RevokeDeviceResponse {
  success: boolean;
  message: string;
}

// ==================== 密码安全相关类型 ====================

/** 密码强度等级 */
export type PasswordStrength = 'weak' | 'fair' | 'good' | 'strong';

/** 密码强度评估结果 */
export interface PasswordStrengthResult {
  strength: PasswordStrength;
  score: number; // 0-100
  requirements: {
    minLength: boolean;
    hasUppercase: boolean;
    hasLowercase: boolean;
    hasNumbers: boolean;
    hasSpecialChars: boolean;
  };
  suggestions: string[];
}

/** 密码强度检查请求 */
export interface PasswordStrengthRequest {
  password: string;
}

/** 密码强度检查响应 */
export interface PasswordStrengthResponse {
  strength: PasswordStrength;
  score: number;
  requirements: {
    minLength: boolean;
    hasUppercase: boolean;
    hasLowercase: boolean;
    hasNumbers: boolean;
    hasSpecialChars: boolean;
  };
  suggestions: string[];
}

/** 修改密码请求 */
export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

/** 修改密码响应 */
export interface ChangePasswordResponse {
  success: boolean;
  message: string;
  passwordStrength: PasswordStrengthResult;
}

// ==================== 安全设置相关类型（已弃用，保留兼容性）====================

/** 安全设置 */
export interface SecuritySettings {
  passwordLastChanged: string;
  twoFactorEnabled: boolean;
  loginNotifications: boolean;
  suspiciousLoginAlerts: boolean;
  trustedDevicesOnly: boolean;
  sessionTimeout: number; // 分钟
}

/** 更新安全设置请求 */
export interface UpdateSecuritySettingsRequest {
  loginNotifications?: boolean;
  suspiciousLoginAlerts?: boolean;
  trustedDevicesOnly?: boolean;
  sessionTimeout?: number;
}

/** 更新安全设置响应 */
export interface UpdateSecuritySettingsResponse {
  success: boolean;
  settings: SecuritySettings;
}

// ==================== 安全等级相关类型 ====================

/** 安全检查项 */
export interface SecurityCheckItem {
  id: string;
  name: string;
  description: string;
  passed: boolean;
  severity: 'low' | 'medium' | 'high';
  recommendation?: string;
}

/** 安全等级评估 */
export interface SecurityLevelAssessment {
  level: 'low' | 'medium' | 'high';
  score: number; // 0-100
  checks: SecurityCheckItem[];
  lastAssessmentAt: string;
}

/** 获取安全等级响应 */
export interface GetSecurityLevelResponse {
  assessment: SecurityLevelAssessment;
}

// ==================== 备用码相关类型 ====================

/** 备用码 */
export interface BackupCode {
  code: string;
  used: boolean;
  usedAt: string | null;
}

/** 重新生成备用码响应 */
export interface RegenerateBackupCodesResponse {
  success: boolean;
  backupCodes: string[];
}

// ==================== 后端响应类型（用于 API 层）====================

/** 后端消息响应 */
export interface BackendMessageResponse {
  message: string;
  success: boolean;
}

/** 2FA 设置响应（后端原始格式） */
export interface TwoFASetupResponse {
  secret: string;
  uri: string;
  backupCodes: string[];
  qrCodeUrl?: string | null;
}