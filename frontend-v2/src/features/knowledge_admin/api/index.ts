/**
 * Knowledge-Admin（知识库管理）API 层
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  KnowledgeArticle,
  KnowledgeCategory,
  KnowledgeStats,
  GetArticlesRequest,
  GetArticlesResponse,
  CreateArticleRequest,
  CreateArticleResponse,
  UpdateArticleRequest,
  UpdateArticleResponse,
  DeleteArticleResponse,
  CreateCategoryRequest,
  CreateCategoryResponse,
  GetStatsResponse,
  SearchKnowledgeRequest,
  SearchKnowledgeResponse,
  BatchImportRequest,
  BatchImportResponse,
  ImportSampleResponse,
} from '../types';



// API 基础路径
const API_BASE = '/knowledge';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
  message?: string;
}

/**
 * 安全获取 JSON 响应
 */
async function safeJson<T>(response: Response): Promise<T> {
  const data = await response.json() as T;
  return data;
}

/**
 * 获取 API 错误信息
 */
function getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiErrorResponse).detail || defaultMsg;
  }
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return (error as ApiErrorResponse).message || defaultMsg;
  }
  return defaultMsg;
}

/**
 * 获取文章列表
 */
export async function apiGetArticles(request: GetArticlesRequest = {}): Promise<GetArticlesResponse> {
  const searchParams = new URLSearchParams();
  if (request.page) searchParams.set('page', String(request.page));
  if (request.pageSize) searchParams.set('page_size', String(request.pageSize));
  if (request.knowledgeType) searchParams.set('knowledge_type', request.knowledgeType);
  if (request.category) searchParams.set('category', request.category);
  if (request.keyword) searchParams.set('keyword', request.keyword);

  const url = `${API_BASE}/articles${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取文章列表失败' }));
    throw new Error(getErrorMessage(error, '获取文章列表失败'));
  }

  return safeJson<GetArticlesResponse>(response);
}

/**
 * 获取单篇文章
 */
export async function apiGetArticle(articleId: number): Promise<KnowledgeArticle> {
  const response = await fetch(`${API_BASE}/articles/${articleId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取文章详情失败' }));
    throw new Error(getErrorMessage(error, '获取文章详情失败'));
  }

  return safeJson<KnowledgeArticle>(response);
}

/**
 * 创建文章
 */
export async function apiCreateArticle(request: CreateArticleRequest): Promise<KnowledgeArticle> {
  const response = await apiClient.post<CreateArticleResponse>(`${API_BASE}/articles`, {
    knowledge_type: request.knowledgeType,
    title: request.title,
    article_number: request.articleNumber,
    content: request.content,
    summary: request.summary,
    category: request.category,
    keywords: request.keywords,
    source: request.source,
    source_version: request.sourceVersion,
    effective_date: request.effectiveDate,
  });

  return response.data.article;
}

/**
 * 更新文章
 */
export async function apiUpdateArticle(
  articleId: number,
  request: UpdateArticleRequest
): Promise<KnowledgeArticle> {
  const response = await apiClient.put<UpdateArticleResponse>(`${API_BASE}/articles/${articleId}`, {
    knowledge_type: request.knowledgeType,
    title: request.title,
    article_number: request.articleNumber,
    content: request.content,
    summary: request.summary,
    category: request.category,
    keywords: request.keywords,
    source: request.source,
    source_version: request.sourceVersion,
    effective_date: request.effectiveDate,
  });

  return response.data.article;
}

/**
 * 删除文章
 */
export async function apiDeleteArticle(articleId: number): Promise<boolean> {
  const response = await apiClient.delete<DeleteArticleResponse>(`${API_BASE}/articles/${articleId}`);
  return response.data.success;
}

/**
 * 获取分类列表
 */
export async function apiGetCategories(includeCount = false): Promise<KnowledgeCategory[]> {
  const searchParams = new URLSearchParams();
  if (includeCount) searchParams.set('include_count', 'true');

  const url = `${API_BASE}/categories${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取分类列表失败' }));
    throw new Error(getErrorMessage(error, '获取分类列表失败'));
  }

  // 后端返回的是 Record<string, number> 格式
  const data = await response.json() as Record<string, number>;
  
  // 转换为 KnowledgeCategory 数组
  return Object.entries(data).map(([name, count], index) => ({
    id: index + 1,
    name,
    description: null,
    sortOrder: index,
    articleCount: count,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }));
}

/**
 * 创建分类
 */
export async function apiCreateCategory(request: CreateCategoryRequest): Promise<KnowledgeCategory> {
  const response = await apiClient.post<CreateCategoryResponse>(`${API_BASE}/categories`, {
    name: request.name,
    description: request.description,
    sort_order: request.sortOrder,
  });

  return response.data.category;
}

/**
 * 获取知识库统计
 */
export async function apiGetStats(): Promise<KnowledgeStats> {
  const response = await apiClient.get<GetStatsResponse>(`${API_BASE}/stats`);

  const data = response.data;
  return data.stats;
}

/**
 * 搜索知识
 */
export async function apiSearchKnowledge(request: SearchKnowledgeRequest): Promise<SearchKnowledgeResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set('keyword', request.keyword);
  if (request.knowledgeType) searchParams.set('knowledge_type', request.knowledgeType);
  if (request.category) searchParams.set('category', request.category);
  if (request.page) searchParams.set('page', String(request.page));
  if (request.pageSize) searchParams.set('page_size', String(request.pageSize));

  const response = await apiClient.get<SearchKnowledgeResponse>(`${API_BASE}/search?${searchParams.toString()}`);

  return response.data;
}

/**
 * 批量导入知识
 */
export async function apiBatchImport(request: BatchImportRequest): Promise<BatchImportResponse> {
  const response = await apiClient.post<BatchImportResponse>(`${API_BASE}/batch/import`, request.items);
  return response.data;
}

/**
 * 导入示例数据
 */
export async function apiImportSample(): Promise<ImportSampleResponse> {
  const response = await apiClient.post<ImportSampleResponse>(`${API_BASE}/import/sample`);
  return response.data;
}