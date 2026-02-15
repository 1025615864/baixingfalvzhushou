/**
 * Settings（系统设置）类型定义
 */

// ==================== 系统配置类型 ====================

/**
 * 站点配置
 */
export interface SiteConfig {
  siteName: string;
  siteDescription: string;
  siteLogo: string | null;
  siteFavicon: string | null;
  contactEmail: string;
  contactPhone: string;
  icp: string;
  copyright: string;
}

/**
 * 用户相关配置
 */
export interface UserConfig {
  defaultUserRole: 'user' | 'lawyer';
  requireEmailVerification: boolean;
  requirePhoneVerification: boolean;
  allowRegistration: boolean;
  passwordMinLength: number;
  passwordRequireUppercase: boolean;
  passwordRequireNumber: boolean;
  passwordRequireSpecial: boolean;
  sessionTimeout: number; // 分钟
}

/**
 * 咨询相关配置
 */
export interface ConsultationConfig {
  enableConsultation: boolean;
  requirePayment: boolean;
  defaultPrice: number;
  minPrice: number;
  maxPrice: number;
  lawyerCommissionRate: number; // 百分比
  platformCommissionRate: number; // 百分比
  autoCompleteHours: number;
  maxConsultationDuration: number; // 分钟
}

/**
 * 文档相关配置
 */
export interface DocumentConfig {
  enableDocumentGeneration: boolean;
  maxDocumentsPerDay: number;
  maxUploadSize: number; // MB
  allowedFileTypes: string[];
  storageProvider: 'local' | 'oss' | 's3';
}

/**
 * 支付相关配置
 */
export interface PaymentConfig {
  enableAlipay: boolean;
  enableWechatPay: boolean;
  enableBalance: boolean;
  minWithdrawalAmount: number;
  withdrawalFeeRate: number; // 百分比
  withdrawalProcessingDays: number;
}

/**
 * 通知相关配置
 */
export interface NotificationConfig {
  enableEmailNotification: boolean;
  enableSmsNotification: boolean;
  enablePushNotification: boolean;
  emailFrom: string;
  smsProvider: string;
}

/**
 * 安全相关配置
 */
export interface SecurityConfig {
  enableCaptcha: boolean;
  maxLoginAttempts: number;
  lockoutDuration: number; // 分钟
  enableIpWhitelist: boolean;
  ipWhitelist: string[];
  enableAuditLog: boolean;
}

/**
 * 系统配置汇总
 */
export interface SystemConfig {
  site: SiteConfig;
  user: UserConfig;
  consultation: ConsultationConfig;
  document: DocumentConfig;
  payment: PaymentConfig;
  notification: NotificationConfig;
  security: SecurityConfig;
}

// ==================== API 请求/响应类型 ====================

/**
 * 获取系统配置响应
 */
export interface GetSystemConfigResponse {
  config: SystemConfig;
  updatedAt: string;
  updatedBy: string;
}

/**
 * 更新系统配置请求
 */
export interface UpdateSystemConfigRequest {
  site?: Partial<SiteConfig>;
  user?: Partial<UserConfig>;
  consultation?: Partial<ConsultationConfig>;
  document?: Partial<DocumentConfig>;
  payment?: Partial<PaymentConfig>;
  notification?: Partial<NotificationConfig>;
  security?: Partial<SecurityConfig>;
}

/**
 * 系统日志
 */
export interface SystemLog {
  id: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  module: string;
  message: string;
  details?: Record<string, unknown>;
  userId?: string;
  ipAddress?: string;
  userAgent?: string;
  createdAt: string;
}

/**
 * 获取系统日志请求
 */
export interface GetSystemLogsRequest {
  page?: number;
  pageSize?: number;
  level?: SystemLog['level'];
  module?: string;
  startDate?: string;
  endDate?: string;
  keyword?: string;
}

/**
 * 获取系统日志响应
 */
export interface GetSystemLogsResponse {
  items: SystemLog[];
  total: number;
  page: number;
  pageSize: number;
}

/**
 * 系统状态
 */
export interface SystemStatus {
  version: string;
  uptime: number;
  environment: 'development' | 'staging' | 'production';
  database: {
    connected: boolean;
    latency: number;
  };
  cache: {
    connected: boolean;
    latency: number;
  };
  storage: {
    connected: boolean;
    used: number;
    total: number;
  };
  memory: {
    used: number;
    total: number;
  };
  cpu: {
    usage: number;
    cores: number;
  };
}

/**
 * 备份信息
 */
export interface BackupInfo {
  id: string;
  name: string;
  size: number;
  type: 'full' | 'incremental';
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: string;
  completedAt: string | null;
  downloadUrl?: string;
}

/**
 * 获取备份列表响应
 */
export interface GetBackupsResponse {
  items: BackupInfo[];
  total: number;
  page: number;
  pageSize: number;
}
