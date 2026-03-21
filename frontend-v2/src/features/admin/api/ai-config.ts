/**
 * AI配置管理 API 层
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  AIProvider,
  AIModelConfigListResponse,
  AIModelConfigStats,
  CreateAIModelConfigRequest,
  UpdateAIModelConfigRequest,
  AIModelConfigItem,
  BatchOperationRequest,
  BatchOperationResponse,
  TestConfigResponse,
  HealthCheckResponse,
  ConfigStatsResponse,
} from '../types/ai-config';

// API 基础路径
const AI_API_BASE = '/system/ai';

/**
 * 获取AI提供商列表
 */
export async function apiGetAIProviders(): Promise<AIProvider[]> {
  const response = await apiClient.get<AIProvider[]>(`${AI_API_BASE}/providers`);
  return response.data;
}

/**
 * 获取AI模型配置列表
 */
export async function apiGetAIModelConfigs(params?: {
  enabled_only?: boolean;
  provider?: string;
}): Promise<AIModelConfigListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.enabled_only) searchParams.set('enabled_only', 'true');
  if (params?.provider) searchParams.set('provider', params.provider);

  const url = `${AI_API_BASE}/models${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await apiClient.get<AIModelConfigListResponse>(url);
  return response.data;
}

/**
 * 创建AI模型配置
 */
export async function apiCreateAIModelConfig(
  data: CreateAIModelConfigRequest
): Promise<AIModelConfigItem> {
  const response = await apiClient.post<AIModelConfigItem>(`${AI_API_BASE}/models`, data);
  return response.data;
}

/**
 * 更新AI模型配置
 */
export async function apiUpdateAIModelConfig(
  configId: number,
  data: UpdateAIModelConfigRequest
): Promise<AIModelConfigItem> {
  const response = await apiClient.put<AIModelConfigItem>(
    `${AI_API_BASE}/models/${configId}`,
    data
  );
  return response.data;
}

/**
 * 删除AI模型配置
 */
export async function apiDeleteAIModelConfig(configId: number): Promise<void> {
  await apiClient.delete(`${AI_API_BASE}/models/${configId}`);
}

/**
 * 批量操作AI模型配置
 */
export async function apiBatchOperationAIModelConfigs(
  data: BatchOperationRequest
): Promise<BatchOperationResponse> {
  const response = await apiClient.post<BatchOperationResponse>(
    `${AI_API_BASE}/models/batch`,
    data
  );
  return response.data;
}

/**
 * 测试AI模型配置
 */
export async function apiTestAIModelConfig(configId: number): Promise<TestConfigResponse> {
  const response = await apiClient.post<TestConfigResponse>(
    `${AI_API_BASE}/models/${configId}/test`
  );
  return response.data;
}

/**
 * 触发健康检查
 */
export async function apiTriggerHealthCheck(configId: number): Promise<HealthCheckResponse> {
  const response = await apiClient.post<HealthCheckResponse>(
    `${AI_API_BASE}/models/${configId}/health-check`
  );
  return response.data;
}

/**
 * 获取单个配置统计
 */
export async function apiGetConfigStats(configId: number): Promise<ConfigStatsResponse> {
  const response = await apiClient.get<ConfigStatsResponse>(
    `${AI_API_BASE}/models/${configId}/stats`
  );
  return response.data;
}

/**
 * 获取AI配置统计概览
 */
export async function apiGetAIConfigStatsSummary(params?: {
  provider?: string;
}): Promise<AIModelConfigStats> {
  const searchParams = new URLSearchParams();
  if (params?.provider) searchParams.set('provider', params.provider);

  const url = `${AI_API_BASE}/stats/summary${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await apiClient.get<AIModelConfigStats>(url);
  return response.data;
}

/**
 * 获取AI配置状态
 */
export async function apiGetAIConfigStatus(): Promise<{
  primary_model: string | null;
  fallback_models: string[];
  total_models: number;
  enabled_models: number;
}> {
  const response = await apiClient.get<{
    primary_model: string | null;
    fallback_models: string[];
    total_models: number;
    enabled_models: number;
  }>(`${AI_API_BASE}/config`);
  return response.data;
}
