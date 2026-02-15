/**
 * Cross-Domain（跨域功能）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  DomainConfig,
  GetDomainListRequest,
  AddDomainRequest,
  UpdateDomainRequest,
  VerifyDomainRequest,
} from '../types';
import {
  apiGetDomainList,
  apiAddDomain,
  apiUpdateDomain,
  apiDeleteDomain,
  apiVerifyDomain,
} from '../api';

// ==================== Query Keys ====================

const CROSS_DOMAIN_QUERY_KEYS = {
  domains: (params?: GetDomainListRequest) => ['cross-domain', 'domains', params] as const,
  domain: (domainId: number) => ['cross-domain', 'domain', domainId] as const,
} as const;

// ==================== Domain Hooks ====================

/**
 * 获取域名列表 Hook
 */
export function useDomainList(params: GetDomainListRequest = {}) {
  return useQuery<DomainConfig[]>({
    queryKey: CROSS_DOMAIN_QUERY_KEYS.domains(params),
    queryFn: async () => {
      const response = await apiGetDomainList(params);
      return response.domains;
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 添加域名 Hook
 */
export function useAddDomain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AddDomainRequest) => apiAddDomain(request),
    onSuccess: () => {
      // 添加成功后刷新域名列表
      void queryClient.invalidateQueries({ queryKey: ['cross-domain', 'domains'] });
    },
  });
}

/**
 * 更新域名 Hook
 */
export function useUpdateDomain(domainId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateDomainRequest) => apiUpdateDomain(domainId, request),
    onSuccess: () => {
      // 更新成功后刷新域名列表和详情
      void queryClient.invalidateQueries({ queryKey: ['cross-domain', 'domains'] });
      void queryClient.invalidateQueries({ queryKey: CROSS_DOMAIN_QUERY_KEYS.domain(domainId) });
    },
  });
}

/**
 * 删除域名 Hook
 */
export function useDeleteDomain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (domainId: number) => apiDeleteDomain(domainId),
    onSuccess: () => {
      // 删除成功后刷新域名列表
      void queryClient.invalidateQueries({ queryKey: ['cross-domain', 'domains'] });
    },
  });
}

/**
 * 验证域名 Hook
 */
export function useVerifyDomain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: VerifyDomainRequest) => apiVerifyDomain(request),
    onSuccess: (_data, variables) => {
      // 验证成功后刷新域名列表和详情
      void queryClient.invalidateQueries({ queryKey: ['cross-domain', 'domains'] });
      void queryClient.invalidateQueries({ queryKey: CROSS_DOMAIN_QUERY_KEYS.domain(variables.domainId) });
    },
  });
}