/**
 * Cross-Domain（跨域功能）类型定义
 */

// ==================== 核心类型 ====================

/** 域名状态 */
export type DomainStatus = 'active' | 'pending' | 'disabled' | 'expired';

/** 跨域规则类型 */
export type CrossDomainRuleType = 'cors' | 'frame' | 'redirect' | 'header';

/** HTTP 方法 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'OPTIONS' | 'HEAD';

/** 域名配置 */
export interface DomainConfig {
  id: number;
  domain: string;
  status: DomainStatus;
  description?: string;
  allowedOrigins: string[];
  allowedMethods: HttpMethod[];
  allowedHeaders: string[];
  allowCredentials: boolean;
  maxAge: number;
  createdAt: string;
  updatedAt: string;
  verifiedAt?: string;
  isVerified: boolean;
  ownerId: number;
  ownerEmail: string;
}

/** 跨域规则 */
export interface CrossDomainRule {
  id: number;
  domainId: number;
  ruleType: CrossDomainRuleType;
  name: string;
  description?: string;
  config: Record<string, unknown>;
  priority: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

/** CORS 配置 */
export interface CorsConfig {
  allowedOrigins: string[];
  allowedMethods: HttpMethod[];
  allowedHeaders: string[];
  exposedHeaders: string[];
  allowCredentials: boolean;
  maxAge: number;
}

/** Frame 配置（点击劫持防护） */
export interface FrameConfig {
  frameAncestors: string[];
  frameOptions: 'DENY' | 'SAMEORIGIN' | 'ALLOW-FROM';
}

/** 域名验证结果 */
export interface DomainVerificationResult {
  domain: string;
  isVerified: boolean;
  verificationMethod: 'dns' | 'file' | 'meta';
  verificationToken: string;
  verifiedAt?: string;
  message?: string;
}

// ==================== API 请求/响应类型 ====================

/** 获取域名列表请求 */
export interface GetDomainListRequest {
  status?: DomainStatus;
  search?: string;
  limit?: number;
  offset?: number;
}

/** 获取域名列表响应 */
export interface GetDomainListResponse {
  domains: DomainConfig[];
  total: number;
}

/** 添加域名请求 */
export interface AddDomainRequest {
  domain: string;
  description?: string;
  allowedOrigins: string[];
  allowedMethods: HttpMethod[];
  allowedHeaders: string[];
  allowCredentials: boolean;
  maxAge: number;
}

/** 添加域名响应 */
export interface AddDomainResponse {
  success: boolean;
  domain: DomainConfig;
  verification: DomainVerificationResult;
}

/** 更新域名请求 */
export interface UpdateDomainRequest {
  description?: string;
  allowedOrigins?: string[];
  allowedMethods?: HttpMethod[];
  allowedHeaders?: string[];
  allowCredentials?: boolean;
  maxAge?: number;
  status?: DomainStatus;
}

/** 更新域名响应 */
export interface UpdateDomainResponse {
  success: boolean;
  domain: DomainConfig;
}

/** 删除域名请求 */
export interface DeleteDomainRequest {
  domainId: number;
}

/** 删除域名响应 */
export interface DeleteDomainResponse {
  success: boolean;
  message: string;
}

/** 验证域名请求 */
export interface VerifyDomainRequest {
  domainId: number;
  verificationMethod: 'dns' | 'file' | 'meta';
}

/** 验证域名响应 */
export interface VerifyDomainResponse {
  success: boolean;
  domain: DomainConfig;
  result: DomainVerificationResult;
}

/** 获取跨域规则列表响应 */
export interface GetCrossDomainRulesResponse {
  rules: CrossDomainRule[];
  total: number;
}

/** 添加跨域规则请求 */
export interface AddCrossDomainRuleRequest {
  domainId: number;
  ruleType: CrossDomainRuleType;
  name: string;
  description?: string;
  config: Record<string, unknown>;
  priority: number;
}

/** 更新跨域规则请求 */
export interface UpdateCrossDomainRuleRequest {
  ruleId: number;
  name?: string;
  description?: string;
  config?: Record<string, unknown>;
  priority?: number;
  isActive?: boolean;
}

/** 删除跨域规则请求 */
export interface DeleteCrossDomainRuleRequest {
  ruleId: number;
}

// ==================== 表单类型 ====================

/** 域名表单数据 */
export interface DomainFormData {
  domain: string;
  description: string;
  allowedOrigins: string;
  allowedMethods: HttpMethod[];
  allowedHeaders: string;
  allowCredentials: boolean;
  maxAge: number;
}

/** 域名验证表单数据 */
export interface DomainVerificationFormData {
  verificationMethod: 'dns' | 'file' | 'meta';
}