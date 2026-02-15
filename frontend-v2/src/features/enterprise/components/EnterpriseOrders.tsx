/**
 * EnterpriseOrders - 企业订单组件
 */

import { useState } from 'react';

import type { OrderStatus, OrderType } from '../types';
import { useEnterpriseOrders } from '../hooks/useEnterprise';

interface EnterpriseOrdersProps {
  accountId: number;
}

const statusLabels: Record<OrderStatus, string> = {
  pending: '待支付',
  paid: '已支付',
  processing: '处理中',
  completed: '已完成',
  cancelled: '已取消',
  refunded: '已退款',
};

const statusColors: Record<OrderStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  paid: 'bg-blue-100 text-blue-800',
  processing: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-gray-100 text-gray-800',
  refunded: 'bg-red-100 text-red-800',
};

const orderTypeLabels: Record<OrderType, string> = {
  subscription: '订阅服务',
  service: '增值服务',
  consultation: '咨询服务',
  document: '文档服务',
  other: '其他',
};

/**
 * 企业订单组件
 */
export function EnterpriseOrders({ accountId }: EnterpriseOrdersProps): JSX.Element {
  const [filterStatus, setFilterStatus] = useState<OrderStatus | ''>('');
  const [filterType, setFilterType] = useState<OrderType | ''>('');

  const { data: orders, isLoading, error } = useEnterpriseOrders(accountId, {
    status: filterStatus || undefined,
    orderType: filterType || undefined,
    limit: 50,
  });

  const filteredOrders = orders || [];

  const getTotalAmount = (): number => {
    return filteredOrders.reduce((sum, order) => sum + order.amount, 0);
  };

  if (isLoading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="space-y-2">
            <div className="h-12 bg-gray-200 rounded" />
            <div className="h-12 bg-gray-200 rounded" />
            <div className="h-12 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="text-red-500">加载订单失败</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">企业订单</h2>
          <p className="text-sm text-gray-500 mt-1">
            共 {filteredOrders.length} 笔订单，总计 ¥{getTotalAmount().toFixed(2)}
          </p>
        </div>
        <div className="flex gap-3">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as OrderStatus | '')}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部状态</option>
            <option value="pending">待支付</option>
            <option value="paid">已支付</option>
            <option value="processing">处理中</option>
            <option value="completed">已完成</option>
            <option value="cancelled">已取消</option>
            <option value="refunded">已退款</option>
          </select>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as OrderType | '')}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部类型</option>
            <option value="subscription">订阅服务</option>
            <option value="service">增值服务</option>
            <option value="consultation">咨询服务</option>
            <option value="document">文档服务</option>
            <option value="other">其他</option>
          </select>
        </div>
      </div>

      {/* 订单列表 */}
      {filteredOrders.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <p className="text-gray-500">暂无订单</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="pb-3 font-medium text-gray-700">订单号</th>
                <th className="pb-3 font-medium text-gray-700">类型</th>
                <th className="pb-3 font-medium text-gray-700">描述</th>
                <th className="pb-3 font-medium text-gray-700">金额</th>
                <th className="pb-3 font-medium text-gray-700">状态</th>
                <th className="pb-3 font-medium text-gray-700">创建时间</th>
                <th className="pb-3 font-medium text-gray-700 text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order) => (
                <tr key={order.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                  <td className="py-4">
                    <span className="font-mono text-sm text-gray-900">#{order.id.slice(-8)}</span>
                  </td>
                  <td className="py-4">
                    <span className="text-sm text-gray-600">{orderTypeLabels[order.orderType]}</span>
                  </td>
                  <td className="py-4">
                    <span className="text-sm text-gray-900 truncate max-w-xs block" title={order.description}>
                      {order.description}
                    </span>
                  </td>
                  <td className="py-4">
                    <span className="font-medium text-gray-900">¥{order.amount.toFixed(2)}</span>
                  </td>
                  <td className="py-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColors[order.status]}`}>
                      {statusLabels[order.status]}
                    </span>
                  </td>
                  <td className="py-4 text-sm text-gray-600">
                    {new Date(order.createdAt).toLocaleDateString('zh-CN')}
                  </td>
                  <td className="py-4 text-right">
                    <button
                      className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
                    >
                      详情
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}