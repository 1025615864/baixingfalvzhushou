/**
 * Enterprise（企业服务）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { queryKeys } from '@/lib/queryKeys';

import type {
  EnterpriseInfo,
  TeamMember,
  EnterpriseOrder,
  ContractReview,
  ComplianceTemplate,
  PermissionItem,
  RolePermissionConfig,
  GetTeamMembersRequest,
  GetEnterpriseOrdersRequest,
  UpdateEnterpriseInfoRequest,
  AddTeamMemberRequest,
  RemoveTeamMemberRequest,
  UpdateMemberRoleRequest,
  SubmitContractReviewRequest,
  UpdateRolePermissionsRequest,
} from '../types';
import {
  apiGetEnterpriseInfo,
  apiUpdateEnterpriseInfo,
  apiGetTeamMembers,
  apiAddTeamMember,
  apiRemoveTeamMember,
  apiUpdateMemberRole,
  apiGetEnterpriseOrders,
  apiGetContractReviews,
  apiSubmitContractReview,
  apiGetComplianceTemplates,
  apiGetPermissions,
  apiGetRolePermissions,
  apiUpdateRolePermissions,
} from '../api';

// ==================== Enterprise Info Hooks ====================

/**
 * 获取企业信息 Hook
 */
export function useEnterpriseInfo(accountId: number) {
  return useQuery<EnterpriseInfo>({
    queryKey: queryKeys.enterprise.info(accountId),
    queryFn: () => apiGetEnterpriseInfo(accountId),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: accountId > 0,
  });
}

/**
 * 更新企业信息 Hook
 */
export function useUpdateEnterpriseInfo(accountId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateEnterpriseInfoRequest) => apiUpdateEnterpriseInfo(accountId, request),
    onSuccess: () => {
      // 更新成功后刷新企业信息
      void queryClient.invalidateQueries({ queryKey: queryKeys.enterprise.info(accountId) });
    },
  });
}

// ==================== Team Member Hooks ====================

/**
 * 获取团队成员列表 Hook
 */
export function useTeamMembers(accountId: number, params: GetTeamMembersRequest = {}) {
  return useQuery<TeamMember[]>({
    queryKey: queryKeys.enterprise.members(accountId, params),
    queryFn: async () => {
      const response = await apiGetTeamMembers(accountId, params);
      return response.members;
    },
    staleTime: 60 * 1000, // 1分钟缓存
    enabled: accountId > 0,
  });
}

/**
 * 添加团队成员 Hook
 */
export function useAddTeamMember(accountId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AddTeamMemberRequest) => apiAddTeamMember(accountId, request),
    onSuccess: () => {
      // 添加成功后刷新成员列表
      void queryClient.invalidateQueries({ queryKey: queryKeys.enterprise.members(accountId) });
      // 刷新企业信息（成员数）
      void queryClient.invalidateQueries({ queryKey: queryKeys.enterprise.info(accountId) });
    },
  });
}

/**
 * 移除团队成员 Hook
 */
export function useRemoveTeamMember(accountId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: RemoveTeamMemberRequest) => apiRemoveTeamMember(accountId, request),
    onSuccess: () => {
      // 移除成功后刷新成员列表
      void queryClient.invalidateQueries({ queryKey: queryKeys.enterprise.members(accountId) });
      // 刷新企业信息（成员数）
      void queryClient.invalidateQueries({ queryKey: queryKeys.enterprise.info(accountId) });
    },
  });
}

/**
 * 更新成员角色 Hook
 */
export function useUpdateMemberRole(accountId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateMemberRoleRequest) => apiUpdateMemberRole(accountId, request),
    onSuccess: () => {
      // 更新成功后刷新成员列表
      void queryClient.invalidateQueries({ queryKey: queryKeys.enterprise.members(accountId) });
    },
  });
}

// ==================== Order Hooks ====================

/**
 * 获取企业订单列表 Hook
 */
export function useEnterpriseOrders(accountId: number, params: GetEnterpriseOrdersRequest = {}) {
  return useQuery<EnterpriseOrder[]>({
    queryKey: queryKeys.enterprise.orders(accountId, params),
    queryFn: async () => {
      const response = await apiGetEnterpriseOrders(accountId, params);
      return response.orders;
    },
    staleTime: 60 * 1000, // 1分钟缓存
    enabled: accountId > 0,
  });
}

// ==================== Contract Review Hooks ====================

/**
 * 获取合同审查列表 Hook
 */
export function useContractReviews(accountId: number) {
  return useQuery<ContractReview[]>({
    queryKey: queryKeys.enterprise.contracts(accountId),
    queryFn: async () => {
      const response = await apiGetContractReviews(accountId);
      return response.contracts;
    },
    staleTime: 30 * 1000, // 30秒缓存
    enabled: accountId > 0,
  });
}

/**
 * 提交合同审查 Hook
 */
export function useSubmitContractReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SubmitContractReviewRequest) => apiSubmitContractReview(request),
    onSuccess: (_data, variables) => {
      // 提交成功后刷新合同列表
      void queryClient.invalidateQueries({ queryKey: queryKeys.enterprise.contracts(variables.accountId) });
      // 刷新企业信息（合同数）
      void queryClient.invalidateQueries({ queryKey: queryKeys.enterprise.info(variables.accountId) });
    },
  });
}

// ==================== Compliance Template Hooks ====================

/**
 * 获取合规模板列表 Hook
 */
export function useComplianceTemplates(category?: string) {
  return useQuery<ComplianceTemplate[]>({
    queryKey: queryKeys.enterprise.templates(category),
    queryFn: () => apiGetComplianceTemplates(category),
    staleTime: 30 * 60 * 1000, // 30分钟缓存，模板不常变化
  });
}

// ==================== Permission Hooks ====================

/**
 * 获取权限列表 Hook
 */
export function usePermissions() {
  return useQuery<PermissionItem[]>({
    queryKey: queryKeys.enterprise.permissions,
    queryFn: async () => {
      const response = await apiGetPermissions();
      return response.permissions;
    },
    staleTime: 30 * 60 * 1000, // 30分钟缓存
  });
}

/**
 * 获取角色权限配置 Hook
 */
export function useRolePermissions(accountId: number) {
  return useQuery<RolePermissionConfig[]>({
    queryKey: queryKeys.enterprise.rolePermissions(accountId),
    queryFn: async () => {
      const response = await apiGetRolePermissions(accountId);
      return response.configs;
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: accountId > 0,
  });
}

/**
 * 更新角色权限 Hook
 */
export function useUpdateRolePermissions(accountId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateRolePermissionsRequest) => apiUpdateRolePermissions(accountId, request),
    onSuccess: () => {
      // 更新成功后刷新角色权限
      void queryClient.invalidateQueries({ queryKey: queryKeys.enterprise.rolePermissions(accountId) });
    },
  });
}