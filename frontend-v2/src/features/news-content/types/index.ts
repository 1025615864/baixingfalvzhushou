/**
 * News Content 类型定义
 * 新闻内容管理和 AI 辅助编辑的类型
 */

// ============ 文章相关类型 ============

export interface ArticleEditor {
  id: string;
  title: string;
  content: string;
  excerpt?: string;
  summary?: string;
  coverImage?: string;
  authorId: string;
  authorName?: string;
  categoryId?: string;
  categoryName?: string;
  tags: string[];
  status: 'draft' | 'published' | 'archived';
  viewCount: number;
  likeCount: number;
  commentCount: number;
  favoriteCount: number;
  isFavorited: boolean;
  createdAt: string;
  updatedAt: string;
  publishedAt?: string;
  isPublished: boolean;
  isTop: boolean;
  source?: string;
  sourceUrl?: string;
  sourceSite?: string;
  aiSummary?: string;
  aiKeywords?: string[];
  aiQualityScore?: number;
  aiRiskLevel?: AiRiskLevel;
  aiAnnotation?: NewsAIAnnotation;
  seoTitle?: string;
  seoDescription?: string;
}

export type AiRiskLevel = 'none' | 'low' | 'medium' | 'high';

export interface NewsAIAnnotation {
  summary: string | null;
  riskLevel: string;
  sensitiveWords: string[];
  highlights: string[];
  keywords: string[];
  duplicateOfNewsId: string | null;
  processedAt: string | null;
}

export interface ArticleDraft {
  id: string;
  title: string;
  content: string;
  excerpt?: string;
  coverImage?: string;
  categoryId?: string;
  tags: string[];
  status: 'draft';
  seoTitle?: string;
  seoDescription?: string;
  autoSavedAt: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateArticleRequest {
  title: string;
  content: string;
  excerpt?: string;
  coverImage?: string;
  categoryId?: string;
  tags?: string[];
  seoTitle?: string;
  seoDescription?: string;
}

export interface UpdateArticleRequest {
  title?: string;
  content?: string;
  excerpt?: string;
  coverImage?: string;
  categoryId?: string;
  tags?: string[];
  seoTitle?: string;
  seoDescription?: string;
}

// ============ 分类相关类型 ============

export interface NewsCategory {
  id: string;
  name: string;
  slug: string;
  description?: string;
  icon?: string;
  parentId?: string;
  articleCount: number;
  sortOrder: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateCategoryRequest {
  name: string;
  description?: string;
  icon?: string;
  sortOrder?: number;
}

export interface UpdateCategoryRequest {
  name?: string;
  description?: string;
  icon?: string;
  sortOrder?: number;
  isActive?: boolean;
}

// ============ 标签相关类型 ============

export interface NewsTag {
  id: string;
  name: string;
  slug: string;
  description?: string;
  count: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateTagRequest {
  name: string;
  slug?: string;
  description?: string;
}

export interface UpdateTagRequest {
  name?: string;
  slug?: string;
  description?: string;
}

// ============ AI 辅助相关类型 ============

export interface AIContentAssistance {
  summary?: string;
  keywords?: string[];
  improvedContent?: string;
  qualityScore?: number;
  suggestions?: string[];
  seoTitle?: string;
  seoDescription?: string;
  riskLevel?: AiRiskLevel;
  sensitiveWords?: string[];
  highlights?: string[];
  generatedAt?: string;
}

export interface AIImproveOptions {
  focus?: 'clarity' | 'engagement' | 'seo' | 'professional';
  tone?: 'formal' | 'casual' | 'persuasive';
}

export interface AIGenerateRequest {
  prompt: string;
  style?: 'news' | 'report' | 'social';
  length?: 'short' | 'medium' | 'long';
}

export interface AIGenerateResponse {
  content: string;
  title: string;
}

// ============ 图片相关类型 ============

export interface UploadImageResponse {
  id: string;
  url: string;
  thumbnailUrl?: string;
  alt?: string;
  width?: number;
  height?: number;
}

export interface ImageGalleryItem {
  id: string;
  url: string;
  thumbnailUrl?: string;
  alt?: string;
  width?: number;
  height?: number;
  createdAt: string;
}

// ============ 列表相关类型 ============

export interface ArticleListParams {
  page?: number;
  pageSize?: number;
  status?: 'draft' | 'published' | 'archived';
  categoryId?: string;
  keyword?: string;
  authorId?: string;
}

export interface ArticleListResponse {
  items: ArticleEditor[];
  total: number;
  page: number;
  pageSize: number;
}

export interface DraftListParams {
  page?: number;
  pageSize?: number;
}

export interface DraftListResponse {
  items: ArticleDraft[];
  total: number;
}

export interface TagListParams {
  page?: number;
  pageSize?: number;
  keyword?: string;
}

export interface TagListResponse {
  items: NewsTag[];
  total: number;
}
