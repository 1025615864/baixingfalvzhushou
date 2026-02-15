/**
 * News（新闻资讯）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/news 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  NewsArticle,
  NewsCategory,
  NewsComment,
  NewsSubscription,
  NewsListItem,
  PaginationMeta,
  GetNewsListRequest,
  SubscribeNewsRequest,
  SearchNewsRequest,
  GetHotNewsRequest,
  GetRecommendedNewsRequest,
  CreateCommentRequest,
} from '../types';


// API 基础路径
const API_BASE = '/news';

// ==================== 后端响应类型定义 ====================

/** 后端返回的作者（snake_case） */
interface BackendAuthor {
  id: string;
  name: string;
  avatar?: string;
}

/** 后端返回的分类（snake_case） */
interface BackendCategory {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  sort_order: number;
  is_active: boolean;
}

/** 后端返回的新闻列表项（snake_case） */
interface BackendNewsListItem {
  id: string;
  title: string;
  summary: string;
  cover_image?: string;
  category_name: string;
  source: string;
  view_count: number;
  favorite_count: number;
  is_favorited: boolean;
  is_top: boolean;
  published_at?: string;
}

/** 后端返回的新闻文章（snake_case） */
interface BackendNewsArticle {
  id: string;
  title: string;
  summary: string;
  content: string;
  cover_image?: string;
  category: BackendCategory;
  source: string;
  source_url?: string;
  author: BackendAuthor;
  view_count: number;
  favorite_count: number;
  is_favorited: boolean;
  ai_risk_level: 'none' | 'low' | 'medium' | 'high';
  is_top: boolean;
  is_published: boolean;
  review_status: 'pending' | 'approved' | 'rejected';
  published_at?: string;
  created_at: string;
  updated_at: string;
}

/** 后端返回的评论（snake_case） */
interface BackendComment {
  id: string;
  news_id: string;
  user_id: string;
  content: string;
  review_status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  author: BackendAuthor;
}

/** 后端返回的订阅（snake_case） */
interface BackendSubscription {
  id: string;
  sub_type: 'category' | 'keyword' | 'author';
  value: string;
  created_at: string;
}

