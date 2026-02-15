/**
 * 通知下拉列表组件
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';

import {
  useNotifications,
  useMarkAsRead,
  useMarkAllAsRead,
  useDeleteNotification,
  useUnreadCount,
  useNotificationActions,
} from '../hooks/useNotifications';
import { Notification } from '../types';

import { NotificationItem } from './NotificationItem';
import { NotificationEmpty } from './NotificationEmpty';
import { NotificationSkeleton } from './NotificationSkeleton';

export interface NotificationDropdownProps {
  /** 是否展开 */
  isOpen: boolean;
  /** 关闭回调 */
  onClose: () => void;
}

/**
 * 通知下拉列表组件
 */
export function NotificationDropdown({ isOpen, onClose }: NotificationDropdownProps): React.ReactElement | null {
  const navigate = useNavigate();
  const { data, isLoading } = useNotifications({ page_size: 10 });
  const { data: unreadData } = useUnreadCount();
  const { handleNotificationClick } = useNotificationActions();
  const { mutate: markAsRead } = useMarkAsRead();
  const { mutate: markAllAsRead } = useMarkAllAsRead();
  const { mutate: deleteNotification } = useDeleteNotification();

  if (!isOpen) return null;

  const notifications = data?.items ?? [];
  const unreadCount = unreadData?.unread_count ?? 0;
  const totalCount = data?.total ?? 0;

  const handleClick = (notification: Notification): void => {
    void handleNotificationClick(notification).then((link) => {
      onClose();
      if (link) {
        navigate(link);
      }
    });
  };

  const handleMarkAllAsRead = (): void => {
    markAllAsRead();
  };

  const handleViewAll = (): void => {
    onClose();
    navigate('/notifications');
  };

  return (
    <div className="absolute right-0 top-full mt-2 w-[400px] bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50/50">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-900">通知消息</h3>
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium text-white bg-blue-500 rounded-full">
              {unreadCount}条未读
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button
              type="button"
              onClick={handleMarkAllAsRead}
              className="text-xs text-blue-600 hover:text-blue-700 hover:underline"
            >
              全部已读
            </button>
          )}
          <button
            type="button"
            onClick={handleViewAll}
            className="text-xs text-gray-500 hover:text-gray-700 hover:underline"
          >
            查看全部
          </button>
        </div>
      </div>

      {/* 通知列表 */}
      <div className="max-h-[400px] overflow-y-auto">
        {isLoading ? (
          <NotificationSkeleton count={3} />
        ) : notifications.length === 0 ? (
          <NotificationEmpty />
        ) : (
          <div>
            {notifications.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onClick={handleClick}
                onMarkAsRead={(id) => markAsRead(id)}
                onDelete={(id) => deleteNotification(id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* 底部 */}
      {totalCount > 10 && (
        <div className="px-4 py-2 border-t border-gray-100 bg-gray-50/50 text-center">
          <button
            type="button"
            onClick={handleViewAll}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            还有 {totalCount - 10} 条通知，点击查看全部
          </button>
        </div>
      )}
    </div>
  );
}