import { apiClient } from '@/shared/lib/api/client';
import type {
  GetPermissionsResponse,
  GetRolePermissionsResponse,
  UpdateRolePermissionsRequest,
  TeamMember,
} from '../types';
import type { BackendPermission } from './transforms';

const API_BASE = '/enterprise';

export async function apiGetPermissions(): Promise<GetPermissionsResponse> {
  const response = await apiClient.get<BackendPermission[]>(`${API_BASE}/permissions`);
  
  return {
    permissions: response.data.map(perm => ({
      id: perm.id,
      name: perm.name,
      code: perm.code,
      description: perm.description,
      category: perm.category,
      defaultRoles: perm.default_roles as TeamMember['role'][],
    })),
  };
}

export async function apiGetRolePermissions(accountId: number): Promise<GetRolePermissionsResponse> {
  const response = await apiClient.get<{
    configs: Array<{
      role: string;
      permissions: string[];
      allowed_actions: string[];
      restricted_actions: string[];
    }>;
  }>(`${API_BASE}/account/${accountId}/role-permissions`);
  
  return {
    configs: response.data.configs.map(config => ({
      role: config.role as TeamMember['role'],
      permissions: config.permissions,
      allowedActions: config.allowed_actions,
      restrictedActions: config.restricted_actions,
    })),
  };
}

export async function apiUpdateRolePermissions(
  accountId: number,
  request: UpdateRolePermissionsRequest
): Promise<void> {
  await apiClient.put(`${API_BASE}/account/${accountId}/role-permissions`, {
    configs: request.configs?.map(config => ({
      role: config.role,
      permissions: config.permissions,
      allowed_actions: config.allowedActions,
      restricted_actions: config.restrictedActions,
    })) ?? [],
  });
}
