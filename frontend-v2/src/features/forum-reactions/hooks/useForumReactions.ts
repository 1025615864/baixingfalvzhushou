/**
 * 论坛点赞和收藏 React Query Hooks
 * 提供乐观更新的状态管理
 */

import { useCallback } from 'react';
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from '@tanstack/react-query';

import { forumReactionsApi } from '../api';
import type {
  FavoriteListParams,
  FavoriteResponse,
  LikeResponse,
  PostListResponse,
  ReactionEmoji,
  ReactionResponse,
} from '../types';

// Query Keys
export const forumReactionsKeys = {
  all: ['forum-reactions'] as const,
  favorites: () => [...forumReactionsKeys.all, 'favorites'] as const,
  favoriteList: (params: FavoriteListParams) =>
    [...forumReactionsKeys.favorites(), { params }] as const,
  postReactions: (postId: number) =>
    [...forumReactionsKeys.all, 'post', postId] as const,
};

/** 乐观更新上下文类型 */
interface LikeContext {
  previousPost: { is_liked: boolean; like_count: number } | undefined;
}

interface FavoriteContext {
  previousPost: { is_favorited: boolean; favorite_count: number } | undefined;
}

interface ReactionContext {
  previousPost: { reactions: Array<{ emoji: string; count: number }> } | undefined;
}

/**
 * 使用点赞/取消点赞 Mutation
 * @returns 点赞操作的 mutation
 */
export function useToggleLike() {
  const queryClient = useQueryClient();

  return useMutation<LikeResponse, Error, number, LikeContext>({
    mutationFn: (postId: number) => forumReactionsApi.toggleLike(postId),

    // 乐观更新
    onMutate: async (postId: number) => {
      // 取消相关查询的重新获取
      await queryClient.cancelQueries({
        queryKey: forumReactionsKeys.postReactions(postId),
      });

      // 获取当前帖子数据
      const previousPost = queryClient.getQueryData<{
        is_liked: boolean;
        like_count: number;
      }>(forumReactionsKeys.postReactions(postId));

      // 乐观更新本地状态
      if (previousPost) {
        queryClient.setQueryData(forumReactionsKeys.postReactions(postId), {
          ...previousPost,
          is_liked: !previousPost.is_liked,
          like_count: previousPost.is_liked
            ? previousPost.like_count - 1
            : previousPost.like_count + 1,
        });
      }

      return { previousPost };
    },

    // 错误时回滚
    onError: (_err, postId, context) => {
      if (context?.previousPost) {
        queryClient.setQueryData(
          forumReactionsKeys.postReactions(postId),
          context.previousPost
        );
      }
    },

    // 完成后重新获取
    onSettled: (_data, _error, postId) => {
      void queryClient.invalidateQueries({
        queryKey: forumReactionsKeys.postReactions(postId),
      });
    },
  });
}

/**
 * 使用收藏/取消收藏 Mutation
 * @returns 收藏操作的 mutation
 */
export function useToggleFavorite() {
  const queryClient = useQueryClient();

  return useMutation<FavoriteResponse, Error, number, FavoriteContext>({
    mutationFn: (postId: number) => forumReactionsApi.toggleFavorite(postId),

    // 乐观更新
    onMutate: async (postId: number) => {
      // 取消相关查询的重新获取
      await queryClient.cancelQueries({
        queryKey: forumReactionsKeys.postReactions(postId),
      });
      await queryClient.cancelQueries({
        queryKey: forumReactionsKeys.favorites(),
      });

      // 获取当前帖子数据
      const previousPost = queryClient.getQueryData<{
        is_favorited: boolean;
        favorite_count: number;
      }>(forumReactionsKeys.postReactions(postId));

      // 乐观更新本地状态
      if (previousPost) {
        queryClient.setQueryData(forumReactionsKeys.postReactions(postId), {
          ...previousPost,
          is_favorited: !previousPost.is_favorited,
          favorite_count: previousPost.is_favorited
            ? previousPost.favorite_count - 1
            : previousPost.favorite_count + 1,
        });
      }

      return { previousPost };
    },

    // 错误时回滚
    onError: (_err, postId, context) => {
      if (context?.previousPost) {
        queryClient.setQueryData(
          forumReactionsKeys.postReactions(postId),
          context.previousPost
        );
      }
    },

    // 完成后重新获取
    onSettled: (_data, _error, postId) => {
      void queryClient.invalidateQueries({
        queryKey: forumReactionsKeys.postReactions(postId),
      });
      void queryClient.invalidateQueries({
        queryKey: forumReactionsKeys.favorites(),
      });
    },
  });
}

