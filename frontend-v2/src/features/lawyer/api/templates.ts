import { apiClient } from '@/shared/lib/api/client';
import type {
  LawyerReplyTemplate,
  CreateReplyTemplateRequest,
  UpdateReplyTemplateRequest,
  ReplyTemplateListResponse,
  ReplyTemplateCategoriesResponse,
  UseReplyTemplateResponse,
} from '../types';
import { transformReplyTemplate } from './transforms';
import type { ReplyTemplateResponseSnake } from '../types';

const LAWFIRM_API_BASE = '/lawfirm';

interface GetReplyTemplatesParams {
  category?: string;
  isActive?: boolean;
  page?: number;
  pageSize?: number;
}

export async function getReplyTemplates(params: GetReplyTemplatesParams = {}): Promise<ReplyTemplateListResponse> {
  const { data } = await apiClient.get<{
    items: ReplyTemplateResponseSnake[];
    total: number;
    page: number;
    page_size: number;
  }>(`${LAWFIRM_API_BASE}/lawyer/reply-templates`, {
    params: {
      ...(params.category && { category: params.category }),
      ...(params.isActive !== undefined && { is_active: params.isActive }),
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
    },
  });

  return {
    items: data.items.map(transformReplyTemplate),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

export async function getReplyTemplate(templateId: string): Promise<LawyerReplyTemplate> {
  const response = await apiClient.get<ReplyTemplateResponseSnake>(
    `${LAWFIRM_API_BASE}/lawyer/reply-templates/${templateId}`
  );
  return transformReplyTemplate(response.data);
}

export async function createReplyTemplate(request: CreateReplyTemplateRequest): Promise<LawyerReplyTemplate> {
  const response = await apiClient.post<ReplyTemplateResponseSnake>(
    `${LAWFIRM_API_BASE}/lawyer/reply-templates`,
    {
      title: request.title,
      content: request.content,
      category: request.category,
    }
  );
  return transformReplyTemplate(response.data);
}

export async function updateReplyTemplate(
  templateId: string,
  request: UpdateReplyTemplateRequest
): Promise<LawyerReplyTemplate> {
  const response = await apiClient.put<ReplyTemplateResponseSnake>(
    `${LAWFIRM_API_BASE}/lawyer/reply-templates/${templateId}`,
    {
      title: request.title,
      content: request.content,
      category: request.category,
      is_active: request.isActive,
    }
  );
  return transformReplyTemplate(response.data);
}

export async function deleteReplyTemplate(templateId: string): Promise<void> {
  await apiClient.delete(`${LAWFIRM_API_BASE}/lawyer/reply-templates/${templateId}`);
}

export async function getReplyTemplateCategories(): Promise<ReplyTemplateCategoriesResponse> {
  const response = await apiClient.get<{ categories: string[] }>(
    `${LAWFIRM_API_BASE}/lawyer/reply-templates/categories`
  );
  return { categories: response.data.categories };
}

export async function useReplyTemplate(templateId: string): Promise<UseReplyTemplateResponse> {
  const response = await apiClient.post<{ content: string }>(
    `${LAWFIRM_API_BASE}/lawyer/reply-templates/${templateId}/use`
  );
  return { content: response.data.content };
}
