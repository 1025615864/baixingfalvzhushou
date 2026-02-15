/**
 * ArticleReview - 文章审核组件
 */

import { useState } from 'react';

import type { NewsAdminListItem, ReviewNewsRequest } from '../types';

interface ArticleReviewProps {
  article: NewsAdminListItem;
  isOpen: boolean;
  isLoading: boolean;
  onClose: () => void;
  onConfirm: (request: ReviewNewsRequest) => void;
}

/**
 * 风险等级标签组件
 */
function RiskBadge({ level }: { level: string | null }): JSX.Element {
  const riskStyles: Record<string, string> = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-red-100 text-red-800',
  };

  const riskLabels: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
  };

  const style = level ? riskStyles[level] || 'bg-gray-100 text-gray-800' : 'bg-gray-100 text-gray-800';
  const label = level ? riskLabels[level] || '未知' : '未评估';

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${style}`}>
      {label}
    </span>
  );
}

/**
 * 文章审核组件
 */
export function ArticleReview({
  article,
  isOpen,
  isLoading,
  onClose,
  onConfirm,
}: ArticleReviewProps): JSX.Element | null {
  const [action, setAction] = useState<'approve' | 'reject' | 'pending'>('pending');
  const [reason, setReason] = useState<string>('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    onConfirm({
      action,
      reason: reason || null,
    });
  };

  const handleClose = (): void => {
    setAction('pending');
    setReason('');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
        {/* 头部 */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">文章审核</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 文章内容预览 */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="flex items-start gap-4">
            {article.coverImage && (
              <img
                src={article.coverImage}
                alt={article.title}
                className="w-24 h-24 object-cover rounded-lg"
              />
            )}
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-gray-900 line-clamp-2">{article.title}</h3>
              <p className="text-sm text-gray-500 mt-1">分类: {article.category}</p>
              <p className="text-sm text-gray-500">来源: {article.source || '未知来源'}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-sm text-gray-600">AI风险评估:</span>
                <RiskBadge level={article.aiRiskLevel} />
              </div>
            </div>
          </div>
        </div>

        {/* 审核表单 */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* 审核操作 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                审核结果 <span className="text-red-500">*</span>
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="action"
                    value="approve"
                    checked={action === 'approve'}
                    onChange={(e) => setAction(e.target.value as 'approve')}
                    className="w-4 h-4 text-green-600 border-gray-300 focus:ring-green-500"
                  />
                  <span className="text-sm text-gray-700">通过</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="action"
                    value="reject"
                    checked={action === 'reject'}
                    onChange={(e) => setAction(e.target.value as 'reject')}
                    className="w-4 h-4 text-red-600 border-gray-300 focus:ring-red-500"
                  />
                  <span className="text-sm text-gray-700">拒绝</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="action"
                    value="pending"
                    checked={action === 'pending'}
                    onChange={(e) => setAction(e.target.value as 'pending')}
                    className="w-4 h-4 text-yellow-600 border-gray-300 focus:ring-yellow-500"
                  />
                  <span className="text-sm text-gray-700">待定</span>
                </label>
              </div>
            </div>

            {/* 审核原因 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                审核原因
                {action === 'reject' && <span className="text-red-500">*</span>}
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder={action === 'reject' ? '请输入拒绝原因（必填）' : '请输入审核原因（可选）'}
                required={action === 'reject'}
              />
            </div>
          </div>

          {/* 按钮 */}
          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              onClick={handleClose}
              disabled={isLoading}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className={`px-4 py-2 text-white rounded-lg disabled:opacity-50 ${
                action === 'approve'
                  ? 'bg-green-600 hover:bg-green-700'
                  : action === 'reject'
                  ? 'bg-red-600 hover:bg-red-700'
                  : 'bg-yellow-600 hover:bg-yellow-700'
              }`}
            >
              {isLoading ? '处理中...' : '确认审核'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