/**
 * 使用表情反应 Mutation
 * @returns 表情反应操作的 mutation
 */
export function useToggleReaction() {
  const queryClient = useQueryClient();

  return useMutation<
    ReactionResponse,
    Error,
    { postId: number; emoji: ReactionEmoji },
    ReactionContext
  >({
    mutationFn: ({ postId, emoji }) =>
      forumReactionsApi.toggleReaction(postId, emoji),

    // 乐观更新
    onMutate: async ({ postId, emoji }) => {
      // 取消相关查询的重新获取
      await queryClient.cancelQueries({
        queryKey: forumReactionsKeys.postReactions(postId),
      });

      // 获取当前帖子数据
      const previousPost = queryClient.getQueryData<{
        reactions: Array<{ emoji: string; count: number }>;
      }>(forumReactionsKeys.postReactions(postId));

      // 乐观更新本地状态
      if (previousPost) {
        const currentReactions = [...previousPost.reactions];
        const existingReactionIndex = currentReactions.findIndex(
          (r) => r.emoji === emoji
        );

        if (existingReactionIndex >= 0) {
          // 如果已存在该反应，减少计数或移除
          const currentCount = currentReactions[existingReactionIndex].count;
          if (currentCount <= 1) {
            currentReactions.splice(existingReactionIndex, 1);
          } else {
            currentReactions[existingReactionIndex] = {
              ...currentReactions[existingReactionIndex],
              count: currentCount - 1,
            };
          }
        } else {
          // 如果不存在，添加新反应
          currentReactions.push({ emoji, count: 1 });
        }

        queryClient.setQueryData(forumReactionsKeys.postReactions(postId), {
          ...previousPost,
          reactions: currentReactions,
        });
      }

      return { previousPost };
    },

    // 错误时回滚
    onError: (_err, variables, context) => {
      if (context?.previousPost) {
        queryClient.setQueryData(
          forumReactionsKeys.postReactions(variables.postId),
          context.previousPost
        );
      }
    },

    // 完成后重新获取
    onSettled: (_data, _error, variables) => {
      void queryClient.invalidateQueries({
        queryKey: forumReactionsKeys.postReactions(variables.postId),
      });
    },
  });
}

/**
 * 使用收藏列表 Query
 * @param params - 查询参数
 * @param options - 额外的 query 选项
 * @returns 收藏列表数据
 */
export function useFavorites(
  params: FavoriteListParams = {},
  options?: Omit<UseQueryOptions<PostListResponse, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<PostListResponse, Error>({
    queryKey: forumReactionsKeys.favoriteList(params),
    queryFn: () => forumReactionsApi.getFavorites(params),
    ...options,
  });
}

/**
 * 使用批量操作 Hook
 * 提供便捷的方法处理多个帖子的反应操作
 */
export function useForumReactions() {
  const queryClient = useQueryClient();
  const toggleLikeMutation = useToggleLike();
  const toggleFavoriteMutation = useToggleFavorite();
  const toggleReactionMutation = useToggleReaction();

  /**
   * 处理点赞/取消点赞
   */
  const handleLike = useCallback(
    (postId: number) => {
      toggleLikeMutation.mutate(postId);
    },
    [toggleLikeMutation]
  );

  /**
   * 处理收藏/取消收藏
   */
  const handleFavorite = useCallback(
    (postId: number) => {
      toggleFavoriteMutation.mutate(postId);
    },
    [toggleFavoriteMutation]
  );

  /**
   * 处理表情反应
   */
  const handleReaction = useCallback(
    (postId: number, emoji: ReactionEmoji) => {
      toggleReactionMutation.mutate({ postId, emoji });
    },
    [toggleReactionMutation]
  );

  /**
   * 预获取帖子反应数据
   */
  const prefetchPostReactions = useCallback(
    (postId: number) => {
      void queryClient.prefetchQuery({
        queryKey: forumReactionsKeys.postReactions(postId),
        queryFn: () => forumReactionsApi.getFavorites({ page: 1, page_size: 1 }),
        staleTime: 5 * 60 * 1000, // 5分钟
      });
    },
    [queryClient]
  );

  return {
    handleLike,
    handleFavorite,
    handleReaction,
    prefetchPostReactions,
    isLoading:
      toggleLikeMutation.isPending ||
      toggleFavoriteMutation.isPending ||
      toggleReactionMutation.isPending,
    likeError: toggleLikeMutation.error,
    favoriteError: toggleFavoriteMutation.error,
    reactionError: toggleReactionMutation.error,
  };
}

// 默认导出
export default useForumReactions;