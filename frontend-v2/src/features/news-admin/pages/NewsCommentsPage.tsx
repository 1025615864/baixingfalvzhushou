/**
 * News Comments Page
 * 新闻评论管理页面
 */

import { useState } from 'react';
import { Check, X, Trash2, MessageSquare, Filter } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Pagination } from '@/components/ui/Pagination';

import { useComments, useReviewComment, useDeleteComment } from '../hooks/useNewsAdmin';
import type { NewsComment, ReviewCommentRequest } from '../types';

/**
 * 新闻评论管理页面
 */
export function NewsCommentsPage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [status, setStatus] = useState<'pending' | 'approved' | 'rejected' | undefined>(undefined);

  // 数据查询
  const { data: commentsData, isLoading } = useComments({
    page,
    pageSize,
    status,
  });

  // Mutations
  const reviewMutation = useReviewComment();
  const deleteMutation = useDeleteComment();

  // 处理审核
  const handleReview = (comment: NewsComment, action: 'approve' | 'reject'): void => {
    const request: ReviewCommentRequest = {
      action: action === 'approve' ? 'approve' : 'reject',
    };
    reviewMutation.mutate({ id: comment.id, request });
  };

  // 处理删除
  const handleDelete = (comment: NewsComment): void => {
    if (window.confirm('确定要删除这条评论吗？此操作不可恢复。')) {
      deleteMutation.mutate(comment.id);
    }
  };

  const comments = commentsData?.items ?? [];
  const total = commentsData?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">新闻评论管理</h1>
          <p className="text-slate-600 mt-1">审核和管理用户评论</p>
        </div>
      </div>

      {/* 筛选栏 */}
      <Card className="mb-6">
        <div className="p-4 flex items-center gap-4">
          <Filter className="h-4 w-4 text-slate-500" />
          <span className="text-sm text-slate-700">筛选：</span>
          <select
            value={status || ''}
            onChange={(e) => {
              setStatus((e.target.value as 'pending' | 'approved' | 'rejected') || undefined);
              setPage(1);
            }}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">全部状态</option>
            <option value="pending">待审核</option>
            <option value="approved">已通过</option>
            <option value="rejected">已拒绝</option>
          </select>
          {status && (
            <Button variant="ghost" size="sm" onClick={() => setStatus(undefined)}>
              清除筛选
            </Button>
          )}
        </div>
      </Card>

      {/* 评论列表 */}
      <Card>
        {isLoading ? (
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-24 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            <div className="divide-y divide-slate-200">
              {comments.map((comment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  onApprove={() => handleReview(comment, 'approve')}
                  onReject={() => handleReview(comment, 'reject')}
                  onDelete={() => handleDelete(comment)}
                  isProcessing={reviewMutation.isPending}
                />
              ))}
              {!comments.length && (
                <div className="p-10 text-center text-slate-500">
                  <MessageSquare className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <p>暂无评论</p>
                  <p className="text-sm mt-1">当用户发表评论后会显示在这里</p>
                </div>
              )}
            </div>
            {totalPages > 1 && (
              <div className="p-4 border-t border-slate-200">
                <Pagination
                  currentPage={page}
                  totalPages={totalPages}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}

// ==================== 子组件 ====================

interface CommentItemProps {
  comment: NewsComment;
  onApprove: () => void;
  onReject: () => void;
  onDelete: () => void;
  isProcessing: boolean;
}

function CommentItem({
  comment,
  onApprove,
  onReject,
  onDelete,
  isProcessing,
}: CommentItemProps): JSX.Element {
  const statusConfig: Record<string, { label: string; variant: 'warning' | 'success' | 'danger' }> = {
    pending: { label: '待审核', variant: 'warning' },
    approved: { label: '已通过', variant: 'success' },
    rejected: { label: '已拒绝', variant: 'danger' },
  };
  const reviewStatus = comment.reviewStatus ?? 'pending';
  const status = statusConfig[reviewStatus] ?? { label: '未知', variant: 'warning' };

  return (
    <div className="p-4 hover:bg-slate-50">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-medium text-slate-900">{comment.author?.nickname ?? comment.author?.username ?? '匿名用户'}</span>
            <Badge variant={status.variant} size="sm">
              {status.label}
            </Badge>
            <span className="text-xs text-slate-400">
              {new Date(comment.createdAt).toLocaleString('zh-CN')}
            </span>
          </div>
          <p className="text-slate-700 mb-2">{comment.content}</p>
          {comment.news?.title && (
            <p className="text-sm text-slate-500">
              评论文章：
              <a
                href={`/news/${comment.newsId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                {comment.news.title}
              </a>
            </p>
          )}
          {comment.reviewReason && (
            <p className="text-sm text-red-600 mt-2">
              审核意见：{comment.reviewReason}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4">
          {reviewStatus === 'pending' && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={onApprove}
                disabled={isProcessing}
                title="通过"
              >
                <Check className="h-4 w-4 text-green-500" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={onReject}
                disabled={isProcessing}
                title="拒绝"
              >
                <X className="h-4 w-4 text-red-500" />
              </Button>
            </>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={onDelete}
            title="删除"
          >
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      </div>
    </div>
  );
}
