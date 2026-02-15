/**
 * 论坛点赞和收藏 API 层
 * 基于统一的 apiClient，对接后端 /api/v1/forum 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  FavoriteListParams,
  FavoriteResponse,
  LikeResponse,
  Post,
  PostListResponse,
  ReactionRequest,
  ReactionResponse,
} from '../types';

// API 基础路径
const API_BASE = '/forum';

/**
 * 论坛反应相关 API
 */
export const forumReactionsApi = {
  /**
   * 点赞/取消点赞帖子
   * @param postId - 帖子ID
   * @returns 点赞响应
   */
  toggleLike: async (postId: number): Promise<LikeResponse> => {
    const response = await apiClient.post<LikeResponse>(
      `${API_BASE}/posts/${postId}/like`
    );
    return response.data;
  },

  /**
   * 添加/取消表情反应
   * @param postId - 帖子ID
   * @param emoji - 表情符号
   * @returns 反应响应
   */
  toggleReaction: async (
    postId: number,
    emoji: string
  ): Promise<ReactionResponse> => {
    const request: ReactionRequest = { emoji };
    const response = await apiClient.post<ReactionResponse>(
      `${API_BASE}/posts/${postId}/reaction`,
      request
    );
    return response.data;
  },

  /**
   * 收藏/取消收藏帖子
   * @param postId - 帖子ID
   * @returns 收藏响应
   */
  toggleFavorite: async (postId: number): Promise<FavoriteResponse> => {
    const response = await apiClient.post<FavoriteResponse>(
      `${API_BASE}/posts/${postId}/favorite`
    );
    return response.data;
  },

  /**
   * 获取收藏列表
   * @param params - 查询参数
   * @returns 帖子列表响应
   */
  getFavorites: async (
    params: FavoriteListParams = {}
  ): Promise<PostListResponse> => {
    const { page = 1, page_size = 20, category, keyword } = params;
    const queryParams = new URLSearchParams();

    queryParams.append('page', String(page));
    queryParams.append('page_size', String(page_size));

    if (category) {
      queryParams.append('category', category);
    }

    if (keyword) {
      queryParams.append('keyword', keyword);
    }

    const response = await apiClient.get<PostListResponse>(
      `${API_BASE}/favorites?${queryParams.toString()}`
    );
    return response.data;
  },
};

/**
 * 获取帖子详情（辅助函数）
 * @param postId - 帖子ID
 * @returns 帖子详情
 */
export const getPostDetail = async (postId: number): Promise<Post> => {
  const response = await apiClient.get<Post>(`${API_BASE}/posts/${postId}`);
  return response.data;
};

// 默认导出
export default forumReactionsApi;