/**
 * Post（帖子管理）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  Post,
  PostListItem,
  PostComment,
  GetPostsRequest,
  GetCommentsRequest,
  CreatePostRequest,
  UpdatePostRequest,
  DeletePostRequest,
  CreateCommentRequest,
  PostFilter,
  PostSortOption,
} from '../types';
import {
  apiGetPosts,
  apiGetPostDetail,
  apiCreatePost,
  apiUpdatePost,
  apiDeletePost,
  apiGetComments,
  apiCreateComment,
  apiDeleteComment,
  apiLikePost,
  apiUnlikePost,
  apiPinPost,
  apiFeaturePost,
  apiUploadImage,
} from '../api';

// ==================== Query Keys ====================

const POST_QUERY_KEYS = {
  posts: (params?: GetPostsRequest) => ['posts', 'list', params] as const,
  postDetail: (id: string) => ['posts', 'detail', id] as const,
  comments: (postId: string, params?: GetCommentsRequest) =>
    ['posts', postId, 'comments', params] as const,
} as const;

// ==================== Post List Hooks ====================

/**
 * 分页帖子列表结果
 */
export interface PaginatedPostsResult {
  posts: PostListItem[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

/**
 * 获取帖子列表 Hook（支持分页和筛选）
 */
export function usePosts(params: GetPostsRequest = {}) {
  return useQuery<PaginatedPostsResult>({
    queryKey: POST_QUERY_KEYS.posts(params),
    queryFn: async () => {
      const response = await apiGetPosts(params);
      return {
        posts: response.posts,
        total: response.total,
        page: response.page,
        limit: response.limit,
        totalPages: response.totalPages,
      };
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Post Detail Hooks ====================

/**
 * 获取帖子详情 Hook
 */
export function usePostDetail(postId: string) {
  return useQuery<Post>({
    queryKey: POST_QUERY_KEYS.postDetail(postId),
    queryFn: () => apiGetPostDetail(postId),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: Boolean(postId),
  });
}

// ==================== Create Post Hooks ====================

/**
 * 创建帖子 Hook
 */
export function useCreatePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreatePostRequest) => apiCreatePost(request),
    onSuccess: () => {
      // 创建成功后，刷新帖子列表
      void queryClient.invalidateQueries({ queryKey: ['posts', 'list'] });
    },
  });
}

// ==================== Update Post Hooks ====================

/**
 * 编辑帖子 Hook
 */
export function useUpdatePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdatePostRequest) => apiUpdatePost(request),
    onSuccess: (data) => {
      // 更新成功后，刷新帖子详情和列表
      void queryClient.invalidateQueries({
        queryKey: POST_QUERY_KEYS.postDetail(data.id),
      });
      void queryClient.invalidateQueries({ queryKey: ['posts', 'list'] });
    },
  });
}

// ==================== Delete Post Hooks ====================

/**
 * 删除帖子 Hook
 */
export function useDeletePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: DeletePostRequest) => apiDeletePost(request),
    onSuccess: () => {
      // 删除成功后，刷新帖子列表
      void queryClient.invalidateQueries({ queryKey: ['posts', 'list'] });
    },
  });
}

// ==================== Comments Hooks ====================

/**
 * 分页评论结果
 */
export interface PaginatedCommentsResult {
  comments: PostComment[];
  total: number;
  page: number;
  limit: number;
}

/**
 * 获取评论列表 Hook（支持分页）
 */
export function useComments(postId: string, params: Omit<GetCommentsRequest, 'postId'> = {}) {
  return useQuery<PaginatedCommentsResult>({
    queryKey: POST_QUERY_KEYS.comments(postId, { postId, ...params }),
    queryFn: async () => {
      const response = await apiGetComments({ postId, ...params });
      return {
        comments: response.comments,
        total: response.total,
        page: response.page,
        limit: response.limit,
      };
    },
    staleTime: 30 * 1000, // 30秒缓存
    enabled: Boolean(postId),
  });
}

/**
 * 创建评论 Hook
 */
export function useCreateComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateCommentRequest) => apiCreateComment(request),
    onSuccess: (_, variables) => {
      // 评论创建成功后，刷新评论列表和帖子详情
      void queryClient.invalidateQueries({
        queryKey: POST_QUERY_KEYS.comments(variables.postId),
      });
      void queryClient.invalidateQueries({
        queryKey: POST_QUERY_KEYS.postDetail(variables.postId),
      });
    },
  });
}

/**
 * 删除评论 Hook
 */
export function useDeleteComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (commentId: string) => apiDeleteComment(commentId),
    onSuccess: () => {
      // 删除成功后，刷新评论列表
      void queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });
}

// ==================== Like Hooks ====================

/**
 * 点赞帖子 Hook
 */
export function useLikePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (postId: string) => apiLikePost(postId),
    onSuccess: (_, postId) => {
      // 点赞成功后，刷新帖子详情
      void queryClient.invalidateQueries({
        queryKey: POST_QUERY_KEYS.postDetail(postId),
      });
    },
  });
}

/**
 * 取消点赞帖子 Hook
 */
export function useUnlikePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (postId: string) => apiUnlikePost(postId),
    onSuccess: (_, postId) => {
      // 取消点赞成功后，刷新帖子详情
      void queryClient.invalidateQueries({
        queryKey: POST_QUERY_KEYS.postDetail(postId),
      });
    },
  });
}

// ==================== Admin Hooks ====================

/**
 * 置顶帖子 Hook
 */
export function usePinPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ postId, isPinned }: { postId: string; isPinned: boolean }) =>
      apiPinPost(postId, isPinned),
    onSuccess: (_, variables) => {
      // 置顶操作成功后，刷新帖子详情和列表
      void queryClient.invalidateQueries({
        queryKey: POST_QUERY_KEYS.postDetail(variables.postId),
      });
      void queryClient.invalidateQueries({ queryKey: ['posts', 'list'] });
    },
  });
}

/**
 * 标记帖子为精华 Hook
 */
export function useFeaturePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ postId, isFeatured }: { postId: string; isFeatured: boolean }) =>
      apiFeaturePost(postId, isFeatured),
    onSuccess: (_, variables) => {
      // 精华操作成功后，刷新帖子详情和列表
      void queryClient.invalidateQueries({
        queryKey: POST_QUERY_KEYS.postDetail(variables.postId),
      });
      void queryClient.invalidateQueries({ queryKey: ['posts', 'list'] });
    },
  });
}

// ==================== Upload Hook ====================

/**
 * 上传图片 Hook
 */
export function useUploadImage() {
  return useMutation({
    mutationFn: (file: File) => apiUploadImage(file),
  });
}

// ==================== Utility Hooks ====================

/**
 * 帖子筛选状态 Hook
 * 返回筛选状态和更新函数
 */
export function createPostFilter(): PostFilter {
  return {
    category: undefined,
    status: undefined,
    authorId: undefined,
    tag: undefined,
    searchQuery: undefined,
    isPinned: undefined,
    isFeatured: undefined,
    startDate: undefined,
    endDate: undefined,
  };
}

/**
 * 默认排序选项
 */
export const DEFAULT_POST_SORT: PostSortOption = 'latest';

/**
 * 默认分页参数
 */
export const DEFAULT_POST_PAGINATION = {
  page: 1,
  limit: 20,
};