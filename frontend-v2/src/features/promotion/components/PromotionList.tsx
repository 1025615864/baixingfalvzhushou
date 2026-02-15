/**
 * PromotionList - 推广链接列表组件
 */

import { useState } from 'react';

import { useCommissionRecords } from '../hooks/usePromotion';
import type { CommissionRecord } from '../types';

interface PromotionListProps {
  className?: string;
}

const statusLabels: Record<CommissionRecord['status'], string> = {
  pending: '待确认',
  confirmed: '已确认',
  paid: '已支付',
  cancelled: '已取消',
};

const statusColors: Record<CommissionRecord['status'], string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  paid: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};

/**
 * 推广链接列表组件
 */
export function PromotionList({ className = '' }: PromotionListProps): JSX.Element {
  const [status, setStatus] = useState<CommissionRecord['status'] | undefined>(undefined);
  const { data, isLoading, error } = useCommissionRecords({ status, limit: 20 });

  const handleStatusChange = (newStatus: CommissionRecord['status'] | ''): void => {
    setStatus(newStatus || undefined);
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4" />
          <div className="space-y-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="text-center text-red-500">
          <p>获取佣金记录失败</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">佣金记录</h3>
        <select
          value={status || ''}
          onChange={(e) => handleStatusChange(e.target.value as CommissionRecord['status'] | '')}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">全部状态</option>
          <option value="pending">待确认</option>
          <option value="confirmed">已确认</option>
          <option value="paid">已支付</option>
          <option value="cancelled">已取消</option>
        </select>
      </div>

      {data?.records && data.records.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="pb-3 text-left font-medium text-gray-700">订单号</th>
                <th className="pb-3 text-left font-medium text-gray-700">来源用户</th>
                <th className="pb-3 text-left font-medium text-gray-700">订单金额</th>
                <th className="pb-3 text-left font-medium text-gray-700">佣金</th>
                <th className="pb-3 text-left font-medium text-gray-700">状态</th>
                <th className="pb-3 text-left font-medium text-gray-700">时间</th>
              </tr>
            </thead>
            <tbody>
              {data.records.map((record) => (
                <tr key={record.id} className="border-b border-gray-100 last:border-0">
                  <td className="py-4 text-sm font-mono text-gray-600">{record.orderId.slice(0, 12)}...</td>
                  <td className="py-4 text-sm text-gray-900">
                    {record.sourceUserName || `用户${record.sourceUserId || ''}`}
                  </td>
                  <td className="py-4 text-sm text-gray-900">¥{record.orderAmount.toFixed(2)}</td>
                  <td className="py-4 text-sm font-medium text-green-600">
                    ¥{record.commissionAmount.toFixed(2)}
                  </td>
                  <td className="py-4">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColors[record.status]}`}
                    >
                      {statusLabels[record.status]}
                    </span>
                  </td>
                  <td className="py-4 text-sm text-gray-500">
                    {new Date(record.createdAt).toLocaleDateString('zh-CN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          </div>
          <p className="text-gray-500">暂无佣金记录</p>
        </div>
      )}

      {/* 汇总信息 */}
      {data?.total !== undefined && (
        <div className="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500 text-center">
          共 {data.total} 条记录
        </div>
      )}
    </div>
  );
}