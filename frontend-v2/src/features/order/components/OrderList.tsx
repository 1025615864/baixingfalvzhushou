/**
 * OrderList - 订单列表组件
 */

import type { Order, GetOrderListRequest } from '../types';
import { useOrderList, useCancelOrder } from '../hooks/useOrder';

import { OrderCard } from './OrderCard';

interface OrderListProps {
  params?: GetOrderListRequest;
  onOrderClick?: (order: Order) => void;
}

/**
 * 订单列表组件
 */
export function OrderList({ params = {}, onOrderClick }: OrderListProps): JSX.Element {
  const { data, isLoading, error, refetch } = useOrderList(params);
  const cancelOrderMutation = useCancelOrder();

  const handleCancelOrder = (order: Order): void => {
    if (!window.confirm(`确定要取消订单 ${order.orderNo} 吗？`)) {
      return;
    }

    cancelOrderMutation.mutateAsync({ orderNo: order.orderNo })
      .then(() => {
        void refetch();
      })
      .catch((err: unknown) => {
        const errorMessage = err instanceof Error ? err.message : '取消订单失败';
        alert(errorMessage);
      });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, index) => (
          <div 
            key={index} 
            className="bg-white rounded-lg border p-4 space-y-4"
          >
            <div className="flex items-center justify-between">
              <div className="w-32 h-4 bg-gray-200 rounded animate-pulse" />
              <div className="w-16 h-6 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="space-y-2">
              <div className="w-full h-4 bg-gray-200 rounded animate-pulse" />
              <div className="w-2/3 h-4 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500 bg-red-50 rounded-lg">
        <svg 
          className="w-12 h-12 mx-auto mb-3 text-red-400" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
          />
        </svg>
        <p className="text-lg font-medium mb-2">获取订单列表失败</p>
        <p className="text-sm text-red-400 mb-4">
          {error instanceof Error ? error.message : '请稍后重试'}
        </p>
        <button
          type="button"
          onClick={() => void refetch()}
          className="px-4 py-2 text-sm text-white bg-red-500 rounded hover:bg-red-600 transition-colors"
        >
          重新加载
        </button>
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500 bg-gray-50 rounded-lg">
        <svg 
          className="w-12 h-12 mx-auto mb-3 text-gray-300" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" 
          />
        </svg>
        <p className="text-lg font-medium mb-1">暂无订单</p>
        <p className="text-sm text-gray-400">您还没有任何订单记录</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {data.items.map((order) => (
        <OrderCard
          key={order.id}
          order={order}
          onClick={onOrderClick}
          onCancel={handleCancelOrder}
        />
      ))}
      
      {/* 分页信息 */}
      {data.totalPages > 1 && (
        <div className="flex items-center justify-between pt-4 text-sm text-gray-500">
          <span>
            共 {data.total} 条记录，第 {data.page}/{data.totalPages} 页
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={data.page <= 1}
              onClick={() => void refetch()}
              className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              上一页
            </button>
            <button
              type="button"
              disabled={data.page >= data.totalPages}
              onClick={() => void refetch()}
              className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );
}