/**
 * LawyerSchedulePicker - 律师时段选择器组件
 * 展示律师可用时段，支持日期选择
 */

import { useState, useMemo } from 'react';
import {
  Calendar,
  Clock,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';

import { Button } from '@/components/ui/Button';

import { useLawyerVideoSlots } from '../hooks/useVideoConsultation';
import type { VideoSlot } from '../types';

interface LawyerSchedulePickerProps {
  lawyerId: number;
  onSlotSelect: (slot: VideoSlot) => void;
  selectedSlot?: VideoSlot;
  minDate?: Date;
  maxDate?: Date;
}

// 生成未来7天的日期列表
function generateDateRange(minDate?: Date, maxDate?: Date): Date[] {
  const dates: Date[] = [];
  const start = minDate || new Date();
  start.setHours(0, 0, 0, 0);

  const end = maxDate || new Date(start);
  end.setDate(end.getDate() + 13); // 默认显示14天

  const current = new Date(start);
  while (current <= end) {
    dates.push(new Date(current));
    current.setDate(current.getDate() + 1);
  }

  return dates;
}

// 格式化日期显示
function formatDateDisplay(date: Date): { weekday: string; day: string; month: string } {
  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  return {
    weekday: `周${weekdays[date.getDay()]}`,
    day: String(date.getDate()).padStart(2, '0'),
    month: `${date.getMonth() + 1}月`,
  };
}

// 格式化时间
function formatTime(timeString: string): string {
  return timeString.slice(0, 5); // "09:00:00" -> "09:00"
}

// 检查日期是否为今天
function isToday(date: Date): boolean {
  const today = new Date();
  return (
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate()
  );
}

// 检查日期是否为明天
function isTomorrow(date: Date): boolean {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return (
    date.getFullYear() === tomorrow.getFullYear() &&
    date.getMonth() === tomorrow.getMonth() &&
    date.getDate() === tomorrow.getDate()
  );
}

export function LawyerSchedulePicker({
  lawyerId,
  onSlotSelect,
  selectedSlot,
  minDate,
  maxDate,
}: LawyerSchedulePickerProps): JSX.Element {
  const dates = useMemo(() => generateDateRange(minDate, maxDate), [minDate, maxDate]);
  const [selectedDate, setSelectedDate] = useState<Date>(dates[0]);
  const [scrollOffset, setScrollOffset] = useState(0);

  const dateStr = selectedDate.toISOString().split('T')[0];
  const { data: slotsData, isLoading, isError } = useLawyerVideoSlots(lawyerId, dateStr);

  const slots = useMemo(() => slotsData?.slots ?? [], [slotsData?.slots]);

  // 按时段分组（上午/下午/晚上）
  const groupedSlots = useMemo(() => {
    const morning: VideoSlot[] = [];
    const afternoon: VideoSlot[] = [];
    const evening: VideoSlot[] = [];

    slots.forEach((slot) => {
      const hour = parseInt(slot.startTime.split(':')[0], 10);
      if (hour < 12) {
        morning.push(slot);
      } else if (hour < 18) {
        afternoon.push(slot);
      } else {
        evening.push(slot);
      }
    });

    return { morning, afternoon, evening };
  }, [slots]);

  const handleDateSelect = (date: Date): void => {
    setSelectedDate(date);
  };

  const handleSlotClick = (slot: VideoSlot): void => {
    if (slot.availableCount > 0) {
      onSlotSelect(slot);
    }
  };

  const handleScrollLeft = (): void => {
    setScrollOffset((prev) => Math.max(0, prev - 1));
  };

  const handleScrollRight = (): void => {
    setScrollOffset((prev) => Math.min(dates.length - 5, prev + 1));
  };

  const visibleDates = dates.slice(scrollOffset, scrollOffset + 7);

  return (
    <div className="space-y-4">
      {/* 日期选择器 */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-gray-700 flex items-center">
            <Calendar className="w-4 h-4 mr-2" />
            选择日期
          </h4>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleScrollLeft}
              disabled={scrollOffset === 0}
              className="!p-1"
            >
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleScrollRight}
              disabled={scrollOffset >= dates.length - 7}
              className="!p-1"
            >
              <ChevronRight className="w-5 h-5" />
            </Button>
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-2">
          {visibleDates.map((date) => {
            const { weekday, day, month } = formatDateDisplay(date);
            const isSelected =
              selectedDate.toDateString() === date.toDateString();
            const isTodayDate = isToday(date);
            const isTomorrowDate = isTomorrow(date);

            return (
              <button
                key={date.toISOString()}
                onClick={() => handleDateSelect(date)}
                className={`
                  flex-shrink-0 w-16 py-3 px-2 rounded-lg text-center transition-all
                  ${isSelected
                    ? 'bg-primary-600 text-white shadow-md'
                    : 'bg-white border border-gray-200 hover:border-primary-300 hover:shadow-sm'
                  }
                `}
              >
                <div className={`text-xs ${isSelected ? 'text-primary-100' : 'text-gray-500'}`}>
                  {isTodayDate ? '今天' : isTomorrowDate ? '明天' : weekday}
                </div>
                <div className={`text-lg font-bold mt-1 ${isSelected ? 'text-white' : 'text-gray-900'}`}>
                  {day}
                </div>
                <div className={`text-xs ${isSelected ? 'text-primary-100' : 'text-gray-400'}`}>
                  {month}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 时段列表 */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="text-sm font-medium text-gray-700 flex items-center mb-4">
          <Clock className="w-4 h-4 mr-2" />
          选择时段
        </h4>

        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-primary-600 mr-2" />
            <span className="text-gray-500">加载时段信息...</span>
          </div>
        )}

        {isError && (
          <div className="flex items-center justify-center py-8 text-red-500">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span>加载时段失败，请稍后重试</span>
          </div>
        )}

        {!isLoading && !isError && slots.length === 0 && (
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">该日期暂无可用时段</p>
            <p className="text-sm text-gray-400 mt-1">请选择其他日期</p>
          </div>
        )}

        {!isLoading && !isError && slots.length > 0 && (
          <div className="space-y-4">
            {/* 上午时段 */}
            {groupedSlots.morning.length > 0 && (
              <SlotGroup
                title="上午"
                slots={groupedSlots.morning}
                selectedSlot={selectedSlot}
                onSlotClick={handleSlotClick}
              />
            )}

            {/* 下午时段 */}
            {groupedSlots.afternoon.length > 0 && (
              <SlotGroup
                title="下午"
                slots={groupedSlots.afternoon}
                selectedSlot={selectedSlot}
                onSlotClick={handleSlotClick}
              />
            )}

            {/* 晚上时段 */}
            {groupedSlots.evening.length > 0 && (
              <SlotGroup
                title="晚上"
                slots={groupedSlots.evening}
                selectedSlot={selectedSlot}
                onSlotClick={handleSlotClick}
              />
            )}
          </div>
        )}
      </div>

      {/* 已选时段信息 */}
      {selectedSlot && (
        <div className="bg-primary-50 rounded-lg p-4 border border-primary-200">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-primary-800">已选时段</p>
              <p className="text-primary-600 mt-1">
                {formatTime(selectedSlot.startTime)} - {formatTime(selectedSlot.endTime)}
              </p>
              <p className="text-sm text-primary-600 mt-1">
                咨询费用：¥{selectedSlot.consultationFee}
              </p>
            </div>
            <CheckCircle className="w-6 h-6 text-primary-600" />
          </div>
        </div>
      )}
    </div>
  );
}

// 时段分组组件
interface SlotGroupProps {
  title: string;
  slots: VideoSlot[];
  selectedSlot?: VideoSlot;
  onSlotClick: (slot: VideoSlot) => void;
}

function SlotGroup({ title, slots, selectedSlot, onSlotClick }: SlotGroupProps): JSX.Element {
  return (
    <div>
      <h5 className="text-xs text-gray-500 font-medium mb-2">{title}</h5>
      <div className="grid grid-cols-3 gap-2">
        {slots.map((slot) => {
          const isSelected = selectedSlot?.scheduleId === slot.scheduleId;
          const isAvailable = slot.availableCount > 0;

          return (
            <button
              key={slot.scheduleId}
              onClick={() => onSlotClick(slot)}
              disabled={!isAvailable}
              className={`
                py-2 px-3 rounded-lg text-sm font-medium transition-all
                ${isSelected
                  ? 'bg-primary-600 text-white shadow-md'
                  : isAvailable
                    ? 'bg-gray-50 border border-gray-200 text-gray-700 hover:border-primary-300 hover:bg-primary-50'
                    : 'bg-gray-100 border border-gray-200 text-gray-400 cursor-not-allowed'
                }
              `}
            >
              <div className="text-center">
                <div>{formatTime(slot.startTime)}</div>
                {isAvailable ? (
                  <div className="text-xs mt-0.5 opacity-75">
                    ¥{slot.consultationFee}
                  </div>
                ) : (
                  <div className="text-xs mt-0.5">已约满</div>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}