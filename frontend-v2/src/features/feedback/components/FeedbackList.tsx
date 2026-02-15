/**
 * 反馈列表组件
 */

import React from 'react';

import type { Feedback, FeedbackStatus } from '../types';

import { FeedbackItem } from './FeedbackItem';

/**
 * FeedbackListProps 接口
 */
export interface FeedbackListProps {
  /** 反馈列表 */
  items: Feedback[];
  /** 是否加载中 */
  isLoading?: boolean;
  /** 是否为管理员视图 */
  isAdmin?: boolean;
  /** 回复回调（管理员） */
  onReply?: (id: number, reply: string) => void;
  /** 状态变更回调（管理员） */
  onStatusChange?: (id: number, status: FeedbackStatus) => void;
  /** 空状态提示 */
  emptyText?: string;
  /** 自定义类名 */
  className?: string;
}

/**
 * 反馈列表组件
 */
export function FeedbackList({
  items,
  isLoading = false,
  isAdmin = false,
  onReply,
  onStatusChange,
  emptyText = '暂无反馈记录',
  className = '',
}: FeedbackListProps): React.ReactElement {
  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-4 animate-pulse">
            <div className="flex items-center space-x-2 mb-3">
              <div className="w-16 h-6 bg-gray-200 rounded-full" />
              <div className="w-16 h-6 bg-gray-200 rounded-full" />
            </div>
            <div className="h-5 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-1/4" />
          </div>
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </div>
        <p className="text-gray-500">{emptyText}</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {items.map((feedback) => (
        <FeedbackItem
          key={feedback.id}
          feedback={feedback}
          isAdmin={isAdmin}
          onReply={onReply}
          onStatusChange={onStatusChange}
        />
      ))}
    </div>
  );
}