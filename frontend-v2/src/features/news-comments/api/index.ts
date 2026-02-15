/**
 * 新闻评论 API 层
 */

import { api } from '@/shared/lib/api/client';

import type {
  GetNewsCommentsRequest,
  GetNewsCommentsResponse,
  CreateNewsCommentRequest,
  CreateNewsCommentResponse,
  DeleteNewsCommentRequest,
  DeleteNewsCommentResponse,
} from '../types';


// API 基础路径
const API_BASE = '/news';

/**
 * 获取新闻评论列表
 */
export async function apiGetNewsComments(
  params: GetNewsCommentsRequest
): Promise<GetNewsCommentsResponse> {
  const { newsId, page = 1, pageSize = 20 } = params;
  
  const response = await api.get<{
    items: Array<{
      id: number;
      news_id: number;
      user_id: number;
      content: string;
      review_status: string | null;
      review_reason: string | null;
      created_at: string;
      author: {
        id: number;
        username: string;
        nickname: string | null;
        avatar: string | null;
      } | null;
    }>;
    total: number;
    page: number;
    page_size: number;
  }>(`${API_BASE}/${newsId}/comments?page=${page}&page_size=${pageSize}`);

  return {
    items: response.items.map(item => ({
      id: item.id,
      newsId: item.news_id,
      userId: item.user_id,
      content: item.content,
      reviewStatus: item.review_status as 'pending' | 'approved' | 'rejected' | null,
      reviewReason: item.review_reason,
      createdAt: item.created_at,
      author: item.author ? {
        id: item.author.id,
        username: item.author.username,
        nickname: item.author.nickname,
        avatar: item.author.avatar,
      } : null,
    })),
    total: response.total,
    page: response.page,
    pageSize: response.page_size,
  };
}

/**
 * 创建新闻评论
 */
export async function apiCreateNewsComment(
  request: CreateNewsCommentRequest
): Promise<CreateNewsCommentResponse> {
  const { newsId, content } = request;
  
  const response = await api.post<{
    id: number;
    news_id: number;
    user_id: number;
    content: string;
    review_status: string | null;
    review_reason: string | null;
    created_at: string;
    author: {
      id: number;
      username: string;
      nickname: string | null;
      avatar: string | null;
    } | null;
  }>(`${API_BASE}/${newsId}/comments`, { content });

  return {
    id: response.id,
    newsId: response.news_id,
    userId: response.user_id,
    content: response.content,
    reviewStatus: response.review_status as 'pending' | 'approved' | 'rejected' | null,
    reviewReason: response.review_reason,
    createdAt: response.created_at,
    author: response.author ? {
      id: response.author.id,
      username: response.author.username,
      nickname: response.author.nickname,
      avatar: response.author.avatar,
    } : null,
  };
}

/**
 * 删除新闻评论
 */
export async function apiDeleteNewsComment(
  request: DeleteNewsCommentRequest
): Promise<DeleteNewsCommentResponse> {
  const { newsId, commentId } = request;
  
  const response = await api.delete<{ message: string }>(
    `${API_BASE}/${newsId}/comments/${commentId}`
  );

  return {
    message: response.message,
  };
}

/**
 * 通过评论ID删除新闻评论（兼容路由）
 */
export async function apiDeleteNewsCommentById(
  commentId: number
): Promise<DeleteNewsCommentResponse> {
  const response = await api.delete<{ message: string }>(
    `${API_BASE}/comments/${commentId}`
  );

  return {
    message: response.message,
  };
}