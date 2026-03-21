/**
 * NetworkStatus - 网络状态提示组件
 *
 * 监听网络连接状态，在断网时显示提示信息
 */
/* eslint-disable react-refresh/only-export-components */

import { useState, useEffect, useCallback } from 'react';
import { WifiOff, Wifi, RefreshCw } from 'lucide-react';

export interface NetworkStatusProps {
  /** 自定义类名 */
  className?: string;
  /** 是否显示恢复连接的提示 */
  showOnlineNotification?: boolean;
  /** 离线时的自定义消息 */
  offlineMessage?: string;
  /** 恢复在线时的自定义消息 */
  onlineMessage?: string;
  /** 提示显示位置 */
  position?: 'top' | 'bottom';
  /** 是否显示重试按钮 */
  showRetryButton?: boolean;
  /** 重试回调 */
  onRetry?: () => void;
}

/**
 * 网络状态提示组件
 * 
 * @example
 * ```tsx
 * // 基本使用
 * <NetworkStatus />
 * 
 * // 带重试按钮
 * <NetworkStatus 
 *   showRetryButton 
 *   onRetry={() => window.location.reload()} 
 * />
 * 
 * // 自定义位置和消息
 * <NetworkStatus 
 *   position="bottom"
 *   offlineMessage="网络已断开"
 *   onlineMessage="网络已恢复"
 * />
 * ```
 */
export function NetworkStatus({
  className = '',
  showOnlineNotification = true,
  offlineMessage = '网络连接已断开，请检查您的网络设置',
  onlineMessage = '网络连接已恢复',
  position = 'top',
  showRetryButton = true,
  onRetry,
}: NetworkStatusProps): JSX.Element | null {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showOnlineToast, setShowOnlineToast] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      if (showOnlineNotification) {
        setShowOnlineToast(true);
        // 3秒后隐藏在线提示
        setTimeout(() => setShowOnlineToast(false), 3000);
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowOnlineToast(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [showOnlineNotification]);

  const handleRetry = useCallback(() => {
    if (isOnline) {
      onRetry?.();
    } else {
      // 尝试重新连接
      window.location.reload();
    }
  }, [isOnline, onRetry]);

  // 在线状态且不显示在线提示时，不渲染任何内容
  if (isOnline && !showOnlineToast) {
    return null;
  }

  // 显示在线恢复提示
  if (showOnlineToast) {
    return (
      <div
        className={`
          fixed ${position === 'top' ? 'top-0' : 'bottom-0'} left-0 right-0 z-[9999]
          bg-green-500 text-white
          py-2.5 px-4
          flex items-center justify-center gap-2
          animate-slide-down
          ${className}
        `}
        role="status"
        aria-live="polite"
      >
        <Wifi className="w-4 h-4" />
        <span className="text-sm font-medium">{onlineMessage}</span>
      </div>
    );
  }

  // 显示离线提示
  return (
    <div
      className={`
        fixed ${position === 'top' ? 'top-0' : 'bottom-0'} left-0 right-0 z-[9999]
        bg-red-500 text-white
        py-3 px-4
        flex items-center justify-center gap-3
        ${className}
      `}
      role="alert"
      aria-live="assertive"
    >
      <WifiOff className="w-5 h-5 flex-shrink-0" />
      <span className="text-sm font-medium">{offlineMessage}</span>
      {showRetryButton && (
        <button
          onClick={handleRetry}
          className="
            flex items-center gap-1.5
            px-3 py-1
            bg-white/20 hover:bg-white/30
            rounded-md
            text-sm font-medium
            transition-colors
            focus:outline-none focus:ring-2 focus:ring-white/50
          "
          aria-label="重试连接"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          重试
        </button>
      )}
    </div>
  );
}

/**
 * useNetworkStatus - 网络状态 Hook
 * 
 * @example
 * ```tsx
 * const { isOnline, isSlowConnection } = useNetworkStatus();
 * 
 * if (!isOnline) {
 *   return <div>您当前处于离线状态</div>;
 * }
 * ```
 */
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [effectiveType, setEffectiveType] = useState<string>('4g');

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    // 监听网络连接变化
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // 监听网络类型变化（如果支持）
    const connection = (navigator as Navigator & { connection?: { effectiveType?: string; addEventListener?: (type: string, listener: () => void) => void; removeEventListener?: (type: string, listener: () => void) => void } }).connection;
    if (connection) {
      setEffectiveType(connection.effectiveType || '4g');
      const handleConnectionChange = () => {
        setEffectiveType(connection.effectiveType || '4g');
      };
      connection.addEventListener?.('change', handleConnectionChange);
      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
        connection.removeEventListener?.('change', handleConnectionChange);
      };
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return {
    isOnline,
    isSlowConnection: effectiveType === '2g' || effectiveType === 'slow-2g',
    effectiveType,
  };
}

/**
 * NetworkStatusIndicator - 网络状态指示器（小型）
 * 
 * 用于在导航栏或状态栏显示网络状态
 */
export interface NetworkStatusIndicatorProps {
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 自定义类名 */
  className?: string;
  /** 是否显示文字 */
  showLabel?: boolean;
}

export function NetworkStatusIndicator({
  size = 'md',
  className = '',
  showLabel = false,
}: NetworkStatusIndicatorProps): JSX.Element {
  const { isOnline, isSlowConnection } = useNetworkStatus();

  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3 h-3',
  };

  const getStatusColor = () => {
    if (!isOnline) return 'bg-red-500';
    if (isSlowConnection) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getStatusLabel = () => {
    if (!isOnline) return '离线';
    if (isSlowConnection) return '网络较慢';
    return '在线';
  };

  return (
    <div
      className={`flex items-center gap-1.5 ${className}`}
      role="status"
      aria-label={`网络状态: ${getStatusLabel()}`}
    >
      <span
        className={`
          ${sizeClasses[size]} ${getStatusColor()}
          rounded-full
          ${isOnline ? 'animate-pulse' : ''}
        `}
      />
      {showLabel && (
        <span className="text-xs text-slate-500">{getStatusLabel()}</span>
      )}
    </div>
  );
}

export default NetworkStatus;