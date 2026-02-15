/**
 * OrderDetailPage - 订单详情页面
 */

import { useParams, useNavigate } from 'react-router-dom';

import { OrderDetail } from '../components/OrderDetail';

/**
 * 订单详情页面
 */
export function OrderDetailPage(): JSX.Element {
  const { orderNo } = useParams<{ orderNo: string }>();
  const navigate = useNavigate();

  const handleClose = (): void => {
    navigate('/orders');
  };

  const handleOrderUpdate = (): void => {
    // 订单更新后刷新页面
    window.location.reload();
  };

  if (!orderNo) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500">无效的订单号</p>
          <button
            type="button"
            onClick={handleClose}
            className="mt-4 px-4 py-2 text-sm text-blue-600 hover:text-blue-700"
          >
            返回订单列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* 返回按钮 */}
        <button
          type="button"
          onClick={handleClose}
          className="mb-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回订单列表
        </button>

        {/* 订单详情 */}
        <OrderDetail 
          orderNo={orderNo} 
          onClose={handleClose}
          onOrderUpdate={handleOrderUpdate}
        />
      </div>
    </div>
  );
}