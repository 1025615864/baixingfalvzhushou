import { useOrders } from '../../hooks/usePayments';
import { OrderCard } from '../OrderCard';
import type { Order } from '../../types';

interface OrderListProps {
  onPay?: (orderId: number) => void;
  onCancel?: (orderId: number) => void;
}

export function OrderList({ onPay, onCancel }: OrderListProps): JSX.Element {
  const { data: orders, isLoading, isError } = useOrders();

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }, (_, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 animate-pulse"
          >
            <div className="space-y-3">
              <div className="h-5 bg-gray-200 rounded w-1/3" />
              <div className="h-4 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">加载订单失败，请稍后重试</p>
      </div>
    );
  }

  const orderList = orders?.items ?? [];

  if (!orderList.length) {
    return (
      <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500">暂无订单</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {orderList.map((order: Order) => (
        <OrderCard
          key={order.id}
          order={order}
          onPay={onPay}
          onCancel={onCancel}
        />
      ))}
    </div>
  );
}
