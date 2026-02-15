// ============================================
// 收藏功能 Hooks
// ============================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  apiGetFavorites,
  apiToggleFavorite,
} from '../api';
import type {
  PostListResponse,
  ToggleFavoriteResponse,
  GetFavoritesRequest,
} from '../types';

// Query Keys
const FAVORITE_KEYS = {
  all: ['forum', 'favorites'] as const,
  list: (params: GetFavoritesRequest) => [...FAVORITE_KEYS.all, 'list', params] as const,
} as const;

/**
 * 获取我的收藏列表
 */
export function useFavorites(params: GetFavoritesRequest = {}) {
  return useQuery({
    queryKey: FAVORITE_KEYS.list(params),
    queryFn: async (): Promise<PostListResponse> => {
      return apiGetFavorites(params);
    },
  });
}

/**
 * 收藏/取消收藏帖子
 */
export function useToggleFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (postId: number): Promise<ToggleFavoriteResponse> => {
      return apiToggleFavorite(postId);
    },
    onSuccess: () => {
      // 使收藏列表失效
      void queryClient.invalidateQueries({
        queryKey: FAVORITE_KEYS.all,
      });
    },
  });
}