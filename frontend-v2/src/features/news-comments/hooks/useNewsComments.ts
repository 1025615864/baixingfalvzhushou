/**
 * 新闻评论 Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import type {
  NewsComment,
  GetNewsCommentsRequest,
  CreateNewsCommentRequest,
  DeleteNewsCommentRequest,
} from '../types';
import {
  apiGetNewsComments,
  apiCreateNewsComment,
  apiDeleteNewsComment,
  apiDeleteNewsCommentById,
} from '../api';

// ==================== Query Keys ====================

const NEWS_COMMENTS_QUERY_KEYS = {
  comments: (newsId: number, page?: number) =>
    ['news', 'comments', newsId, page] as const,
  commentDetail: (commentId: number) =>
    ['news', 'comment', commentId] as const,
} as const;

// ==================== 评论列表 Hook ====================

/**
 * 分页结果类型
 */
export interface PaginatedCommentsResult {
  items: NewsComment[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/**
 * 获取新闻评论列表 Hook（支持分页）
 */
export function useNewsComments(params: GetNewsCommentsRequest) {
  const { newsId, page = 1, pageSize = 20 } = params;

  return useQuery<PaginatedCommentsResult, Error>({
    queryKey: NEWS_COMMENTS_QUERY_KEYS.comments(newsId, page),
    queryFn: async () => {
      const response = await apiGetNewsComments({ newsId, page, pageSize });
      return {
        items: response.items,
        total: response.total,
        page: response.page,
        pageSize: response.pageSize,
        totalPages: Math.ceil(response.total / response.pageSize),
      };
    },
    staleTime: 30 * 1000, // 30秒缓存
    enabled: newsId > 0,
  });
}

// ==================== 创建评论 Hook ====================

/**
 * 创建评论 Hook
 */
export function useCreateNewsComment() {
  const queryClient = useQueryClient();

  return useMutation<NewsComment, Error, CreateNewsCommentRequest>({
    mutationFn: async (request) => {
      const response = await apiCreateNewsComment(request);
      return {
        id: response.id,
        newsId: response.newsId,
        userId: response.userId,
        content: response.content,
        reviewStatus: response.reviewStatus,
        reviewReason: response.reviewReason,
        createdAt: response.createdAt,
        author: response.author,
      };
    },
    onSuccess: (_, variables) => {
      // 创建成功后，刷新评论列表（第一页）
      void queryClient.invalidateQueries({
        queryKey: NEWS_COMMENTS_QUERY_KEYS.comments(variables.newsId),
      });
    },
  });
}

// ==================== 删除评论 Hook ====================

/**
 * 删除评论 Hook
 */
export function useDeleteNewsComment() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, DeleteNewsCommentRequest>({
    mutationFn: apiDeleteNewsComment,
    onSuccess: (_, variables) => {
      // 删除成功后，刷新评论列表
      void queryClient.invalidateQueries({
        queryKey: NEWS_COMMENTS_QUERY_KEYS.comments(variables.newsId),
      });
    },
  });
}

/**
 * 通过评论ID删除 Hook（兼容路由）
 */
export function useDeleteNewsCommentById() {
  const queryClient = useQueryClient();

  return useMutation<
    { message: string; newsId?: number },
    Error,
    { commentId: number; newsId?: number }
  >({
    mutationFn: async ({ commentId }) => {
      const response = await apiDeleteNewsCommentById(commentId);
      return { ...response };
    },
    onSuccess: (_, variables) => {
      // 如果有 newsId，刷新对应的评论列表
      if (variables.newsId) {
        void queryClient.invalidateQueries({
          queryKey: NEWS_COMMENTS_QUERY_KEYS.comments(variables.newsId),
        });
      }
    },
  });
}

// ==================== 便捷组合 Hook ====================

/**
 * 新闻评论面板完整功能 Hook
 * 整合了获取列表、创建、删除功能
 */
export function useNewsCommentPanel(newsId: number, currentUserId?: number | null) {
  // 获取评论列表
  const {
    data: commentsData,
    isLoading: isLoadingComments,
    isError: isCommentsError,
    error: commentsError,
    refetch: refetchComments,
  } = useNewsComments({ newsId, page: 1, pageSize: 20 });

  // 创建评论
  const {
    mutateAsync: createComment,
    isPending: isCreating,
    error: createError,
  } = useCreateNewsComment();

  // 删除评论
  const {
    mutateAsync: deleteComment,
    isPending: isDeleting,
    error: deleteError,
  } = useDeleteNewsComment();

  // 判断用户是否是评论作者
  const isCommentOwner = useCallback(
    (commentUserId: number): boolean => {
      if (!currentUserId) return false;
      return commentUserId === currentUserId;
    },
    [currentUserId]
  );

  // 处理创建评论
  const handleCreateComment = useCallback(
    async (content: string) => {
      if (!content.trim()) {
        throw new Error('评论内容不能为空');
      }
      return createComment({ newsId, content: content.trim() });
    },
    [newsId, createComment]
  );

  // 处理删除评论
  const handleDeleteComment = useCallback(
    async (commentId: number, commentUserId: number) => {
      if (!isCommentOwner(commentUserId)) {
        throw new Error('您没有权限删除此评论');
      }
      return deleteComment({ newsId, commentId });
    },
    [newsId, deleteComment, isCommentOwner]
  );

  return {
    // 数据
    comments: commentsData?.items ?? [],
    total: commentsData?.total ?? 0,
    totalPages: commentsData?.totalPages ?? 0,
    page: commentsData?.page ?? 1,
    pageSize: commentsData?.pageSize ?? 20,

    // 加载状态
    isLoading: isLoadingComments,
    isCreating,
    isDeleting,

    // 错误状态
    isError: isCommentsError || !!createError || !!deleteError,
    error: commentsError || createError || deleteError,

    // 操作
    refetch: refetchComments,
    createComment: handleCreateComment,
    deleteComment: handleDeleteComment,
    isCommentOwner,
  };
}