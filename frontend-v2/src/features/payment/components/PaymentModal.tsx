/**
 * 支付弹窗组件
 */

import React, { useState, useCallback } from 'react';

import type { Order, PaymentMethod } from '../types';
import { useBalance, usePayOrder, usePaymentPolling } from '../hooks/usePayment';

import { PaymentMethodSelector } from './PaymentMethodSelector';
import { PaymentQRCode } from './PaymentQRCode';
import { PaymentStatus } from './PaymentStatus';

export interface PaymentModalProps {
  order: Order | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

/**
 * 格式化金额
 */
function formatAmount(amount: number): string {
  return `¥${amount.toFixed(2)}`;
}

export const PaymentModal: React.FC<PaymentModalProps> = ({
  order,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod | null>(null);
  const [payUrl, setPayUrl] = useState<string | null>(null);
  
  const { data: balance } = useBalance();
  const payOrderMutation = usePayOrder();

  // 支付状态轮询
  const {
    pollingStatus,
    attempts,
    startPolling,
    stopPolling,
  } = usePaymentPolling(
    order?.order_no ?? null,
    order?.status ?? 'pending',
    () => {
      // 支付成功
      onSuccess?.();
    },
    () => {
      // 支付失败
      // 可以在这里显示错误提示
    }
  );

  const handleMethodSelect = useCallback((method: PaymentMethod) => {
    setSelectedMethod(method);
  }, []);

  const handlePay = useCallback(async () => {
    if (!order || !selectedMethod) return;

    try {
      const result = await payOrderMutation.mutateAsync({
        orderNo: order.order_no,
        data: { payment_method: selectedMethod },
      });

      if (result.pay_url) {
        setPayUrl(result.pay_url);
      }

      // 开始轮询支付状态
      startPolling();
    } catch {
      // 错误已在 mutation 中处理
    }
  }, [order, selectedMethod, payOrderMutation, startPolling]);

  const handleClose = useCallback(() => {
    stopPolling();
    setSelectedMethod(null);
    setPayUrl(null);
    onClose();
  }, [onClose, stopPolling]);

  const handleRetry = useCallback(() => {
    setSelectedMethod(null);
    setPayUrl(null);
    stopPolling();
  }, [stopPolling]);

  if (!isOpen || !order) return null;

  // 支付状态显示
  const showPaymentStatus = pollingStatus === 'polling' || pollingStatus === 'success' || pollingStatus === 'failed' || pollingStatus === 'timeout';

  // 支付二维码显示
  const showQRCode = payUrl && pollingStatus === 'polling';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 遮罩层 */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={handleClose}
      />

      {/* 弹窗内容 */}
      <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            订单支付
          </h2>
          <button
            type="button"
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 订单信息 */}
        {!showPaymentStatus && (
          <div className="p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">订单号</span>
              <span className="text-sm font-mono text-gray-800">{order.order_no}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">支付金额</span>
              <span className="text-2xl font-bold text-blue-600">{formatAmount(order.actual_amount)}</span>
            </div>
          </div>
        )}

        {/* 内容区域 */}
        <div className="p-4">
          {showPaymentStatus ? (
            <PaymentStatus 
              status={pollingStatus} 
              attempts={attempts}
              errorMessage={payOrderMutation.error?.message}
            />
          ) : showQRCode ? (
            <PaymentQRCode
              payUrl={payUrl}
              orderNo={order.order_no}
              amount={order.actual_amount}
              paymentMethod={selectedMethod || 'alipay'}
              onTimeout={() => {
                stopPolling();
              }}
            />
          ) : (
            <PaymentMethodSelector
              selectedMethod={selectedMethod}
              onSelect={handleMethodSelect}
              balance={balance?.balance || 0}
            />
          )}
        </div>

        {/* 底部按钮 */}
        <div className="p-4 border-t border-gray-200 space-y-2">
          {pollingStatus === 'success' ? (
            <button
              type="button"
              onClick={handleClose}
              className="w-full bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 transition-colors"
            >
              完成
            </button>
          ) : pollingStatus === 'failed' || pollingStatus === 'timeout' ? (
            <>
              <button
                type="button"
                onClick={handleRetry}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                重新支付
              </button>
              <button
                type="button"
                onClick={handleClose}
                className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
              >
                稍后再说
              </button>
            </>
          ) : !showQRCode && (
            <button
              type="button"
              onClick={() => void handlePay()}
              disabled={!selectedMethod || payOrderMutation.isPending}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {payOrderMutation.isPending ? '处理中...' : '确认支付'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PaymentModal;