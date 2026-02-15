/**
 * 支付二维码组件
 */

import React, { useEffect, useState } from 'react';

export interface PaymentQRCodeProps {
  payUrl: string;
  orderNo: string;
  amount: number;
  paymentMethod: string;
  onTimeout?: () => void;
  onSuccess?: () => void;
}

/**
 * 倒计时组件
 */
function CountdownTimer({ 
  seconds, 
  onTimeout 
}: { 
  seconds: number; 
  onTimeout?: () => void;
}): React.ReactElement {
  const [remaining, setRemaining] = useState(seconds);

  useEffect(() => {
    if (remaining <= 0) {
      onTimeout?.();
      return;
    }

    const timer = setInterval(() => {
      setRemaining((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [remaining, onTimeout]);

  const minutes = Math.floor(remaining / 60);
  const secs = remaining % 60;

  return (
    <span className="text-sm text-gray-600">
      {minutes.toString().padStart(2, '0')}:{secs.toString().padStart(2, '0')}
    </span>
  );
}

export const PaymentQRCode: React.FC<PaymentQRCodeProps> = ({
  payUrl,
  orderNo,
  amount,
  paymentMethod,
  onTimeout,
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // 模拟二维码加载
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  // 支付方式名称映射
  const methodNameMap: Record<string, string> = {
    alipay: '支付宝',
    wechat: '微信支付',
    ikunpay: '爱坤支付',
  };

  const methodName = methodNameMap[paymentMethod] || paymentMethod;

  return (
    <div className="flex flex-col items-center space-y-6 p-6">
      {/* 支付信息 */}
      <div className="text-center">
        <p className="text-gray-600 mb-1">支付金额</p>
        <p className="text-3xl font-bold text-gray-900">¥{amount.toFixed(2)}</p>
        <p className="text-sm text-gray-500 mt-1">订单号: {orderNo}</p>
      </div>

      {/* 二维码区域 */}
      <div className="relative">
        {isLoading ? (
          <div className="w-48 h-48 bg-gray-100 rounded-lg animate-pulse flex items-center justify-center">
            <svg className="w-12 h-12 text-gray-300" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 3h6v6H3V3zm2 2v2h2V5H5zm8-2h6v6h-6V3zm2 2v2h2V5h-2zM3 13h6v6H3v-6zm2 2v2h2v-2H5zm13-2h3v3h-3v-3zm-2 2h3v3h-3v-3zm2 2h3v3h-3v-3zM9 13h2v2H9v-2zm2 2h2v2h-2v-2zm-2 2h2v2H9v-2z" />
            </svg>
          </div>
        ) : hasError ? (
          <div className="w-48 h-48 bg-red-50 rounded-lg flex flex-col items-center justify-center border-2 border-red-200">
            <svg className="w-12 h-12 text-red-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-sm text-red-600">二维码生成失败</p>
            <button
              type="button"
              onClick={() => setHasError(false)}
              className="mt-2 text-xs text-blue-600 hover:text-blue-700"
            >
              重试
            </button>
          </div>
        ) : (
          <div className="w-48 h-48 bg-white rounded-lg border-2 border-gray-200 p-2">
            {/* 这里应该显示真实的二维码图片 */}
            <div className="w-full h-full bg-gray-900 rounded flex items-center justify-center">
              <div className="text-white text-xs text-center p-4">
                <svg className="w-24 h-24 mx-auto mb-2 text-white" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3 3h6v6H3V3zm2 2v2h2V5H5zm8-2h6v6h-6V3zm2 2v2h2V5h-2zM3 13h6v6H3v-6zm2 2v2h2v-2H5zm13-2h3v3h-3v-3zm-2 2h3v3h-3v-3zm2 2h3v3h-3v-3zM9 13h2v2H9v-2zm2 2h2v2h-2v-2zm-2 2h2v2H9v-2z" />
                </svg>
                <p>模拟二维码</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 支付提示 */}
      <div className="text-center space-y-2">
        <p className="text-sm text-gray-700">
          请使用<span className="font-medium text-blue-600">{methodName}</span>扫一扫
        </p>
        <p className="text-xs text-gray-500">
          二维码有效期剩余 <CountdownTimer seconds={120} onTimeout={onTimeout} />
        </p>
      </div>

      {/* 备用支付方式 */}
      <div className="w-full pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={() => window.open(payUrl, '_blank')}
          className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          点击跳转{methodName}支付
        </button>
        <p className="text-xs text-gray-400 text-center mt-2">
          如果无法扫码，请点击上方按钮跳转支付
        </p>
      </div>
    </div>
  );
};

export default PaymentQRCode;