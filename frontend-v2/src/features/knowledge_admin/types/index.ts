/**
 * Knowledge-Admin（知识库管理）类型定义
 */

// ==================== 核心类型 ====================

/** 知识类型 */
export type KnowledgeType = 'law' | 'case' | 'regulation' | 'interpretation';

/** 知识类型显示名称 */
export const KnowledgeTypeLabels: Record<KnowledgeType, string> = {
  law: '法律法规',
  case: '典型案例',
  regulation: '规章制度',
  interpretation: '司法解释',
};

/** 文章状态 */
export type ArticleStatus = 'draft' | 'published' | 'archived';

/** 文章状态显示名称 */
export const ArticleStatusLabels: Record<ArticleStatus, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
};

/** 知识库文章 */
export interface KnowledgeArticle {
  id: number;
  knowledgeType: KnowledgeType;
  title: string;
  articleNumber: string | null;
  content: string;
  summary: string | null;
  category: string;
  keywords: string | null;
  source: string | null;
  sourceVersion: string | null;
  effectiveDate: string | null;
  isVectorized: boolean;
  createdAt: string;
  updatedAt: string;
}

/** 知识库文章列表项（简化版） */
export interface KnowledgeArticleListItem {
  id: number;
  knowledgeType: KnowledgeType;
  title: string;
  articleNumber: string | null;
  summary: string | null;
  category: string;
  keywords: string | null;
  isVectorized: boolean;
  createdAt: string;
}

/** 知识库分类 */
export interface KnowledgeCategory {
  id: number;
  name: string;
  description: string | null;
  sortOrder: number;
  articleCount: number;
  createdAt: string;
  updatedAt: string;
}

/** 知识库统计 */
export interface KnowledgeStats {
  totalArticles: number;
  totalCategories: number;
  vectorizedCount: number;
  byType: Record<KnowledgeType, number>;
  byCategory: Record<string, number>;
  recentAdditions: number;
}

/** 批量导入结果 */
export interface BatchImportResult {
  success: number;
  failed: number;
  total: number;
  message: string;
}

// ==================== API 请求/响应类型 ====================

/** 获取文章列表请求 */
export interface GetArticlesRequest {
  page?: number;
  pageSize?: number;
  knowledgeType?: KnowledgeType;
  category?: string;
  keyword?: string;
}

/** 获取文章列表响应 */
export interface GetArticlesResponse {
  items: KnowledgeArticleListItem[];
  total: number;
  page: number;
  pageSize: number;
}

/** 获取单篇文章请求 */
export interface GetArticleRequest {
  articleId: number;
}

/** 获取单篇文章响应 */
export interface GetArticleResponse {
  article: KnowledgeArticle;
}

/** 创建文章请求 */
export interface CreateArticleRequest {
  knowledgeType: KnowledgeType;
  title: string;
  articleNumber?: string | null;
  content: string;
  summary?: string | null;
  category: string;
  keywords?: string | null;
  source?: string | null;
  sourceVersion?: string | null;
  effectiveDate?: string | null;
}

/** 创建文章响应 */
export interface CreateArticleResponse {
  article: KnowledgeArticle;
}

/** 更新文章请求 */
export interface UpdateArticleRequest {
  knowledgeType?: KnowledgeType;
  title?: string;
  articleNumber?: string | null;
  content?: string;
  summary?: string | null;
  category?: string;
  keywords?: string | null;
  source?: string | null;
  sourceVersion?: string | null;
  effectiveDate?: string | null;
}

/** 更新文章响应 */
export interface UpdateArticleResponse {
  article: KnowledgeArticle;
}

/** 删除文章请求 */
export interface DeleteArticleRequest {
  articleId: number;
}

/** 删除文章响应 */
export interface DeleteArticleResponse {
  success: boolean;
}

/** 获取分类列表请求 */
export interface GetCategoriesRequest {
  includeCount?: boolean;
}

/** 获取分类列表响应 */
export interface GetCategoriesResponse {
  categories: KnowledgeCategory[];
}

/** 创建分类请求 */
export interface CreateCategoryRequest {
  name: string;
  description?: string | null;
  sortOrder?: number;
}

/** 创建分类响应 */
export interface CreateCategoryResponse {
  category: KnowledgeCategory;
}

/** 更新分类请求 */
export interface UpdateCategoryRequest {
  name?: string;
  description?: string | null;
  sortOrder?: number;
}

/** 更新分类响应 */
export interface UpdateCategoryResponse {
  category: KnowledgeCategory;
}

/** 删除分类请求 */
export interface DeleteCategoryRequest {
  categoryId: number;
}

/** 删除分类响应 */
export interface DeleteCategoryResponse {
  success: boolean;
}

/** 获取统计信息响应 */
export interface GetStatsResponse {
  stats: KnowledgeStats;
}

/** 搜索知识请求 */
export interface SearchKnowledgeRequest {
  keyword: string;
  knowledgeType?: KnowledgeType;
  category?: string;
  page?: number;
  pageSize?: number;
}

/** 搜索知识响应 */
export interface SearchKnowledgeResponse {
  items: KnowledgeArticleListItem[];
  total: number;
  page: number;
  pageSize: number;
}

/** 批量导入请求 */
export interface BatchImportRequest {
  items: CreateArticleRequest[];
}

/** 批量导入响应 */
export interface BatchImportResponse extends BatchImportResult {}

/** 导入示例数据响应 */
export interface ImportSampleResponse extends BatchImportResult {}