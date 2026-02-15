/**
 * 律所管理 Hook
 * 使用 React Query 管理律所相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type { LawFirm, CreateLawFirmRequest, UpdateLawFirmRequest } from '../types';
import {
  getLawFirms as getLawFirmsApi,
  createLawFirm as createLawFirmApi,
  updateLawFirm as updateLawFirmApi,
  deleteLawFirm as deleteLawFirmApi,
  verifyLawFirm as verifyLawFirmApi,
  toggleLawFirmActive as toggleLawFirmActiveApi,
} from '../api';

// Query Keys
const LAW_FIRM_KEYS = {
  all: ['lawyer', 'lawFirms'] as const,
  list: (params: { keyword?: string; includeInactive?: boolean }) =>
    [...LAW_FIRM_KEYS.all, 'list', params] as const,
} as const;

interface GetLawFirmsParams {
  keyword?: string;
  includeInactive?: boolean;
}

/**
 * 获取律所列表（管理员用）
 */
export function useLawFirms(params: GetLawFirmsParams = {}) {
  return useQuery<LawFirm[], Error>({
    queryKey: LAW_FIRM_KEYS.list(params),
    queryFn: () => getLawFirmsApi(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 创建律所（管理员用）
 */
export function useCreateLawFirm() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateLawFirmRequest) => createLawFirmApi(request),
    onSuccess: () => {
      // 创建成功后刷新律所列表
      void queryClient.invalidateQueries({ queryKey: LAW_FIRM_KEYS.all });
    },
  });
}

/**
 * 更新律所（管理员用）
 */
export function useUpdateLawFirm() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateLawFirmRequest }) =>
      updateLawFirmApi(id, request),
    onSuccess: () => {
      // 更新成功后刷新律所列表
      void queryClient.invalidateQueries({ queryKey: LAW_FIRM_KEYS.all });
    },
  });
}

/**
 * 删除律所（管理员用）
 */
export function useDeleteLawFirm() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteLawFirmApi(id),
    onSuccess: () => {
      // 删除成功后刷新律所列表
      void queryClient.invalidateQueries({ queryKey: LAW_FIRM_KEYS.all });
    },
  });
}

/**
 * 验证律所（管理员用）
 */
export function useVerifyLawFirm() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, verified }: { id: string; verified: boolean }) =>
      verifyLawFirmApi(id, verified),
    onSuccess: () => {
      // 验证成功后刷新律所列表
      void queryClient.invalidateQueries({ queryKey: LAW_FIRM_KEYS.all });
    },
  });
}

/**
 * 启用/禁用律所（管理员用）
 */
export function useToggleLawFirmActive() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      toggleLawFirmActiveApi(id, isActive),
    onSuccess: () => {
      // 操作成功后刷新律所列表
      void queryClient.invalidateQueries({ queryKey: LAW_FIRM_KEYS.all });
    },
  });
}
