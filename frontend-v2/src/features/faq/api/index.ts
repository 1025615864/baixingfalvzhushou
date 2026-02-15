/**
 * FAQ（常见问题）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/faq 端点
 */

import { api } from "@/shared/lib/api/client";

import type {
  FAQItem,
  FAQListResponse,
  FAQSmartSearchResult,
  CreateFAQRequest,
  UpdateFAQRequest,
  FAQSearchParams,
  FAQSmartSearchRequest,
} from '../types';

// API 基础路径
const API_BASE = '/faq';

// ==================== 后端响应类型定义 ====================

/** 后端FAQ响应 */
interface BackendFAQResponse {
  id: number;
  question: string;
  answer: string;
  category: string | null;
  tags: string[] | null;
  priority: number;
  is_active: boolean;
  view_count: number;
  created_at: string;
  updated_at: string;
}

/** 后端FAQ列表响应 */
interface BackendFAQListResponse {
  items: BackendFAQResponse[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端FAQ分类响应 */
interface BackendFAQCategoryResponse {
  categories: string[];
}

/** 后端热门FAQ响应 */
interface BackendFAQPopularResponse {
  items: BackendFAQResponse[];
}

/** 后端FAQ智能搜索响应 */
interface BackendFAQSmartSearchResponse {
  matched: boolean;
  answer: string | null;
  faq_id: number | null;
  confidence: number;
  suggestions: BackendFAQResponse[];
}

// ==================== 转换函数 ====================

/**
 * 转换后端FAQ到前端格式
 */
function mapBackendToFAQ(data: BackendFAQResponse): FAQItem {
  return {
    id: data.id,
    question: data.question,
    answer: data.answer,
    category: data.category,
    tags: data.tags,
    priority: data.priority,
    isActive: data.is_active,
    viewCount: data.view_count,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

// ==================== 公开API ====================

/**
 * 搜索FAQ列表
 */
export async function apiGetFAQs(params: FAQSearchParams = {}): Promise<FAQListResponse> {
  const data = await api.get<BackendFAQListResponse>(`${API_BASE}/search`, {
    params: {
      keyword: params.keyword,
      category: params.category,
      tags: params.tags?.join(','),
      page: params.page,
      page_size: params.pageSize,
    },
  });

  return {
    items: data.items.map(mapBackendToFAQ),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

/**
 * 获取FAQ详情
 */
export async function apiGetFAQ(id: number): Promise<FAQItem> {
  const data = await api.get<BackendFAQResponse>(`${API_BASE}/${id}`);
  return mapBackendToFAQ(data);
}

/**
 * 获取FAQ分类列表
 */
export async function apiGetFAQCcategories(): Promise<string[]> {
  const data = await api.get<BackendFAQCategoryResponse>(`${API_BASE}/categories`);
  return data.categories;
}

/**
 * 获取热门FAQ
 */
export async function apiGetPopularFAQs(category?: string, limit: number = 10): Promise<FAQItem[]> {
  const data = await api.get<BackendFAQPopularResponse>(`${API_BASE}/popular`, {
    params: {
      category,
      limit,
    },
  });

  return data.items.map(mapBackendToFAQ);
}

/**
 * FAQ智能搜索
 */
export async function apiSmartSearchFAQ(request: FAQSmartSearchRequest): Promise<FAQSmartSearchResult> {
  const data = await api.post<BackendFAQSmartSearchResponse>(`${API_BASE}/smart-search`, {
    question: request.question,
    category: request.category,
    limit: request.limit,
  });

  return {
    matched: data.matched,
    answer: data.answer,
    faqId: data.faq_id,
    confidence: data.confidence,
    suggestions: data.suggestions.map(mapBackendToFAQ),
  };
}

// ==================== 管理员API ====================

/**
 * 管理员-创建FAQ
 */
export async function apiCreateFAQ(request: CreateFAQRequest): Promise<FAQItem> {
  const data = await api.post<BackendFAQResponse>(`${API_BASE}/admin/faqs`, {
    question: request.question,
    answer: request.answer,
    category: request.category,
    tags: request.tags,
    priority: request.priority,
    is_active: request.isActive,
  });

  return mapBackendToFAQ(data);
}

/**
 * 管理员-更新FAQ
 */
export async function apiUpdateFAQ(id: number, request: UpdateFAQRequest): Promise<FAQItem> {
  const data = await api.put<BackendFAQResponse>(`${API_BASE}/admin/faqs/${id}`, {
    question: request.question,
    answer: request.answer,
    category: request.category,
    tags: request.tags,
    priority: request.priority,
    is_active: request.isActive,
  });

  return mapBackendToFAQ(data);
}

/**
 * 管理员-删除FAQ
 */
export async function apiDeleteFAQ(id: number): Promise<void> {
  await api.delete(`${API_BASE}/admin/faqs/${id}`);
}

/**
 * 管理员-获取FAQ列表（包含未激活的）
 */
export async function apiGetAdminFAQs(params: FAQSearchParams = {}): Promise<FAQListResponse> {
  const data = await api.get<BackendFAQListResponse>(`${API_BASE}/admin/faqs`, {
    params: {
      keyword: params.keyword,
      category: params.category,
      page: params.page,
      page_size: params.pageSize,
    },
  });

  return {
    items: data.items.map(mapBackendToFAQ),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}
