/**
 * 收藏按钮组件
 * 显示收藏状态和数量
 */

import React, { useCallback } from 'react';

import type { FavoriteButtonProps } from '../types';

/**
 * 收藏按钮组件
 */
export const FavoriteButton: React.FC<FavoriteButtonProps> = ({
  isFavorited,
  favoriteCount,
  onToggle,
  disabled = false,
  showCount = true,
}) => {
  /**
   * 处理收藏切换
   */
  const handleClick = useCallback(() => {
    if (!disabled) {
      onToggle();
    }
  }, [disabled, onToggle]);

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      className={`
        inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
        text-sm font-medium transition-all duration-200
        ${isFavorited
          ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2
      `}
      aria-label={isFavorited ? '取消收藏' : '收藏'}
      aria-pressed={isFavorited}
    >
      <svg
        className={`w-4 h-4 ${isFavorited ? 'fill-current' : ''}`}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
      {showCount && (
        <span>{favoriteCount > 0 ? favoriteCount : '收藏'}</span>
      )}
      {!showCount && <span>{isFavorited ? '已收藏' : '收藏'}</span>}
    </button>
  );
};

// 默认导出
export default FavoriteButton;