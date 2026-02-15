/**
 * 单个评论项组件
 */

import { memo } from 'react';

import type { NewsComment } from '../types';

interface CommentItemProps {
  comment: NewsComment;
  isOwner: boolean;
  onDelete?: (commentId: number) => void;
  isDeleting?: boolean;
}

/**
 * 格式化时间显示
 */
function formatTime(timeStr: string): string {
  const date = new Date(timeStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  // 小于1分钟
  if (diff < 60 * 1000) {
    return '刚刚';
  }
  
  // 小于1小时
  if (diff < 60 * 60 * 1000) {
    return `${Math.floor(diff / (60 * 1000))}分钟前`;
  }
  
  // 小于24小时
  if (diff < 24 * 60 * 60 * 1000) {
    return `${Math.floor(diff / (60 * 60 * 1000))}小时前`;
  }
  
  // 小于7天
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    return `${Math.floor(diff / (24 * 60 * 60 * 1000))}天前`;
  }
  
  // 超过7天显示具体日期
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

/**
 * 评论项组件
 */
export const CommentItem = memo<CommentItemProps>(function CommentItem({
  comment,
  isOwner,
  onDelete,
  isDeleting,
}) {
  const handleDelete = () => {
    if (onDelete && !isDeleting) {
      onDelete(comment.id);
    }
  };

  return (
    <div className="flex gap-3 py-4 border-b border-gray-100 last:border-b-0">
      {/* 用户头像 */}
      <div className="flex-shrink-0">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-medium text-sm">
          {comment.author?.nickname?.[0] || comment.author?.username?.[0] || 'U'}
        </div>
      </div>
      
      {/* 评论内容 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-gray-900 text-sm">
            {comment.author?.nickname || comment.author?.username || '匿名用户'}
          </span>
          <span className="text-xs text-gray-400">
            {formatTime(comment.createdAt)}
          </span>
          
          {/* 审核状态标签 */}
          {comment.reviewStatus === 'pending' && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">
              审核中
            </span>
          )}
          {comment.reviewStatus === 'rejected' && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">
              未通过
            </span>
          )}
        </div>
        
        <p className="text-gray-700 text-sm leading-relaxed break-words">
          {comment.content}
        </p>
        
        {/* 操作按钮 */}
        <div className="flex items-center gap-4 mt-2">
          {isOwner && (
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="text-xs text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
              type="button"
            >
              {isDeleting ? '删除中...' : '删除'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
});

export default CommentItem;