/**
 * ComplianceCheckList - 合规检查列表组件
 */

import { useState } from 'react';

import type { ContractReview, ContractReviewStatus, RiskLevel } from '../types';

interface ComplianceCheckListProps {
  reviews: ContractReview[];
  isLoading?: boolean;
  onReviewClick?: (review: ContractReview) => void;
  className?: string;
}

const statusLabels: Record<ContractReviewStatus, string> = {
  pending: '待审核',
  reviewing: '审核中',
  completed: '已完成',
  failed: '失败',
};

const statusColors: Record<ContractReviewStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  reviewing: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const riskLabels: Record<RiskLevel, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
};

const riskColors: Record<RiskLevel, string> = {
  low: 'text-green-600 bg-green-50',
  medium: 'text-yellow-600 bg-yellow-50',
  high: 'text-red-600 bg-red-50',
};

/**
 * 合规检查列表组件
 */
export function ComplianceCheckList({
  reviews,
  isLoading = false,
  onReviewClick,
  className = '',
}: ComplianceCheckListProps): JSX.Element {
  const [filter, setFilter] = useState<ContractReviewStatus | 'all'>('all');

  const filteredReviews =
    filter === 'all' ? reviews : reviews.filter((r) => r.status === filter);

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">合规检查列表</h3>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as ContractReviewStatus | 'all')}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">全部状态</option>
          <option value="pending">待审核</option>
          <option value="reviewing">审核中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
      </div>

      {filteredReviews.length > 0 ? (
        <div className="space-y-3">
          {filteredReviews.map((review) => (
            <div
              key={review.id}
              onClick={() => onReviewClick?.(review)}
              className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h4 className="font-medium text-gray-900">{review.title}</h4>
                    <span
                      className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-full ${statusColors[review.status]}`}
                    >
                      {statusLabels[review.status]}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                    <span>类型: {review.contractType}</span>
                    <span>提交: {new Date(review.createdAt).toLocaleDateString('zh-CN')}</span>
                  </div>
                </div>
                {review.riskLevel && (
                  <div className={`ml-4 px-3 py-1 rounded-lg text-sm font-medium ${riskColors[review.riskLevel]}`}>
                    {riskLabels[review.riskLevel]}
                  </div>
                )}
              </div>

              {review.reviewResult && (
                <div className="mt-3 p-3 bg-gray-50 rounded text-sm text-gray-700">
                  {review.reviewResult.substring(0, 100)}...
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <p className="text-gray-500">暂无合规检查记录</p>
        </div>
      )}

      <div className="mt-4 text-sm text-gray-500 text-center">
        共 {filteredReviews.length} 条记录
      </div>
    </div>
  );
}