import { apiClient } from '@/shared/lib/api/client';
import type {
  LawFirm,
  CreateLawFirmRequest,
  UpdateLawFirmRequest,
} from '../types';
import type { LawFirmResponseSnake } from '../types';

const LAWFIRM_API_BASE = '/lawfirm';

function transformLawFirm(data: LawFirmResponseSnake): LawFirm {
  return {
    id: String(data.id),
    name: data.name,
    city: data.city,
    phone: data.phone,
    address: data.address,
    description: data.description,
    isVerified: data.is_verified,
    isActive: data.is_active,
    lawyerCount: data.lawyer_count,
    rating: data.rating,
    createdAt: data.created_at,
  };
}

export async function getMyLawFirm(): Promise<LawFirm> {
  const { data } = await apiClient.get<LawFirmResponseSnake>(`${LAWFIRM_API_BASE}`);
  return transformLawFirm(data);
}

export async function createLawFirm(request: CreateLawFirmRequest): Promise<LawFirm> {
  const response = await apiClient.post<LawFirmResponseSnake>(`${LAWFIRM_API_BASE}`, {
    name: request.name,
    city: request.city,
    phone: request.phone,
    address: request.address,
    description: request.description,
  });
  return transformLawFirm(response.data);
}

export async function updateLawFirm(request: UpdateLawFirmRequest): Promise<LawFirm> {
  const response = await apiClient.put<LawFirmResponseSnake>(`${LAWFIRM_API_BASE}`, {
    name: request.name,
    city: request.city,
    phone: request.phone,
    address: request.address,
    description: request.description,
  });
  return transformLawFirm(response.data);
}

export async function getLawFirmMembers(params: {
  page?: number;
  pageSize?: number;
  role?: string;
}): Promise<{ items: LawFirm['id'][]; total: number }> {
  const { data } = await apiClient.get<{
    items: { id: number }[];
    total: number;
  }>(`${LAWFIRM_API_BASE}/members`, {
    params: {
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
      ...(params.role && { role: params.role }),
    },
  });
  return {
    items: data.items.map((item) => String(item.id)),
    total: data.total,
  };
}

export async function getLawFirms(params: {
  keyword?: string;
  includeInactive?: boolean;
} = {}): Promise<LawFirm[]> {
  const { data } = await apiClient.get<{ items: LawFirmResponseSnake[] }>(
    `${LAWFIRM_API_BASE}/admin/firms`,
    {
      params: {
        ...(params.includeInactive && { include_inactive: 'true' }),
        ...(params.keyword && { keyword: params.keyword }),
      },
    }
  );
  return (data.items ?? []).map(transformLawFirm);
}

export async function createLawFirmAdmin(request: CreateLawFirmRequest): Promise<LawFirm> {
  const response = await apiClient.post<LawFirmResponseSnake>(`${LAWFIRM_API_BASE}/admin/firms`, {
    name: request.name,
    city: request.city,
    phone: request.phone,
    address: request.address,
    description: request.description,
  });
  return transformLawFirm(response.data);
}

export async function updateLawFirmAdmin(id: string, request: UpdateLawFirmRequest): Promise<LawFirm> {
  const response = await apiClient.put<LawFirmResponseSnake>(
    `${LAWFIRM_API_BASE}/admin/firms/${id}`,
    {
      name: request.name,
      city: request.city,
      phone: request.phone,
      address: request.address,
      description: request.description,
    }
  );
  return transformLawFirm(response.data);
}

export async function deleteLawFirmAdmin(id: string): Promise<void> {
  await apiClient.delete(`${LAWFIRM_API_BASE}/admin/firms/${id}`);
}

export async function verifyLawFirmAdmin(id: string, verified: boolean): Promise<LawFirm> {
  const response = await apiClient.post<LawFirmResponseSnake>(
    `${LAWFIRM_API_BASE}/admin/firms/${id}/verify`,
    { verified }
  );
  return transformLawFirm(response.data);
}

export async function toggleLawFirmActiveAdmin(id: string, isActive: boolean): Promise<LawFirm> {
  const response = await apiClient.post<LawFirmResponseSnake>(
    `${LAWFIRM_API_BASE}/admin/firms/${id}/active`,
    { is_active: isActive }
  );
  return transformLawFirm(response.data);
}
