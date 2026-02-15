// ============================================
// 表情反应条组件
// ============================================

import { useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { useToggleReaction } from '../hooks/useReactions';
import type { ReactionEmoji, ReactionCount, Post } from '../types';

interface ReactionBarProps {
  postId: number;
  reactions: ReactionCount[];
  userReaction?: ReactionEmoji | null;
  size?: 'sm' | 'md';
  showCounts?: boolean;
}

const REACTION_EMOJIS: ReactionEmoji[] = ['👍', '👎', '😄', '😢', '🔥', '🎉'];

const REACTION_LABELS: Record<ReactionEmoji, string> = {
  '👍': '赞',
  '👎': '踩',
  '😄': '开心',
  '😢': '难过',
  '🔥': '热门',
  '🎉': '庆祝',
};

export function ReactionBar({
  postId,
  reactions: initialReactions,
  userReaction: initialUserReaction,
  size = 'md',
  showCounts = true,
}: ReactionBarProps) {
  const queryClient = useQueryClient();
  const [optimisticState, setOptimisticState] = useState<{
    reactions: ReactionCount[];
    userReaction: ReactionEmoji | null;
  }>({
    reactions: initialReactions,
    userReaction: initialUserReaction ?? null,
  });

  const { mutate, isPending } = useToggleReaction();

  const sizeClasses = {
    sm: 'w-7 h-7 text-sm',
    md: 'w-9 h-9 text-base',
  };

  const getReactionCount = useCallback((emoji: ReactionEmoji): number => {
    const reaction = optimisticState.reactions.find((r) => r.emoji === emoji);
    return reaction?.count ?? 0;
  }, [optimisticState.reactions]);

  const isSelected = useCallback((emoji: ReactionEmoji): boolean => {
    return optimisticState.userReaction === emoji;
  }, [optimisticState.userReaction]);

  const handleReactionClick = useCallback((emoji: ReactionEmoji) => {
    if (isPending) return;

    const currentReaction = optimisticState.userReaction;
    const isAdding = currentReaction !== emoji;
    const isTogglingOff = currentReaction === emoji;

    // 乐观更新
    setOptimisticState((prev) => {
      let newReactions = [...prev.reactions];

      // 如果之前有反应，减少计数
      if (currentReaction && !isTogglingOff) {
        newReactions = newReactions.map((r) =>
          r.emoji === currentReaction
            ? { ...r, count: Math.max(0, r.count - 1) }
            : r
        );
      }

      // 如果是添加新反应或切换反应，增加计数
      if (isAdding) {
        const existingIndex = newReactions.findIndex((r) => r.emoji === emoji);
        if (existingIndex >= 0) {
          newReactions[existingIndex] = {
            ...newReactions[existingIndex],
            count: newReactions[existingIndex].count + 1,
          };
        } else {
          newReactions.push({ emoji, count: 1 });
        }
      }

      // 如果是取消反应，减少计数
      if (isTogglingOff) {
        newReactions = newReactions.map((r) =>
          r.emoji === emoji
            ? { ...r, count: Math.max(0, r.count - 1) }
            : r
        );
      }

      // 清理计数为0的反应
      newReactions = newReactions.filter((r) => r.count > 0);

      return {
        reactions: newReactions,
        userReaction: isAdding ? emoji : null,
      };
    });

    mutate(
      { postId, emoji },
      {
        onSuccess: (result) => {
          // 更新所有相关的查询缓存
          queryClient.setQueriesData<Post>(
            { queryKey: ['forum', 'post', postId] },
            (old) => {
              if (!old) return old;
              return {
                ...old,
                user_reaction: result.reacted ? result.emoji : null,
                reactions: result.reactions,
              };
            }
          );

          queryClient.setQueriesData<{ items: Post[] }>(
            { queryKey: ['forum', 'posts'] },
            (old) => {
              if (!old) return old;
              return {
                ...old,
                items: old.items.map((post) =>
                  post.id === postId
                    ? {
                        ...post,
                        user_reaction: result.reacted ? result.emoji : null,
                        reactions: result.reactions,
                      }
                    : post
                ),
              };
            }
          );
        },
        onError: () => {
          // 回滚乐观更新
          setOptimisticState({
            reactions: initialReactions,
            userReaction: initialUserReaction ?? null,
          });
        },
      }
    );
  }, [isPending, optimisticState.userReaction, postId, mutate, queryClient, initialReactions, initialUserReaction]);

  return (
    <div className="flex items-center gap-1.5">
      {REACTION_EMOJIS.map((emoji) => {
        const count = getReactionCount(emoji);
        const selected = isSelected(emoji);
        const hasReactions = count > 0;

        return (
          <button
            key={emoji}
            type="button"
            onClick={() => handleReactionClick(emoji)}
            disabled={isPending}
            title={REACTION_LABELS[emoji]}
            className={`
              relative flex items-center justify-center rounded-full
              transition-all duration-200
              ${sizeClasses[size]}
              ${selected
                ? 'bg-blue-100 ring-2 ring-blue-300 transform scale-110'
                : hasReactions
                ? 'bg-gray-100 hover:bg-gray-200'
                : 'bg-transparent hover:bg-gray-100 opacity-60 hover:opacity-100'
              }
              ${isPending ? 'cursor-not-allowed opacity-70' : 'cursor-pointer'}
            `}
            aria-label={`${REACTION_LABELS[emoji]}${count > 0 ? ` (${count})` : ''}`}
            aria-pressed={selected}
          >
            <span className="leading-none">{emoji}</span>
            {showCounts && count > 0 && (
              <span
                className={`
                  absolute -top-1 -right-1 min-w-[16px] h-4 px-1
                  text-[10px] font-medium rounded-full
                  flex items-center justify-center
                  ${selected ? 'bg-blue-500 text-white' : 'bg-gray-500 text-white'}
                `}
              >
                {count > 99 ? '99+' : count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}