/**
 * 支付结果页面
 */

import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

import { useOrderDetail } from '../hooks/usePayment';

/**
 * 支付结果状态
 */
type ResultStatus = 'loading' | 'success' | 'failed' | 'error';

/**
 * 结果图标组件
 */
function ResultIcon({ status }: { status: ResultStatus }): React.ReactElement {
  switch (status) {
    case 'success':
      return (
        <div className="w-24 h-24 rounded-full bg-green-100 flex items-center justify-center mb-6">
          <svg className="w-12 h-12 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      );
    case 'failed':
    case 'error':
      return (
        <div className="w-24 h-24 rounded-full bg-red-100 flex items-center justify-center mb-6">
          <svg className="w-12 h-12 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      );
    default:
      return (
        <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center mb-6">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-200 border-t-blue-600" />
        </div>
      );
  }
}

/**
 * 结果标题
 */
function ResultTitle({ status }: { status: ResultStatus }): string {
  switch (status) {
    case 'success':
      return '支付成功';
    case 'failed':
      return '支付失败';
    case 'error':
      return '查询失败';
    default:
      return '正在查询支付结果...';
  }
}

/**
 * 结果描述
 */
function ResultDescription({ status, orderNo }: { status: ResultStatus; orderNo?: string }): React.ReactElement {
  switch (status) {
    case 'success':
      return (
        <div className="space-y-2">
          <p className="text-gray-600">您的订单已成功支付</p>
          {orderNo && (
            <p className="text-sm text-gray-500">
              订单号：<span className="font-mono">{orderNo}</span>
            </p>
          )}
        </div>
      );
    case 'failed':
      return <p className="text-gray-600">支付未成功，请重试或联系客服</p>;
    case 'error':
      return <p className="text-gray-600">无法查询订单状态，请稍后查看订单列表</p>;
    default:
      return <p className="text-gray-600">请稍候，正在确认支付结果...</p>;
  }
}

export const PaymentResultPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [resultStatus, setResultStatus] = useState<ResultStatus>('loading');

  // 从URL参数获取订单号
  const orderNo = searchParams.get('order_no') || '';

  // 查询订单详情
  const { data: order, isLoading, isError } = useOrderDetail(orderNo);

  useEffect(() => {
    if (isLoading) {
      setResultStatus('loading');
    } else if (isError) {
      setResultStatus('error');
    } else if (order) {
      if (order.status === 'paid') {
        setResultStatus('success');
      } else if (order.status === 'failed' || order.status === 'cancelled') {
        setResultStatus('failed');
      } else {
        // 订单状态仍为 pending，继续等待
        setResultStatus('loading');
      }
    }
  }, [order, isLoading, isError]);

  const handleGoToOrders = () => {
    navigate('/orders');
  };

  const handleGoToHome = () => {
    navigate('/');
  };

  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
        {/* 结果图标 */}
        <div className="flex justify-center">
          <ResultIcon status={resultStatus} />
        </div>

        {/* 结果标题 */}
        <h1 className={`text-2xl font-bold mb-4 ${
          resultStatus === 'success' ? 'text-green-600' : 
          resultStatus === 'failed' || resultStatus === 'error' ? 'text-red-600' : 
          'text-blue-600'
        }`}>
          {ResultTitle({ status: resultStatus })}
        </h1>

        {/* 结果描述 */}
        <div className="mb-8">
          <ResultDescription status={resultStatus} orderNo={orderNo} />
        </div>

        {/* 操作按钮 */}
        <div className="space-y-3">
          {resultStatus === 'success' ? (
            <>
              <button
                type="button"
                onClick={handleGoToOrders}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                查看订单
              </button>
              <button
                type="button"
                onClick={handleGoToHome}
                className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
              >
                返回首页
              </button>
            </>
          ) : resultStatus === 'failed' || resultStatus === 'error' ? (
            <>
              <button
                type="button"
                onClick={handleGoToOrders}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                查看订单状态
              </button>
              {resultStatus === 'error' && (
                <button
                  type="button"
                  onClick={handleRetry}
                  className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  重新查询
                </button>
              )}
            </>
          ) : (
            <div className="text-sm text-gray-500">
              <p>请勿关闭页面，等待支付结果确认</p>
              <p className="mt-2">预计需要 2-3 秒</p>
            </div>
          )}
        </div>

        {/* 客服信息 */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            遇到问题？请联系客服
          </p>
          <p className="text-sm text-gray-400 mt-1">
            客服电话：400-xxx-xxxx
          </p>
        </div>
      </div>
    </div>
  );
};

export default PaymentResultPage;