/** 后端新闻列表响应 */
interface BackendNewsListResponse {
  items: BackendNewsListItem[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端评论列表响应 */
interface BackendCommentListResponse {
  items: BackendComment[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端文章详情响应 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface BackendNewsDetailResponse {
  article: BackendNewsArticle;
}

/** 后端评论创建响应 */
interface BackendCommentCreateResponse {
  comment: BackendComment;
}

/** 后端订阅响应 */
interface BackendSubscriptionResponse {
  subscription: BackendSubscription;
}

/** 后端订阅列表响应 */
interface BackendSubscriptionListResponse {
  subscriptions: BackendSubscription[];
}

/** 后端分类列表响应 */
interface BackendCategoryListResponse {
  categories: BackendCategory[];
}

/** 后端收藏响应 */
interface BackendFavoriteResponse {
  is_favorited: boolean;
  favorite_count: number;
}

/** 后端相关新闻响应 */
interface BackendRelatedNewsResponse {
  items: BackendNewsListItem[];
}

// ==================== 转换函数 ====================

/**
 * 转换后端作者到前端格式
 */
function mapBackendToAuthor(author: BackendAuthor): { id: string; name: string; avatar?: string } {
  return {
    id: author.id,
    name: author.name,
    avatar: author.avatar,
  };
}

/**
 * 转换后端分类到前端格式
 */
function mapBackendToCategory(category: BackendCategory): NewsCategory {
  return {
    id: category.id,
    name: category.name,
    description: category.description,
    icon: category.icon,
    sortOrder: category.sort_order,
    isActive: category.is_active,
  };
}

/**
 * 转换后端列表项到前端格式
 */
function mapBackendToNewsListItem(item: BackendNewsListItem): NewsListItem {
  return {
    id: item.id,
    title: item.title,
    summary: item.summary,
    coverImage: item.cover_image,
    categoryName: item.category_name,
    source: item.source,
    viewCount: item.view_count,
    favoriteCount: item.favorite_count,
    isFavorited: item.is_favorited,
    isTop: item.is_top,
    publishedAt: item.published_at,
  };
}

/**
 * 转换后端文章到前端格式
 */
function mapBackendToNewsArticle(article: BackendNewsArticle): NewsArticle {
  return {
    id: article.id,
    title: article.title,
    summary: article.summary,
    content: article.content,
    coverImage: article.cover_image,
    category: mapBackendToCategory(article.category),
    source: article.source,
    sourceUrl: article.source_url,
    author: mapBackendToAuthor(article.author),
    viewCount: article.view_count,
    favoriteCount: article.favorite_count,
    isFavorited: article.is_favorited,
    aiRiskLevel: article.ai_risk_level,
    isTop: article.is_top,
    isPublished: article.is_published,
    reviewStatus: article.review_status,
    publishedAt: article.published_at,
    createdAt: article.created_at,
    updatedAt: article.updated_at,
  };
}

/**
 * 转换后端评论到前端格式
 */
function mapBackendToComment(comment: BackendComment): NewsComment {
  return {
    id: comment.id,
    newsId: comment.news_id,
    userId: comment.user_id,
    content: comment.content,
    reviewStatus: comment.review_status,
    createdAt: comment.created_at,
    author: mapBackendToAuthor(comment.author),
  };
}

/**
 * 转换后端订阅到前端格式
 */
function mapBackendToSubscription(sub: BackendSubscription): NewsSubscription {
  return {
    id: sub.id,
    subType: sub.sub_type,
    value: sub.value,
    createdAt: sub.created_at,
  };
}

/**
 * 构建分页元数据
 */
function buildPaginationMeta(page: number, pageSize: number, total: number): PaginationMeta {
  return {
    page,
    pageSize,
    total,
    totalPages: Math.ceil(total / pageSize),
  };
}

// ==================== 新闻列表 API ====================

/**
 * 获取新闻列表
 */
export async function apiGetNewsList(params: GetNewsListRequest = {}): Promise<{
  items: NewsListItem[];
  meta: PaginationMeta;
}> {
  const response = await apiClient.get<BackendNewsListResponse>(API_BASE, {
    params: {
      page: params.page,
      page_size: params.pageSize,
      category: params.categoryId,
      keyword: params.keyword,
      source_site: params.source,
    },
  });

  return {
    items: response.data.items.map(mapBackendToNewsListItem),
    meta: buildPaginationMeta(
      response.data.page,
      response.data.page_size,
      response.data.total
    ),
  };
}

/**
 * 获取新闻详情
 */
export async function apiGetNewsDetail(newsId: string): Promise<NewsArticle> {
  const response = await apiClient.get<BackendNewsArticle>(`${API_BASE}/${newsId}`);
  return mapBackendToNewsArticle(response.data);
}

// ==================== 推荐与热门 API ====================

/**
 * 获取推荐新闻
 */
export async function apiGetRecommendedNews(
  params: GetRecommendedNewsRequest = {}
): Promise<{
  items: NewsListItem[];
  meta: PaginationMeta;
}> {
  const response = await apiClient.get<BackendNewsListResponse>(`${API_BASE}/recommended`, {
    params: {
      page: params.page,
      page_size: params.pageSize,
    },
  });

  return {
    items: response.data.items.map(mapBackendToNewsListItem),
    meta: buildPaginationMeta(
      response.data.page,
      response.data.page_size,
      response.data.total
    ),
  };
}

/**
 * 获取热门新闻
 */
export async function apiGetHotNews(params: GetHotNewsRequest = {}): Promise<{
  items: NewsListItem[];
  meta: PaginationMeta;
}> {
  const response = await apiClient.get<BackendNewsListResponse>(`${API_BASE}/hot`, {
    params: {
      page: params.page,
      page_size: params.pageSize,
      days: params.period === 'day' ? 1 : params.period === 'week' ? 7 : 30,
    },
  });

  return {
    items: response.data.items.map(mapBackendToNewsListItem),
    meta: buildPaginationMeta(
      response.data.page,
      response.data.page_size,
      response.data.total
    ),
  };
}

/**
 * 获取置顶新闻
 */
export async function apiGetTopNews(limit: number = 5): Promise<NewsListItem[]> {
  const response = await apiClient.get<BackendNewsListItem[]>(`${API_BASE}/top`, {
    params: { limit },
  });

  return response.data.map(mapBackendToNewsListItem);
}

/**
 * 获取相关新闻
 */
export async function apiGetRelatedNews(
  newsId: string,
  limit: number = 5
): Promise<NewsListItem[]> {
  const response = await apiClient.get<BackendRelatedNewsResponse>(
    `${API_BASE}/${newsId}/related`,
    {
      params: { limit },
    }
  );

  return response.data.items.map(mapBackendToNewsListItem);
}

// ==================== 搜索 API ====================

/**
 * 搜索新闻
 */
export async function apiSearchNews(params: SearchNewsRequest): Promise<{
  items: NewsListItem[];
  meta: PaginationMeta;
}> {
  const response = await apiClient.get<BackendNewsListResponse>(`${API_BASE}`, {
    params: {
      keyword: params.keyword,
      page: params.page,
      page_size: params.pageSize,
      category: params.categoryId,
    },
  });

  return {
    items: response.data.items.map(mapBackendToNewsListItem),
    meta: buildPaginationMeta(
      response.data.page,
      response.data.page_size,
      response.data.total
    ),
  };
}

// ==================== 评论 API ====================

/**
 * 获取新闻评论
 */
export async function apiGetNewsComments(
  newsId: string,
  params: { page?: number; pageSize?: number } = {}
): Promise<{
  items: NewsComment[];
  meta: PaginationMeta;
}> {
  const response = await apiClient.get<BackendCommentListResponse>(
    `${API_BASE}/${newsId}/comments`,
    {
      params: {
        page: params.page,
        page_size: params.pageSize,
      },
    }
  );

  return {
    items: response.data.items.map(mapBackendToComment),
    meta: buildPaginationMeta(
      response.data.page,
      response.data.page_size,
      response.data.total
    ),
  };
}

/**
 * 创建评论
 */
export async function apiCreateComment(
  request: CreateCommentRequest
): Promise<NewsComment> {
  const response = await apiClient.post<BackendCommentCreateResponse>(
    `${API_BASE}/${request.newsId}/comments`,
    {
      content: request.content,
    }
  );

  return mapBackendToComment(response.data.comment);
}

/**
 * 删除评论
 */
export async function apiDeleteComment(
  newsId: string,
  commentId: string
): Promise<{ message: string }> {
  await apiClient.delete(`${API_BASE}/${newsId}/comments/${commentId}`);
  return { message: '评论已删除' };
}

// ==================== 订阅 API ====================

/**
 * 获取用户订阅列表
 */
export async function apiGetUserSubscriptions(): Promise<NewsSubscription[]> {
  const response = await apiClient.get<BackendSubscriptionListResponse>(
    `${API_BASE}/subscriptions`
  );
  return response.data.subscriptions.map(mapBackendToSubscription);
}

/**
 * 订阅新闻
 */
export async function apiSubscribeNews(
  request: SubscribeNewsRequest
): Promise<NewsSubscription> {
  const response = await apiClient.post<BackendSubscriptionResponse>(
    `${API_BASE}/subscriptions`,
    {
      sub_type: request.subType,
      value: request.value,
    }
  );

  return mapBackendToSubscription(response.data.subscription);
}

/**
 * 取消订阅
 */
export async function apiUnsubscribeNews(category: string): Promise<{ message: string }> {
  await apiClient.delete(`${API_BASE}/subscriptions/${category}`);
  return { message: '取消订阅成功' };
}

// ==================== 分类 API ====================

/**
 * 获取分类列表
 */
export async function apiGetCategories(): Promise<NewsCategory[]> {
  const response = await apiClient.get<BackendCategoryListResponse>(
    `${API_BASE}/categories`
  );
  return response.data.categories.map(mapBackendToCategory);
}

// ==================== 收藏 API ====================

/**
 * 切换收藏
 */
export async function apiToggleFavorite(newsId: string): Promise<{
  isFavorited: boolean;
  favoriteCount: number;
}> {
  const response = await apiClient.post<BackendFavoriteResponse>(
    `${API_BASE}/${newsId}/favorite`
  );

  return {
    isFavorited: response.data.is_favorited,
    favoriteCount: response.data.favorite_count,
  };
}

// ==================== 兼容旧版 API 导出 ====================

/** @deprecated 使用 apiGetNewsList 替代 */
export const getNewsList = apiGetNewsList;

/** @deprecated 使用 apiGetNewsDetail 替代 */
export const getNewsDetail = apiGetNewsDetail;

/** @deprecated 使用 apiGetNewsComments 替代 */
export const getNewsComments = apiGetNewsComments;

/** @deprecated 使用 apiCreateComment 替代 */
export const createComment = apiCreateComment;

/** @deprecated 使用 apiSubscribeNews 替代 */
export const subscribeNews = apiSubscribeNews;

/** @deprecated 使用 apiUnsubscribeNews 替代 */
export const unsubscribeNews = apiUnsubscribeNews;

/** @deprecated 使用 apiGetCategories 替代 */
export const getCategories = apiGetCategories;

/** @deprecated 使用 apiToggleFavorite 替代 */
export const toggleFavorite = apiToggleFavorite;

/** @deprecated 使用 apiGetHotNews 替代 */
export const getHotNews = apiGetHotNews;

/** @deprecated 使用 apiGetRecommendedNews 替代 */
export const getRecommendedNews = apiGetRecommendedNews;

/** @deprecated 使用 apiGetUserSubscriptions 替代 */
export const getUserSubscriptions = apiGetUserSubscriptions;

/** @deprecated 使用 apiSearchNews 替代 */
export const searchNews = apiSearchNews;

/** @deprecated 使用 apiGetRelatedNews 替代 */
export const getRelatedNews = apiGetRelatedNews;