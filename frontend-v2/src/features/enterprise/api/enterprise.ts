import { apiClient } from '@/shared/lib/api/client';
import type { EnterpriseInfo, UpdateEnterpriseInfoRequest, UpdateEnterpriseInfoResponse } from '../types';
import { mapBackendToEnterpriseInfo, type BackendEnterpriseInfo } from './transforms';

const API_BASE = '/enterprise';

export async function apiGetEnterpriseInfo(accountId: number): Promise<EnterpriseInfo> {
  const response = await apiClient.get<BackendEnterpriseInfo>(`${API_BASE}/account/${accountId}`);
  return mapBackendToEnterpriseInfo(response.data);
}

export async function apiUpdateEnterpriseInfo(
  accountId: number,
  request: UpdateEnterpriseInfoRequest
): Promise<UpdateEnterpriseInfoResponse> {
  const response = await apiClient.post<{
    success: boolean;
    enterprise: BackendEnterpriseInfo;
  }>(`${API_BASE}/account/${accountId}/update`, {
    company_name: request.companyName,
    industry: request.industry,
    scale: request.scale,
    subscription_plan: request.subscriptionPlan,
    contact_phone: request.contactPhone,
    contact_name: request.contactName,
    address: request.address,
    website: request.website,
    description: request.description,
  });
  
  return {
    success: response.data.success,
    enterprise: mapBackendToEnterpriseInfo(response.data.enterprise),
  };
}
