import { apiClient } from '@/shared/lib/api/client';
import type {
  TeamMember,
  GetTeamMembersRequest,
  GetTeamMembersResponse,
  AddTeamMemberRequest,
  AddTeamMemberResponse,
  RemoveTeamMemberRequest,
  UpdateMemberRoleRequest,
} from '../types';
import { mapBackendToTeamMember, type BackendTeamMember } from './transforms';

const API_BASE = '/enterprise';

export async function apiGetTeamMembers(
  accountId: number,
  _params: GetTeamMembersRequest = {}
): Promise<GetTeamMembersResponse> {
  const response = await apiClient.get<{
    users: BackendTeamMember[];
    total: number;
  }>(`${API_BASE}/account/${accountId}/users`);
  
  return {
    members: response.data.users.map(mapBackendToTeamMember),
    total: response.data.total,
  };
}

export async function apiAddTeamMember(
  accountId: number,
  request: AddTeamMemberRequest
): Promise<AddTeamMemberResponse> {
  const response = await apiClient.post<{
    success: boolean;
    member: BackendTeamMember;
    invite_link?: string;
  }>(`${API_BASE}/account/${accountId}/users`, {
    email: request.email,
    name: request.name,
    role: request.role,
  });
  
  return {
    success: response.data.success,
    member: mapBackendToTeamMember(response.data.member),
    inviteLink: response.data.invite_link,
  };
}

export async function apiRemoveTeamMember(
  accountId: number,
  request: RemoveTeamMemberRequest
): Promise<void> {
  await apiClient.delete(`${API_BASE}/account/${accountId}/users/${request.memberId}`);
}

export async function apiUpdateMemberRole(
  accountId: number,
  request: UpdateMemberRoleRequest
): Promise<void> {
  await apiClient.put(`${API_BASE}/account/${accountId}/users/${request.memberId}/role`, {
    role: request.role,
  });
}
