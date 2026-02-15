// ============================================
// 通知中心页面
// ============================================

import { useNotificationList, useMarkAsRead, useMarkAllAsRead, useDeleteNotification } from '../../features/notification/hooks/useNotification';

export function NotificationPage() {
  const { data, isLoading } = useNotificationList();
  const markAsRead = useMarkAsRead();
  const markAllAsRead = useMarkAllAsRead();
  const deleteNotification = useDeleteNotification();

  const getIconByType = (type: string) => {
    switch (type) {
      case 'consultation':
        return <span className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
        </span>;
      case 'payment':
        return <span className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </span>;
      case 'system':
        return <span className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-600">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </span>;
      case 'forum':
        return <span className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" /></svg>
        </span>;
      default:
        return <span className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
        </span>;
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">消息通知</h1>
            <p className="text-gray-600 mt-1">您有 {data?.unread_count || 0} 条未读消息</p>
          </div>
          {data && data.unread_count > 0 && (
            <button
              onClick={() => { markAllAsRead.mutate(); }}
              className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              全部已读
            </button>
          )}
        </div>

        {isLoading ? (
          <div className="text-center py-12 text-gray-500">加载中...</div>
        ) : data?.items.length === 0 ? (
          <div className="text-center py-12 text-gray-500">暂无通知</div>
        ) : (
          <div className="space-y-3">
            {data?.items.map((notification) => (
              <div
                key={notification.id}
                onClick={() => { 
                  if (!notification.is_read) markAsRead.mutate(notification.id); 
                }}
                className={`bg-white rounded-lg p-4 shadow-sm border cursor-pointer hover:shadow-md transition-all ${
                  notification.is_read ? 'border-gray-100 opacity-70' : 'border-blue-200 bg-blue-50/30'
                }`}
              >
                <div className="flex items-start gap-4">
                  {getIconByType(notification.type)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className={`font-medium ${notification.is_read ? 'text-gray-700' : 'text-gray-900'}`}>
                        {notification.title}
                        {!notification.is_read && <span className="ml-2 w-2 h-2 bg-red-500 rounded-full inline-block"></span>}
                      </h3>
                      <span className="text-xs text-gray-400 whitespace-nowrap">{formatTime(notification.created_at)}</span>
                    </div>
                    {notification.content && (
                      <p className="text-sm text-gray-600 mt-1">{notification.content}</p>
                    )}
                    {notification.related_user_name && (
                      <p className="text-xs text-gray-500 mt-1">来自：{notification.related_user_name}</p>
                    )}
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteNotification.mutate(notification.id); }}
                    className="text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}