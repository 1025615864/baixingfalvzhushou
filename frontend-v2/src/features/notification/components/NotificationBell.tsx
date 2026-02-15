/**
 * 通知铃铛组件
 * 显示未读数量，点击展开下拉通知列表
 */

import React, { useState, useRef, useEffect } from 'react';
import { Bell } from 'lucide-react';

import { useUnreadCount } from '../hooks/useNotifications';

import { NotificationDropdown } from './NotificationDropdown';

export interface NotificationBellProps {
  /** 自定义类名 */
  className?: string;
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg';
}

/**
 * 通知铃铛组件
 */
export function NotificationBell({ className = '', size = 'md' }: NotificationBellProps): React.ReactElement {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const { data: unreadData } = useUnreadCount();

  const unreadCount = unreadData?.unread_count ?? 0;

  // 尺寸映射
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
  };

  const iconSizes = {
    sm: 16,
    md: 20,
    lg: 24,
  };

  // 点击外部关闭下拉框
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // 格式化未读数量显示
  const formatUnreadCount = (count: number): string => {
    if (count > 99) return '99+';
    return String(count);
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          relative flex items-center justify-center rounded-full
          transition-colors duration-200
          hover:bg-gray-100 active:bg-gray-200
          focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
          ${sizeClasses[size]}
        `}
        aria-label={`通知${unreadCount > 0 ? `，有${unreadCount}条未读` : ''}`}
      >
        <Bell size={iconSizes[size]} className="text-gray-600" />
        
        {/* 未读数量徽章 */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-xs font-medium text-white bg-red-500 rounded-full animate-in fade-in zoom-in duration-200">
            {formatUnreadCount(unreadCount)}
          </span>
        )}
      </button>

      {/* 下拉通知列表 */}
      <NotificationDropdown isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </div>
  );
}