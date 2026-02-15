/**
 * OrderCard - 订单卡片组件
 */

import type { Order } from '../types';

interface OrderCardProps {
  order: Order;
  onClick?: (order: Order) => void;
  onCancel?: (order: Order) => void;
}

/**
 * 获取订单状态显示文本
 */
function getStatusLabel(status: Order['status']): string {
  const statusMap: Record<Order['status'], string> = {
    pending: '待支付',
    paid: '已支付',
    processing: '处理中',
    completed: '已完成',
    cancelled: '已取消',
    refunded: '已退款',
  };
  return statusMap[status];
}

/**
 * 获取订单状态样式
 */
function getStatusStyle(status: Order['status']): string {
  const styleMap: Record<Order['status'], string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    paid: 'bg-blue-100 text-blue-700',
    processing: 'bg-indigo-100 text-indigo-700',
    completed: 'bg-green-100 text-green-700',
    cancelled: 'bg-gray-100 text-gray-700',
    refunded: 'bg-purple-100 text-purple-700',
  };
  return styleMap[status];
}

/**
 * 获取订单类型显示文本
 */
function getOrderTypeLabel(orderType: Order['orderType']): string {
  const typeMap: Record<Order['orderType'], string> = {
    consultation: '咨询订单',
    document: '文档订单',
    membership: '会员订单',
    service: '服务订单',
    other: '其他订单',
  };
  return typeMap[orderType];
}

/**
 * 获取支付方式显示文本
 */
function getPaymentMethodLabel(method: Order['paymentMethod']): string {
  if (!method) return '-';
  const methodMap: Record<string, string> = {
    wechat: '微信支付',
    alipay: '支付宝',
    balance: '余额支付',
    card: '银行卡',
    other: '其他',
  };
  return methodMap[method] || method;
}

/**
 * 格式化日期
 */
function formatDate(dateString: string | null): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 格式化金额
 */
function formatAmount(amount: number): string {
  return `¥${amount.toFixed(2)}`;
}

/**
 * 订单卡片组件
 */
export function OrderCard({ order, onClick, onCancel }: OrderCardProps): JSX.Element {
  const isCancellable = order.status === 'pending';

  return (
    <div 
      className="bg-white rounded-lg border hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onClick?.(order)}
      role="button"
      tabIndex={0}
    >
      {/* 头部：订单号和状态 */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">订单号：</span>
          <span className="text-sm font-medium text-gray-900">{order.orderNo}</span>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusStyle(order.status)}`}>
          {getStatusLabel(order.status)}
        </span>
      </div>

      {/* 主体内容 */}
      <div className="px-4 py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            {/* 订单标题 */}
            <h3 className="text-base font-medium text-gray-900 truncate mb-2">
              {order.title}
            </h3>
            
            {/* 订单信息 */}
            <div className="space-y-1 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <span>类型：</span>
                <span>{getOrderTypeLabel(order.orderType)}</span>
              </div>
              <div className="flex items-center gap-2">
                <span>支付方式：</span>
                <span>{getPaymentMethodLabel(order.paymentMethod)}</span>
              </div>
              <div className="flex items-center gap-2">
                <span>创建时间：</span>
                <span>{formatDate(order.createdAt)}</span>
              </div>
              {order.paidAt && (
                <div className="flex items-center gap-2">
                  <span>支付时间：</span>
                  <span>{formatDate(order.paidAt)}</span>
                </div>
              )}
            </div>
          </div>

          {/* 金额信息 */}
          <div className="text-right">
            <div className="text-lg font-bold text-gray-900">
              {formatAmount(order.actualAmount)}
            </div>
            {order.actualAmount !== order.amount && (
              <div className="text-sm text-gray-400 line-through">
                {formatAmount(order.amount)}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 底部操作按钮 */}
      <div className="flex items-center justify-end gap-2 px-4 py-3 border-t bg-gray-50 rounded-b-lg">
        <button
          type="button"
          className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          onClick={(e) => {
            e.stopPropagation();
            onClick?.(order);
          }}
        >
          查看详情
        </button>
        {isCancellable && onCancel && (
          <button
            type="button"
            className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onCancel(order);
            }}
          >
            取消订单
          </button>
        )}
      </div>
    </div>
  );
}
