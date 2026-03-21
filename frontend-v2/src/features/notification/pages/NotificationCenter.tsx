// ============================================
// 通知中心页面
// ============================================

import { useState, useEffect, useCallback, useRef } from 'react';

import {
  NotificationType,
  NotificationData,
  MessagePriority,
  WebSocketConnectionState,
} from '../types/websocket';
import { ConnectionStatus } from '../components/ConnectionStatus';
import { useNotificationStream } from '../hooks/useWebSocket';
import {
  getNotifications,
  markAsRead as apiMarkAsRead,
  markAllAsRead as apiMarkAllAsRead,
  deleteNotification as apiDeleteNotification,
  batchMarkAsRead as apiBatchMarkAsRead,
  batchDeleteNotifications as apiBatchDeleteNotifications,
} from '../api';
import type { GetNotificationsParams } from '../types';

/**
 * 筛选标签配置
 */
const filterTabs = [
  { key: 'all', label: '全部', type: null as NotificationType | null },
  { key: 'system', label: '系统', type: NotificationType.SYSTEM },
  { key: 'chat', label: '聊天', type: NotificationType.CHAT },
  { key: 'order', label: '订单', type: NotificationType.ORDER },
  { key: 'promotion', label: '推广', type: NotificationType.PROMOTION },
];

/**
 * 获取类型样式
 */
function getTypeStyle(type: NotificationType): { bg: string; text: string; label: string } {
  const styles: Record<NotificationType, { bg: string; text: string; label: string }> = {
    [NotificationType.SYSTEM]: { bg: 'bg-blue-100', text: 'text-blue-700', label: '系统' },
    [NotificationType.CHAT]: { bg: 'bg-green-100', text: 'text-green-700', label: '聊天' },
    [NotificationType.ORDER]: { bg: 'bg-purple-100', text: 'text-purple-700', label: '订单' },
    [NotificationType.CONSULTATION]: { bg: 'bg-orange-100', text: 'text-orange-700', label: '咨询' },
    [NotificationType.FORUM]: { bg: 'bg-pink-100', text: 'text-pink-700', label: '论坛' },
    [NotificationType.PAYMENT]: { bg: 'bg-red-100', text: 'text-red-700', label: '支付' },
    [NotificationType.PROMOTION]: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '推广' },
    [NotificationType.SECURITY]: { bg: 'bg-red-100', text: 'text-red-700', label: '安全' },
    [NotificationType.ACTIVITY]: { bg: 'bg-cyan-100', text: 'text-cyan-700', label: '活动' },
  };
  return styles[type] || { bg: 'bg-gray-100', text: 'text-gray-700', label: '其他' };
}

/**
 * 格式化时间
 */
function formatTime(createdAt: string): string {
  const date = new Date(createdAt);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;

  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

/**
 * 将后端通知数据转换为前端格式
 */
function mapNotificationData(data: {
  id: number;
  type?: string;
  notification_type?: string;
  title: string;
  content?: string | null;
  link?: string | null;
  priority?: string;
  is_read?: boolean;
  isRead?: boolean;
  related_user_id?: number | null;
  related_user_name?: string | null;
  created_at: string;
}): NotificationData {
  const notificationType = data.notification_type || data.type || 'system';
  // 将后端类型映射到 WebSocket 类型
  const typeMapping: Record<string, NotificationType> = {
    'comment_reply': NotificationType.CHAT,
    'post_like': NotificationType.ACTIVITY,
    'post_favorite': NotificationType.ACTIVITY,
    'post_comment': NotificationType.FORUM,
    'system': NotificationType.SYSTEM,
    'consultation': NotificationType.CONSULTATION,
    'news': NotificationType.ACTIVITY,
    'order': NotificationType.ORDER,
    'chat': NotificationType.CHAT,
    'forum': NotificationType.FORUM,
    'payment': NotificationType.PAYMENT,
    'promotion': NotificationType.PROMOTION,
    'security': NotificationType.SECURITY,
    'activity': NotificationType.ACTIVITY,
  };
  
  return {
    id: data.id,
    type: typeMapping[notificationType] || NotificationType.SYSTEM,
    title: data.title,
    content: data.content ?? undefined,
    link: data.link ?? undefined,
    priority: (data.priority as MessagePriority) || MessagePriority.NORMAL,
    isRead: data.is_read ?? data.isRead ?? false,
    senderId: data.related_user_id ?? undefined,
    senderName: data.related_user_name ?? undefined,
    createdAt: data.created_at,
  };
}

/**
 * 获取 WebSocket URL
 */
function getWebSocketUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return `${protocol}//${host}/api/v1/ws/notifications`;
}

/**
 * 获取认证 Token
 */
function getAuthToken(): string | null {
  // 尝试从 localStorage 获取 token
  try {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token');
    return token;
  } catch {
    return null;
  }
}

/**
 * 通知中心页面
 */
