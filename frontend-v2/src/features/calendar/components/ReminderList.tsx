/**
 * ReminderList 组件
 * 展示提醒列表
 */

import type { ReminderListProps } from '../types';

import { ReminderCard } from './ReminderCard';

export const ReminderList: React.FC<ReminderListProps> = ({
  reminders,
  onEdit,
  onDelete,
  onToggleStatus,
  selectedDate,
}) => {
  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long',
    });
  };

  // 按时间排序
  const sortedReminders = [...reminders].sort((a, b) => {
    return new Date(a.dueAt).getTime() - new Date(b.dueAt).getTime();
  });

  // 分离已完成和未完成的提醒
  const pendingReminders = sortedReminders.filter((r) => !r.isDone);
  const completedReminders = sortedReminders.filter((r) => r.isDone);

  return (
    <div className="space-y-4">
      {/* 标题 */}
      {selectedDate && (
        <div className="flex items-center gap-2 pb-2 border-b border-gray-200">
          <svg
            className="h-5 w-5 text-blue-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900">
            {formatDate(selectedDate)}
          </h3>
          <span className="text-sm text-gray-500">
            ({reminders.length} 个提醒)
          </span>
        </div>
      )}

      {/* 待办提醒 */}
      {pendingReminders.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
            待办 ({pendingReminders.length})
          </h4>
          <div className="space-y-2">
            {pendingReminders.map((reminder) => (
              <ReminderCard
                key={reminder.id}
                reminder={reminder}
                onEdit={onEdit}
                onDelete={onDelete}
                onToggleStatus={onToggleStatus}
              />
            ))}
          </div>
        </div>
      )}

      {/* 已完成提醒 */}
      {completedReminders.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-500 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            已完成 ({completedReminders.length})
          </h4>
          <div className="space-y-2 opacity-75">
            {completedReminders.map((reminder) => (
              <ReminderCard
                key={reminder.id}
                reminder={reminder}
                onEdit={onEdit}
                onDelete={onDelete}
                onToggleStatus={onToggleStatus}
              />
            ))}
          </div>
        </div>
      )}

      {/* 空状态 */}
      {reminders.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <svg
            className="mx-auto h-12 w-12 text-gray-300 mb-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <p>暂无提醒事项</p>
          <p className="text-sm text-gray-400 mt-1">点击&ldquo;新建提醒&rdquo;添加</p>
        </div>
      )}
    </div>
  );
};