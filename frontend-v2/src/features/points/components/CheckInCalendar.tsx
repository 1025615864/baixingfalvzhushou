/**
 * CheckInCalendar - 签到日历组件
 *
 * 月度日历展示，标记已签到日期，显示今日高亮，支持点击日期查看详情
 */

import { useMemo } from 'react';

import { Skeleton } from '../../../components/ui/Skeleton';

/**
 * CheckInCalendar Props 接口
 */
export interface CheckInCalendarProps {
  /** 年份 */
  year: number;
  /** 月份 (0-11) */
  month: number;
  /** 已签到的日期数组 */
  signedDates: number[];
  /** 日期点击回调 */
  onDateClick?: (date: number) => void;
  /** 签到按钮点击回调 */
  onCheckIn: () => void;
  /** 是否正在签到中 */
  isCheckingIn: boolean;
  /** 今日是否已签到 */
  hasCheckedInToday: boolean;
  /** 是否加载中 */
  isLoading?: boolean;
  /** 连续签到天数 */
  continuousDays?: number;
}

/**
 * 星期标题配置
 */
const WEEK_DAYS = ['日', '一', '二', '三', '四', '五', '六'];

/**
 * 日历日期项数据
 */
interface CalendarDayItem {
  /** 日期 (0 表示空白填充) */
  date: number;
  /** 是否为今日 */
  isToday: boolean;
  /** 是否已签到 */
  isSigned: boolean;
  /** 是否可点击 */
  isClickable: boolean;
}

/**
 * 签到日历组件
 *
 * @param props - 组件属性
 * @returns JSX.Element
 */
