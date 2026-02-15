/**
 * 表情选择器组件
 * 显示可选的表情反应列表
 */

import React, { useCallback, useEffect, useRef } from 'react';

import type { ReactionEmoji, ReactionPickerProps } from '../types';

/** 可用表情列表 */
const AVAILABLE_EMOJIS: ReactionEmoji[] = ['👍', '👎', '😄', '❤️', '🎉', '😮', '🚀', '👀'];

/**
 * 表情选择器组件
 */
export const ReactionPicker: React.FC<ReactionPickerProps> = ({
  isOpen,
  onSelect,
  onClose,
  selectedEmoji,
}) => {
  const pickerRef = useRef<HTMLDivElement>(null);

  /**
   * 处理表情选择
   */
  const handleEmojiClick = useCallback(
    (emoji: ReactionEmoji) => {
      onSelect(emoji);
    },
    [onSelect]
  );

  /**
   * 点击外部关闭选择器
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        pickerRef.current &&
        !pickerRef.current.contains(event.target as Node)
      ) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      ref={pickerRef}
      className="absolute bottom-full left-0 mb-2 p-2 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
      role="dialog"
      aria-label="选择表情反应"
    >
      <div className="flex flex-wrap gap-1 max-w-[200px]">
        {AVAILABLE_EMOJIS.map((emoji) => (
          <button
            key={emoji}
            type="button"
            onClick={() => handleEmojiClick(emoji)}
            className={`
              w-8 h-8 flex items-center justify-center rounded
              text-xl hover:bg-gray-100 transition-colors duration-150
              ${selectedEmoji === emoji ? 'bg-blue-100 ring-2 ring-blue-400' : ''}
            `}
            aria-label={`选择 ${emoji}`}
            aria-pressed={selectedEmoji === emoji}
          >
            {emoji}
          </button>
        ))}
      </div>
    </div>
  );
};

// 默认导出
export default ReactionPicker;