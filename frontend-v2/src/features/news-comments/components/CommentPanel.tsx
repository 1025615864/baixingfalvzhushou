/**
 * 评论面板整合组件
 */

import { useState } from 'react';

import { useNewsComments, useCreateNewsComment, useDeleteNewsComment } from '../hooks/useNewsComments';

import { CommentForm } from './CommentForm';
import { CommentList } from './CommentList';
import { CommentEmpty } from './CommentEmpty';
import { CommentLoading } from './CommentLoading';
import { CommentError } from './CommentError';
import { CommentPagination } from './CommentPagination';

interface CommentPanelProps {
  newsId: number;
  currentUserId?: number | null;
  className?: string;
}

/**
 * 评论面板组件
 */
export function CommentPanel({
  newsId,
  currentUserId,
  className = '',
}: CommentPanelProps): JSX.Element {
  const [currentPage, setCurrentPage] = useState(1);
  const [deletingCommentId, setDeletingCommentId] = useState<number | null>(null);

  // 获取评论列表
  const {
    data: commentsData,
    isLoading: isLoadingComments,
    isError: isCommentsError,
    error: commentsError,
    refetch: refetchComments,
  } = useNewsComments({ newsId, page: currentPage, pageSize: 20 });

  // 创建评论
  const {
    mutateAsync: createComment,
    isPending: isCreating,
  } = useCreateNewsComment();

  // 删除评论
  const {
    mutateAsync: deleteComment,
    isPending: isDeleting,
  } = useDeleteNewsComment();

  // 处理创建评论
  const handleCreateComment = async (content: string): Promise<void> => {
    await createComment({ newsId, content });
  };

  // 处理删除评论
  const handleDeleteComment = async (commentId: number): Promise<void> => {
    const comment = commentsData?.items.find(c => c.id === commentId);
    if (!comment) return;

    if (comment.userId !== currentUserId) {
      throw new Error('您没有权限删除此评论');
    }

    setDeletingCommentId(commentId);
    try {
      await deleteComment({ newsId, commentId });
    } finally {
      setDeletingCommentId(null);
    }
  };

  // 处理分页
  const handlePageChange = (page: number): void => {
    setCurrentPage(page);
    // 滚动到评论区域顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // 渲染内容
  const renderContent = (): JSX.Element => {
    if (isLoadingComments) {
      return <CommentLoading count={3} />;
    }

    if (isCommentsError) {
      return (
        <CommentError
          error={commentsError?.message || '加载评论失败'}
          onRetry={() => { void refetchComments(); }}
        />
      );
    }

    if (!commentsData?.items || commentsData.items.length === 0) {
      return <CommentEmpty />;
    }

    return (
      <>
        <CommentList
          comments={commentsData.items}
          currentUserId={currentUserId}
          onDelete={(commentId) => { void handleDeleteComment(commentId); }}
          isDeleting={isDeleting}
          deletingCommentId={deletingCommentId}
        />
        <CommentPagination
          currentPage={currentPage}
          totalPages={commentsData.totalPages}
          onPageChange={handlePageChange}
        />
      </>
    );
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm ${className}`}>
      {/* 头部 */}
      <div className="px-4 py-4 border-b border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900">
          评论
          {commentsData && commentsData.total > 0 && (
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({commentsData.total})
            </span>
          )}
        </h3>
      </div>

      {/* 评论表单 */}
      <div className="px-4 py-4 border-b border-gray-100">
        <CommentForm
          onSubmit={handleCreateComment}
          isSubmitting={isCreating}
          placeholder="写下你的评论..."
        />
      </div>

      {/* 评论列表 */}
      <div className="px-4">
        {renderContent()}
      </div>
    </div>
  );
}

export default CommentPanel;