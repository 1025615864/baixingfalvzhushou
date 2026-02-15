/**
 * 单个通知项组件
 */

import React from 'react';
import {
  MessageSquare,
  Heart,
  Bookmark,
  Bell,
  Briefcase,
  FileText,
  ShoppingCart,
  Check,
  Trash2,
  Clock,
} from 'lucide-react';

import { Notification, NotificationType, NotificationTypeLabels, NotificationTypeColors } from '../types';

export interface NotificationItemProps {
  /** 通知数据 */
  notification: Notification;
  /** 点击回调 */
  onClick?: (notification: Notification) => void;
  /** 标记已读回调 */
  onMarkAsRead?: (id: number) => void;
  /** 删除回调 */
  onDelete?: (id: number) => void;
  /** 是否显示操作按钮 */
  showActions?: boolean;
}

/**
 * 获取通知类型图标
 */
function getNotificationIcon(type: NotificationType): React.ReactNode {
  const iconProps = { size: 16 };

  switch (type) {
    case NotificationType.COMMENT_REPLY:
      return <MessageSquare {...iconProps} />;
    case NotificationType.POST_LIKE:
      return <Heart {...iconProps} />;
    case NotificationType.POST_FAVORITE:
      return <Bookmark {...iconProps} />;
    case NotificationType.POST_COMMENT:
      return <MessageSquare {...iconProps} />;
    case NotificationType.SYSTEM:
      return <Bell {...iconProps} />;
    case NotificationType.CONSULTATION:
      return <Briefcase {...iconProps} />;
    case NotificationType.NEWS:
      return <FileText {...iconProps} />;
    case NotificationType.ORDER:
      return <ShoppingCart {...iconProps} />;
    default:
      return <Bell {...iconProps} />;
  }
}

/**
 * 格式化时间显示
 */
function formatTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  const week = 7 * day;
  
  if (diff < minute) {
    return '刚刚';
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)}分钟前`;
  } else if (diff < day) {
    return `${Math.floor(diff / hour)}小时前`;
  } else if (diff < week) {
    return `${Math.floor(diff / day)}天前`;
  } else {
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
    });
  }
}

/**
 * 通知项组件
 */
export function NotificationItem({
  notification,
  onClick,
  onMarkAsRead,
  onDelete,
  showActions = true,
}: NotificationItemProps): React.ReactElement {
  const handleClick = (): void => {
    onClick?.(notification);
  };

  const handleMarkAsRead = (e: React.MouseEvent): void => {
    e.stopPropagation();
    onMarkAsRead?.(notification.id);
  };

  const handleDelete = (e: React.MouseEvent): void => {
    e.stopPropagation();
    onDelete?.(notification.id);
  };

  const typeColorClass = NotificationTypeColors[notification.type] || 'text-gray-500 bg-gray-50';

  return (
    <div
      onClick={handleClick}
      className={`
        group relative flex items-start gap-3 p-4 cursor-pointer
        transition-colors duration-200
        hover:bg-gray-50
        ${!notification.is_read ? 'bg-blue-50/50' : ''}
        border-b border-gray-100 last:border-b-0
      `}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
    >
      {/* 未读指示器 */}
      {!notification.is_read && (
        <span className="absolute left-1 top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-blue-500 rounded-full" />
      )}

      {/* 类型图标 */}
      <div className={`
        flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
        ${typeColorClass}
      `}>
        {getNotificationIcon(notification.type)}
      </div>

      {/* 内容区域 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            {/* 标题 */}
            <p className={`
              text-sm font-medium truncate
              ${!notification.is_read ? 'text-gray-900' : 'text-gray-700'}
            `}>
              {notification.title}
            </p>
            
            {/* 内容 */}
            {notification.content && (
              <p className="mt-0.5 text-xs text-gray-500 line-clamp-2">
                {notification.content}
              </p>
            )}
            
            {/* 元信息 */}
            <div className="mt-1.5 flex items-center gap-2 text-xs text-gray-400">
              <Clock size={12} />
              <span>{formatTime(notification.created_at)}</span>
              <span className="text-gray-300">·</span>
              <span className="text-gray-500">
                {NotificationTypeLabels[notification.type]}
              </span>
              {notification.related_user_name && (
                <>
                  <span className="text-gray-300">·</span>
                  <span className="text-gray-500">
                    {notification.related_user_name}
                  </span>
                </>
              )}
            </div>
          </div>

          {/* 操作按钮 */}
          {showActions && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {!notification.is_read && (
                <button
                  type="button"
                  onClick={handleMarkAsRead}
                  className="p-1.5 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded transition-colors"
                  title="标记为已读"
                >
                  <Check size={14} />
                </button>
              )}
              <button
                type="button"
                onClick={handleDelete}
                className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                title="删除"
              >
                <Trash2 size={14} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}