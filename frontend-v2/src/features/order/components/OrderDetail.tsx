/**
 * OrderDetail - 订单详情组件
 */

import { useOrderDetail, useCancelOrder } from '../hooks/useOrder';
import type { Order } from '../types';

interface OrderDetailProps {
  orderNo: string;
  onClose?: () => void;
  onOrderUpdate?: () => void;
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
 * 订单详情组件
 */
export function OrderDetail({ orderNo, onClose, onOrderUpdate }: OrderDetailProps): JSX.Element {
  const { data: order, isLoading, error } = useOrderDetail(orderNo);
  const cancelOrderMutation = useCancelOrder();

  const handleCancelOrder = (): void => {
    if (!order) return;
    
    if (!window.confirm(`确定要取消订单 ${order.orderNo} 吗？`)) {
      return;
    }

    void cancelOrderMutation.mutateAsync({ orderNo: order.orderNo })
      .then(() => {
        onOrderUpdate?.();
      })
      .catch((err: unknown) => {
        const errorMessage = err instanceof Error ? err.message : '取消订单失败';
        alert(errorMessage);
      });
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="w-32 h-6 bg-gray-200 rounded animate-pulse" />
          <div className="w-20 h-8 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="flex items-center gap-4">
              <div className="w-24 h-4 bg-gray-200 rounded animate-pulse" />
              <div className="flex-1 h-4 bg-gray-200 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="bg-white rounded-lg border p-8 text-center">
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
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
          />
        </svg>
        <p className="text-lg font-medium text-gray-900 mb-2">加载订单详情失败</p>
        <p className="text-sm text-gray-500 mb-4">
          {error instanceof Error ? error.message : '请稍后重试'}
        </p>
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border rounded hover:bg-gray-50"
        >
          返回
        </button>
      </div>
    );
  }

  const isCancellable = order.status === 'pending';

  return (
    <div className="bg-white rounded-lg border">
      {/* 头部 */}
      <div className="flex items-center justify-between px-6 py-4 border-b">
        <div>
          <h2 className="text-lg font-medium text-gray-900">订单详情</h2>
          <p className="text-sm text-gray-500 mt-1">订单号：{order.orderNo}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusStyle(order.status)}`}>
            {getStatusLabel(order.status)}
          </span>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* 订单信息 */}
      <div className="px-6 py-6 space-y-6">
        {/* 基本信息 */}
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">基本信息</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">订单类型</span>
              <span className="text-gray-900">{getOrderTypeLabel(order.orderType)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">订单标题</span>
              <span className="text-gray-900 text-right max-w-[200px] truncate">{order.title}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">创建时间</span>
              <span className="text-gray-900">{formatDate(order.createdAt)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">支付时间</span>
              <span className="text-gray-900">{formatDate(order.paidAt)}</span>
            </div>
          </div>
        </div>

        {/* 支付信息 */}
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">支付信息</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">订单金额</span>
              <span className="text-gray-900">{formatAmount(order.amount)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">实付金额</span>
              <span className="text-lg font-bold text-blue-600">{formatAmount(order.actualAmount)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">支付方式</span>
              <span className="text-gray-900">{getPaymentMethodLabel(order.paymentMethod)}</span>
            </div>
          </div>
        </div>

        {/* 订单描述 */}
        {order.description && (
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">订单描述</h3>
            <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
              {order.description}
            </p>
          </div>
        )}
      </div>

      {/* 底部操作 */}
      <div className="flex items-center justify-end gap-3 px-6 py-4 border-t bg-gray-50 rounded-b-lg">
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border rounded hover:bg-white transition-colors"
          >
            返回列表
          </button>
        )}
        {isCancellable && (
          <button
            type="button"
            onClick={handleCancelOrder}
            disabled={cancelOrderMutation.isPending}
            className="px-4 py-2 text-sm text-white bg-red-500 rounded hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {cancelOrderMutation.isPending ? '取消中...' : '取消订单'}
          </button>
        )}
      </div>
    </div>
  );
}