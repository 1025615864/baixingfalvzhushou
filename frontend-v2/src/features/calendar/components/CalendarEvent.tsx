/**
 * CalendarEvent 组件
 * 日历事件展示（用于事件列表和弹窗展示）
 */

import type { CalendarEventProps, CalendarEvent as CalendarEventType } from '../types';

export const CalendarEvent: React.FC<CalendarEventProps> = ({
  events,
  onEventClick,
}) => {
  const handleClick = (event: CalendarEventType): void => {
    onEventClick(event);
  };

  const formatTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (events.length === 0) {
    return (
      <div className="text-center py-6 text-gray-400">
        <svg
          className="mx-auto h-8 w-8 mb-2 text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <p className="text-sm">暂无事件</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {events.map((event) => (
        <div
          key={event.id}
          onClick={() => handleClick(event)}
          className={`p-3 rounded-lg cursor-pointer transition-colors ${
            event.isDone
              ? 'bg-gray-100 text-gray-500 line-through'
              : 'bg-blue-50 hover:bg-blue-100 border border-blue-200'
          }`}
        >
          <div className="flex items-start gap-3">
            {/* 时间 */}
            <div className="flex-shrink-0">
              <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-0.5 rounded">
                {formatTime(event.date)}
              </span>
            </div>

            {/* 内容 */}
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {event.title}
              </h4>
              {event.reminder.note && (
                <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">
                  {event.reminder.note}
                </p>
              )}
            </div>

            {/* 状态指示 */}
            {event.isDone && (
              <span className="flex-shrink-0 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                已完成
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};