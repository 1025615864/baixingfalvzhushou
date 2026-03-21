/**
 * 支付弹窗组件 - 增强版
 */

import React, { useState, useCallback, useMemo } from 'react';

import type { Order, PaymentMethod, PaymentError } from '../types';
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

/**
 * 解析支付错误
 */
function parsePaymentError(error: unknown): PaymentError | null {
  if (!error) return null;
  
  // 检查是否是支付错误对象
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>;
    if (err['error_code'] && err['suggestion']) {
      return {
        message: (err['message'] as string) || '支付失败',
        error_code: err['error_code'] as PaymentError['error_code'],
        suggestion: err['suggestion'] as string,
        details: err['details'] as Record<string, unknown> | undefined,
      };
    }
    
    // 处理 Axios 错误
    if (err['response'] && typeof err['response'] === 'object') {
      const response = err['response'] as Record<string, unknown>;
      const data = response['data'] as Record<string, unknown> | undefined;
      if (data) {
        return {
          message: (data['message'] as string) || (data['detail'] as string) || '支付失败',
          error_code: (data['error_code'] as PaymentError['error_code']) || 'PAYMENT_FAILED',
          suggestion: (data['suggestion'] as string) || '请稍后重试或联系客服',
          details: data['details'] as Record<string, unknown> | undefined,
        };
      }
    }
  }
  
  return null;
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

  // 解析支付错误
  const paymentError = useMemo(() => parsePaymentError(payOrderMutation.error), [payOrderMutation.error]);
  
  // 优先使用解析后的错误信息，否则使用原始错误消息
  const displayErrorMessage = paymentError?.message || payOrderMutation.error?.message;
  const errorSuggestion = paymentError?.suggestion;

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
    (error) => {
      // 支付失败
      console.error('支付轮询失败:', error);
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
      // 检查是否是余额不足等可恢复错误
      if (paymentError?.error_code === 'INSUFFICIENT_BALANCE') {
        // 可以在这里添加自动处理逻辑，如提示充值
      }
    }
  }, [order, selectedMethod, payOrderMutation, startPolling, paymentError]);

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

  const handleContactSupport = useCallback(() => {
    // 打开客服聊天或显示联系方式的逻辑
    // 例如：window.open('/contact', '_blank');
    window.open('/contact', '_blank');
  }, []);

  if (!isOpen || !order) return null;

  // 支付状态显示
  const showPaymentStatus = pollingStatus === 'polling' || pollingStatus === 'success' || pollingStatus === 'failed' || pollingStatus === 'timeout';

  // 支付二维码显示
  const showQRCode = payUrl && pollingStatus === 'polling';

  // 判断是否显示错误建议（仅在支付失败时）
  const showErrorSuggestion = (pollingStatus === 'failed' || pollingStatus === 'timeout') && errorSuggestion;
  
  // 判断是否显示余额不足等初始错误
  const showInitialError = payOrderMutation.error && !showPaymentStatus && !showQRCode;

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
          <h2 className="text-lg font-semibold text-gray-900" data-testid="payment-modal-title">
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

        {/* 错误提示区域 */}
        {showInitialError && paymentError && (
          <div className="p-4 bg-red-50 border-b border-red-100">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800">{paymentError.message}</h3>
                {paymentError.suggestion && (
                  <p className="mt-1 text-sm text-red-600">{paymentError.suggestion}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 内容区域 */}
        <div className="p-4">
          {showPaymentStatus ? (
            <PaymentStatus
              status={pollingStatus}
              attempts={attempts}
              errorMessage={displayErrorMessage}
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

        {/* 底部按钮区域 */}
        <div className="p-4 border-t border-gray-200 space-y-2">
          {/* 支付失败后的建议 */}
          {showErrorSuggestion && (
            <div className="mb-3 p-3 bg-yellow-50 rounded-lg">
              <div className="flex items-start gap-2">
                <svg className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-yellow-700">{errorSuggestion}</p>
              </div>
            </div>
          )}
          
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
                onClick={handleContactSupport}
                className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
              >
                联系客服
              </button>
              <button
                type="button"
                onClick={handleClose}
                className="w-full text-gray-500 py-2 text-sm hover:text-gray-700 transition-colors"
              >
                稍后再说
              </button>
            </>
          ) : !showQRCode && (
            <>
              <button
                type="button"
                data-testid="pay-button"
                onClick={() => void handlePay()}
                disabled={!selectedMethod || payOrderMutation.isPending}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {payOrderMutation.isPending ? '处理中...' : '确认支付'}
              </button>
              
              {/* 余额不足时显示充值入口 */}
              {paymentError?.error_code === 'INSUFFICIENT_BALANCE' && (
                <button
                  type="button"
                  onClick={() => {
                    // 跳转到充值页面
                    window.location.href = '/settlement/recharge';
                  }}
                  className="w-full bg-orange-500 text-white py-2 rounded-lg font-medium hover:bg-orange-600 transition-colors text-sm"
                >
                  立即充值
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PaymentModal;