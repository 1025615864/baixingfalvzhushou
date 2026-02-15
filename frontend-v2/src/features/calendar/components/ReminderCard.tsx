/**
 * ReminderCard 组件
 * 展示单个提醒的卡片
 */

import type { ReminderCardProps } from '../types';

export const ReminderCard: React.FC<ReminderCardProps> = ({
  reminder,
  onEdit,
  onDelete,
  onToggleStatus,
}) => {
  const handleToggleStatus = (): void => {
    onToggleStatus(reminder.id, !reminder.isDone);
  };

  const handleEdit = (): void => {
    onEdit(reminder);
  };

  const handleDelete = (): void => {
    onDelete(reminder.id);
  };

  const formatDateTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isOverdue = !reminder.isDone && new Date(reminder.dueAt) < new Date();

  return (
    <div
      className={`group relative rounded-lg border p-4 transition-all hover:shadow-md ${
        reminder.isDone
          ? 'border-gray-200 bg-gray-50'
          : isOverdue
            ? 'border-red-200 bg-red-50'
            : 'border-blue-200 bg-blue-50'
      }`}
    >
      <div className="flex items-start gap-3">
        {/* 状态复选框 */}
        <button
          type="button"
          onClick={handleToggleStatus}
          className={`mt-1 flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
            reminder.isDone 
              ? 'bg-green-500 border-green-500 text-white' 
              : 'border-gray-300 hover:border-green-400'
          }`}
          aria-label={reminder.isDone ? '标记为未完成' : '标记为已完成'}
        >
          {reminder.isDone && (
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </button>

        {/* 内容区域 */}
        <div className="flex-1 min-w-0">
          <h4
            className={`font-medium text-sm ${
              reminder.isDone ? 'text-gray-500 line-through' : 'text-gray-900'
            }`}
          >
            {reminder.title}
          </h4>

          {reminder.note && (
            <p
              className={`mt-1 text-xs ${
                reminder.isDone ? 'text-gray-400' : 'text-gray-600'
              } line-clamp-2`}
            >
              {reminder.note}
            </p>
          )}

          <div className="mt-2 flex items-center gap-2 text-xs">
            <svg 
              className={`h-3.5 w-3.5 ${isOverdue ? 'text-red-500' : 'text-gray-400'}`}
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span
              className={
                isOverdue ? 'text-red-600 font-medium' : 'text-gray-500'
              }
            >
              {formatDateTime(reminder.dueAt)}
              {isOverdue && ' (已逾期)'}
            </span>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            type="button"
            onClick={handleEdit}
            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-100 rounded-md transition-colors"
            aria-label="编辑"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
          <button
            type="button"
            onClick={handleDelete}
            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-100 rounded-md transition-colors"
            aria-label="删除"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};