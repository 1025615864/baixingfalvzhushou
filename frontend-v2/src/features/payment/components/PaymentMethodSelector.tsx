/**
 * 支付方式选择组件
 */

import React, { useCallback } from 'react';

import type { PaymentMethod, PaymentMethodConfig } from '../types';

// 支付方式配置 - 优化：完善支付方式说明、添加支付推荐
const paymentMethods: PaymentMethodConfig[] = [
  {
    id: 'alipay',
    name: '支付宝',
    icon: 'alipay',
    description: '推荐使用，安全便捷，最快到账',
    enabled: true,
    recommended: true,
    testId: 'payment-method-alipay',
  },
  {
    id: 'wechat',
    name: '微信支付',
    icon: 'wechat',
    description: '微信用户首选，快速支付',
    enabled: false, // 后端暂未开放
    testId: 'payment-method-wechat',
  },
  {
    id: 'balance',
    name: '余额支付',
    icon: 'balance',
    description: '使用账户余额支付，尊享会员优惠',
    enabled: true,
    recommended: false,
    testId: 'payment-method-balance',
  },
  {
    id: 'ikunpay',
    name: '爱坤支付',
    icon: 'card',
    description: '第三方支付平台，新用户专享折扣',
    enabled: true,
    recommended: false,
    testId: 'payment-method-ikunpay',
  },
];

export interface PaymentMethodSelectorProps {
  selectedMethod: PaymentMethod | null;
  onSelect: (method: PaymentMethod) => void;
  disabled?: boolean;
  balance?: number;
}

/**
 * 支付方式图标
 */
function PaymentIcon({ type }: { type: string }): React.ReactElement {
  switch (type) {
    case 'alipay':
      return (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="#1677FF">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.39 14.79c-.63.23-1.32.36-2.05.36-2.48 0-4.55-1.64-5.28-3.89h5.74c.23 0 .42-.19.42-.42V10.5H9.06c-.03-.22-.06-.45-.06-.69 0-.24.03-.47.06-.69h6.16c.23 0 .42-.19.42-.42V6.69c0-.23-.19-.42-.42-.42H9.69c.95-2.01 2.98-3.4 5.31-3.4.73 0 1.42.13 2.05.36l.72-2.69C17.61 0 16.84 0 16 0 10.48 0 6 4.48 6 10c0 .24.02.48.05.71H3v3.58h3.05c.98 3.37 4.01 5.82 7.59 5.82.84 0 1.61-.13 2.32-.36l-.57-2.96z" />
        </svg>
      );
    case 'wechat':
      return (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="#07C160">
          <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.047c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.01-.27-.027-.407-.03zm-2.53 3.274c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.97-.982zm4.844 0c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.969-.982z" />
        </svg>
      );
    case 'balance':
      return (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="#F59E0B">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.67v-1.93c-1.71-.36-3.15-1.46-3.27-3.4h1.96c.1 1.05.82 1.87 2.65 1.87 1.96 0 2.4-.98 2.4-1.59 0-.83-.44-1.61-2.67-2.14-2.48-.6-4.18-1.62-4.18-3.67 0-1.72 1.39-2.84 3.11-3.21V4h2.67v1.95c1.86.45 2.79 1.86 2.85 3.39H14.3c-.05-1.11-.64-1.87-2.22-1.87-1.5 0-2.4.68-2.4 1.64 0 .84.65 1.39 2.67 1.91s4.18 1.39 4.18 3.91c-.01 1.83-1.38 2.83-3.12 3.16z" />
        </svg>
      );
    default:
      return (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="#6B7280">
          <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z" />
        </svg>
      );
  }
}

export const PaymentMethodSelector: React.FC<PaymentMethodSelectorProps> = ({
  selectedMethod,
  onSelect,
  disabled = false,
  balance = 0,
}) => {
  const handleSelect = useCallback((method: PaymentMethod) => {
    if (!disabled) {
      onSelect(method);
    }
  }, [disabled, onSelect]);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-700 mb-3">选择支付方式</h3>
      <div className="grid grid-cols-1 gap-3">
        {paymentMethods.map((method) => {
          const isSelected = selectedMethod === method.id;
          const isBalanceMethod = method.id === 'balance';

          return (
            <button
              key={method.id}
              type="button"
              data-testid={method.testId}
              onClick={() => handleSelect(method.id as PaymentMethod)}
              disabled={disabled || !method.enabled || (isBalanceMethod && balance <= 0)}
              className={`
                relative flex items-center p-4 rounded-lg border-2 transition-all
                ${isSelected 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300 bg-white'
                }
                ${(!method.enabled || (isBalanceMethod && balance <= 0)) ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <div className="flex-shrink-0 mr-4">
                <PaymentIcon type={method.icon} />
              </div>
              <div className="flex-1 text-left">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-gray-900">{method.name}</span>
                  {method.recommended && (
                    <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full font-medium">
                      推荐
                    </span>
                  )}
                  {isBalanceMethod && (
                    <span className="text-sm text-gray-500">
                      (余额: ¥{balance.toFixed(2)})
                    </span>
                  )}
                  {!method.enabled && (
                    <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">
                      暂未开放
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-0.5">{method.description}</p>
              </div>
              {isSelected && (
                <div className="flex-shrink-0 ml-4">
                  <svg className="w-6 h-6 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
              {isBalanceMethod && balance <= 0 && (
                <div className="flex-shrink-0 ml-4 text-xs text-red-500">
                  余额不足
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default PaymentMethodSelector;