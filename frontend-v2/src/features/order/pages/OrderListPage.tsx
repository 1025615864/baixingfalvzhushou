/**
 * OrderListPage - 订单列表页面
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import type { OrderFilterParams } from '../types';
import { OrderFilter } from '../components/OrderFilter';
import { OrderList } from '../components/OrderList';
import { useOrderStats } from '../hooks/useOrder';

/**
 * 订单列表页面
 */
export function OrderListPage(): JSX.Element {
  const navigate = useNavigate();
  const [filterParams, setFilterParams] = useState<OrderFilterParams>({});
  const { data: stats, isLoading: statsLoading } = useOrderStats();

  const handleOrderClick = (order: { orderNo: string }): void => {
    navigate(`/orders/${order.orderNo}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">我的订单</h1>
          <p className="text-gray-500 mt-1">查看和管理您的所有订单</p>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-sm text-gray-500 mb-1">总订单数</p>
            <p className="text-2xl font-bold text-gray-900">
              {statsLoading ? '-' : stats?.totalOrders || 0}
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-sm text-gray-500 mb-1">已完成</p>
            <p className="text-2xl font-bold text-green-600">
              {statsLoading ? '-' : stats?.completedCount || 0}
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-sm text-gray-500 mb-1">待处理</p>
            <p className="text-2xl font-bold text-yellow-600">
              {statsLoading ? '-' : stats?.pendingCount || 0}
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-sm text-gray-500 mb-1">总消费</p>
            <p className="text-2xl font-bold text-blue-600">
              {statsLoading ? '-' : `¥${(stats?.totalAmount || 0).toFixed(2)}`}
            </p>
          </div>
        </div>

        {/* 筛选器 */}
        <div className="mb-6">
          <OrderFilter 
            value={filterParams} 
            onChange={setFilterParams} 
          />
        </div>

        {/* 订单列表 */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">订单列表</h2>
          </div>
          <OrderList 
            params={{ 
              page: 1, 
              pageSize: 20,
              ...filterParams 
            }} 
            onOrderClick={handleOrderClick}
          />
        </div>
      </div>
    </div>
  );
}