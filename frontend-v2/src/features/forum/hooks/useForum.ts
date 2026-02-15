// ============================================
// 论坛模块 API Hooks
// ============================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  apiGetPosts,
  apiGetPostDetail,
  apiCreatePost,
  apiTogglePostLike,
  apiGetComments,
  apiCreateComment,
  apiToggleFavorite,
  apiGetHotPosts,
} from '../api';
import type {
  Post,
  PostListResponse,
  ForumComment,
  CommentListResponse,
  CreatePostRequest,
  CreateCommentRequest,
  LikeResponse,
  PostCategory,
  ToggleFavoriteResponse,
} from '../types';

// ============================================
// Query Keys
// ============================================

const FORUM_KEYS = {
  all: ['forum'] as const,
  posts: () => [...FORUM_KEYS.all, 'posts'] as const,
  post: (id: number) => [...FORUM_KEYS.all, 'post', id] as const,
  comments: (postId: number) => [...FORUM_KEYS.all, 'comments', postId] as const,
  hot: () => [...FORUM_KEYS.all, 'hot'] as const,
} as const;

// ============================================
// Hooks
// ============================================

/** 获取帖子列表 */
export function usePostList(options: {
  page?: number;
  page_size?: number;
  category?: PostCategory | null;
  keyword?: string;
} = {}) {
  const { page = 1, page_size = 20, category, keyword } = options;

  return useQuery<PostListResponse>({
    queryKey: [...FORUM_KEYS.posts(), { page, page_size, category, keyword }],
    queryFn: () => apiGetPosts(page, page_size, category, keyword),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/** 获取热门帖子 */
export function useHotPosts(limit = 10) {
  return useQuery<PostListResponse>({
    queryKey: [...FORUM_KEYS.hot(), limit],
    queryFn: () => apiGetHotPosts(limit),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/** 获取帖子详情 */
export function usePostDetail(postId: number) {
  return useQuery<Post>({
    queryKey: FORUM_KEYS.post(postId),
    queryFn: () => apiGetPostDetail(postId),
    enabled: postId > 0,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/** 获取评论列表 */
export function useCommentList(postId: number) {
  return useQuery<CommentListResponse>({
    queryKey: FORUM_KEYS.comments(postId),
    queryFn: () => apiGetComments(postId),
    enabled: postId > 0,
    staleTime: 2 * 60 * 1000, // 2分钟缓存
  });
}

/** 创建帖子 */
export function useCreatePost() {
  const queryClient = useQueryClient();

  return useMutation<Post, Error, CreatePostRequest>({
    mutationFn: (data) => apiCreatePost(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: FORUM_KEYS.posts() });
    },
  });
}

/** 创建评论 */
export function useCreateComment() {
  const queryClient = useQueryClient();

  return useMutation<ForumComment, Error, { postId: number; data: CreateCommentRequest }>({
    mutationFn: ({ postId, data }) => apiCreateComment(postId, data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ 
        queryKey: FORUM_KEYS.comments(variables.postId) 
      });
      void queryClient.invalidateQueries({ 
        queryKey: FORUM_KEYS.post(variables.postId) 
      });
    },
  });
}

/** 点赞/取消点赞帖子 */
export function useTogglePostLike() {
  const queryClient = useQueryClient();

  return useMutation<LikeResponse, Error, number>({
    mutationFn: (postId) => apiTogglePostLike(postId),
    onSuccess: (_, postId) => {
      void queryClient.invalidateQueries({ queryKey: FORUM_KEYS.post(postId) });
      void queryClient.invalidateQueries({ queryKey: FORUM_KEYS.posts() });
    },
  });
}

/** 收藏/取消收藏帖子 */
export function useTogglePostFavorite() {
  const queryClient = useQueryClient();

  return useMutation<ToggleFavoriteResponse, Error, number>({
    mutationFn: (postId) => apiToggleFavorite(postId),
    onSuccess: (data, postId) => {
      // 更新本地缓存
      queryClient.setQueriesData<Post>({ queryKey: FORUM_KEYS.post(postId) }, (old) => {
        if (!old) return old;
        return {
          ...old,
          is_favorited: data.favorited,
          favorite_count: data.favorite_count,
        };
      });
      
      void queryClient.invalidateQueries({ queryKey: FORUM_KEYS.post(postId) });
      void queryClient.invalidateQueries({ queryKey: ['forum', 'favorites'] });
    },
  });
}