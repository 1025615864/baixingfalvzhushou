/**
 * 支付历史组件（余额交易记录）
 */

import React, { useState, useCallback } from 'react';

import type { BalanceTransaction } from '../types';
import { useBalanceTransactions } from '../hooks/usePayment';

export interface PaymentHistoryProps {
  pageSize?: number;
}

// 交易类型映射
const transactionTypeMap: Record<string, { label: string; color: string; sign: string }> = {
  recharge: { label: '充值', color: 'text-green-600', sign: '+' },
  consume: { label: '消费', color: 'text-red-600', sign: '-' },
  refund: { label: '退款', color: 'text-blue-600', sign: '+' },
};

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 格式化金额
 */
function formatAmount(amount: number): string {
  return `¥${Math.abs(amount).toFixed(2)}`;
}

/**
 * 加载中骨架屏
 */
function LoadingSkeleton(): React.ReactElement {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="bg-gray-50 rounded-lg p-4 animate-pulse">
          <div className="flex justify-between items-center">
            <div className="h-4 bg-gray-200 rounded w-1/3" />
            <div className="h-4 bg-gray-200 rounded w-20" />
          </div>
          <div className="mt-2 h-3 bg-gray-200 rounded w-2/3" />
        </div>
      ))}
    </div>
  );
}

/**
 * 空状态
 */
function EmptyState(): React.ReactElement {
  return (
    <div className="text-center py-12">
      <div className="text-gray-400 mb-2">
        <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">暂无交易记录</h3>
      <p className="text-gray-500 text-sm">您还没有余额交易记录</p>
    </div>
  );
}

/**
 * 交易记录项
 */
function TransactionItem({ transaction }: { transaction: BalanceTransaction }): React.ReactElement {
  const typeInfo = transactionTypeMap[transaction.type] || { label: transaction.type, color: 'text-gray-600', sign: '' };

  return (
    <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`font-medium ${typeInfo.color}`}>
              {typeInfo.sign}{formatAmount(transaction.amount)}
            </span>
            <span className="text-sm text-gray-500">·</span>
            <span className="text-sm text-gray-600">{typeInfo.label}</span>
          </div>
          {transaction.description && (
            <p className="text-sm text-gray-600 mb-1">{transaction.description}</p>
          )}
          <p className="text-xs text-gray-400">{formatDate(transaction.created_at)}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">余额</p>
          <p className="text-sm font-medium text-gray-700">¥{transaction.balance_after.toFixed(2)}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * 分页组件
 */
function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}): React.ReactElement | null {
  if (totalPages <= 1) return null;

  return (
    <div className="flex justify-center items-center gap-2 mt-6">
      <button
        type="button"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        上一页
      </button>
      
      <span className="px-4 py-2 text-sm text-gray-600">
        第 {currentPage} 页 / 共 {totalPages} 页
      </span>
      
      <button
        type="button"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        下一页
      </button>
    </div>
  );
}

export const PaymentHistory: React.FC<PaymentHistoryProps> = ({ pageSize = 20 }) => {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, refetch } = useBalanceTransactions(page, pageSize);

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const handleRetry = useCallback(() => {
    void refetch();
  }, [refetch]);

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (isError) {
    return (
      <div className="text-center py-12">
        <div className="text-red-400 mb-2">
          <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">加载失败</h3>
        <p className="text-gray-500 text-sm mb-4">无法加载交易记录</p>
        <button
          type="button"
          onClick={handleRetry}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          重新加载
        </button>
      </div>
    );
  }

  if (!data?.items.length) {
    return <EmptyState />;
  }

  return (
    <div data-testid="payment-history-table">
      <div className="space-y-3">
        {data.items.map((transaction) => (
          <TransactionItem key={transaction.id} transaction={transaction} />
        ))}
      </div>
      
      {totalPages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
};

export default PaymentHistory;