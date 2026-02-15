/**
 * Toast - Toast通知组件
 * 
 * 用于显示临时通知消息
 */

import React, { useEffect, useState, useCallback } from 'react';

/**
 * Toast类型
 */
export type ToastType = 'success' | 'error' | 'warning' | 'info';

/**
 * Toast位置
 */
export type ToastPosition = 
  | 'top-left'
  | 'top-center'
  | 'top-right'
  | 'bottom-left'
  | 'bottom-center'
  | 'bottom-right';

/**
 * Toast数据
 */
export interface ToastData {
  /** 唯一标识 */
  id: string;
  /** 消息类型 */
  type: ToastType;
  /** 标题 */
  title?: string;
  /** 消息内容 */
  message: string;
  /** 显示时长（毫秒），0表示不自动关闭 */
  duration: number;
  /** 创建时间 */
  createdAt: number;
}

/**
 * Toast组件属性
 */
export interface ToastProps {
  /** Toast数据 */
  toast: ToastData;
  /** 关闭回调 */
  onClose: (id: string) => void;
  /** 位置 */
  position?: ToastPosition;
}

/**
 * 图标映射
 */
const iconMap: Record<ToastType, React.ReactNode> = {
  success: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
  error: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  warning: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  info: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

/**
 * 样式映射
 */
const styleMap: Record<ToastType, { bg: string; border: string; icon: string }> = {
  success: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
    icon: 'text-green-500',
  },
  error: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    icon: 'text-red-500',
  },
  warning: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    icon: 'text-yellow-500',
  },
  info: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    icon: 'text-blue-500',
  },
};

/**
 * 位置样式映射
 */
const positionMap: Record<ToastPosition, string> = {
  'top-left': 'top-0 left-0',
  'top-center': 'top-0 left-1/2 -translate-x-1/2',
  'top-right': 'top-0 right-0',
  'bottom-left': 'bottom-0 left-0',
  'bottom-center': 'bottom-0 left-1/2 -translate-x-1/2',
  'bottom-right': 'bottom-0 right-0',
};

/**
 * 单个Toast组件
 */
export function ToastItem({ toast, onClose }: ToastProps): JSX.Element {
  const [progress, setProgress] = useState(100);
  const [isExiting, setIsExiting] = useState(false);
  const styles = styleMap[toast.type];

  // 处理关闭 - 使用 useCallback 避免依赖问题
  const handleClose = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => onClose(toast.id), 300);
  }, [onClose, toast.id]);

  // 自动关闭逻辑
  useEffect(() => {
    if (toast.duration === 0) return;

    const startTime = Date.now();
    const endTime = startTime + toast.duration;

    const updateProgress = () => {
      const now = Date.now();
      const remaining = Math.max(0, endTime - now);
      const newProgress = (remaining / toast.duration) * 100;

      if (remaining === 0) {
        handleClose();
      } else {
        setProgress(newProgress);
        requestAnimationFrame(updateProgress);
      }
    };

    const animationFrame = requestAnimationFrame(updateProgress);

    return () => cancelAnimationFrame(animationFrame);
  }, [toast.duration, handleClose]);

  return (
    <div
      className={`
        relative flex items-start gap-3 p-4 mb-3 min-w-[320px] max-w-md
        ${styles.bg} ${styles.border}
        border rounded-lg shadow-lg
        transform transition-all duration-300 ease-out
        ${isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'}
      `}
      role="alert"
    >
      {/* 图标 */}
      <div className={`flex-shrink-0 ${styles.icon}`}>
        {iconMap[toast.type]}
      </div>

      {/* 内容 */}
      <div className="flex-1 min-w-0">
        {toast.title && (
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
            {toast.title}
          </h4>
        )}
        <p className="text-sm text-gray-700 dark:text-gray-300 break-words">
          {toast.message}
        </p>
      </div>

      {/* 关闭按钮 */}
      <button
        onClick={handleClose}
        className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        aria-label="关闭通知"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {/* 进度条 */}
      {toast.duration > 0 && (
        <div
          className={`
            absolute bottom-0 left-0 h-1 ${styles.icon.replace('text-', 'bg-')}
            transition-all duration-100 ease-linear
          `}
          style={{ width: `${progress}%` }}
        />
      )}
    </div>
  );
}

/**
 * Toast容器组件属性
 */
export interface ToastContainerProps {
  /** Toast列表 */
  toasts: ToastData[];
  /** 关闭回调 */
  onClose: (id: string) => void;
  /** 位置 */
  position?: ToastPosition;
  /** 自定义类名 */
  className?: string;
}

/**
 * Toast容器组件
 */
export function ToastContainer({
  toasts,
  onClose,
  position = 'top-right',
  className = '',
}: ToastContainerProps): JSX.Element | null {
  if (toasts.length === 0) return null;

  const isTop = position.startsWith('top');

  return (
    <div
      className={`
        fixed z-50 p-4 flex flex-col pointer-events-none
        ${positionMap[position]}
        ${isTop ? '' : 'flex-col-reverse'}
        ${className}
      `}
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastItem toast={toast} onClose={onClose} position={position} />
        </div>
      ))}
    </div>
  );
}

/**
 * 简单的Toast展示组件（用于静态展示）
 */
export function Toast({
  type = 'info',
  title,
  message,
  className = '',
}: {
  type?: ToastType;
  title?: string;
  message: string;
  className?: string;
}): JSX.Element {
  const styles = styleMap[type];

  return (
    <div
      className={`
        flex items-start gap-3 p-4
        ${styles.bg} ${styles.border}
        border rounded-lg
        ${className}
      `}
    >
      <div className={`flex-shrink-0 ${styles.icon}`}>
        {iconMap[type]}
      </div>
      <div className="flex-1">
        {title && (
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
            {title}
          </h4>
        )}
        <p className="text-sm text-gray-700 dark:text-gray-300">
          {message}
        </p>
      </div>
    </div>
  );
}

export default ToastContainer;