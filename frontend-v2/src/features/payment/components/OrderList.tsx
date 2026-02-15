/**
 * 订单列表组件
 */

import React, { useState, useCallback } from 'react';

import type { Order, OrderListParams, PaymentStatus } from '../types';
import { useOrderList, useCancelOrder } from '../hooks/usePayment';

import { OrderCard } from './OrderCard/index';

export interface OrderListProps {
  onPayOrder?: (order: Order) => void;
  onViewDetail?: (order: Order) => void;
  pageSize?: number;
}

// 状态筛选选项
const statusOptions: Array<{ value: PaymentStatus | ''; label: string }> = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '待支付' },
  { value: 'paid', label: '已支付' },
  { value: 'cancelled', label: '已取消' },
  { value: 'refunded', label: '已退款' },
  { value: 'failed', label: '支付失败' },
];

/**
 * 加载中骨架屏
 */
function LoadingSkeleton(): React.ReactElement {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
          <div className="flex justify-between items-start mb-3">
            <div className="h-4 bg-gray-200 rounded w-32" />
            <div className="h-6 bg-gray-200 rounded-full w-16" />
          </div>
          <div className="space-y-2 mb-4">
            <div className="h-4 bg-gray-200 rounded w-full" />
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-4 bg-gray-200 rounded w-1/2" />
          </div>
          <div className="h-10 bg-gray-200 rounded w-full" />
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
    <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
      <div className="text-gray-400 mb-2">
        <svg
          className="mx-auto h-12 w-12"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">暂无订单</h3>
      <p className="text-gray-500 text-sm">您还没有任何订单记录</p>
    </div>
  );
}

/**
 * 错误状态
 */
function ErrorState({ onRetry }: { onRetry: () => void }): React.ReactElement {
  return (
    <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
      <div className="text-red-400 mb-2">
        <svg
          className="mx-auto h-12 w-12"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">加载失败</h3>
      <p className="text-gray-500 text-sm mb-4">无法加载订单列表，请稍后重试</p>
      <button
        type="button"
        onClick={onRetry}
        className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
      >
        重新加载
      </button>
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

  const pages: (number | string)[] = [];
  const maxVisiblePages = 5;

  if (totalPages <= maxVisiblePages) {
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i);
    }
  } else {
    if (currentPage <= 3) {
      pages.push(1, 2, 3, 4, '...', totalPages);
    } else if (currentPage >= totalPages - 2) {
      pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
    } else {
      pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
    }
  }

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
      
      {pages.map((page, index) => (
        <React.Fragment key={index}>
          {page === '...' ? (
            <span className="px-2 text-gray-500">...</span>
          ) : (
            <button
              type="button"
              onClick={() => onPageChange(page as number)}
              className={`px-3 py-2 rounded-lg text-sm font-medium ${
                currentPage === page
                  ? 'bg-blue-600 text-white'
                  : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {page}
            </button>
          )}
        </React.Fragment>
      ))}
      
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

export const OrderList: React.FC<OrderListProps> = ({
  onPayOrder,
  onViewDetail,
  pageSize = 10,
}) => {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<PaymentStatus | ''>('');

  const params: OrderListParams = {
    page,
    page_size: pageSize,
    ...(statusFilter && { status_filter: statusFilter }),
  };

  const { data, isLoading, isError, refetch } = useOrderList(params);
  const cancelOrderMutation = useCancelOrder();

  const handleStatusChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value as PaymentStatus | '');
    setPage(1);
  }, []);

  const handlePay = useCallback((orderId: number) => {
    const order = data?.items.find(o => o.id === orderId);
    if (order) {
      onPayOrder?.(order);
    }
  }, [onPayOrder, data?.items]);

  const handleCancel = useCallback((orderId: number) => {
    if (!window.confirm('确定要取消该订单吗？')) {
      return;
    }

    void cancelOrderMutation.mutateAsync(String(orderId));
  }, [cancelOrderMutation]);

  const handleViewDetail = useCallback((orderId: number) => {
    const order = data?.items.find(o => o.id === orderId);
    if (order) {
      onViewDetail?.(order);
    }
  }, [onViewDetail, data?.items]);

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const handleRetry = useCallback(() => {
    void refetch();
  }, [refetch]);

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div className="space-y-4">
      {/* 筛选栏 */}
      <div className="flex justify-between items-center bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center gap-4">
          <label htmlFor="status-filter" className="text-sm font-medium text-gray-700">
            订单状态：
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={handleStatusChange}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="text-sm text-gray-500">
          共 {data?.total || 0} 条记录
        </div>
      </div>

      {/* 订单列表 */}
      {isLoading ? (
        <LoadingSkeleton />
      ) : isError ? (
        <ErrorState onRetry={handleRetry} />
      ) : data?.items.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-4">
          {data?.items.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              onPay={handlePay}
              onCancel={handleCancel}
              onViewDetail={handleViewDetail}
            />
          ))}
        </div>
      )}

      {/* 分页 */}
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

export default OrderList;