/**
 * Post（帖子管理）Hook
 * 使用 React Query 管理帖子相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  Post,
  GetPostsRequest,
  GetPostsResponse,
  CreatePostRequest,
  UpdatePostRequest,
  DeletePostRequest,
} from '../types';
import {
  apiGetPosts,
  apiGetPostDetail,
  apiCreatePost,
  apiUpdatePost,
  apiDeletePost,
  apiPinPost,
  apiFeaturePost,
} from '../api';

// Query Keys
const POST_KEYS = {
  all: ['posts'] as const,
  list: (params: GetPostsRequest) => [...POST_KEYS.all, 'list', params] as const,
  detail: (id: string) => [...POST_KEYS.all, 'detail', id] as const,
} as const;

/**
 * 获取帖子列表
 */
export function usePosts(params: GetPostsRequest = {}) {
  return useQuery<GetPostsResponse, Error>({
    queryKey: POST_KEYS.list(params),
    queryFn: () => apiGetPosts(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 获取帖子详情
 */
export function usePostDetail(id: string | null) {
  return useQuery<Post, Error>({
    queryKey: POST_KEYS.detail(id ?? ''),
    queryFn: () => apiGetPostDetail(id!),
    enabled: !!id,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 创建帖子
 */
export function useCreatePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreatePostRequest) => apiCreatePost(request),
    onSuccess: () => {
      // 创建成功后刷新帖子列表
      void queryClient.invalidateQueries({ queryKey: POST_KEYS.all });
    },
  });
}

/**
 * 更新帖子
 */
export function useUpdatePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdatePostRequest) => apiUpdatePost(request),
    onSuccess: (_, variables) => {
      // 更新成功后刷新帖子列表和详情
      void queryClient.invalidateQueries({ queryKey: POST_KEYS.all });
      void queryClient.invalidateQueries({ queryKey: POST_KEYS.detail(variables.id) });
    },
  });
}

/**
 * 删除帖子
 */
export function useDeletePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: DeletePostRequest) => apiDeletePost(request),
    onSuccess: () => {
      // 删除成功后刷新帖子列表
      void queryClient.invalidateQueries({ queryKey: POST_KEYS.all });
    },
  });
}

/**
 * 置顶/取消置顶帖子
 */
export function usePinPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ postId, isPinned }: { postId: string; isPinned: boolean }) =>
      apiPinPost(postId, isPinned),
    onSuccess: (_, variables) => {
      // 操作成功后刷新帖子列表和详情
      void queryClient.invalidateQueries({ queryKey: POST_KEYS.all });
      void queryClient.invalidateQueries({ queryKey: POST_KEYS.detail(variables.postId) });
    },
  });
}

/**
 * 加精/取消加精帖子
 */
export function useFeaturePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ postId, isFeatured }: { postId: string; isFeatured: boolean }) =>
      apiFeaturePost(postId, isFeatured),
    onSuccess: (_, variables) => {
      // 操作成功后刷新帖子列表和详情
      void queryClient.invalidateQueries({ queryKey: POST_KEYS.all });
      void queryClient.invalidateQueries({ queryKey: POST_KEYS.detail(variables.postId) });
    },
  });
}
