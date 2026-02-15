/**
 * Cross-Domain（跨域功能）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/cross-domain 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  DomainConfig,
  CrossDomainRule,
  DomainVerificationResult,
  GetDomainListRequest,
  GetDomainListResponse,
  AddDomainRequest,
  AddDomainResponse,
  UpdateDomainRequest,
  UpdateDomainResponse,
  DeleteDomainResponse,
  VerifyDomainRequest,
  VerifyDomainResponse,
  GetCrossDomainRulesResponse,
  AddCrossDomainRuleRequest,
  UpdateCrossDomainRuleRequest,
} from '../types';


// API 基础路径
const API_BASE = '/cross-domain';

// ==================== 后端响应类型定义 ====================

/** 后端域名响应 */
interface BackendDomainResponse {
  id: number;
  domain: string;
  status: string;
  description?: string;
  allowed_origins: string[];
  allowed_methods: string[];
  allowed_headers: string[];
  allow_credentials: boolean;
  max_age: number;
  created_at: string;
  updated_at: string;
  verified_at?: string;
  is_verified: boolean;
  owner_id: number;
  owner_email: string;
}

/** 后端域名列表响应 */
interface BackendDomainListResponse {
  items: BackendDomainResponse[];
  total: number;
}

/** 后端域名详情响应 */
interface BackendDomainDetailResponse extends BackendDomainResponse {
  verification_code?: string;
}

/** 后端验证结果 */
interface BackendVerificationResult {
  domain: string;
  is_verified: boolean;
  verification_method: string;
  verification_token: string;
  verified_at?: string;
  message?: string;
}

