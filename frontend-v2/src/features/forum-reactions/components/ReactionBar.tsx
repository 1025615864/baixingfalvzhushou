/**
 * 反应栏组件
 * 显示点赞、踩和表情反应
 */

import React, { useCallback, useState } from 'react';

import type { ReactionBarProps, ReactionEmoji } from '../types';

import { ReactionPicker } from './ReactionPicker';

/**
 * 反应栏组件
 */
export const ReactionBar: React.FC<ReactionBarProps> = ({
  likeCount,
  isLiked,
  reactions,
  onLikeToggle,
  onReactionSelect,
  disabled = false,
}) => {
  const [isPickerOpen, setIsPickerOpen] = useState(false);

  /**
   * 处理点赞切换
   */
  const handleLikeClick = useCallback(() => {
    if (!disabled) {
      onLikeToggle();
    }
  }, [disabled, onLikeToggle]);

  /**
   * 处理表情选择
   */
  const handleEmojiSelect = useCallback(
    (emoji: ReactionEmoji) => {
      onReactionSelect(emoji);
      setIsPickerOpen(false);
    },
    [onReactionSelect]
  );

  /**
   * 切换表情选择器
   */
  const togglePicker = useCallback(() => {
    if (!disabled) {
      setIsPickerOpen((prev) => !prev);
    }
  }, [disabled]);

  /**
   * 关闭表情选择器
   */
  const closePicker = useCallback(() => {
    setIsPickerOpen(false);
  }, []);

  return (
    <div className="flex items-center gap-2">
      {/* 点赞按钮 */}
      <button
        type="button"
        onClick={handleLikeClick}
        disabled={disabled}
        className={`
          inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
          text-sm font-medium transition-all duration-200
          ${isLiked
            ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        `}
        aria-label={isLiked ? '取消点赞' : '点赞'}
        aria-pressed={isLiked}
      >
        <svg
          className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
        </svg>
        <span>{likeCount > 0 ? likeCount : '点赞'}</span>
      </button>

      {/* 表情反应显示 */}
      {reactions.length > 0 && (
        <div className="flex items-center gap-1">
          {reactions.slice(0, 3).map((reaction) => (
            <button
              key={reaction.emoji}
              type="button"
              onClick={() => handleEmojiSelect(reaction.emoji as ReactionEmoji)}
              disabled={disabled}
              className={`
                inline-flex items-center gap-1 px-2 py-1 rounded-full
                text-sm bg-gray-50 hover:bg-gray-100
                transition-colors duration-150
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
              aria-label={`${reaction.emoji} 反应，共 ${reaction.count} 个`}
            >
              <span>{reaction.emoji}</span>
              <span className="text-gray-600 text-xs">{reaction.count}</span>
            </button>
          ))}
          {reactions.length > 3 && (
            <span className="text-gray-400 text-xs">
              +{reactions.length - 3}
            </span>
          )}
        </div>
      )}

      {/* 添加表情按钮 */}
      <div className="relative">
        <button
          type="button"
          onClick={togglePicker}
          disabled={disabled}
          className={`
            inline-flex items-center justify-center w-8 h-8 rounded-full
            text-gray-400 hover:text-gray-600 hover:bg-gray-100
            transition-colors duration-150
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            ${isPickerOpen ? 'bg-gray-100 text-gray-600' : ''}
          `}
          aria-label="添加表情反应"
          aria-expanded={isPickerOpen}
        >
          <span className="text-lg">😊</span>
        </button>

        {/* 表情选择器 */}
        <ReactionPicker
          isOpen={isPickerOpen}
          onSelect={handleEmojiSelect}
          onClose={closePicker}
        />
      </div>
    </div>
  );
};

// 默认导出
export default ReactionBar;