import { apiClient } from '@/shared/lib/api/client';
import type {
  LawyerPromotionLink,
  CreatePromotionLinkRequest,
  UpdatePromotionLinkRequest,
  PromotionLinkListResponse,
  PromotionLinkStats,
} from '../types';
import { transformPromotionLink, transformPromotionLinkStats } from './transforms';
import type { PromotionLinkResponseSnake, PromotionLinkStatsResponseSnake } from '../types';

const API_BASE = '/lawyers';

export async function getPromotionLinks(): Promise<PromotionLinkListResponse> {
  const { data } = await apiClient.get<{
    items: PromotionLinkResponseSnake[];
    total: number;
  }>(`${API_BASE}/promotion-links`);

  return {
    items: data.items.map(transformPromotionLink),
    total: data.total,
  };
}

export async function createPromotionLink(request: CreatePromotionLinkRequest): Promise<LawyerPromotionLink> {
  const response = await apiClient.post<PromotionLinkResponseSnake>(`${API_BASE}/promotion-links`, {
    link_name: request.linkName,
    description: request.description,
  });

  return transformPromotionLink(response.data);
}

export async function updatePromotionLink(
  linkId: string,
  request: UpdatePromotionLinkRequest
): Promise<LawyerPromotionLink> {
  const response = await apiClient.put<PromotionLinkResponseSnake>(
    `${API_BASE}/promotion-links/${linkId}`,
    {
      link_name: request.linkName,
      description: request.description,
      is_active: request.isActive,
    }
  );

  return transformPromotionLink(response.data);
}

export async function deletePromotionLink(linkId: string): Promise<{ success: boolean }> {
  const response = await apiClient.delete<{ success: boolean }>(
    `${API_BASE}/promotion-links/${linkId}`
  );
  return response.data;
}

export async function getPromotionLinkStats(linkId: string): Promise<PromotionLinkStats> {
  const { data } = await apiClient.get<PromotionLinkStatsResponseSnake>(
    `${API_BASE}/promotion-links/${linkId}/stats`
  );
  return transformPromotionLinkStats(data);
}
