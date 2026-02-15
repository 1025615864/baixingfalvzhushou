/**
 * 评论列表组件
 */

import { memo } from 'react';

import type { NewsComment } from '../types';

import { CommentItem } from './CommentItem';

interface CommentListProps {
  comments: NewsComment[];
  currentUserId?: number | null;
  onDelete?: (commentId: number) => void;
  isDeleting?: boolean;
  deletingCommentId?: number | null;
}

/**
 * 评论列表组件
 */
export const CommentList = memo<CommentListProps>(function CommentList({
  comments,
  currentUserId,
  onDelete,
  isDeleting,
  deletingCommentId,
}) {
  if (comments.length === 0) {
    return null;
  }

  return (
    <div className="divide-y divide-gray-100">
      {comments.map((comment) => (
        <CommentItem
          key={comment.id}
          comment={comment}
          isOwner={comment.userId === currentUserId}
          onDelete={onDelete}
          isDeleting={isDeleting && deletingCommentId === comment.id}
        />
      ))}
    </div>
  );
});

export default CommentList;