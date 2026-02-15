/**
 * System-Config（系统配置）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  ConfigItem,
  ConfigGroup,
  ConfigHistory,
  GetConfigListRequest,
  GetConfigHistoryRequest,
  UpdateConfigRequest,
  BatchUpdateConfigRequest,
  ResetConfigRequest,
  ResetConfigResponse,
} from '../types';
import {
  apiGetConfigList,
  apiGetConfigDetail,
  apiUpdateConfig,
  apiBatchUpdateConfig,
  apiGetConfigHistory,
  apiGetConfigGroups,
  apiResetConfig,
  apiExportConfig,
  apiImportConfig,
  apiRefreshConfigCache,
  apiGetConfigCache,
} from '../api';

// ==================== Query Keys ====================

const SYSTEM_CONFIG_QUERY_KEYS = {
  list: (params?: GetConfigListRequest) => ['system-config', 'list', params] as const,
  detail: (configId: string) => ['system-config', 'detail', configId] as const,
  history: (params?: GetConfigHistoryRequest) => ['system-config', 'history', params] as const,
  groups: ['system-config', 'groups'] as const,
  cache: ['system-config', 'cache'] as const,
} as const;

// ==================== Config List Hooks ====================

/**
 * 获取配置列表 Hook
 */
export function useConfigList(params: GetConfigListRequest = {}) {
  return useQuery<{ configs: ConfigItem[]; groups: ConfigGroup[] }>({
    queryKey: SYSTEM_CONFIG_QUERY_KEYS.list(params),
    queryFn: () => apiGetConfigList(params),
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Config Detail Hooks ====================

/**
 * 获取配置详情 Hook
 */
export function useConfigDetail(configId: string) {
  return useQuery<ConfigItem>({
    queryKey: SYSTEM_CONFIG_QUERY_KEYS.detail(configId),
    queryFn: async () => {
      const response = await apiGetConfigDetail({ configId });
      return response.config;
    },
    enabled: configId.length > 0,
    staleTime: 30 * 1000, // 30秒缓存
  });
}

// ==================== Config Update Hooks ====================

/**
 * 更新配置 Hook
 */
export function useUpdateConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateConfigRequest) => apiUpdateConfig(request),
    onSuccess: (_data, variables) => {
      // 更新成功后刷新配置详情
      void queryClient.invalidateQueries({ queryKey: SYSTEM_CONFIG_QUERY_KEYS.detail(variables.configId) });
      // 刷新配置列表
      void queryClient.invalidateQueries({ queryKey: ['system-config', 'list'] });
      // 刷新历史记录
      void queryClient.invalidateQueries({ queryKey: ['system-config', 'history'] });
    },
  });
}

/**
 * 批量更新配置 Hook
 */
export function useBatchUpdateConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: BatchUpdateConfigRequest) => apiBatchUpdateConfig(request),
    onSuccess: () => {
      // 批量更新成功后刷新配置列表
      void queryClient.invalidateQueries({ queryKey: ['system-config', 'list'] });
      // 刷新历史记录
      void queryClient.invalidateQueries({ queryKey: ['system-config', 'history'] });
      // 刷新所有配置详情
      void queryClient.invalidateQueries({ queryKey: ['system-config', 'detail'] });
    },
  });
}

// ==================== Config History Hooks ====================

/**
 * 获取配置历史 Hook
 */
export function useConfigHistory(params: GetConfigHistoryRequest = {}) {
  return useQuery<{ histories: ConfigHistory[]; total: number }>({
    queryKey: SYSTEM_CONFIG_QUERY_KEYS.history(params),
    queryFn: () => apiGetConfigHistory(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

// ==================== Config Group Hooks ====================

/**
 * 获取配置分组列表 Hook
 */
export function useConfigGroups() {
  return useQuery<ConfigGroup[]>({
    queryKey: SYSTEM_CONFIG_QUERY_KEYS.groups,
    queryFn: async () => {
      const response = await apiGetConfigGroups();
      return response.groups;
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存，分组不常变化
  });
}

// ==================== Config Reset Hooks ====================

/**
 * 重置配置为默认值 Hook
 */
export function useResetConfig() {
  const queryClient = useQueryClient();

  return useMutation<ResetConfigResponse, Error, ResetConfigRequest>({
    mutationFn: (request: ResetConfigRequest) => apiResetConfig(request),
    onSuccess: (_data, variables) => {
      // 重置成功后刷新配置详情
      void queryClient.invalidateQueries({ queryKey: SYSTEM_CONFIG_QUERY_KEYS.detail(variables.configId) });
      // 刷新配置列表
      void queryClient.invalidateQueries({ queryKey: ['system-config', 'list'] });
      // 刷新历史记录
      void queryClient.invalidateQueries({ queryKey: ['system-config', 'history'] });
    },
  });
}

// ==================== Config Export/Import Hooks ====================

/**
 * 导出配置 Hook
 */
export function useExportConfig() {
  return useMutation({
    mutationFn: () => apiExportConfig(),
  });
}

/**
 * 导入配置 Hook
 */
export function useImportConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ importData, overwrite }: { importData: string; overwrite?: boolean }) =>
      apiImportConfig({ importData, overwrite }),
    onSuccess: () => {
      // 导入成功后刷新配置列表
      void queryClient.invalidateQueries({ queryKey: ['system-config', 'list'] });
      // 刷新历史记录
      void queryClient.invalidateQueries({ queryKey: ['system-config', 'history'] });
    },
  });
}

// ==================== Config Cache Hooks ====================

/**
 * 刷新配置缓存 Hook
 */
export function useRefreshConfigCache() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiRefreshConfigCache(),
    onSuccess: () => {
      // 刷新成功后刷新缓存信息
      void queryClient.invalidateQueries({ queryKey: SYSTEM_CONFIG_QUERY_KEYS.cache });
    },
  });
}

/**
 * 获取配置缓存信息 Hook
 */
export function useConfigCache() {
  return useQuery({
    queryKey: SYSTEM_CONFIG_QUERY_KEYS.cache,
    queryFn: () => apiGetConfigCache(),
    staleTime: 10 * 1000, // 10秒缓存
  });
}

// ==================== Utility Hooks ====================

/**
 * 根据分组获取配置列表 Hook
 */
export function useConfigsByGroup(groupId: string) {
  return useQuery<ConfigItem[]>({
    queryKey: [...SYSTEM_CONFIG_QUERY_KEYS.list({ group: groupId }), 'by-group'],
    queryFn: async () => {
      const response = await apiGetConfigList({ group: groupId });
      return response.configs;
    },
    enabled: groupId.length > 0,
    staleTime: 60 * 1000,
  });
}

/**
 * 搜索配置 Hook
 */
export function useSearchConfigs(search: string) {
  return useQuery<ConfigItem[]>({
    queryKey: [...SYSTEM_CONFIG_QUERY_KEYS.list({ search }), 'search'],
    queryFn: async () => {
      const response = await apiGetConfigList({ search });
      return response.configs;
    },
    enabled: search.length > 0,
    staleTime: 30 * 1000,
  });
}

/**
 * 获取可编辑配置列表 Hook
 */
export function useEditableConfigs() {
  return useQuery<ConfigItem[]>({
    queryKey: [...SYSTEM_CONFIG_QUERY_KEYS.list({ editable: true }), 'editable'],
    queryFn: async () => {
      const response = await apiGetConfigList({ editable: true });
      return response.configs;
    },
    staleTime: 60 * 1000,
  });
}