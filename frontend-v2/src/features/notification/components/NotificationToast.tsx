// ============================================
// 实时通知弹窗组件
// ============================================

import { useState, useEffect, useCallback } from 'react';

import type { NotificationData, NotificationType } from '../types/websocket';

/**
 * Toast 位置
 */
export type ToastPosition = 
  | 'top-left' 
  | 'top-right' 
  | 'top-center' 
  | 'bottom-left' 
  | 'bottom-right' 
  | 'bottom-center';

/**
 * 通知Toast项
 */
export interface ToastItem extends NotificationData {
  /** 唯一ID */
  toastId: string;
  /** 显示时间 */
  showAt: number;
}

export interface NotificationToastProps {
  /** 通知数据 */
  notification: NotificationData | null;
  /** 显示时长（毫秒） */
  duration?: number;
  /** 位置 */
  position?: ToastPosition;
  /** 最大显示数量 */
  maxCount?: number;
  /** 点击通知 */
  onClick?: (notification: NotificationData) => void;
  /** 关闭回调 */
  onClose?: (notificationId: number) => void;
  /** 是否启用声音 */
  enableSound?: boolean;
  /** 声音URL */
  soundUrl?: string;
  /** 忽略的类别 */
  ignoredTypes?: NotificationType[];
}

/**
 * 通知类型配置
 */
const typeConfig: Record<string, { icon: JSX.Element; bgColor: string; borderColor: string }> = {
  system: {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
  },
  chat: {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
  },
  order: {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
      </svg>
    ),
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
  },
  consultation: {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
  },
  forum: {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
      </svg>
    ),
    bgColor: 'bg-pink-50',
    borderColor: 'border-pink-200',
  },
  payment: {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
      </svg>
    ),
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
  },
  promotion: {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
      </svg>
    ),
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
  },
  security: {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
    bgColor: 'bg-red-50',
    borderColor: 'border-red-300',
  },
};

/**
 * 获取类型配置
 */
function getTypeConfig(type: string): { icon: JSX.Element; bgColor: string; borderColor: string } {
  return typeConfig[type] || {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    ),
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
  };
}

/**
 * 播放通知声音
 */
function playNotificationSound(url: string): void {
  try {
    const audio = new Audio(url);
    void audio.play().catch(() => {
      // 忽略自动播放限制错误
    });
  } catch {
    // 忽略音频播放错误
  }
}

/**
 * 实时通知弹窗组件
 */
export function NotificationToast({
  notification,
  duration = 5000,
  position = 'top-right',
  maxCount = 3,
  onClick,
  onClose,
  enableSound = false,
  soundUrl = '/sounds/notification.mp3',
  ignoredTypes = [],
}: NotificationToastProps): JSX.Element {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  // 添加新通知
  useEffect(() => {
    if (!notification) return;

    // 检查是否被忽略
    if (ignoredTypes.includes(notification.type)) return;

    const toastId = `${notification.id}-${Date.now()}`;
    const newToast: ToastItem = {
      ...notification,
      toastId,
      showAt: Date.now(),
    };

    setToasts((prev) => {
      const updated = [newToast, ...prev].slice(0, maxCount);
      return updated;
    });

    // 播放声音
    if (enableSound) {
      playNotificationSound(soundUrl);
    }
  }, [notification, maxCount, enableSound, soundUrl, ignoredTypes]);

  // 自动移除过期通知
  useEffect(() => {
    if (toasts.length === 0) return;

    const timer = setInterval(() => {
      const now = Date.now();
      setToasts((prev) => prev.filter((toast) => now - toast.showAt < duration));
    }, 100);

    return () => clearInterval(timer);
  }, [toasts.length, duration]);

  // 手动移除通知
  const removeToast = useCallback((toastId: string, notificationId: number) => {
    setToasts((prev) => prev.filter((t) => t.toastId !== toastId));
    onClose?.(notificationId);
  }, [onClose]);

  // 处理点击
  const handleClick = useCallback((toast: ToastItem) => {
    onClick?.(toast);
    removeToast(toast.toastId, toast.id);
  }, [onClick, removeToast]);

  // 位置样式
  const positionStyles: Record<ToastPosition, string> = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'top-center': 'top-4 left-1/2 -translate-x-1/2',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
  };

  if (toasts.length === 0) {
    return <></>;
  }

  return (
    <div
      className={`fixed z-50 flex flex-col gap-2 ${positionStyles[position]}`}
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast, index) => {
        const config = getTypeConfig(toast.type);
        const progress = ((Date.now() - toast.showAt) / duration) * 100;

        return (
          <div
            key={toast.toastId}
            className={`
              relative w-80 md:w-96 overflow-hidden rounded-lg border shadow-lg
              transition-all duration-300 ease-out
              ${config.bgColor} ${config.borderColor}
              animate-slide-in-right
            `}
            style={{
              animationDelay: `${index * 100}ms`,
              transform: `translateY(${index * 8}px)`,
              zIndex: toasts.length - index,
            }}
          >
            {/* 进度条 */}
            <div
              className="absolute bottom-0 left-0 h-0.5 bg-blue-500 transition-all duration-100"
              style={{ width: `${100 - progress}%` }}
            />

            <div className="flex items-start gap-3 p-4">
              {/* 图标 */}
              <div className={`
                flex-shrink-0 rounded-full p-2
                ${config.bgColor.replace('50', '100')}
                text-gray-600
              `}>
                {config.icon}
              </div>

              {/* 内容 */}
              <div className="min-w-0 flex-1">
                <h4 className="text-sm font-semibold text-gray-900 line-clamp-1">
                  {toast.title}
                </h4>
                {toast.content && (
                  <p className="mt-1 text-xs text-gray-600 line-clamp-2">
                    {toast.content}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-400">
                  {new Date(toast.createdAt).toLocaleTimeString('zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>

              {/* 关闭按钮 */}
              <button
                type="button"
                onClick={() => removeToast(toast.toastId, toast.id)}
                className="flex-shrink-0 rounded p-1 text-gray-400 hover:bg-gray-200 hover:text-gray-600 focus:outline-none"
                aria-label="关闭通知"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* 点击区域 */}
            <button
              type="button"
              onClick={() => handleClick(toast)}
              className="absolute inset-0 cursor-pointer"
              aria-label={`查看通知: ${toast.title}`}
            >
              <span className="sr-only">查看通知</span>
            </button>
          </div>
        );
      })}
    </div>
  );
}

export default NotificationToast;