/**
 * ContractList - 合同审查历史列表组件
 */

import { useState } from 'react';

import type { ContractReviewHistoryItem, RiskLevel } from '../types';
import { useReviewHistory, useDeleteReview } from '../hooks/useContracts';

/** 风险等级配置 */
const RISK_CONFIG: Record<RiskLevel, { label: string; color: string; bg: string }> = {
  low: { label: '低风险', color: 'text-green-700', bg: 'bg-green-100' },
  medium: { label: '中风险', color: 'text-yellow-700', bg: 'bg-yellow-100' },
  high: { label: '高风险', color: 'text-red-700', bg: 'bg-red-100' },
};

/** 合同类型映射 */
const CONTRACT_TYPE_MAP: Record<string, string> = {
  sales: '买卖合同',
  lease: '租赁合同',
  labor: '劳动合同',
  loan: '借款合同',
  service: '服务合同',
  cooperation: '合作协议',
  confidentiality: '保密协议',
  other: '其他',
};

interface ContractListProps {
  /** 每页数量 */
  pageSize?: number;
  /** 点击查看详情回调 */
  onViewDetail?: (reviewId: string) => void;
}

/**
 * 合同审查历史列表组件
 */
export function ContractList({ pageSize = 10, onViewDetail }: ContractListProps): JSX.Element {
  const [page, setPage] = useState<number>(1);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data, isLoading, error } = useReviewHistory({ page, pageSize });
  const deleteMutation = useDeleteReview();

  /** 处理删除 */
  const handleDelete = async (reviewId: string): Promise<void> => {
    if (!window.confirm('确定要删除这条审查记录吗？')) {
      return;
    }

    setDeletingId(reviewId);
    try {
      const result = await deleteMutation.mutateAsync(reviewId);
      if (result.success) {
        alert('删除成功');
      } else {
        alert(result.error || '删除失败');
      }
    } catch (err) {
      alert('删除失败: ' + (err instanceof Error ? err.message : '未知错误'));
    } finally {
      setDeletingId(null);
    }
  };

  /** 处理查看详情 */
  const handleViewDetail = (reviewId: string): void => {
    if (onViewDetail) {
      onViewDetail(reviewId);
    }
  };

  /** 格式化日期 */
  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  /** 渲染加载状态 */
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">加载中...</span>
        </div>
      </div>
    );
  }

  /** 渲染错误状态 */
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="text-center text-red-600">
          <p>加载失败: {error.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  /** 渲染空状态 */
  if (!data || data.items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="text-center text-gray-500">
          <svg
            className="mx-auto h-12 w-12 text-gray-400 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-lg font-medium">暂无审查记录</p>
          <p className="text-sm mt-1">上传合同文件开始审查</p>
        </div>
      </div>
    );
  }

  const { items, total } = data;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* 列表头部 */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">审查记录</h3>
          <span className="text-sm text-gray-500">共 {total} 条记录</span>
        </div>
      </div>

      {/* 列表内容 */}
      <div className="divide-y divide-gray-200">
        {items.map((item: ContractReviewHistoryItem) => {
          const riskConfig = RISK_CONFIG[item.riskLevel];

          return (
            <div
              key={item.id}
              className="px-6 py-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                {/* 左侧：文件名和类型 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <svg
                      className="h-5 w-5 text-gray-400 flex-shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                      />
                    </svg>
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {item.filename}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                    {item.contractType && (
                      <span className="px-2 py-0.5 bg-gray-100 rounded">
                        {CONTRACT_TYPE_MAP[item.contractType] || item.contractType}
                      </span>
                    )}
                    <span>{formatDate(item.createdAt)}</span>
                    <span>ID: {item.requestId}</span>
                  </div>
                </div>

                {/* 中间：风险等级 */}
                <div className="mx-4">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${riskConfig.bg} ${riskConfig.color}`}
                  >
                    {riskConfig.label}
                    {item.riskCount > 0 && ` (${item.riskCount})`}
                  </span>
                </div>

                {/* 右侧：操作按钮 */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleViewDetail(item.id)}
                    className="px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors"
                  >
                    查看详情
                  </button>
                  <button
                    onClick={() => { void handleDelete(item.id); }}
                    disabled={deletingId === item.id}
                    className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50"
                  >
                    {deletingId === item.id ? '删除中...' : '删除'}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <span className="text-sm text-gray-700">
              第 {page} 页，共 {totalPages} 页
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );
}