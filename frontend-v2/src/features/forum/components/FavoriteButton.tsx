// ============================================
// 收藏按钮组件
// ============================================

import { useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { useToggleFavorite } from '../hooks/useFavorites';
import type { Post } from '../types';

interface FavoriteButtonProps {
  postId: number;
  isFavorited: boolean;
  favoriteCount: number;
  size?: 'sm' | 'md' | 'lg';
  showCount?: boolean;
  variant?: 'default' | 'ghost';
  onToggle?: (favorited: boolean) => void;
}

const BookmarkIcon = ({ filled, className }: { filled: boolean; className?: string }) => (
  <svg 
    className={className} 
    fill={filled ? 'currentColor' : 'none'} 
    stroke="currentColor" 
    viewBox="0 0 24 24"
  >
    <path 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      strokeWidth={2} 
      d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" 
    />
  </svg>
);

export function FavoriteButton({
  postId,
  isFavorited: initialFavorited,
  favoriteCount: initialCount,
  size = 'md',
  showCount = true,
  variant = 'default',
  onToggle,
}: FavoriteButtonProps) {
  const queryClient = useQueryClient();
  const [optimisticState, setOptimisticState] = useState<{
    isFavorited: boolean;
    count: number;
  }>({
    isFavorited: initialFavorited,
    count: initialCount,
  });

  const { mutate, isPending } = useToggleFavorite();

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  const buttonClasses = {
    default: 'p-2 rounded-full hover:bg-amber-50 transition-colors',
    ghost: 'hover:text-amber-600 transition-colors',
  };

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();

      if (isPending) return;

      // 乐观更新
      const newFavorited = !optimisticState.isFavorited;
      const newCount = newFavorited 
        ? optimisticState.count + 1 
        : Math.max(0, optimisticState.count - 1);

      setOptimisticState({
        isFavorited: newFavorited,
        count: newCount,
      });

      mutate(postId, {
        onSuccess: (result) => {
          // 更新所有相关的查询缓存
          queryClient.setQueriesData<Post>({ queryKey: ['forum', 'post', postId] }, (old) => {
            if (!old) return old;
            return {
              ...old,
              is_favorited: result.favorited,
              favorite_count: result.favorite_count,
            };
          });

          queryClient.setQueriesData<{ items: Post[] }>({ queryKey: ['forum', 'posts'] }, (old) => {
            if (!old) return old;
            return {
              ...old,
              items: old.items.map((post) =>
                post.id === postId
                  ? {
                      ...post,
                      is_favorited: result.favorited,
                      favorite_count: result.favorite_count,
                    }
                  : post
              ),
            };
          });

          // 使收藏列表失效
          void queryClient.invalidateQueries({ queryKey: ['forum', 'favorites'] });

          onToggle?.(result.favorited);
        },
        onError: () => {
          // 回滚乐观更新
          setOptimisticState({
            isFavorited: initialFavorited,
            count: initialCount,
          });
        },
      });
    },
    [isPending, optimisticState, postId, mutate, queryClient, initialFavorited, initialCount, onToggle]
  );

  const isActive = optimisticState.isFavorited;

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isPending}
      className={`flex items-center gap-1.5 ${
        isActive ? 'text-amber-500' : 'text-gray-400'
      } ${buttonClasses[variant]} ${isPending ? 'opacity-70 cursor-not-allowed' : ''}`}
      aria-label={isActive ? '取消收藏' : '添加收藏'}
      title={isActive ? '取消收藏' : '添加收藏'}
    >
      <BookmarkIcon 
        filled={isActive} 
        className={`${sizeClasses[size]} transition-transform ${isPending ? 'scale-95' : ''}`} 
      />
      {showCount && (
        <span className="text-sm font-medium tabular-nums">
          {optimisticState.count}
        </span>
      )}
    </button>
  );
}
