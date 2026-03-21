import { apiClient } from '@/shared/lib/api/client';
import type {
  Lawyer,
  GetLawyersRequest,
  GetLawyersResponse,
} from '../types';
import { transformLawyer } from './transforms';
import type { LawyerResponseSnake } from '../types';

const API_BASE = '/lawyers';

export async function getLawyers(params: GetLawyersRequest = {}): Promise<GetLawyersResponse> {
  const { data } = await apiClient.get<{
    items: LawyerResponseSnake[];
    total: number;
    page: number;
    page_size: number;
  }>(`/lawyers`, {
    params: {
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
      ...(params.firmId && { firm_id: params.firmId }),
      ...(params.specialty && { specialty: params.specialty }),
      ...(params.keyword && { keyword: params.keyword }),
    },
  });

  return {
    lawyers: data.items.map(transformLawyer),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

export async function getLawyer(lawyerId: string): Promise<Lawyer> {
  const { data } = await apiClient.get<LawyerResponseSnake>(`/lawyers/${lawyerId}`);
  return transformLawyer(data);
}

export async function getLawyerRanking(params: {
  specialty?: string;
  period?: 'day' | 'week' | 'month' | 'all';
  limit?: number;
}): Promise<{ items: Lawyer[]; period: string }> {
  const { data } = await apiClient.get<{
    items: LawyerResponseSnake[];
    period: string;
  }>(`${API_BASE}/ranking`, {
    params: {
      ...(params.specialty && { specialty: params.specialty }),
      ...(params.period && { period: params.period }),
      ...(params.limit && { limit: params.limit }),
    },
  });

  return {
    items: data.items.map(transformLawyer),
    period: data.period,
  };
}
