/**
 * WechatPayButton - 微信支付按钮组件
 * 支持JSAPI支付（微信内浏览器）
 */
import { useState, useCallback } from 'react';

import { useWechatPay } from '../hooks/useWechat';
import type { WechatUnifiedOrderRequest } from '../types';

interface WechatPayButtonProps {
  /** 订单信息 */
  orderRequest: Omit<WechatUnifiedOrderRequest, 'userId'>;
  /** 用户ID */
  userId: number;
  /** 按钮尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 按钮样式 */
  variant?: 'primary' | 'outline' | 'ghost';
  /** 支付成功回调 */
  onSuccess?: (outTradeNo: string) => void;
  /** 支付失败回调 */
  onError?: (error: Error) => void;
  /** 自定义按钮文字 */
  children?: React.ReactNode;
  /** 是否禁用 */
  disabled?: boolean;
  /** 额外的CSS类 */
  className?: string;
}

/**
 * 微信支付图标组件
 */
function WechatPayIcon(): JSX.Element {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.6 11.1c0-.8-.6-1.4-1.4-1.4s-1.4.6-1.4 1.4.6 1.4 1.4 1.4 1.4-.6 1.4-1.4zm-7.8 0c0-.8-.6-1.4-1.4-1.4s-1.4.6-1.4 1.4.6 1.4 1.4 1.4 1.4-.6 1.4-1.4z"/>
      <path d="M12 2C6.5 2 2 6 2 10.8c0 2.6 1.4 5 3.5 6.6v3.6l3.2-1.8c.9.2 1.8.4 2.8.4 5.5 0 10-4 10-8.8S17.5 2 12 2zm0 15.8c-.8 0-1.6-.1-2.3-.3l-.4-.1-2.5 1.4v-2.8l-.5-.4C4.7 14.3 3.6 12.6 3.6 10.8 3.6 6.9 7.4 3.6 12 3.6s8.4 3.3 8.4 7.2-3.8 7-8.4 7z"/>
    </svg>
  );
}

/**
 * 加载图标组件
 */
function LoaderIcon(): JSX.Element {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  );
}

/**
 * 微信支付按钮组件
 */
export function WechatPayButton({
  orderRequest,
  userId,
  size = 'medium',
  variant = 'primary',
  onSuccess,
  onError,
  children,
  disabled = false,
  className = '',
}: WechatPayButtonProps): JSX.Element {
  const [isProcessing, setIsProcessing] = useState(false);
  const { pay, isPaying } = useWechatPay();

  // 按钮尺寸样式
  const sizeClasses = {
    small: 'px-3 py-1.5 text-sm',
    medium: 'px-4 py-2 text-sm',
    large: 'px-6 py-3 text-base',
  };

  // 按钮样式变体
  const variantClasses = {
    primary: 'bg-green-600 text-white hover:bg-green-700 border-transparent',
    outline: 'bg-white text-green-600 border-green-600 hover:bg-green-50',
    ghost: 'bg-transparent text-green-600 hover:bg-green-50 border-transparent',
  };

  /**
   * 处理支付
   */
  const handlePay = useCallback(async (): Promise<void> => {
    if (isProcessing || isPaying) return;

    setIsProcessing(true);
    try {
      const request: WechatUnifiedOrderRequest = {
        ...orderRequest,
        userId,
      };

      const success = await pay(request);

      if (success) {
        onSuccess?.(orderRequest.outTradeNo);
      } else {
        onError?.(new Error('支付失败或被取消'));
      }
    } catch (error) {
      const err = error instanceof Error ? error : new Error('支付过程发生错误');
      onError?.(err);
    } finally {
      setIsProcessing(false);
    }
  }, [orderRequest, userId, pay, isProcessing, isPaying, onSuccess, onError]);

  /**
   * 检查是否在微信浏览器中
   */
  const isWechatBrowser = useCallback((): boolean => {
    if (typeof window === 'undefined') return false;
    const ua = window.navigator.userAgent.toLowerCase();
    return ua.includes('micromessenger');
  }, []);

  const isLoading = isProcessing || isPaying;
  const isDisabled = disabled || isLoading;
  const inWechat = isWechatBrowser();

  // 如果不在微信浏览器中，显示提示
  if (!inWechat) {
    return (
      <div className={`inline-flex flex-col ${className}`}>
        <button
          disabled={true}
          className={`
            inline-flex items-center justify-center space-x-2 
            rounded-md font-medium transition-colors 
            opacity-50 cursor-not-allowed
            border border-gray-300 bg-gray-100 text-gray-500
            ${sizeClasses[size]}
          `}
        >
          <WechatPayIcon />
          <span>请在微信中打开</span>
        </button>
        <span className="text-xs text-gray-500 mt-1">
          微信支付仅支持在微信内使用
        </span>
      </div>
    );
  }

  return (
    <button
      onClick={() => void handlePay()}
      disabled={isDisabled}
      className={`
        inline-flex items-center justify-center space-x-2 
        rounded-md font-medium transition-colors 
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500
        disabled:opacity-50 disabled:cursor-not-allowed
        border
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {isLoading ? (
        <>
          <LoaderIcon />
          <span>支付中...</span>
        </>
      ) : (
        <>
          <WechatPayIcon />
          <span>{children || '微信支付'}</span>
        </>
      )}
    </button>
  );
}