/**
 * 支付状态组件
 */

import React from 'react';

import type { PaymentPollingStatus, PaymentStatus as OrderPaymentStatus } from '../types';

export interface PaymentStatusProps {
  status: PaymentPollingStatus;
  attempts?: number;
  maxAttempts?: number;
  orderStatus?: OrderPaymentStatus;
  errorMessage?: string;
}

/**
 * 支付状态图标
 */
function StatusIcon({ status }: { status: PaymentPollingStatus }): React.ReactElement {
  switch (status) {
    case 'polling':
      return (
        <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600" />
      );
    case 'success':
      return (
        <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center">
          <svg className="h-10 w-10 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      );
    case 'failed':
      return (
        <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center">
          <svg className="h-10 w-10 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      );
    case 'timeout':
      return (
        <div className="h-16 w-16 rounded-full bg-yellow-100 flex items-center justify-center">
          <svg className="h-10 w-10 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      );
    default:
      return (
        <div className="h-16 w-16 rounded-full bg-gray-100 flex items-center justify-center">
          <svg className="h-10 w-10 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      );
  }
}

/**
 * 支付状态标题
 */
function StatusTitle({ status }: { status: PaymentPollingStatus }): string {
  switch (status) {
    case 'polling':
      return '正在查询支付结果...';
    case 'success':
      return '支付成功';
    case 'failed':
      return '支付失败';
    case 'timeout':
      return '支付超时';
    default:
      return '等待支付';
  }
}

/**
 * 支付状态描述
 */
function StatusDescription({ 
  status, 
  attempts, 
  maxAttempts,
  errorMessage 
}: { 
  status: PaymentPollingStatus; 
  attempts?: number;
  maxAttempts?: number;
  errorMessage?: string;
}): React.ReactElement {
  switch (status) {
    case 'polling':
      return (
        <div className="space-y-2">
          <p className="text-gray-600">正在查询支付结果，请稍候...</p>
          {attempts !== undefined && maxAttempts !== undefined && (
            <div className="w-full bg-gray-200 rounded-full h-2 max-w-xs mx-auto">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min((attempts / maxAttempts) * 100, 100)}%` }}
              />
            </div>
          )}
        </div>
      );
    case 'success':
      return <p className="text-green-600">您的订单已支付成功，感谢您的购买！</p>;
    case 'failed':
      return <p className="text-red-600">{errorMessage || '支付过程中发生错误，请重试或联系客服。'}</p>;
    case 'timeout':
      return <p className="text-yellow-600">支付查询超时，请稍后在我的订单中查看支付结果。</p>;
    default:
      return <p className="text-gray-600">请完成支付操作</p>;
  }
}

export const PaymentStatus: React.FC<PaymentStatusProps> = ({
  status,
  attempts = 0,
  maxAttempts = 60,
  errorMessage,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="mb-6">
        <StatusIcon status={status} />
      </div>
      
      <h3
        className={`text-xl font-semibold mb-2 ${
          status === 'success' ? 'text-green-600' :
          status === 'failed' ? 'text-red-600' :
          status === 'timeout' ? 'text-yellow-600' :
          'text-gray-900'
        }`}
        data-testid={status === 'failed' ? 'payment-error-title' : undefined}
      >
        {StatusTitle({ status })}
      </h3>
      
      <div className="text-sm">
        <div data-testid={status === 'failed' ? 'payment-error' : undefined}>
          <StatusDescription
            status={status}
            attempts={attempts}
            maxAttempts={maxAttempts}
            errorMessage={errorMessage}
          />
        </div>
      </div>
    </div>
  );
};

export default PaymentStatus;