export function CheckInCalendar({
  year,
  month,
  signedDates,
  onDateClick,
  onCheckIn,
  isCheckingIn,
  hasCheckedInToday,
  isLoading = false,
  continuousDays = 0,
}: CheckInCalendarProps): JSX.Element {
  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth();
  const currentDate = today.getDate();

  // 判断是否为当前显示的月份
  const isCurrentMonth = year === currentYear && month === currentMonth;

  // 获取当月天数
  const daysInMonth = useMemo(() => {
    return new Date(year, month + 1, 0).getDate();
  }, [year, month]);

  // 获取当月第一天是星期几
  const firstDayOfMonth = useMemo(() => {
    return new Date(year, month, 1).getDay();
  }, [year, month]);

  // 生成日历数据
  const calendarDays = useMemo<CalendarDayItem[]>(() => {
    const days: CalendarDayItem[] = [];

    // 填充月初空白
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push({
        date: 0,
        isToday: false,
        isSigned: false,
        isClickable: false,
      });
    }

    // 填充日期
    for (let i = 1; i <= daysInMonth; i++) {
      const isToday = isCurrentMonth && i === currentDate;
      const isSigned = signedDates.includes(i);
      // 只能点击今天或已签到的日期查看详情
      const isClickable = i <= currentDate || !isCurrentMonth;

      days.push({
        date: i,
        isToday,
        isSigned,
        isClickable,
      });
    }

    return days;
  }, [daysInMonth, firstDayOfMonth, currentDate, signedDates, isCurrentMonth]);

  // 获取本月签到次数
  const signedCount = useMemo(() => {
    return signedDates.length;
  }, [signedDates]);

  // 处理日期点击
  const handleDateClick = (date: number): void => {
    if (date > 0 && onDateClick) {
      onDateClick(date);
    }
  };

  // 处理签到按钮点击
  const handleCheckIn = (): void => {
    if (!hasCheckedInToday && !isCheckingIn) {
      onCheckIn();
    }
  };

  // 获取月份名称
  const monthName = useMemo(() => {
    return `${year}年${month + 1}月`;
  }, [year, month]);

  // 加载状态
  if (isLoading) {
    return <CheckInCalendarSkeleton />;
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4 sm:p-6 transition-colors">
      {/* 日历头部 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {monthName}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            本月已签到{' '}
            <span className="text-orange-600 dark:text-orange-400 font-semibold">
              {signedCount}
            </span>{' '}
            天
            {continuousDays > 0 && (
              <span className="ml-2 text-green-600 dark:text-green-400">
                连续 {continuousDays} 天
              </span>
            )}
          </p>
        </div>
        <button
          onClick={handleCheckIn}
          disabled={hasCheckedInToday || isCheckingIn}
          className={`w-full sm:w-auto px-6 py-2.5 rounded-lg font-medium transition-all duration-200 ${
            hasCheckedInToday
              ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-orange-500 to-yellow-500 text-white hover:from-orange-600 hover:to-yellow-600 shadow-lg shadow-orange-200 dark:shadow-orange-900/30 active:scale-95'
          }`}
        >
          {isCheckingIn
            ? '签到中...'
            : hasCheckedInToday
              ? '今日已签到'
              : '立即签到'}
        </button>
      </div>

      {/* 星期标题 */}
      <div className="grid grid-cols-7 gap-1 sm:gap-2 mb-2">
        {WEEK_DAYS.map((day) => (
          <div
            key={day}
            className="text-center text-xs sm:text-sm font-medium text-gray-500 dark:text-gray-400 py-2"
          >
            {day}
          </div>
        ))}
      </div>

      {/* 日期网格 */}
      <div className="grid grid-cols-7 gap-1 sm:gap-2">
        {calendarDays.map((day, index) => (
          <div
            key={index}
            onClick={() => day.isClickable && handleDateClick(day.date)}
            className={`
              aspect-square flex flex-col items-center justify-center rounded-lg text-xs sm:text-sm
              transition-all duration-200
              ${day.date === 0
                ? 'invisible'
                : day.isToday
                  ? 'bg-orange-100 dark:bg-orange-900/30 border-2 border-orange-400 dark:border-orange-500 text-orange-700 dark:text-orange-300'
                  : day.isSigned
                    ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                    : day.isClickable
                      ? 'bg-gray-50 dark:bg-gray-700/50 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer'
                      : 'bg-gray-50 dark:bg-gray-800 text-gray-400 dark:text-gray-600 cursor-not-allowed'
              }
            `}
          >
            {day.date > 0 && (
              <>
                <span className="font-medium">{day.date}</span>
                {day.isSigned && (
                  <svg
                    className="w-3 h-3 sm:w-4 sm:h-4 mt-0.5 text-green-500 dark:text-green-400"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </>
            )}
          </div>
        ))}
      </div>

      {/* 图例说明 */}
      <div className="mt-6 flex flex-wrap items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-4 rounded bg-orange-100 dark:bg-orange-900/30 border-2 border-orange-400 dark:border-orange-500" />
          <span>今天</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-4 rounded bg-green-50 dark:bg-green-900/20 flex items-center justify-center">
            <svg
              className="w-3 h-3 text-green-500 dark:text-green-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <span>已签到</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-4 rounded bg-gray-50 dark:bg-gray-700/50" />
          <span>未签到</span>
        </div>
      </div>
    </div>
  );
}

/**
 * 签到日历骨架屏组件
 *
 * @returns JSX.Element
 */
export function CheckInCalendarSkeleton(): JSX.Element {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4 sm:p-6">
      {/* 头部骨架 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div className="space-y-2">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-10 w-full sm:w-28 rounded-lg" />
      </div>

      {/* 星期标题骨架 */}
      <div className="grid grid-cols-7 gap-1 sm:gap-2 mb-2">
        {WEEK_DAYS.map((day) => (
          <div
            key={day}
            className="text-center text-xs sm:text-sm font-medium text-gray-400 dark:text-gray-600 py-2"
          >
            {day}
          </div>
        ))}
      </div>

      {/* 日期网格骨架 */}
      <div className="grid grid-cols-7 gap-1 sm:gap-2">
        {Array.from({ length: 35 }).map((_, index) => (
          <Skeleton
            key={index}
            className="aspect-square rounded-lg"
          />
        ))}
      </div>

      {/* 图例骨架 */}
      <div className="mt-6 flex flex-wrap items-center gap-4">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-16" />
      </div>
    </div>
  );
}

export default CheckInCalendar;