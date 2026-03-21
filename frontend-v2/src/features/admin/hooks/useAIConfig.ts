/**
 * AI配置管理 Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  AIProvider,
  AIModelConfigListResponse,
  AIModelConfigStats,
  CreateAIModelConfigRequest,
  UpdateAIModelConfigRequest,
  BatchOperationRequest,
} from '../types/ai-config';
import {
  apiGetAIProviders,
  apiGetAIModelConfigs,
  apiCreateAIModelConfig,
  apiUpdateAIModelConfig,
  apiDeleteAIModelConfig,
  apiBatchOperationAIModelConfigs,
  apiTestAIModelConfig,
  apiTriggerHealthCheck,
  apiGetAIConfigStatsSummary,
} from '../api/ai-config';

// ==================== Query Keys ====================

const AI_CONFIG_QUERY_KEYS = {
  providers: () => ['ai-config', 'providers'] as const,
  configs: (params?: { enabled_only?: boolean; provider?: string }) =>
    ['ai-config', 'configs', params] as const,
  statsSummary: (params?: { provider?: string }) =>
    ['ai-config', 'stats-summary', params] as const,
} as const;

// ==================== Providers Hooks ====================

/**
 * 获取AI提供商列表 Hook
 */
export function useAIProviders(enabled = true) {
  return useQuery<AIProvider[]>({
    queryKey: AI_CONFIG_QUERY_KEYS.providers(),
    queryFn: apiGetAIProviders,
    enabled,
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

// ==================== Configs Hooks ====================

/**
 * 获取AI模型配置列表 Hook
 */
export function useAIModelConfigs(
  params?: {
    enabled_only?: boolean;
    provider?: string;
  },
  enabled = true
) {
  return useQuery<AIModelConfigListResponse>({
    queryKey: AI_CONFIG_QUERY_KEYS.configs(params),
    queryFn: () => apiGetAIModelConfigs(params),
    enabled,
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 创建AI模型配置 Hook
 */
export function useCreateAIModelConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAIModelConfigRequest) => apiCreateAIModelConfig(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'configs'] });
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'stats-summary'] });
    },
  });
}

/**
 * 更新AI模型配置 Hook
 */
export function useUpdateAIModelConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      configId,
      data,
    }: {
      configId: number;
      data: UpdateAIModelConfigRequest;
    }) => apiUpdateAIModelConfig(configId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'configs'] });
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'stats-summary'] });
    },
  });
}

/**
 * 删除AI模型配置 Hook
 */
export function useDeleteAIModelConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (configId: number) => apiDeleteAIModelConfig(configId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'configs'] });
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'stats-summary'] });
    },
  });
}

/**
 * 批量操作AI模型配置 Hook
 */
export function useBatchOperationAIModelConfigs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BatchOperationRequest) => apiBatchOperationAIModelConfigs(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'configs'] });
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'stats-summary'] });
    },
  });
}

/**
 * 测试AI模型配置 Hook
 */
export function useTestAIModelConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (configId: number) => apiTestAIModelConfig(configId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'configs'] });
    },
  });
}

/**
 * 触发健康检查 Hook
 */
export function useTriggerHealthCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (configId: number) => apiTriggerHealthCheck(configId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'configs'] });
      void queryClient.invalidateQueries({ queryKey: ['ai-config', 'stats-summary'] });
    },
  });
}

// ==================== Stats Hooks ====================

/**
 * 获取AI配置统计概览 Hook
 */
export function useAIConfigStatsSummary(params?: { provider?: string }, enabled = true) {
  return useQuery<AIModelConfigStats>({
    queryKey: AI_CONFIG_QUERY_KEYS.statsSummary(params),
    queryFn: () => apiGetAIConfigStatsSummary(params),
    enabled,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Helper Hooks ====================

/**
 * 切换配置启用状态 Hook
 */
export function useToggleAIConfigEnabled() {
  return useUpdateAIModelConfig();
}

/**
 * AI配置操作组合 Hook
 */
export function useAIConfigActions() {
  const createMutation = useCreateAIModelConfig();
  const updateMutation = useUpdateAIModelConfig();
  const deleteMutation = useDeleteAIModelConfig();
  const batchMutation = useBatchOperationAIModelConfigs();
  const testMutation = useTestAIModelConfig();
  const healthCheckMutation = useTriggerHealthCheck();

  return {
    create: createMutation,
    update: updateMutation,
    delete: deleteMutation,
    batch: batchMutation,
    test: testMutation,
    healthCheck: healthCheckMutation,
  };
}
