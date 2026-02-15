/**
 * OfficialAccountQrCode - 公众号二维码组件
 * 用于展示公众号关注二维码
 */

import { useState, useEffect, useCallback } from 'react';

import { useOfficialAccountQrCode } from '../hooks/useWechat';

interface OfficialAccountQrCodeProps {
  userId: number;
  /** 二维码尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 是否显示刷新按钮 */
  showRefresh?: boolean;
  /** 扫码成功回调 */
  onScanSuccess?: () => void;
  /** 自定义标题 */
  title?: string;
  /** 自定义描述 */
  description?: string;
}

/**
 * 刷新图标组件
 */
function RefreshIcon(): JSX.Element {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  );
}

/**
 * 复制图标组件
 */
function CopyIcon(): JSX.Element {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

/**
 * 成功图标组件
 */
function SuccessIcon(): JSX.Element {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}

/**
 * 时钟图标组件
 */
function ClockIcon(): JSX.Element {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

/**
 * 公众号二维码组件
 */
export function OfficialAccountQrCode({
  userId,
  size = 'medium',
  showRefresh = true,
  onScanSuccess,
  title = '关注公众号',
  description = '微信扫码关注，获取更多服务',
}: OfficialAccountQrCodeProps): JSX.Element {
  const [copied, setCopied] = useState(false);
  const [timeLeft, setTimeLeft] = useState<number>(0);
  
  const { 
    data: qrCodeData, 
    isLoading, 
    error, 
    refetch 
  } = useOfficialAccountQrCode(userId);

  // 尺寸配置
  const sizeClasses = {
    small: {
      container: 'w-48',
      qrCode: 'w-32 h-32',
      text: 'text-xs',
    },
    medium: {
      container: 'w-64',
      qrCode: 'w-44 h-44',
      text: 'text-sm',
    },
    large: {
      container: 'w-80',
      qrCode: 'w-56 h-56',
      text: 'text-base',
    },
  };

  // 计算剩余时间
  useEffect(() => {
    if (!qrCodeData?.expireAt) {
      setTimeLeft(0);
      return;
    }

    const calculateTimeLeft = (): number => {
      const expireTime = new Date(qrCodeData.expireAt).getTime();
      const now = Date.now();
      return Math.max(0, Math.floor((expireTime - now) / 1000));
    };

    setTimeLeft(calculateTimeLeft());

    const timer = setInterval(() => {
      const remaining = calculateTimeLeft();
      setTimeLeft(remaining);
      
      if (remaining <= 0) {
        clearInterval(timer);
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [qrCodeData?.expireAt]);

  /**
   * 格式化时间
   */
  const formatTime = useCallback((seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  /**
   * 处理复制链接
   */
  const handleCopyLink = useCallback((): void => {
    if (!qrCodeData?.qrCodeUrl) return;
    
    void navigator.clipboard.writeText(qrCodeData.qrCodeUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [qrCodeData?.qrCodeUrl]);

  /**
   * 处理刷新二维码
   */
  const handleRefresh = useCallback((): void => {
    void refetch();
  }, [refetch]);

  /**
   * 模拟扫码成功（实际使用时应由后端推送）
   */
  const handleSimulateScan = useCallback((): void => {
    onScanSuccess?.();
  }, [onScanSuccess]);

  const currentSize = sizeClasses[size];

  if (isLoading) {
    return (
      <div className={`${currentSize.container} bg-white rounded-lg shadow-sm border border-gray-200 p-6`}>
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-pulse space-y-4 w-full">
            <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto"></div>
            <div className={`${currentSize.qrCode} bg-gray-200 rounded-lg mx-auto`}></div>
            <div className="h-3 bg-gray-200 rounded w-1/2 mx-auto"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${currentSize.container} bg-white rounded-lg shadow-sm border border-gray-200 p-6`}>
        <div className="text-center">
          <div className="text-red-500 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            {error.message || '加载二维码失败'}
          </p>
          {showRefresh && (
            <button
              onClick={handleRefresh}
              className="inline-flex items-center space-x-1 px-4 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 transition-colors"
            >
              <RefreshIcon />
              <span>重新加载</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  const isExpired = timeLeft === 0 && qrCodeData;

  return (
    <div className={`${currentSize.container} bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden`}>
      {/* 头部 */}
      <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
        <h3 className={`font-medium text-gray-900 text-center ${currentSize.text}`}>
          {title}
        </h3>
      </div>

      {/* 二维码区域 */}
      <div className="p-6 flex flex-col items-center">
        <div className="relative">
          {/* 二维码图片 */}
          <div className={`
            ${currentSize.qrCode} 
            rounded-lg overflow-hidden border-2 border-gray-200
            ${isExpired ? 'opacity-50 grayscale' : ''}
          `}>
            {qrCodeData?.qrCodeUrl ? (
              <img
                src={qrCodeData.qrCodeUrl}
                alt="公众号二维码"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                <span className="text-gray-400 text-xs">暂无二维码</span>
              </div>
            )}
          </div>

          {/* 已过期遮罩 */}
          {isExpired && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-black bg-opacity-60 rounded-lg px-3 py-2">
                <p className="text-white text-xs font-medium">二维码已过期</p>
              </div>
            </div>
          )}
        </div>

        {/* 描述文字 */}
        <p className={`mt-4 text-gray-600 text-center ${currentSize.text}`}>
          {description}
        </p>

        {/* 倒计时 */}
        {timeLeft > 0 && (
          <div className="mt-2 flex items-center justify-center space-x-1 text-xs text-gray-500">
            <ClockIcon />
            <span>有效期剩余：{formatTime(timeLeft)}</span>
          </div>
        )}

        {/* 场景值 */}
        {qrCodeData?.scene && (
          <div className="mt-2 text-xs text-gray-400">
            场景：{qrCodeData.scene}
          </div>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="px-4 py-3 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {showRefresh && (
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              <RefreshIcon />
              <span>刷新</span>
            </button>
          )}
          
          <button
            onClick={handleCopyLink}
            disabled={!qrCodeData?.qrCodeUrl}
            className={`
              inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-medium rounded-md transition-colors
              ${copied 
                ? 'bg-green-100 text-green-700' 
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }
              disabled:opacity-50
            `}
          >
            {copied ? (
              <>
                <SuccessIcon />
                <span>已复制</span>
              </>
            ) : (
              <>
                <CopyIcon />
                <span>复制链接</span>
              </>
            )}
          </button>
        </div>

        {/* 模拟扫码按钮（仅用于演示） */}
        <button
          onClick={handleSimulateScan}
          className="text-xs text-green-600 hover:text-green-700 transition-colors"
        >
          模拟扫码
        </button>
      </div>
    </div>
  );
}