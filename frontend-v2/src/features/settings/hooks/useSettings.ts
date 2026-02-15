/**
 * Settings（系统设置）Hook（管理员用）
 * 使用 React Query 管理系统设置相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  GetSystemConfigResponse,
  UpdateSystemConfigRequest,
  GetSystemLogsRequest,
  GetSystemLogsResponse,
  SystemStatus,
  GetBackupsResponse,
} from '../types';
import {
  apiGetSystemConfig,
  apiUpdateSystemConfig,
  apiGetSystemLogs,
  apiGetSystemStatus,
  apiGetBackups,
  apiCreateBackup,
  apiDeleteBackup,
  apiDownloadBackup,
} from '../api';

// Query Keys
const SETTINGS_KEYS = {
  all: ['settings', 'admin'] as const,
  config: () => [...SETTINGS_KEYS.all, 'config'] as const,
  logs: (params: GetSystemLogsRequest) => [...SETTINGS_KEYS.all, 'logs', params] as const,
  status: () => [...SETTINGS_KEYS.all, 'status'] as const,
  backups: () => [...SETTINGS_KEYS.all, 'backups'] as const,
} as const;

/**
 * 获取系统配置
 */
export function useSystemConfig() {
  return useQuery<GetSystemConfigResponse, Error>({
    queryKey: SETTINGS_KEYS.config(),
    queryFn: apiGetSystemConfig,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 更新系统配置
 */
export function useUpdateSystemConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateSystemConfigRequest) => apiUpdateSystemConfig(request),
    onSuccess: () => {
      // 更新成功后刷新配置
      void queryClient.invalidateQueries({ queryKey: SETTINGS_KEYS.config() });
    },
  });
}

/**
 * 获取系统日志
 */
export function useSystemLogs(params: GetSystemLogsRequest = {}) {
  return useQuery<GetSystemLogsResponse, Error>({
    queryKey: SETTINGS_KEYS.logs(params),
    queryFn: () => apiGetSystemLogs(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 获取系统状态
 */
export function useSystemStatus() {
  return useQuery<SystemStatus, Error>({
    queryKey: SETTINGS_KEYS.status(),
    queryFn: apiGetSystemStatus,
    refetchInterval: 30 * 1000, // 每30秒自动刷新
    staleTime: 30 * 1000,
  });
}

/**
 * 获取备份列表
 */
export function useBackups(params?: { page?: number; pageSize?: number }) {
  return useQuery<GetBackupsResponse, Error>({
    queryKey: SETTINGS_KEYS.backups(),
    queryFn: () => apiGetBackups(params),
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 创建备份
 */
export function useCreateBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (type: 'full' | 'incremental') => apiCreateBackup(type),
    onSuccess: () => {
      // 创建成功后刷新备份列表
      void queryClient.invalidateQueries({ queryKey: SETTINGS_KEYS.backups() });
    },
  });
}

/**
 * 删除备份
 */
export function useDeleteBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiDeleteBackup(id),
    onSuccess: () => {
      // 删除成功后刷新备份列表
      void queryClient.invalidateQueries({ queryKey: SETTINGS_KEYS.backups() });
    },
  });
}

/**
 * 下载备份
 */
export function useDownloadBackup() {
  return useMutation({
    mutationFn: (id: string) => apiDownloadBackup(id),
  });
}
