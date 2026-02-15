/**
 * ToastProvider - Toast上下文提供者
 *
 * 提供全局Toast通知功能
 */
/* eslint-disable react-refresh/only-export-components */

import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

import { ToastContainer } from './Toast';
import type { ToastData, ToastPosition, ToastType } from './Toast';

/**
 * Toast选项
 */
export interface ToastOptions {
  /** 标题 */
  title?: string;
  /** 消息内容 */
  message: string;
  /** 消息类型 */
  type?: ToastType;
  /** 显示时长（毫秒），默认5000ms，0表示不自动关闭 */
  duration?: number;
}

/**
 * Toast上下文类型
 */
export interface ToastContextType {
  /** 显示Toast */
  show: (options: ToastOptions) => string;
  /** 显示成功Toast */
  success: (message: string, title?: string, duration?: number) => string;
  /** 显示错误Toast */
  error: (message: string, title?: string, duration?: number) => string;
  /** 显示警告Toast */
  warning: (message: string, title?: string, duration?: number) => string;
  /** 显示信息Toast */
  info: (message: string, title?: string, duration?: number) => string;
  /** 关闭指定Toast */
  close: (id: string) => void;
  /** 关闭所有Toast */
  closeAll: () => void;
}

// 创建上下文
const ToastContext = createContext<ToastContextType | undefined>(undefined);

/**
 * ToastProvider属性
 */
export interface ToastProviderProps {
  /** 子元素 */
  children: React.ReactNode;
  /** Toast位置 */
  position?: ToastPosition;
  /** 默认显示时长 */
  defaultDuration?: number;
  /** 最大Toast数量 */
  maxToasts?: number;
}

/**
 * 生成唯一ID
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Toast提供者组件
 * 
 * @example
 * ```tsx
 * // 在应用根组件中使用
 * function App() {
 *   return (
 *     <ToastProvider position="top-right" defaultDuration={5000}>
 *       <YourApp />
 *     </ToastProvider>
 *   );
 * }
 * 
 * // 在组件中使用
 * function MyComponent() {
 *   const toast = useToast();
 *   
 *   const handleClick = () => {
 *     toast.success('操作成功！');
 *     toast.error('操作失败', '错误', 10000);
 *   };
 *   
 *   return <button onClick={handleClick}>点击</button>;
 * }
 * ```
 */
export function ToastProvider({
  children,
  position = 'top-right',
  defaultDuration = 5000,
  maxToasts = 5,
}: ToastProviderProps): JSX.Element {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  /**
   * 显示Toast
   */
  const show = useCallback(
    (options: ToastOptions): string => {
      const id = generateId();
      const newToast: ToastData = {
        id,
        type: options.type || 'info',
        title: options.title,
        message: options.message,
        duration: options.duration !== undefined ? options.duration : defaultDuration,
        createdAt: Date.now(),
      };

      setToasts((prev) => {
        // 如果超过最大数量，移除最早的
        const updated = [...prev, newToast];
        if (updated.length > maxToasts) {
          return updated.slice(updated.length - maxToasts);
        }
        return updated;
      });

      return id;
    },
    [defaultDuration, maxToasts]
  );

  /**
   * 显示成功Toast
   */
  const success = useCallback(
    (message: string, title?: string, duration?: number): string => {
      return show({ type: 'success', message, title, duration });
    },
    [show]
  );

  /**
   * 显示错误Toast
   */
  const error = useCallback(
    (message: string, title?: string, duration?: number): string => {
      return show({ type: 'error', message, title, duration });
    },
    [show]
  );

  /**
   * 显示警告Toast
   */
  const warning = useCallback(
    (message: string, title?: string, duration?: number): string => {
      return show({ type: 'warning', message, title, duration });
    },
    [show]
  );

  /**
   * 显示信息Toast
   */
  const info = useCallback(
    (message: string, title?: string, duration?: number): string => {
      return show({ type: 'info', message, title, duration });
    },
    [show]
  );

  /**
   * 关闭指定Toast
   */
  const close = useCallback((id: string): void => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  /**
   * 关闭所有Toast
   */
  const closeAll = useCallback((): void => {
    setToasts([]);
  }, []);

  // 上下文值
  const contextValue = useMemo(
    () => ({
      show,
      success,
      error,
      warning,
      info,
      close,
      closeAll,
    }),
    [show, success, error, warning, info, close, closeAll]
  );

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ToastContainer toasts={toasts} onClose={close} position={position} />
    </ToastContext.Provider>
  );
}

/**
 * 使用Toast的Hook
 * 
 * 必须在ToastProvider内部使用
 */
export function useToast(): ToastContextType {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

export default ToastProvider;