/**
 * Knowledge（知识库）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/knowledge 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  KnowledgeArticle,
  KnowledgeStats,
  CategoryCount,
  CreateArticleRequest,
  UpdateArticleRequest,
  GetArticlesRequest,
  GetArticlesResponse,
  SearchArticlesRequest,
  SearchArticlesResponse,
  GetCategoriesResponse,
  BatchOperationRequest,
  BatchOperationResponse,
  BatchImportRequest,
  BatchImportResponse,
} from '../types';


// API 基础路径
const API_BASE = '/knowledge';

// ==================== 后端响应类型定义 ====================

/** 后端法律知识条目响应 */
interface BackendKnowledgeArticle {
  id: number;
  knowledge_type: string;
  title: string;
  article_number?: string;
  content: string;
  summary?: string;
  category: string;
  keywords?: string;
  source?: string;
  source_url?: string;
  source_version?: string;
  effective_date?: string;
  weight: number;
  is_active: boolean;
  is_vectorized: boolean;
  created_at: string;
  updated_at: string;
}

/** 后端法律知识列表响应 */
interface BackendKnowledgeListResponse {
  items: BackendKnowledgeArticle[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端搜索响应 */
interface BackendSearchResponse {
  items: Array<{
    id: number;
    knowledge_type: string;
    title: string;
    article_number?: string;
    summary?: string;
    category: string;
    keywords?: string;
    is_vectorized?: boolean;
    created_at: string;
  }>;
  total: number;
  page: number;
  page_size: number;
}

/** 后端分类统计响应 */
interface BackendCategoryCount {
  category: string;
  count: number;
}

/** 后端统计响应 */
interface BackendKnowledgeStats {
  total_laws: number;
  total_cases: number;
  total_regulations: number;
  total_interpretations: number;
  vectorized_count: number;
  categories: BackendCategoryCount[];
}

/** 后端批量操作响应 */
interface BackendBatchOperationResponse {
  success_count: number;
  failed_count: number;
  message: string;
}

/** 后端批量导入响应 */
interface BackendBatchImportResponse {
  success_count: number;
  failed_count: number;
  message: string;
}

// ==================== 转换函数 ====================

/**
 * 转换后端法律知识条目到前端格式
 */
function mapBackendToKnowledgeArticle(data: BackendKnowledgeArticle): KnowledgeArticle {
  return {
    id: String(data.id),
    knowledgeType: data.knowledge_type as KnowledgeArticle['knowledgeType'],
    title: data.title,
    articleNumber: data.article_number,
    content: data.content,
    summary: data.summary,
    category: data.category,
    keywords: data.keywords,
    source: data.source,
    sourceUrl: data.source_url,
    sourceVersion: data.source_version,
    effectiveDate: data.effective_date,
    weight: data.weight,
    isActive: data.is_active,
    isVectorized: data.is_vectorized,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 转换后端分类统计到前端格式
 */
function mapBackendToCategoryCount(data: BackendCategoryCount): CategoryCount {
  return {
    category: data.category,
    count: data.count,
  };
}

// ==================== 法律知识条目 API ====================

/**
 * 创建法律知识条目
 */
export async function apiCreateArticle(request: CreateArticleRequest): Promise<KnowledgeArticle> {
  const response = await apiClient.post<BackendKnowledgeArticle>(`${API_BASE}/laws`, {
    knowledge_type: request.knowledgeType,
    title: request.title,
    article_number: request.articleNumber,
    content: request.content,
    summary: request.summary,
    category: request.category,
    keywords: request.keywords,
    source: request.source,
    source_url: request.sourceUrl,
    effective_date: request.effectiveDate,
    weight: request.weight,
    is_active: request.isActive,
  });

  return mapBackendToKnowledgeArticle(response.data);
}

/**
 * 获取法律知识列表
 */
export async function apiGetArticles(
  params: GetArticlesRequest = {}
): Promise<GetArticlesResponse> {
  const response = await apiClient.get<BackendKnowledgeListResponse>(`${API_BASE}/laws`, {
    params: {
      page: params.page,
      page_size: params.pageSize,
      knowledge_type: params.knowledgeType,
      category: params.category,
      keyword: params.keyword,
      is_active: params.isActive,
    },
  });

  return {
    items: response.data.items.map(mapBackendToKnowledgeArticle),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

/**
 * 获取单个法律知识详情
 */
export async function apiGetArticle(articleId: string): Promise<KnowledgeArticle> {
  const response = await apiClient.get<BackendKnowledgeArticle>(`${API_BASE}/laws/${articleId}`);
  return mapBackendToKnowledgeArticle(response.data);
}

/**
 * 更新法律知识
 */
export async function apiUpdateArticle(
  articleId: string,
  request: UpdateArticleRequest
): Promise<KnowledgeArticle> {
  const response = await apiClient.put<BackendKnowledgeArticle>(`${API_BASE}/laws/${articleId}`, {
    knowledge_type: request.knowledgeType,
    title: request.title,
    article_number: request.articleNumber,
    content: request.content,
    summary: request.summary,
    category: request.category,
    keywords: request.keywords,
    source: request.source,
    source_url: request.sourceUrl,
    effective_date: request.effectiveDate,
    weight: request.weight,
    is_active: request.isActive,
  });

  return mapBackendToKnowledgeArticle(response.data);
}

/**
 * 删除法律知识
 */
export async function apiDeleteArticle(articleId: string): Promise<{ message: string }> {
  await apiClient.delete(`${API_BASE}/laws/${articleId}`);
  return { message: '删除成功' };
}

// ==================== 搜索 API ====================

/**
 * 搜索法律知识
 */
export async function apiSearchArticles(
  params: SearchArticlesRequest
): Promise<SearchArticlesResponse> {
  const response = await apiClient.get<BackendSearchResponse>(`${API_BASE}/search`, {
    params: {
      keyword: params.query,
      category: params.category,
      knowledge_type: params.knowledgeType,
      limit: params.limit,
    },
  });

  return {
    items: response.data.items.map(item => ({
      id: String(item.id),
      knowledgeType: item.knowledge_type as KnowledgeArticle['knowledgeType'],
      title: item.title,
      articleNumber: item.article_number,
      content: '',
      summary: item.summary,
      category: item.category,
      keywords: item.keywords,
      weight: 1,
      isActive: true,
      isVectorized: item.is_vectorized ?? false,
      createdAt: item.created_at,
      updatedAt: item.created_at,
    })),
    total: response.data.total,
  };
}

// ==================== 分类和统计 API ====================

/**
 * 获取知识分类列表
 */
export async function apiGetCategories(): Promise<GetCategoriesResponse> {
  const response = await apiClient.get<string[]>(`${API_BASE}/laws/distinct-categories`);

  return {
    categories: response.data.map((name, index) => ({
      id: String(index),
      name,
      icon: 'Folder',
      sortOrder: index,
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    })),
  };
}

/**
 * 获取知识库统计
 */
export async function apiGetKnowledgeStats(): Promise<KnowledgeStats> {
  const response = await apiClient.get<BackendKnowledgeStats>(`${API_BASE}/stats`);

  return {
    totalLaws: response.data.total_laws,
    totalCases: response.data.total_cases,
    totalRegulations: response.data.total_regulations,
    totalInterpretations: response.data.total_interpretations,
    vectorizedCount: response.data.vectorized_count,
    categories: response.data.categories.map(mapBackendToCategoryCount),
  };
}

// ==================== 批量操作 API ====================

/**
 * 批量删除知识条目
 */
export async function apiBatchDeleteArticles(
  request: BatchOperationRequest
): Promise<BatchOperationResponse> {
  const response = await apiClient.post<BackendBatchOperationResponse>(`${API_BASE}/laws/batch-delete`, {
    ids: request.ids.map((id: string) => parseInt(id, 10)),
  });

  return {
    successCount: response.data.success_count,
    failedCount: response.data.failed_count,
    message: response.data.message,
  };
}

/**
 * 批量导入知识条目
 */
export async function apiBatchImportArticles(
  request: BatchImportRequest
): Promise<BatchImportResponse> {
  const response = await apiClient.post<BackendBatchImportResponse>(`${API_BASE}/laws/batch-import`, {
    items: request.items.map(item => ({
      knowledge_type: item.knowledgeType,
      title: item.title,
      article_number: item.articleNumber,
      content: item.content,
      summary: item.summary,
      category: item.category,
      keywords: item.keywords,
      source: item.source,
      source_url: item.sourceUrl,
      effective_date: item.effectiveDate,
      weight: item.weight,
      is_active: item.isActive,
    })),
    dry_run: request.dryRun,
  });

  return {
    successCount: response.data.success_count,
    failedCount: response.data.failed_count,
    message: response.data.message,
  };
}

// ==================== 向量化 API ====================

/**
 * 向量化知识条目
 */
export async function apiVectorizeArticle(articleId: string): Promise<{ message: string }> {
  await apiClient.post(`${API_BASE}/laws/${articleId}/vectorize`);
  return { message: '向量化成功' };
}

/**
 * 批量向量化知识条目
 */
export async function apiBatchVectorizeArticles(
  request: BatchOperationRequest
): Promise<BatchOperationResponse> {
  const response = await apiClient.post<BackendBatchOperationResponse>(`${API_BASE}/laws/batch-vectorize`, {
    ids: request.ids.map((id: string) => parseInt(id, 10)),
  });

  return {
    successCount: response.data.success_count,
    failedCount: response.data.failed_count,
    message: response.data.message,
  };
}

/**
 * 同步向量库
 */
export async function apiSyncVectorStore(): Promise<BatchOperationResponse> {
  const response = await apiClient.post<BackendBatchOperationResponse>(`${API_BASE}/sync-vector-store`);

  return {
    successCount: response.data.success_count,
    failedCount: response.data.failed_count,
    message: response.data.message,
  };
}

// ==================== 统一导出 ====================

/**
 * Knowledge API 统一导出对象
 */
export const knowledgeApi = {
  // 知识条目管理
  createArticle: apiCreateArticle,
  getArticles: apiGetArticles,
  getArticle: apiGetArticle,
  updateArticle: apiUpdateArticle,
  deleteArticle: apiDeleteArticle,

  // 搜索
  searchArticles: apiSearchArticles,

  // 分类和统计
  getCategories: apiGetCategories,
  getKnowledgeStats: apiGetKnowledgeStats,

  // 批量操作
  batchDeleteArticles: apiBatchDeleteArticles,
  batchImportArticles: apiBatchImportArticles,

  // 向量化
  vectorizeArticle: apiVectorizeArticle,
  batchVectorizeArticles: apiBatchVectorizeArticles,
  syncVectorStore: apiSyncVectorStore,
} as const;

export default knowledgeApi;