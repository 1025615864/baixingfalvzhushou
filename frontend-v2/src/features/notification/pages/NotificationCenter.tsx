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
 * 模拟通知数据
 */
const MOCK_NOTIFICATIONS: NotificationData[] = [
  {
    id: 1,
    type: NotificationType.SYSTEM,
    title: '账户安全提醒',
    content: '您的账户在新设备上登录，如非本人操作请及时修改密码',
    isRead: false,
    priority: MessagePriority.HIGH,
    createdAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
  },
  {
    id: 2,
    type: NotificationType.CHAT,
    title: '张律师回复了您的咨询',
    content: '关于劳动仲裁的问题，我已经给您详细解答了，请查看...',
    isRead: false,
    priority: MessagePriority.NORMAL,
    senderName: '张律师',
    createdAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
  },
  {
    id: 3,
    type: NotificationType.ORDER,
    title: '订单支付成功',
    content: '您购买的法律咨询服务订单已支付成功，订单号：ORD20240201001',
    isRead: true,
    priority: MessagePriority.NORMAL,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: 4,
    type: NotificationType.PROMOTION,
    title: '限时优惠',
    content: '本周法律顾问服务限时8折优惠，立即查看',
    isRead: false,
    priority: MessagePriority.LOW,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
  },
  {
    id: 5,
    type: NotificationType.FORUM,
    title: '您的帖子收到回复',
    content: '您的帖子《劳动合同纠纷求助》收到了新的回复',
    isRead: true,
    priority: MessagePriority.NORMAL,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
  },
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
 * 通知中心页面
 */
export function NotificationCenter(): JSX.Element {
  // 状态
  const [notifications, setNotifications] = useState<NotificationData[]>(MOCK_NOTIFICATIONS);
  const [activeTab, setActiveTab] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [showBatchActions, setShowBatchActions] = useState(false);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // 统计数据
  const unreadCount = notifications.filter((n) => !n.isRead).length;
  const filteredNotifications = activeTab === 'all'
    ? notifications
    : notifications.filter((n) => n.type === (activeTab as NotificationType));

  // 加载更多（模拟无限滚动）
  const loadMore = useCallback(() => {
    if (isLoading || !hasMore) return;
    
    setIsLoading(true);
    // 模拟API调用
    setTimeout(() => {
      const newItems: NotificationData[] = Array.from({ length: 5 }, (_, i) => ({
        id: Date.now() + i,
        type: NotificationType.SYSTEM,
        title: `历史通知 ${i + 1}`,
        content: '这是一条历史通知消息内容...',
        isRead: true,
        priority: MessagePriority.NORMAL,
        createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * (i + 1)).toISOString(),
      }));
      
      setNotifications((prev) => [...prev, ...newItems]);
      setIsLoading(false);
      if (newItems.length < 5) {
        setHasMore(false);
      }
    }, 800);
  }, [isLoading, hasMore]);

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
  const markAsRead = useCallback((id: number) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
    );
  }, []);

  // 标记全部已读
  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
  }, []);

  // 删除通知
  const deleteNotification = useCallback((id: number) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
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
  const batchMarkAsRead = useCallback(() => {
    setNotifications((prev) =>
      prev.map((n) => (selectedItems.has(n.id) ? { ...n, isRead: true } : n))
    );
    setSelectedItems(new Set());
    setShowBatchActions(false);
  }, [selectedItems]);

  // 批量删除
  const batchDelete = useCallback(() => {
    setNotifications((prev) => prev.filter((n) => !selectedItems.has(n.id)));
    setSelectedItems(new Set());
    setShowBatchActions(false);
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
                state={WebSocketConnectionState.CONNECTED}
                latency={45}
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
                  onClick={markAllAsRead}
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
                  onClick={batchMarkAsRead}
                  className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                >
                  标记已读
                </button>
                <button
                  type="button"
                  onClick={batchDelete}
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
          {filteredNotifications.length === 0 ? (
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
                              onClick={() => markAsRead(notification.id)}
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
                            onClick={() => deleteNotification(notification.id)}
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