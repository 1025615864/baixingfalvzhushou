/**
 * News Content API
 * 新闻内容管理和 AI 辅助编辑的 API 接口
 */

import { api } from '@/shared/lib/api/client';

import type {
  ArticleEditor,
  NewsCategory,
  NewsTag,
  AIContentAssistance,
  ArticleDraft,
  CreateArticleRequest,
  UpdateArticleRequest,
  UploadImageResponse,
} from '../types';

// ============ API 端点 ============

const endpoints = {
  // 文章管理
  list: '/news-content/articles',
  get: (id: string) => `/news-content/articles/${id}`,
  create: '/news-content/articles',
  update: (id: string) => `/news-content/articles/${id}`,
  delete: (id: string) => `/news-content/articles/${id}`,
  publish: (id: string) => `/news-content/articles/${id}/publish`,
  archive: (id: string) => `/news-content/articles/${id}/archive`,

  // 草稿管理
  drafts: '/news-content/drafts',
  getDraft: (id: string) => `/news-content/drafts/${id}`,
  saveDraft: '/news-content/drafts',
  deleteDraft: (id: string) => `/news-content/drafts/${id}`,

  // 分类管理
  categories: '/news-content/categories',
  getCategory: (id: string) => `/news-content/categories/${id}`,
  createCategory: '/news-content/categories',
  updateCategory: (id: string) => `/news-content/categories/${id}`,
  deleteCategory: (id: string) => `/news-content/categories/${id}`,
  reorderCategories: '/news-content/categories/reorder',

  // 标签管理
  tags: '/news-content/tags',
  getTag: (id: string) => `/news-content/tags/${id}`,
  createTag: '/news-content/tags',
  updateTag: (id: string) => `/news-content/tags/${id}`,
  deleteTag: (id: string) => `/news-content/tags/${id}`,

  // AI 辅助
  aiSummary: (id: string) => `/news-content/articles/${id}/ai-summary`,
  aiAnalysis: (id: string) => `/news-content/articles/${id}/ai-analysis`,
  aiTags: (id: string) => `/news-content/articles/${id}/ai-tags`,
  aiImprove: (id: string) => `/news-content/articles/${id}/ai-improve`,
  aiGenerate: '/news-content/ai-generate',

  // 图片管理
  uploadImage: '/news-content/images',
  deleteImage: (id: string) => `/news-content/images/${id}`,
};

// ============ API 函数 ============

export const newsContentApi = {
  // 文章管理
  list: async (params?: {
    page?: number;
    pageSize?: number;
    status?: 'draft' | 'published' | 'archived';
    categoryId?: string;
    keyword?: string;
    authorId?: string;
  }): Promise<{
    items: ArticleEditor[];
    total: number;
    page: number;
    pageSize: number;
  }> => {
    return api.get(endpoints.list, { params });
  },

  get: async (id: string): Promise<ArticleEditor> => {
    return api.get(endpoints.get(id));
  },

  create: async (data: CreateArticleRequest): Promise<ArticleEditor> => {
    return api.post(endpoints.create, data);
  },

  update: async (id: string, data: UpdateArticleRequest): Promise<ArticleEditor> => {
    return api.patch(endpoints.update(id), data);
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(endpoints.delete(id));
  },

  publish: async (id: string): Promise<ArticleEditor> => {
    return api.post(endpoints.publish(id));
  },

  archive: async (id: string): Promise<ArticleEditor> => {
    return api.post(endpoints.archive(id));
  },

  // 草稿管理
  getDrafts: async (params?: { page?: number; pageSize?: number }): Promise<{ items: ArticleDraft[]; total: number }> => {
    return api.get(endpoints.drafts, { params });
  },

  getDraft: async (id: string): Promise<ArticleDraft> => {
    return api.get(endpoints.getDraft(id));
  },

  saveDraft: async (data: Partial<ArticleDraft>): Promise<ArticleDraft> => {
    return api.post(endpoints.saveDraft, data);
  },

  deleteDraft: async (id: string): Promise<void> => {
    await api.delete(endpoints.deleteDraft(id));
  },

  // 分类管理
  getCategories: async (): Promise<NewsCategory[]> => {
    return api.get(endpoints.categories);
  },

  getCategory: async (id: string): Promise<NewsCategory> => {
    return api.get(endpoints.getCategory(id));
  },

  createCategory: async (data: { name: string; description?: string; icon?: string; sortOrder?: number }): Promise<NewsCategory> => {
    return api.post(endpoints.createCategory, data);
  },

  updateCategory: async (
    id: string,
    data: { name?: string; description?: string; icon?: string; sortOrder?: number; isActive?: boolean }
  ): Promise<NewsCategory> => {
    return api.patch(endpoints.updateCategory(id), data);
  },

  deleteCategory: async (id: string): Promise<void> => {
    await api.delete(endpoints.deleteCategory(id));
  },

  reorderCategories: async (categoryIds: string[]): Promise<void> => {
    await api.post(endpoints.reorderCategories, { categoryIds });
  },

  // 标签管理
  getTags: async (params?: { page?: number; pageSize?: number; keyword?: string }): Promise<{ items: NewsTag[]; total: number }> => {
    return api.get(endpoints.tags, { params });
  },

  getTag: async (id: string): Promise<NewsTag> => {
    return api.get(endpoints.getTag(id));
  },

  createTag: async (data: { name: string; slug?: string; description?: string }): Promise<NewsTag> => {
    return api.post(endpoints.createTag, data);
  },

  updateTag: async (id: string, data: { name?: string; slug?: string; description?: string }): Promise<NewsTag> => {
    return api.patch(endpoints.updateTag(id), data);
  },

  deleteTag: async (id: string): Promise<void> => {
    await api.delete(endpoints.deleteTag(id));
  },

  // AI 辅助
  getAISummary: async (articleId: string): Promise<AIContentAssistance> => {
    return api.get(endpoints.aiSummary(articleId));
  },

  getAIAnalysis: async (articleId: string): Promise<AIContentAssistance> => {
    return api.get(endpoints.aiAnalysis(articleId));
  },

  getAITags: async (articleId: string): Promise<AIContentAssistance> => {
    return api.get(endpoints.aiTags(articleId));
  },

  improveWithAI: async (
    articleId: string,
    options?: { focus?: 'clarity' | 'engagement' | 'seo' | 'professional'; tone?: 'formal' | 'casual' | 'persuasive' }
  ): Promise<AIContentAssistance> => {
    return api.post(endpoints.aiImprove(articleId), options);
  },

  generateWithAI: async (prompt: string, options?: { style?: 'news' | 'report' | 'social'; length?: 'short' | 'medium' | 'long' }): Promise<{ content: string; title: string }> => {
    return api.post(endpoints.aiGenerate, { prompt, ...options });
  },

  // 图片管理
  uploadImage: async (file: File): Promise<UploadImageResponse> => {
    const formData = new FormData();
    formData.append('image', file);
    return api.post(endpoints.uploadImage, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  },

  deleteImage: async (id: string): Promise<void> => {
    await api.delete(endpoints.deleteImage(id));
  },
};
