/**
 * 帖子反应统计组件
 * 显示点赞数、评论数、收藏数和浏览量
 */

import React from 'react';

import type { PostReactionsProps } from '../types';

/**
 * 格式化数字显示
 */
function formatNumber(num: number): string {
  if (num >= 10000) {
    return `${(num / 10000).toFixed(1)}w`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}k`;
  }
  return String(num);
}

/**
 * 帖子反应统计组件
 */
export const PostReactions: React.FC<PostReactionsProps> = ({
  likeCount,
  commentCount,
  favoriteCount,
  viewCount,
  reactions = [],
  showReactions = true,
  compact = false,
}) => {
  if (compact) {
    // 紧凑模式 - 简化显示
    return (
      <div className="flex items-center gap-4 text-sm text-gray-500">
        <span className="inline-flex items-center gap-1">
          <svg
            className="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
          </svg>
          {formatNumber(likeCount)}
        </span>
        <span className="inline-flex items-center gap-1">
          <svg
            className="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          {formatNumber(commentCount)}
        </span>
        <span className="inline-flex items-center gap-1">
          <svg
            className="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
          {formatNumber(favoriteCount)}
        </span>
        <span className="inline-flex items-center gap-1">
          <svg
            className="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          {formatNumber(viewCount)}
        </span>
      </div>
    );
  }

  // 完整模式
  return (
    <div className="space-y-3">
      {/* 主要统计 */}
      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
        <div
          className="inline-flex items-center gap-1.5 px-2 py-1 bg-blue-50 rounded-md"
          aria-label={`${likeCount} 个赞`}
        >
          <svg
            className="w-4 h-4 text-blue-500"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
          </svg>
          <span className="font-medium">{formatNumber(likeCount)}</span>
          <span className="text-gray-400">赞</span>
        </div>

        <div
          className="inline-flex items-center gap-1.5 px-2 py-1 bg-green-50 rounded-md"
          aria-label={`${commentCount} 条评论`}
        >
          <svg
            className="w-4 h-4 text-green-500"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span className="font-medium">{formatNumber(commentCount)}</span>
          <span className="text-gray-400">评论</span>
        </div>

        <div
          className="inline-flex items-center gap-1.5 px-2 py-1 bg-yellow-50 rounded-md"
          aria-label={`${favoriteCount} 个收藏`}
        >
          <svg
            className="w-4 h-4 text-yellow-500"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
          <span className="font-medium">{formatNumber(favoriteCount)}</span>
          <span className="text-gray-400">收藏</span>
        </div>

        <div
          className="inline-flex items-center gap-1.5 px-2 py-1 bg-gray-50 rounded-md"
          aria-label={`${viewCount} 次浏览`}
        >
          <svg
            className="w-4 h-4 text-gray-500"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          <span className="font-medium">{formatNumber(viewCount)}</span>
          <span className="text-gray-400">浏览</span>
        </div>
      </div>

      {/* 表情反应 */}
      {showReactions && reactions.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-gray-500">反应：</span>
          <div className="flex flex-wrap gap-1.5">
            {reactions.map((reaction) => (
              <span
                key={reaction.emoji}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded-full text-sm"
                title={`${reaction.emoji} ${reaction.count} 个`}
              >
                <span>{reaction.emoji}</span>
                <span className="text-gray-600 text-xs">
                  {formatNumber(reaction.count)}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// 默认导出
export default PostReactions;