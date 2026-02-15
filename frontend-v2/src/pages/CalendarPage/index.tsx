// ============================================
// 日历提醒页面
// ============================================

import { useState } from 'react';

import { useReminders, useCreateReminder, useUpdateReminder, useDeleteReminder } from '../../features/calendar/hooks/useCalendar';
import type { CalendarReminder } from '../../features/calendar/types';

export function CalendarPage() {
  const { data: remindersData, isLoading } = useReminders();
  const createReminder = useCreateReminder();
  const updateReminder = useUpdateReminder();
  const deleteReminder = useDeleteReminder();
  
  const [showForm, setShowForm] = useState(false);
  const [newReminder, setNewReminder] = useState({ title: '', note: '', dueAt: '' });

  const handleCreate = () => {
    if (!newReminder.title || !newReminder.dueAt) return;
    createReminder.mutate(newReminder, {
      onSuccess: () => {
        setShowForm(false);
        setNewReminder({ title: '', note: '', dueAt: '' });
      },
    });
  };

  const handleToggleDone = (reminder: CalendarReminder) => {
    updateReminder.mutate({ id: reminder.id, data: { isDone: !reminder.isDone } });
  };

  const handleDelete = (id: number) => {
    if (confirm('确定要删除这个提醒吗？')) {
      deleteReminder.mutate(id);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const reminders = remindersData?.items || [];
  const pendingReminders = reminders.filter((r) => !r.isDone);
  const completedReminders = reminders.filter((r) => r.isDone);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">法律日历</h1>
            <p className="text-gray-600 mt-1">管理您的法律事务提醒</p>
          </div>
          <button
            onClick={() => { setShowForm(!showForm); }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建提醒
          </button>
        </div>

        {/* 新建提醒表单 */}
        {showForm && (
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">新建提醒</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">标题</label>
                <input
                  type="text"
                  value={newReminder.title}
                  onChange={(e) => { setNewReminder({ ...newReminder, title: e.target.value }); }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="例如：劳动仲裁开庭"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">备注</label>
                <textarea
                  value={newReminder.note}
                  onChange={(e) => { setNewReminder({ ...newReminder, note: e.target.value }); }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  placeholder="补充说明..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">截止时间</label>
                <input
                  type="datetime-local"
                  value={newReminder.dueAt}
                  onChange={(e) => { setNewReminder({ ...newReminder, dueAt: e.target.value }); }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCreate}
                  disabled={createReminder.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {createReminder.isPending ? '创建中...' : '创建'}
                </button>
                <button
                  onClick={() => { setShowForm(false); }}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 待处理提醒 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 mb-6">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              待处理 ({pendingReminders.length})
            </h2>
          </div>
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">加载中...</div>
          ) : pendingReminders.length === 0 ? (
            <div className="p-8 text-center text-gray-500">暂无待处理提醒</div>
          ) : (
            <div className="divide-y divide-gray-100">
              {pendingReminders.map((reminder) => (
                <div key={reminder.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <button
                        onClick={() => { handleToggleDone(reminder); }}
                        className="mt-1 w-5 h-5 border-2 border-gray-300 rounded hover:border-blue-500 transition-colors"
                      />
                      <div>
                        <h3 className="font-medium text-gray-900">{reminder.title}</h3>
                        {reminder.note && (
                          <p className="text-sm text-gray-600 mt-1">{reminder.note}</p>
                        )}
                        <p className="text-sm text-red-600 mt-2 flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {formatDate(reminder.dueAt)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => { handleDelete(reminder.id); }}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 已完成提醒 */}
        {completedReminders.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-100">
            <div className="p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                已完成 ({completedReminders.length})
              </h2>
            </div>
            <div className="divide-y divide-gray-100">
              {completedReminders.map((reminder) => (
                <div key={reminder.id} className="p-4 hover:bg-gray-50 transition-colors opacity-60">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <button
                        onClick={() => { handleToggleDone(reminder); }}
                        className="mt-1 w-5 h-5 bg-green-500 rounded flex items-center justify-center"
                      >
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      </button>
                      <div>
                        <h3 className="font-medium text-gray-900 line-through">{reminder.title}</h3>
                        {reminder.note && (
                          <p className="text-sm text-gray-600 mt-1">{reminder.note}</p>
                        )}
                        <p className="text-sm text-gray-400 mt-2">{formatDate(reminder.dueAt)}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => { handleDelete(reminder.id); }}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
