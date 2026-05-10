/**
 * 订单管理页面
 */

import React, { useState, useCallback } from 'react';

import type { Order } from '../types';
import { useBalance } from '../hooks/usePayment';
import { OrderList } from '../components/OrderList';
import { PaymentModal } from '../components/PaymentModal';
import { PaymentHistory } from '../components/PaymentHistory';

/**
 * 余额卡片组件
 */
function BalanceCard(): React.ReactElement {
  const { data: balance, isLoading } = useBalance();

  if (isLoading) {
    return (
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl p-6 text-white animate-pulse">
        <div className="h-4 bg-white/20 rounded w-20 mb-4" />
        <div className="h-8 bg-white/20 rounded w-32" />
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl p-6 text-white" data-testid="wallet-balance">
      <p className="text-blue-100 text-sm mb-1">账户余额</p>
      <p className="text-3xl font-bold">¥{balance?.balance.toFixed(2) || '0.00'}</p>
      <div className="flex gap-4 mt-4 text-sm">
        <div>
          <p className="text-blue-100">累计充值</p>
          <p className="font-medium">¥{balance?.total_recharged.toFixed(2) || '0.00'}</p>
        </div>
        <div>
          <p className="text-blue-100">累计消费</p>
          <p className="font-medium">¥{balance?.total_consumed.toFixed(2) || '0.00'}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * 快速操作卡片
 */
function QuickActions(): React.ReactElement {
  const actions = [
    {
      label: 'VIP会员',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
      ),
      href: '/pricing',
    },
    {
      label: '余额充值',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      ),
      href: '/recharge',
    },
    {
      label: 'AI咨询',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      ),
      href: '/ai-chat',
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">快速操作</h3>
      <div className="grid grid-cols-3 gap-4">
        {actions.map((action) => (
          <a
            key={action.label}
            href={action.href}
            className="flex flex-col items-center p-4 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="text-blue-600 mb-2">{action.icon}</div>
            <span className="text-sm text-gray-700">{action.label}</span>
          </a>
        ))}
      </div>
    </div>
  );
}

export const OrdersPage: React.FC = () => {
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'orders' | 'history'>('orders');

  interface Product {
    id: string;
    name: string;
    price: number;
    type: string;
  }

  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // 产品列表
  const products: Product[] = [
    { id: 'consultation-1', name: 'AI 法律咨询', price: 9.9, type: 'consultation' },
    { id: 'consultation-5', name: '5 次 AI 法律咨询', price: 39.9, type: 'consultation' },
    { id: 'vip-month', name: '月度 VIP 会员', price: 29.9, type: 'vip' },
  ];

  const handleSelectProduct = (product: Product) => {
    setSelectedProduct(product);
  };

  const handleBuyProduct = () => {
    if (!selectedProduct) return;
    // 创建订单逻辑 - 这里可以调用 API 创建订单
    alert(`购买产品：${selectedProduct.name}`);
  };

  const handlePayOrder = useCallback((order: Order) => {
    setSelectedOrder(order);
    setIsPaymentModalOpen(true);
  }, []);

  const handleClosePaymentModal = useCallback(() => {
    setIsPaymentModalOpen(false);
    setSelectedOrder(null);
  }, []);

  const handlePaymentSuccess = useCallback(() => {
    setIsPaymentModalOpen(false);
    setSelectedOrder(null);
  }, []);

  const handleViewDetail = useCallback((order: Order) => {
    // 可以导航到订单详情页或显示详情弹窗
    alert(`订单详情: ${order.order_no}`);
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">支付订单</h1>
        <p className="text-gray-600 mt-1">管理您的订单和支付记录</p>
      </div>

      {/* 产品选择区域 */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">选择服务</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {products.map((product) => (
            <button
              key={product.id}
              type="button"
              data-testid={`product-${product.id}`}
              onClick={() => handleSelectProduct(product)}
              className={`p-4 rounded-lg border-2 transition-all text-left ${
                selectedProduct?.id === product.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <h3 className="font-medium text-gray-900">{product.name}</h3>
              <p className="text-lg font-bold text-blue-600 mt-1">¥{product.price.toFixed(2)}</p>
            </button>
          ))}
        </div>
        {selectedProduct && (
          <div className="mt-4">
            <button
              type="button"
              data-testid="buy-product-button"
              onClick={handleBuyProduct}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              立即购买
            </button>
          </div>
        )}
      </div>

      {/* 顶部信息区 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="md:col-span-2">
          <BalanceCard />
        </div>
        <div>
          <QuickActions />
        </div>
      </div>

      {/* 标签页切换 */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="flex border-b border-gray-200">
          <button
            type="button"
            onClick={() => setActiveTab('orders')}
            className={`flex-1 py-4 text-sm font-medium text-center transition-colors ${
              activeTab === 'orders'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            订单列表
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('history')}
            className={`flex-1 py-4 text-sm font-medium text-center transition-colors ${
              activeTab === 'history'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            交易记录
          </button>
        </div>

        {/* 内容区域 */}
        <div className="p-6">
          {activeTab === 'orders' ? (
            <OrderList
              onPay={(orderId: number) => handlePayOrder({ id: orderId } as Order)}
              onCancel={() => {}}
            />
          ) : (
            <PaymentHistory pageSize={10} />
          )}
        </div>
      </div>

      {/* 支付弹窗 */}
      <PaymentModal
        order={selectedOrder}
        isOpen={isPaymentModalOpen}
        onClose={handleClosePaymentModal}
        onSuccess={handlePaymentSuccess}
      />
    </div>
  );
};

export default OrdersPage;