/** 后端跨域规则响应 */
interface BackendCrossDomainRuleResponse {
  id: number;
  domain_id: number;
  rule_type: string;
  name: string;
  description?: string;
  config: Record<string, unknown>;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** 后端跨域规则列表响应 */
interface BackendCrossDomainRulesResponse {
  rules: BackendCrossDomainRuleResponse[];
  total: number;
}

// ==================== 转换函数 ====================

/**
 * 转换后端域名到前端格式
 */
function mapBackendToDomainConfig(data: BackendDomainResponse): DomainConfig {
  return {
    id: data.id,
    domain: data.domain,
    status: data.status as DomainConfig['status'],
    description: data.description,
    allowedOrigins: data.allowed_origins,
    allowedMethods: data.allowed_methods as DomainConfig['allowedMethods'],
    allowedHeaders: data.allowed_headers,
    allowCredentials: data.allow_credentials,
    maxAge: data.max_age,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    verifiedAt: data.verified_at,
    isVerified: data.is_verified,
    ownerId: data.owner_id,
    ownerEmail: data.owner_email,
  };
}

/**
 * 转换后端验证结果到前端格式
 */
function mapBackendToVerificationResult(data: BackendVerificationResult): DomainVerificationResult {
  return {
    domain: data.domain,
    isVerified: data.is_verified,
    verificationMethod: data.verification_method as DomainVerificationResult['verificationMethod'],
    verificationToken: data.verification_token,
    verifiedAt: data.verified_at,
    message: data.message,
  };
}

/**
 * 转换后端跨域规则到前端格式
 */
function mapBackendToCrossDomainRule(data: BackendCrossDomainRuleResponse): CrossDomainRule {
  return {
    id: data.id,
    domainId: data.domain_id,
    ruleType: data.rule_type as CrossDomainRule['ruleType'],
    name: data.name,
    description: data.description,
    config: data.config,
    priority: data.priority,
    isActive: data.is_active,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

// ==================== 域名管理 API ====================

/**
 * 获取域名列表
 */
export async function apiGetDomainList(params: GetDomainListRequest = {}): Promise<GetDomainListResponse> {
  const response = await apiClient.get<BackendDomainListResponse>(`${API_BASE}/domains`, {
    params: {
      status: params.status,
      search: params.search,
      limit: params.limit,
      offset: params.offset,
    },
  });

  return {
    domains: response.data.items.map(mapBackendToDomainConfig),
    total: response.data.total,
  };
}

/**
 * 添加域名
 */
export async function apiAddDomain(request: AddDomainRequest): Promise<AddDomainResponse> {
  const response = await apiClient.post<{
    success: boolean;
    domain: BackendDomainResponse;
    verification: BackendVerificationResult;
  }>(`${API_BASE}/domains`, {
    domain: request.domain,
    description: request.description,
    allowed_origins: request.allowedOrigins,
    allowed_methods: request.allowedMethods,
    allowed_headers: request.allowedHeaders,
    allow_credentials: request.allowCredentials,
    max_age: request.maxAge,
  });

  return {
    success: response.data.success,
    domain: mapBackendToDomainConfig(response.data.domain),
    verification: mapBackendToVerificationResult(response.data.verification),
  };
}

/**
 * 获取域名详情
 */
export async function apiGetDomainDetail(domainId: number): Promise<DomainConfig> {
  const response = await apiClient.get<BackendDomainDetailResponse>(`${API_BASE}/domains/${domainId}`);
  return mapBackendToDomainConfig(response.data);
}

/**
 * 更新域名
 */
export async function apiUpdateDomain(
  domainId: number,
  request: UpdateDomainRequest
): Promise<UpdateDomainResponse> {
  const response = await apiClient.put<{
    success: boolean;
    domain: BackendDomainResponse;
  }>(`${API_BASE}/domains/${domainId}`, {
    description: request.description,
    allowed_origins: request.allowedOrigins,
    allowed_methods: request.allowedMethods,
    allowed_headers: request.allowedHeaders,
    allow_credentials: request.allowCredentials,
    max_age: request.maxAge,
    status: request.status,
  });

  return {
    success: response.data.success,
    domain: mapBackendToDomainConfig(response.data.domain),
  };
}

/**
 * 删除域名
 */
export async function apiDeleteDomain(domainId: number): Promise<DeleteDomainResponse> {
  const response = await apiClient.delete<{ success: boolean; message: string }>(`${API_BASE}/domains/${domainId}`);
  return response.data;
}

/**
 * 验证域名
 */
export async function apiVerifyDomain(request: VerifyDomainRequest): Promise<VerifyDomainResponse> {
  const response = await apiClient.post<{
    success: boolean;
    domain: BackendDomainResponse;
    result: BackendVerificationResult;
  }>(`${API_BASE}/domains/${request.domainId}/verify`, {
    verification_method: request.verificationMethod,
  });

  return {
    success: response.data.success,
    domain: mapBackendToDomainConfig(response.data.domain),
    result: mapBackendToVerificationResult(response.data.result),
  };
}

// ==================== 跨域规则 API ====================

/**
 * 获取跨域规则列表
 */
export async function apiGetCrossDomainRules(domainId: number): Promise<GetCrossDomainRulesResponse> {
  const response = await apiClient.get<BackendCrossDomainRulesResponse>(`${API_BASE}/domains/${domainId}/rules`);

  return {
    rules: response.data.rules.map(mapBackendToCrossDomainRule),
    total: response.data.total,
  };
}

/**
 * 添加跨域规则
 */
export async function apiAddCrossDomainRule(request: AddCrossDomainRuleRequest): Promise<{ success: boolean; rule: CrossDomainRule }> {
  const response = await apiClient.post<{
    success: boolean;
    rule: BackendCrossDomainRuleResponse;
  }>(`${API_BASE}/domains/${request.domainId}/rules`, {
    rule_type: request.ruleType,
    name: request.name,
    description: request.description,
    config: request.config,
    priority: request.priority,
  });

  return {
    success: response.data.success,
    rule: mapBackendToCrossDomainRule(response.data.rule),
  };
}

/**
 * 更新跨域规则
 */
export async function apiUpdateCrossDomainRule(request: UpdateCrossDomainRuleRequest): Promise<{ success: boolean; rule: CrossDomainRule }> {
  const response = await apiClient.put<{
    success: boolean;
    rule: BackendCrossDomainRuleResponse;
  }>(`${API_BASE}/rules/${request.ruleId}`, {
    name: request.name,
    description: request.description,
    config: request.config,
    priority: request.priority,
    is_active: request.isActive,
  });

  return {
    success: response.data.success,
    rule: mapBackendToCrossDomainRule(response.data.rule),
  };
}

/**
 * 删除跨域规则
 */
export async function apiDeleteCrossDomainRule(ruleId: number): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete<{ success: boolean; message: string }>(`${API_BASE}/rules/${ruleId}`);
  return response.data;
}
