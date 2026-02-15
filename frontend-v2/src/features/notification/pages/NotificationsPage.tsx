/**
 * 通知中心页面
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Notification } from '../types';
import {
  useNotifications,
  useMarkAsRead,
  useMarkAllAsRead,
  useDeleteNotification,
  useBatchMarkAsRead,
  useBatchDeleteNotifications,
  useNotificationTypesStats,
  useNotificationActions,
} from '../hooks/useNotifications';
import { NotificationItem } from '../components/NotificationItem';
import { NotificationEmpty } from '../components/NotificationEmpty';
import { NotificationSkeleton } from '../components/NotificationSkeleton';
import { NotificationSettings } from '../components/NotificationSettings';

/** 分页大小 */
const PAGE_SIZE = 20;

/**
 * 通知中心页面
 */
export function NotificationsPage(): React.ReactElement {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');

  const { data, isLoading } = useNotifications({
    page,
    page_size: PAGE_SIZE,
  });

  const { data: statsData } = useNotificationTypesStats();
  const { handleNotificationClick } = useNotificationActions();
  const { mutate: markAsRead } = useMarkAsRead();
  const { mutate: markAllAsRead } = useMarkAllAsRead();
  const { mutate: deleteNotification } = useDeleteNotification();
  const { mutate: batchMarkAsRead } = useBatchMarkAsRead();
  const { mutate: batchDelete } = useBatchDeleteNotifications();

  const notifications = data?.items ?? [];
  const totalCount = data?.total ?? 0;
  const unreadCount = data?.unread_count ?? 0;
  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  /** 处理通知点击 */
  const handleClick = (notification: Notification): void => {
    void (async () => {
      const link = await handleNotificationClick(notification);
      if (link) {
        navigate(link);
      }
    })();
  };

  /** 处理选择 */
  const handleSelect = (id: number, selected: boolean): void => {
    if (selected) {
      setSelectedIds((prev) => [...prev, id]);
    } else {
      setSelectedIds((prev) => prev.filter((item) => item !== id));
    }
  };

  /** 全选 */
  const handleSelectAll = (): void => {
    if (selectedIds.length === notifications.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(notifications.map((n) => n.id));
    }
  };

  /** 批量标记已读 */
  const handleBatchMarkAsRead = (): void => {
    if (selectedIds.length === 0) return;
    batchMarkAsRead(selectedIds, {
      onSuccess: () => setSelectedIds([]),
    });
  };

  /** 批量删除 */
  const handleBatchDelete = (): void => {
    if (selectedIds.length === 0) return;
    batchDelete(selectedIds, {
      onSuccess: () => setSelectedIds([]),
    });
  };

  /** 渲染过滤器 */
  const renderFilter = (): React.ReactElement => (
    <div className="flex items-center gap-2 mb-4">
      <button
        type="button"
        onClick={() => setFilterType('all')}
        className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
          filterType === 'all'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        全部
      </button>
      <button
        type="button"
        onClick={() => setFilterType('unread')}
        className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
          filterType === 'unread'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        未读 {unreadCount > 0 && `(${unreadCount})`}
      </button>
      {statsData?.types &&
        Object.entries(statsData.types).map(([type, count]) => (
          <button
            key={type}
            type="button"
            onClick={() => setFilterType(type)}
            className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
              filterType === type
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {statsData.type_labels[type] || type} ({count})
          </button>
        ))}
    </div>
  );

  /** 渲染批量操作栏 */
  const renderBatchActions = (): React.ReactElement | null => {
    if (selectedIds.length === 0) return null;

    return (
      <div className="flex items-center justify-between px-4 py-3 bg-blue-50 rounded-lg mb-4">
        <span className="text-sm text-blue-700">
          已选择 {selectedIds.length} 条通知
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleBatchMarkAsRead}
            className="px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-100 rounded transition-colors"
          >
            标记已读
          </button>
          <button
            type="button"
            onClick={handleBatchDelete}
            className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-100 rounded transition-colors"
          >
            删除
          </button>
          <button
            type="button"
            onClick={() => setSelectedIds([])}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
          >
            取消
          </button>
        </div>
      </div>
    );
  };

  /** 渲染分页 */
  const renderPagination = (): React.ReactElement | null => {
    if (totalPages <= 1) return null;

    return (
      <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
        <span className="text-sm text-gray-500">
          共 {totalCount} 条，第 {page}/{totalPages} 页
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一页
          </button>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一页
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">通知中心</h1>
            <p className="mt-1 text-sm text-gray-500">
              管理您的所有通知消息
              {unreadCount > 0 && (
                <span className="ml-2 text-blue-600">
                  有 {unreadCount} 条未读消息
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={() => markAllAsRead()}
                className="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
              >
                全部已读
              </button>
            )}
            <button
              type="button"
              onClick={() => setShowSettings(!showSettings)}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {showSettings ? '返回列表' : '通知设置'}
            </button>
          </div>
        </div>

        {showSettings ? (
          <NotificationSettings />
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            {/* 过滤器 */}
            <div className="px-4 py-3 border-b border-gray-100">
              {renderFilter()}
            </div>

            {/* 批量操作 */}
            <div className="px-4 pt-4">{renderBatchActions()}</div>

            {/* 全选 */}
            {notifications.length > 0 && (
              <div className="px-4 py-2 border-b border-gray-100">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={
                      selectedIds.length === notifications.length &&
                      notifications.length > 0
                    }
                    onChange={handleSelectAll}
                    className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-600">全选</span>
                </label>
              </div>
            )}

            {/* 通知列表 */}
            <div>
              {isLoading ? (
                <NotificationSkeleton count={5} />
              ) : notifications.length === 0 ? (
                <NotificationEmpty />
              ) : (
                notifications.map((notification) => (
                  <div key={notification.id} className="flex items-center px-4">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(notification.id)}
                      onChange={(e) =>
                        handleSelect(notification.id, e.target.checked)
                      }
                      className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 mr-3"
                    />
                    <div className="flex-1">
                      <NotificationItem
                        notification={notification}
                        onClick={handleClick}
                        onMarkAsRead={(id) => { void markAsRead(id); }}
                        onDelete={(id) => { void deleteNotification(id); }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* 分页 */}
            {renderPagination()}
          </div>
        )}
      </div>
    </div>
  );
}