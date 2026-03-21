import { statusConfig } from '../../hooks/usePayments';
import type { Order } from '../../types';

interface OrderCardProps {
  order: Order;
  onPay?: (orderId: number) => void;
  onCancel?: (orderId: number) => void;
  onViewDetail?: (_orderId: number) => void;
}

export function OrderCard({ order, onPay, onCancel, onViewDetail: _onViewDetail }: OrderCardProps): JSX.Element {
  const status = statusConfig[order.status];

  const handlePay = (e: React.MouseEvent): void => {
    e.stopPropagation();
    onPay?.(order.id);
  };

  const handleCancel = (e: React.MouseEvent): void => {
    e.stopPropagation();
    onCancel?.(order.id);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4" data-testid={`order-card-${order.id}`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-gray-400">订单号：{order.order_no}</span>
            <span className={`px-2 py-0.5 text-xs font-medium rounded ${status.color}`}>
              {status.label}
            </span>
          </div>
          <h3 className="font-semibold text-gray-900" data-testid={`order-title-${order.id}`}>{order.title}</h3>
          {order.description && (
            <p className="text-sm text-gray-500 mt-1">{order.description}</p>
          )}
        </div>
        <div className="text-right">
          <p className="text-lg font-bold text-gray-900">¥{Number(order.actual_amount).toFixed(2)}</p>
          {order.amount > order.actual_amount && (
            <p className="text-xs text-gray-400 line-through">
              ¥{Number(order.amount).toFixed(2)}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="text-xs text-gray-400">
          <time dateTime={order.created_at}>
            创建时间：{new Date(order.created_at).toLocaleString('zh-CN')}
          </time>
          {order.paid_at && (
            <div>
              支付时间：{new Date(order.paid_at).toLocaleString('zh-CN')}
            </div>
          )}
          {order.payment_method && (
            <div className="mt-1">
              支付方式：{
                ({
                  wechat: '微信支付',
                  alipay: '支付宝',
                  card: '银行卡',
                  balance: '余额',
                  ikunpay: 'IKunPay',
                } as Record<string, string>)[order.payment_method] || order.payment_method
              }
            </div>
          )}
        </div>

        {order.status === 'pending' && (
          <div className="flex gap-2">
            <button
              onClick={handleCancel}
              className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 transition-colors"
              type="button"
              data-testid={`order-cancel-${order.id}`}
            >
              取消
            </button>
            <button
              onClick={handlePay}
              className="px-4 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors"
              type="button"
              data-testid={`order-pay-${order.id}`}
            >
              立即支付
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
