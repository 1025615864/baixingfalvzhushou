/**
 * 反馈项组件
 */

import React, { useState } from 'react';

import type { Feedback, FeedbackStatus } from '../types';
import { getFeedbackStatusLabel, getFeedbackStatusClass, getFeedbackTypeLabel, getFeedbackTypeClass } from '../types';

/**
 * FeedbackItemProps 接口
 */
export interface FeedbackItemProps {
  /** 反馈数据 */
  feedback: Feedback;
  /** 是否为管理员视图 */
  isAdmin?: boolean;
  /** 回复回调（管理员） */
  onReply?: (id: number, reply: string) => void;
  /** 状态变更回调（管理员） */
  onStatusChange?: (id: number, status: FeedbackStatus) => void;
}

/**
 * 格式化日期
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 反馈项组件
 */
export function FeedbackItem({
  feedback,
  isAdmin = false,
  onReply,
  onStatusChange,
}: FeedbackItemProps): React.ReactElement {
  const [isExpanded, setIsExpanded] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [isReplying, setIsReplying] = useState(false);

  const statusClass = getFeedbackStatusClass(feedback.status);
  const statusLabel = getFeedbackStatusLabel(feedback.status);
  const typeClass = getFeedbackTypeClass(feedback.type);
  const typeLabel = getFeedbackTypeLabel(feedback.type);

  /**
   * 处理回复提交
   */
  const handleReplySubmit = () => {
    if (!replyText.trim() || !onReply) return;
    onReply(feedback.id, replyText.trim());
    setReplyText('');
    setIsReplying(false);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
      {/* 头部信息 */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {/* 类型标签 */}
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${typeClass}`}>
            {typeLabel}
          </span>
          {/* 状态标签 */}
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusClass}`}>
            {statusLabel}
          </span>
        </div>
        <span className="text-xs text-gray-500">{formatDate(feedback.createdAt)}</span>
      </div>

      {/* 标题 */}
      <h4 className="font-semibold text-gray-900 mb-2">{feedback.subject}</h4>

      {/* 内容 */}
      <div className="text-gray-600 text-sm mb-3">
        {isExpanded ? (
          <p>{feedback.content}</p>
        ) : (
          <p className="line-clamp-2">{feedback.content}</p>
        )}
        {feedback.content.length > 100 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 text-xs mt-1 hover:underline"
          >
            {isExpanded ? '收起' : '展开'}
          </button>
        )}
      </div>

      {/* 附件图片预览 */}
      {feedback.images && feedback.images.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {feedback.images.map((url, index) => (
            <a
              key={index}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="w-16 h-16 rounded-lg overflow-hidden border border-gray-200 hover:border-blue-400 transition-colors"
            >
              <img
                src={url}
                alt={`附件 ${index + 1}`}
                className="w-full h-full object-cover"
              />
            </a>
          ))}
        </div>
      )}

      {/* 联系方式 */}
      {feedback.contact && (
        <div className="flex items-center text-xs text-gray-500 mb-3">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
          {feedback.contact}
        </div>
      )}

      {/* 管理员回复 */}
      {feedback.adminReply && (
        <div className="bg-blue-50 rounded-lg p-3 mt-3">
          <div className="flex items-center text-xs text-blue-700 mb-1">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            管理员回复
          </div>
          <p className="text-sm text-gray-700">{feedback.adminReply}</p>
        </div>
      )}

      {/* 管理员操作区域 */}
      {isAdmin && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          {/* 状态操作 */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex space-x-2">
              {(['open', 'processing', 'closed'] as FeedbackStatus[]).map((status) => (
                <button
                  key={status}
                  onClick={() => onStatusChange?.(feedback.id, status)}
                  disabled={feedback.status === status}
                  className={`
                    px-3 py-1 text-xs rounded-full transition-colors
                    ${feedback.status === status
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                    }
                  `}
                >
                  {status === 'open' && '标记待处理'}
                  {status === 'processing' && '标记处理中'}
                  {status === 'closed' && '标记已解决'}
                </button>
              ))}
            </div>
            {!isReplying && (
              <button
                onClick={() => setIsReplying(true)}
                className="px-3 py-1 text-xs text-blue-600 bg-blue-50 rounded-full hover:bg-blue-100 transition-colors"
              >
                回复
              </button>
            )}
          </div>

          {/* 回复输入框 */}
          {isReplying && (
            <div className="space-y-2">
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="请输入回复内容..."
                rows={3}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => {
                    setIsReplying(false);
                    setReplyText('');
                  }}
                  className="px-3 py-1 text-xs text-gray-600 hover:text-gray-800"
                >
                  取消
                </button>
                <button
                  onClick={handleReplySubmit}
                  disabled={!replyText.trim()}
                  className="px-3 py-1 text-xs text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  提交回复
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}