export function NotificationCenter(): JSX.Element {
  // 状态
  const [notifications, setNotifications] = useState<NotificationData[]>([]);
  const [activeTab, setActiveTab] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [showBatchActions, setShowBatchActions] = useState(false);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // WebSocket 连接
  const wsUrl = getWebSocketUrl();
  const authToken = getAuthToken();
  
  const {
    isConnected,
    latestNotification,
  } = useNotificationStream(wsUrl, authToken, true);

  // 当收到新通知时，添加到列表
  useEffect(() => {
    if (latestNotification) {
      setNotifications((prev) => {
        // 避免重复添加
        if (prev.some((n) => n.id === latestNotification.id)) {
          return prev;
        }
        return [latestNotification, ...prev];
      });
    }
  }, [latestNotification]);

  // 统计数据
  const unreadCount = notifications.filter((n) => !n.isRead).length;
  const filteredNotifications = activeTab === 'all'
    ? notifications
    : notifications.filter((n) => n.type === (activeTab as NotificationType));

  // 初始加载通知
  const loadNotifications = useCallback(async (page: number, append = false) => {
    if (isLoading && append) return;
    
    setIsLoading(true);
    try {
      const params: GetNotificationsParams = {
        page,
        page_size: 20,
        unread_only: false,
      };
      
      const response = await getNotifications(params);
      const mappedNotifications = (response.items || []).map(mapNotificationData);
      
      if (append) {
        setNotifications((prev) => [...prev, ...mappedNotifications]);
      } else {
        setNotifications(mappedNotifications);
      }
      
      setHasMore(mappedNotifications.length >= 20);
    } catch (error) {
      console.error('加载通知失败:', error);
      // 如果 API 失败，使用空数组
      if (!append) {
        setNotifications([]);
      }
      setHasMore(false);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  // 初始加载 - 只在组件挂载时执行一次
  useEffect(() => {
    void loadNotifications(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 加载更多
  const loadMore = useCallback(() => {
    if (isLoading || !hasMore) return;
    const nextPage = currentPage + 1;
    setCurrentPage(nextPage);
    void loadNotifications(nextPage, true);
  }, [isLoading, hasMore, currentPage, loadNotifications]);

  // 无限滚动观察器
  useEffect(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMore();
        }
      },
      { threshold: 0.5 }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      observerRef.current?.disconnect();
    };
  }, [loadMore]);

  // 标记已读
  const markAsRead = useCallback(async (id: number) => {
    // 乐观更新
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
    );
    
    try {
      await apiMarkAsRead(id);
    } catch (error) {
      console.error('标记已读失败:', error);
    }
  }, []);

  // 标记全部已读
  const markAllAsRead = useCallback(async () => {
    // 乐观更新
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
    
    try {
      await apiMarkAllAsRead();
    } catch (error) {
      console.error('标记全部已读失败:', error);
    }
  }, []);

  // 删除通知
  const deleteNotification = useCallback(async (id: number) => {
    // 乐观更新
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    
    try {
      await apiDeleteNotification(id);
    } catch (error) {
      console.error('删除通知失败:', error);
    }
  }, []);

  // 选择/取消选择
  const toggleSelect = useCallback((id: number) => {
    setSelectedItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  // 批量已读
  const batchMarkAsRead = useCallback(async () => {
    const ids = Array.from(selectedItems);
    // 乐观更新
    setNotifications((prev) =>
      prev.map((n) => (selectedItems.has(n.id) ? { ...n, isRead: true } : n))
    );
    setSelectedItems(new Set());
    setShowBatchActions(false);
    
    try {
      await apiBatchMarkAsRead({ ids });
    } catch (error) {
      console.error('批量标记已读失败:', error);
    }
  }, [selectedItems]);

  // 批量删除
  const batchDelete = useCallback(async () => {
    const ids = Array.from(selectedItems);
    // 乐观更新
    setNotifications((prev) => prev.filter((n) => !selectedItems.has(n.id)));
    setSelectedItems(new Set());
    setShowBatchActions(false);
    
    try {
      await apiBatchDeleteNotifications({ ids });
    } catch (error) {
      console.error('批量删除失败:', error);
    }
  }, [selectedItems]);

  // 切换批量选择模式
  const toggleBatchMode = useCallback(() => {
    setShowBatchActions((prev) => !prev);
    if (showBatchActions) {
      setSelectedItems(new Set());
    }
  }, [showBatchActions]);

  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      {/* 页面头部 */}
      <div className="bg-white shadow-sm">
        <div className="mx-auto max-w-5xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">通知中心</h1>
              <p className="mt-1 text-sm text-gray-500">
                您有 {unreadCount} 条未读通知
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              {/* 连接状态 */}
              <ConnectionStatus
                state={isConnected ? WebSocketConnectionState.CONNECTED : WebSocketConnectionState.DISCONNECTED}
                latency={isConnected ? 45 : undefined}
                showLabel={false}
                size="sm"
              />
              
              {/* 批量操作按钮 */}
              <button
                type="button"
                onClick={toggleBatchMode}
                className={`
                  rounded-lg px-4 py-2 text-sm font-medium transition-colors
                  ${showBatchActions
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
                `}
              >
                {showBatchActions ? '取消选择' : '批量选择'}
              </button>
              
              {/* 全部已读 */}
              {!showBatchActions && unreadCount > 0 && (
                <button
                  type="button"
                  onClick={() => void markAllAsRead()}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  全部已读
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 批量操作栏 */}
      {showBatchActions && selectedItems.size > 0 && (
        <div className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
          <div className="mx-auto max-w-5xl px-4 py-3 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">
                已选择 {selectedItems.size} 条通知
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => void batchMarkAsRead()}
                  className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                >
                  标记已读
                </button>
                <button
                  type="button"
                  onClick={() => void batchDelete()}
                  className="rounded-lg border border-red-300 bg-white px-3 py-1.5 text-sm text-red-600 hover:bg-red-50"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
        {/* 筛选标签 */}
        <div className="mb-6 flex flex-wrap gap-2">
          {filterTabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`
                rounded-full px-4 py-2 text-sm font-medium transition-colors
                ${activeTab === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'}
              `}
            >
              {tab.label}
              {tab.key === 'all' && unreadCount > 0 && (
                <span className="ml-2 rounded-full bg-red-500 px-1.5 py-0.5 text-xs">
                  {unreadCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* 通知列表 */}
        <div className="space-y-3">
          {isLoading && notifications.length === 0 ? (
            // 首次加载骨架屏
            <div className="space-y-3">
              {Array.from({ length: 5 }, (_, index) => (
                <div
                  key={index}
                  className="animate-pulse rounded-lg border border-gray-200 bg-white p-4"
                >
                  <div className="flex items-start gap-4">
                    <div className="h-10 w-10 rounded-lg bg-gray-200" />
                    <div className="flex-1">
                      <div className="h-5 bg-gray-200 rounded w-1/3 mb-2" />
                      <div className="h-4 bg-gray-200 rounded w-full mb-1" />
                      <div className="h-4 bg-gray-200 rounded w-2/3" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-lg bg-white py-16">
              <svg
                className="h-16 w-16 text-gray-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
              <p className="mt-4 text-gray-500">暂无通知</p>
            </div>
          ) : (
            filteredNotifications.map((notification) => {
              const typeStyle = getTypeStyle(notification.type);
              const isSelected = selectedItems.has(notification.id);

              return (
                <div
                  key={notification.id}
                  className={`
                    group relative flex items-start gap-4 rounded-lg border bg-white p-4 transition-all
                    ${notification.isRead ? 'border-gray-200' : 'border-blue-200 bg-blue-50/30'}
                    ${isSelected ? 'ring-2 ring-blue-500' : ''}
                    hover:shadow-md
                  `}
                >
                  {/* 选择框 */}
                  {showBatchActions && (
                    <div className="flex-shrink-0 pt-1">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelect(notification.id)}
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </div>
                  )}

                  {/* 类型图标 */}
                  <div
                    className={`flex-shrink-0 rounded-lg ${typeStyle.bg} p-2`}
                  >
                    <span className={`text-lg ${typeStyle.text}`}>
                      {typeStyle.label}
                    </span>
                  </div>

                  {/* 内容 */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3
                          className={`text-base ${
                            notification.isRead
                              ? 'font-normal text-gray-700'
                              : 'font-semibold text-gray-900'
                          }`}
                        >
                          {notification.title}
                        </h3>
                        {notification.content && (
                          <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                            {notification.content}
                          </p>
                        )}
                        <div className="mt-2 flex items-center gap-4 text-xs text-gray-400">
                          <span>{formatTime(notification.createdAt)}</span>
                          {notification.senderName && (
                            <span>来自: {notification.senderName}</span>
                          )}
                        </div>
                      </div>

                      {/* 操作按钮 */}
                      {!showBatchActions && (
                        <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                          {!notification.isRead && (
                            <button
                              type="button"
                              onClick={() => void markAsRead(notification.id)}
                              className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-blue-600"
                              title="标记为已读"
                            >
                              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => void deleteNotification(notification.id)}
                            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600"
                            title="删除"
                          >
                            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 未读指示器 */}
                  {!notification.isRead && (
                    <span className="absolute right-4 top-4 h-2 w-2 rounded-full bg-blue-500" />
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* 加载更多 */}
        {hasMore && (
          <div ref={loadMoreRef} className="mt-6 flex justify-center">
            {isLoading ? (
              <div className="flex items-center gap-2 text-gray-500">
                <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span>加载中...</span>
              </div>
            ) : (
              <div className="h-10" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default NotificationCenter;