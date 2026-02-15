/**
 * CalendarPage 页面
 * 法律日历主页面
 */

import { useState, useMemo } from 'react';

import type { CalendarReminder, CalendarViewType, CreateReminderRequest, UpdateReminderRequest } from '../types';
import { useReminders, useCreateReminder, useUpdateReminder, useDeleteReminder, useToggleReminderStatus } from '../hooks/useCalendar';
import { CalendarView } from '../components/CalendarView';
import { ReminderList } from '../components/ReminderList';
import { ReminderModal } from '../components/ReminderModal';

export const CalendarPage: React.FC = () => {
  // 视图状态
  const [viewType, setViewType] = useState<CalendarViewType>('month');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  
  // 弹窗状态
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [editingReminder, setEditingReminder] = useState<CalendarReminder | undefined>(undefined);

  // 获取提醒列表
  const { data: remindersData, isLoading: isLoadingReminders } = useReminders({
    pageSize: 1000,
  });

  // Mutations
  const createMutation = useCreateReminder();
  const updateMutation = useUpdateReminder();
  const deleteMutation = useDeleteReminder();
  const toggleMutation = useToggleReminderStatus();

  const reminders = useMemo(() => remindersData?.items || [], [remindersData?.items]);

  // 获取选中日期的提醒
  const selectedDateReminders = useMemo(() => {
    if (!selectedDate) return [];
    const dateStr = selectedDate.toISOString().split('T')[0];
    return reminders.filter((r) => r.dueAt.startsWith(dateStr));
  }, [reminders, selectedDate]);

  // 格式化日期范围显示
  const formatDateRange = (): string => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1;
    
    if (viewType === 'month') {
      return `${year}年${month}月`;
    } else if (viewType === 'week') {
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);
      return `${startOfWeek.getMonth() + 1}月${startOfWeek.getDate()}日 - ${endOfWeek.getMonth() + 1}月${endOfWeek.getDate()}日`;
    } else {
      return currentDate.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long',
      });
    }
  };

  // 导航函数
  const goToPrevious = (): void => {
    const newDate = new Date(currentDate);
    if (viewType === 'month') {
      newDate.setMonth(newDate.getMonth() - 1);
    } else if (viewType === 'week') {
      newDate.setDate(newDate.getDate() - 7);
    } else {
      newDate.setDate(newDate.getDate() - 1);
    }
    setCurrentDate(newDate);
  };

  const goToNext = (): void => {
    const newDate = new Date(currentDate);
    if (viewType === 'month') {
      newDate.setMonth(newDate.getMonth() + 1);
    } else if (viewType === 'week') {
      newDate.setDate(newDate.getDate() + 7);
    } else {
      newDate.setDate(newDate.getDate() + 1);
    }
    setCurrentDate(newDate);
  };

  const goToToday = (): void => {
    const today = new Date();
    setCurrentDate(today);
    setSelectedDate(today);
  };

  // 处理日期点击
  const handleDateClick = (date: Date): void => {
    setSelectedDate(date);
  };

  // 处理事件点击
  const handleEventClick = (reminder: CalendarReminder): void => {
    setEditingReminder(reminder);
    setModalMode('edit');
    setIsModalOpen(true);
  };

  // 新建提醒
  const handleCreateClick = (): void => {
    setEditingReminder(undefined);
    setModalMode('create');
    setIsModalOpen(true);
  };

  // 编辑提醒
  const handleEditClick = (reminder: CalendarReminder): void => {
    setEditingReminder(reminder);
    setModalMode('edit');
    setIsModalOpen(true);
  };

  // 删除提醒
  const handleDeleteClick = (id: number): void => {
    if (window.confirm('确定要删除这个提醒吗？')) {
      deleteMutation.mutate(id);
    }
  };

  // 切换状态
  const handleToggleStatus = (id: number, isDone: boolean): void => {
    toggleMutation.mutate({ id, isDone });
  };

  // 提交表单
  const handleSubmit = (data: CreateReminderRequest | UpdateReminderRequest): void => {
    if (modalMode === 'create') {
      createMutation.mutate(data as CreateReminderRequest, {
        onSuccess: () => {
          setIsModalOpen(false);
        },
      });
    } else if (editingReminder) {
      updateMutation.mutate(
        { id: editingReminder.id, data: data as UpdateReminderRequest },
        {
          onSuccess: () => {
            setIsModalOpen(false);
          },
        }
      );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">法律日历</h1>
          <p className="text-gray-600 mt-1">管理您的法律事务提醒</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：日历视图 */}
          <div className="lg:col-span-2 space-y-4">
            {/* 工具栏 */}
            <div className="bg-white rounded-lg shadow p-4 flex flex-wrap items-center justify-between gap-4">
              {/* 视图切换 */}
              <div className="flex bg-gray-100 rounded-lg p-1">
                {(['month', 'week', 'day'] as CalendarViewType[]).map((type) => (
                  <button
                    key={type}
                    onClick={() => setViewType(type)}
                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                      viewType === type
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {type === 'month' ? '月' : type === 'week' ? '周' : '日'}
                  </button>
                ))}
              </div>

              {/* 日期导航 */}
              <div className="flex items-center gap-2">
                <button
                  onClick={goToPrevious}
                  className="p-2 hover:bg-gray-100 rounded-lg text-gray-600"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <span className="text-lg font-semibold min-w-[150px] text-center">
                  {formatDateRange()}
                </span>
                <button
                  onClick={goToNext}
                  className="p-2 hover:bg-gray-100 rounded-lg text-gray-600"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
                <button
                  onClick={goToToday}
                  className="ml-2 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg font-medium"
                >
                  今天
                </button>
              </div>

              {/* 新建按钮 */}
              <button
                onClick={handleCreateClick}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                新建提醒
              </button>
            </div>

            {/* 日历 */}
            {isLoadingReminders ? (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-gray-600">加载中...</p>
              </div>
            ) : (
              <CalendarView
                viewType={viewType}
                currentDate={currentDate}
                reminders={reminders}
                onDateClick={handleDateClick}
                onEventClick={handleEventClick}
              />
            )}
          </div>

          {/* 右侧：提醒列表 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-4 sticky top-4">
              <ReminderList
                reminders={selectedDateReminders}
                onEdit={handleEditClick}
                onDelete={handleDeleteClick}
                onToggleStatus={handleToggleStatus}
                selectedDate={selectedDate}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 弹窗 */}
      <ReminderModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        reminder={editingReminder}
        mode={modalMode}
        onSubmit={handleSubmit}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  );
};