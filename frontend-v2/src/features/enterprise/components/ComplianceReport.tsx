/**
 * ComplianceReport - 合规报告组件
 */

import type { ContractReview } from '../types';

interface ComplianceReportProps {
  review: ContractReview | null;
  className?: string;
}

/**
 * 合规报告组件
 */
export function ComplianceReport({ review, className = '' }: ComplianceReportProps): JSX.Element {
  if (!review) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
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
          <p className="text-gray-500">请选择一份合同查看详细报告</p>
        </div>
      </div>
    );
  }

  const riskColors: Record<string, string> = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-red-100 text-red-800',
  };

  const riskLabels: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
      {/* 标题区域 */}
      <div className="border-b border-gray-100 pb-4 mb-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">{review.title}</h3>
          <span
            className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${riskColors[review.riskLevel || 'low']}`}
          >
            {riskLabels[review.riskLevel || 'low']}
          </span>
        </div>
        <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
          <span>类型: {review.contractType}</span>
          <span>提交时间: {new Date(review.createdAt).toLocaleString('zh-CN')}</span>
          {review.completedAt && (
            <span>完成时间: {new Date(review.completedAt).toLocaleString('zh-CN')}</span>
          )}
        </div>
      </div>

      {/* 审查结果 */}
      <div className="space-y-6">
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">审查结果</h4>
          <div className="p-4 bg-gray-50 rounded-lg text-gray-800 leading-relaxed">
            {review.reviewResult || '暂无审查结果'}
          </div>
        </div>

        {/* 合同内容摘要 */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">合同内容摘要</h4>
          <div className="p-4 bg-gray-50 rounded-lg text-gray-600 text-sm max-h-64 overflow-y-auto">
            {review.content.substring(0, 500)}...
          </div>
        </div>

        {/* 状态信息 */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-100">
          <div className="text-center">
            <p className="text-xs text-gray-500">当前状态</p>
            <p className="mt-1 text-sm font-medium text-gray-900">
              {review.status === 'pending' && '待审核'}
              {review.status === 'reviewing' && '审核中'}
              {review.status === 'completed' && '已完成'}
              {review.status === 'failed' && '失败'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500">审查员</p>
            <p className="mt-1 text-sm font-medium text-gray-900">
              {review.reviewerId ? `ID: ${review.reviewerId}` : '未分配'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500">合同ID</p>
            <p className="mt-1 text-sm font-medium text-gray-900">#{review.id}</p>
          </div>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="mt-6 flex gap-3">
        <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          下载报告
        </button>
        <button className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
          分享报告
        </button>
      </div>
    </div>
  );
}