// ============================================
// 表情反应功能 Hooks
// ============================================

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { apiToggleReaction } from '../api';
import type {
  ReactionResponse,
  ReactionEmoji,
} from '../types';

/**
 * 切换表情反应
 */
export function useToggleReaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      postId,
      emoji,
    }: {
      postId: number;
      emoji: ReactionEmoji;
    }): Promise<ReactionResponse> => {
      return apiToggleReaction(postId, emoji);
    },
    onSuccess: () => {
      // 使相关的查询失效
      void queryClient.invalidateQueries({
        queryKey: ['forum', 'posts'],
      });
      void queryClient.invalidateQueries({
        queryKey: ['forum', 'post'],
      });
    },
  });
}