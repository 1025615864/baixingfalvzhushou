/**
 * CalendarView 组件
 * 日历视图（月/周/日）
 */

import { useMemo, useState } from 'react';

import type { CalendarViewProps, CalendarEvent } from '../types';

const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六'];

export const CalendarView: React.FC<CalendarViewProps> = ({
  viewType,
  currentDate,
  reminders,
  onDateClick,
  onEventClick,
}) => {
  const [hoveredDate, setHoveredDate] = useState<Date | null>(null);

  // 将提醒转换为日历事件
  const events = useMemo<CalendarEvent[]>(() => {
    return reminders.map((reminder) => ({
      id: reminder.id,
      title: reminder.title,
      date: reminder.dueAt?.split('T')[0] ?? '',
      isDone: reminder.isDone,
      reminder,
    }));
  }, [reminders]);

  // 获取某日期的事件
  const getEventsForDate = (dateStr: string): CalendarEvent[] => {
    return events.filter((e) => e.date === dateStr);
  };

  // 月视图
  const renderMonthView = (): JSX.Element => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    // 获取当月第一天和最后一天
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    // 获取第一天是星期几（0=周日）
    const startDayOfWeek = firstDay.getDay();

    // 获取当月天数
    const daysInMonth = lastDay.getDate();

    // 生成日历网格
    const days: JSX.Element[] = [];

    // 空白格子（上个月）
    for (let i = 0; i < startDayOfWeek; i++) {
      days.push(
        <div
          key={`empty-${i}`}
          className="h-24 border border-gray-100 bg-gray-50"
        />
      );
    }

    // 当月日期
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateStr = date.toISOString().split('T')[0];
      const dayEvents = getEventsForDate(dateStr);
      const isToday = new Date().toDateString() === date.toDateString();
      const isHovered = hoveredDate?.toDateString() === date.toDateString();

      days.push(
        <div
          key={day}
          className={`h-24 border border-gray-200 p-1 cursor-pointer transition-colors ${
            isToday ? 'bg-blue-50 border-blue-300' : 'hover:bg-gray-50'
          } ${isHovered ? 'bg-gray-100' : ''}`}
          onClick={() => onDateClick(date)}
          onMouseEnter={() => setHoveredDate(date)}
          onMouseLeave={() => setHoveredDate(null)}
        >
          <div className="flex justify-between items-start">
            <span
              className={`text-sm font-medium ${
                isToday ? 'text-blue-600' : 'text-gray-700'
              }`}
            >
              {day}
            </span>
            {dayEvents.length > 0 && (
              <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full">
                {dayEvents.length}
              </span>
            )}
          </div>
          <div className="mt-1 space-y-0.5 overflow-hidden">
            {dayEvents.slice(0, 3).map((event) => (
              <div
                key={event.id}
                onClick={(e) => {
                  e.stopPropagation();
                  onEventClick(event.reminder);
                }}
                className={`text-xs px-1.5 py-0.5 rounded truncate cursor-pointer ${
                  event.isDone
                    ? 'bg-gray-100 text-gray-500 line-through'
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }`}
              >
                {event.title}
              </div>
            ))}
            {dayEvents.length > 3 && (
              <div className="text-xs text-gray-400 px-1.5">
                +{dayEvents.length - 3} 更多
              </div>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-7 gap-0">
        {/* 星期标题 */}
        {WEEKDAYS.map((day) => (
          <div
            key={day}
            className="bg-gray-100 border border-gray-200 py-2 text-center text-sm font-medium text-gray-700"
          >
            {day}
          </div>
        ))}
        {/* 日期格子 */}
        {days}
      </div>
    );
  };

  // 周视图
  const renderWeekView = (): JSX.Element => {
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());

    const weekDays: JSX.Element[] = [];

    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];
      const dayEvents = getEventsForDate(dateStr);
      const isToday = new Date().toDateString() === date.toDateString();

      weekDays.push(
        <div
          key={i}
          className={`flex-1 border border-gray-200 min-h-[300px] cursor-pointer hover:bg-gray-50 ${
            isToday ? 'bg-blue-50' : ''
          }`}
          onClick={() => onDateClick(date)}
        >
          <div
            className={`p-2 text-center border-b border-gray-200 ${
              isToday ? 'bg-blue-100' : 'bg-gray-50'
            }`}
          >
            <div className="text-xs text-gray-500">{WEEKDAYS[i]}</div>
            <div
              className={`text-lg font-semibold ${
                isToday ? 'text-blue-600' : 'text-gray-700'
              }`}
            >
              {date.getDate()}
            </div>
          </div>
          <div className="p-2 space-y-1">
            {dayEvents.map((event) => (
              <div
                key={event.id}
                onClick={(e) => {
                  e.stopPropagation();
                  onEventClick(event.reminder);
                }}
                className={`text-sm px-2 py-1 rounded cursor-pointer ${
                  event.isDone
                    ? 'bg-gray-100 text-gray-500 line-through'
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }`}
              >
                {event.title}
              </div>
            ))}
          </div>
        </div>
      );
    }

    return <div className="flex">{weekDays}</div>;
  };

  // 日视图
  const renderDayView = (): JSX.Element => {
    const dateStr = currentDate.toISOString().split('T')[0];
    const dayEvents = getEventsForDate(dateStr);
    const isToday = new Date().toDateString() === currentDate.toDateString();

    // 按小时分组
    const hours: JSX.Element[] = [];
    for (let hour = 0; hour < 24; hour++) {
      const hourEvents = dayEvents.filter((e) => {
        const eventHour = new Date(e.reminder.dueAt).getHours();
        return eventHour === hour;
      });

      hours.push(
        <div
          key={hour}
          className="flex border-b border-gray-100 min-h-[60px]"
          onClick={() => {
            const clickedDate = new Date(currentDate);
            clickedDate.setHours(hour);
            onDateClick(clickedDate);
          }}
        >
          <div className="w-16 py-2 px-2 text-xs text-gray-500 border-r border-gray-200 bg-gray-50 text-right">
            {hour.toString().padStart(2, '0')}:00
          </div>
          <div className="flex-1 p-1 space-y-1">
            {hourEvents.map((event) => (
              <div
                key={event.id}
                onClick={(e) => {
                  e.stopPropagation();
                  onEventClick(event.reminder);
                }}
                className={`text-sm px-3 py-2 rounded cursor-pointer ${
                  event.isDone
                    ? 'bg-gray-100 text-gray-500 line-through'
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }`}
              >
                <span className="font-medium">
                  {new Date(event.reminder.dueAt).toLocaleTimeString('zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
                <span className="ml-2\">{event.title}</span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    return (
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div
          className={`p-3 border-b border-gray-200 ${
            isToday ? 'bg-blue-100' : 'bg-gray-100'
          }`}
        >
          <div className="text-lg font-semibold">
            {currentDate.toLocaleDateString('zh-CN', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              weekday: 'long',
            })}
          </div>
        </div>
        <div className="max-h-[500px] overflow-y-auto\">{hours}</div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {viewType === 'month' && renderMonthView()}
      {viewType === 'week' && renderWeekView()}
      {viewType === 'day' && renderDayView()}
    </div>
  );
};