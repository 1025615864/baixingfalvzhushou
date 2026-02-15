/**
 * DateRangePicker - 日期范围选择器
 *
 * 支持预设范围（今天/本周/本月/自定义）和日期范围选择
 */

import React, { useState, useRef, useEffect } from 'react';

/**
 * 日期范围
 */
export interface DateRange {
  /** 开始日期 */
  startDate: Date | null;
  /** 结束日期 */
  endDate: Date | null;
}

/**
 * 预设范围类型
 */
export type PresetRange =
  | 'today'
  | 'yesterday'
  | 'thisWeek'
  | 'lastWeek'
  | 'thisMonth'
  | 'lastMonth'
  | 'thisYear'
  | 'custom';

/**
 * DateRangePicker 组件属性
 */
export interface DateRangePickerProps {
  /** 当前值 */
  value: DateRange;
  /** 值变化回调 */
  onChange: (range: DateRange, preset?: PresetRange) => void;
  /** 自定义类名 */
  className?: string;
  /** 占位符 */
  placeholder?: string;
  /** 是否显示预设范围 */
  showPresets?: boolean;
  /** 自定义预设范围 */
  customPresets?: Array<{
    key: PresetRange;
    label: string;
  }>;
  /** 最大日期 */
  maxDate?: Date;
  /** 最小日期 */
  minDate?: Date;
}

/**
 * 格式化日期为 YYYY-MM-DD
 */
function formatDate(date: Date | null | undefined): string {
  if (!date) return '';
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * 解析 YYYY-MM-DD 字符串为 Date
 */
function parseDate(dateString: string): Date | null {
  if (!dateString) return null;
  const date = new Date(dateString);
  return isNaN(date.getTime()) ? null : date;
}

/**
 * 获取预设范围的日期
 */
function getPresetRange(preset: PresetRange): DateRange {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  switch (preset) {
    case 'today':
      return { startDate: today, endDate: today };

    case 'yesterday': {
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      return { startDate: yesterday, endDate: yesterday };
    }

    case 'thisWeek': {
      const dayOfWeek = today.getDay();
      const startOfWeek = new Date(today);
      startOfWeek.setDate(today.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
      return { startDate: startOfWeek, endDate: today };
    }

    case 'lastWeek': {
      const dayOfWeek = today.getDay();
      const endOfLastWeek = new Date(today);
      endOfLastWeek.setDate(today.getDate() - (dayOfWeek === 0 ? 0 : dayOfWeek));
      const startOfLastWeek = new Date(endOfLastWeek);
      startOfLastWeek.setDate(endOfLastWeek.getDate() - 6);
      return { startDate: startOfLastWeek, endDate: endOfLastWeek };
    }

    case 'thisMonth': {
      const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      return { startDate: startOfMonth, endDate: today };
    }

    case 'lastMonth': {
      const endOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
      const startOfLastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      return { startDate: startOfLastMonth, endDate: endOfLastMonth };
    }

    case 'thisYear': {
      const startOfYear = new Date(today.getFullYear(), 0, 1);
      return { startDate: startOfYear, endDate: today };
    }

    default:
      return { startDate: null, endDate: null };
  }
}

/**
 * 日期范围选择器
 *
 * @example
 * ```tsx
 * const [range, setRange] = useState<DateRange>({ startDate: null, endDate: null });
 *
 * <DateRangePicker
 *   value={range}
 *   onChange={(range, preset) => {
 *     setRange(range);
 *     console.log('Preset:', preset);
 *   }}
 *   showPresets
 * />
 * ```
 */
export function DateRangePicker({
  value,
  onChange,
  className = '',
  placeholder = '选择日期范围',
  showPresets = true,
  customPresets,
  maxDate,
  minDate,
}: DateRangePickerProps): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [activePreset, setActivePreset] = useState<PresetRange | null>(null);
  const [startInput, setStartInput] = useState('');
  const [endInput, setEndInput] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 默认预设范围
  const defaultPresets: Array<{ key: PresetRange; label: string }> = [
    { key: 'today', label: '今天' },
    { key: 'thisWeek', label: '本周' },
    { key: 'thisMonth', label: '本月' },
    { key: 'custom', label: '自定义' },
  ];

  const presets = customPresets || defaultPresets;

  // 处理点击外部关闭
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 同步输入框值
  useEffect(() => {
    setStartInput(formatDate(value.startDate));
    setEndInput(formatDate(value.endDate));
  }, [value]);

  // 处理预设选择
  const handlePresetClick = (preset: PresetRange): void => {
    setActivePreset(preset);

    if (preset === 'custom') {
      return;
    }

    const range = getPresetRange(preset);
    onChange(range, preset);
    setIsOpen(false);
  };

  // 处理日期输入
  const handleStartInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const dateString = e.target.value;
    setStartInput(dateString);
    setActivePreset('custom');

    const date = parseDate(dateString);
    if (date && (!minDate || date >= minDate) && (!maxDate || date <= maxDate)) {
      onChange({ startDate: date, endDate: value.endDate }, 'custom');
    }
  };

  const handleEndInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const dateString = e.target.value;
    setEndInput(dateString);
    setActivePreset('custom');

    const date = parseDate(dateString);
    if (date && (!minDate || date >= minDate) && (!maxDate || date <= maxDate)) {
      onChange({ startDate: value.startDate, endDate: date }, 'custom');
    }
  };

  // 清除选择
  const handleClear = (e: React.MouseEvent): void => {
    e.stopPropagation();
    setActivePreset(null);
    onChange({ startDate: null, endDate: null });
    setStartInput('');
    setEndInput('');
  };

  // 确认选择
  const handleConfirm = (): void => {
    setIsOpen(false);
  };

  // 获取显示文本
  const displayText = React.useMemo(() => {
    if (!value.startDate && !value.endDate) return placeholder;

    if (activePreset && activePreset !== 'custom') {
      const preset = presets.find((p) => p.key === activePreset);
      if (preset) return preset.label;
    }

    const start = formatDate(value.startDate);
    const end = formatDate(value.endDate);

    if (start && end) {
      if (start === end) return start;
      return `${start} 至 ${end}`;
    }

    return start || end || placeholder;
  }, [value, activePreset, presets, placeholder]);

  const hasValue = value.startDate !== null || value.endDate !== null;

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      {/* 触发按钮 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center gap-2 px-3 py-2
          text-sm font-medium
          rounded-lg border
          transition-colors
          ${
            hasValue
              ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300'
              : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:border-gray-600'
          }
        `}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <span className={hasValue ? 'text-inherit' : 'text-gray-400 dark:text-gray-500'}>
          {displayText}
        </span>

        {/* 清除按钮 */}
        {hasValue && (
          <span
            onClick={handleClear}
            className="ml-1 p-0.5 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          >
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </span>
        )}

        {/* 下拉箭头 */}
        <svg
          className={`w-4 h-4 ml-1 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* 下拉面板 */}
      {isOpen && (
        <div
          className={`
            absolute z-50 mt-1 right-0
            w-[320px]
            bg-white dark:bg-gray-800
            rounded-lg shadow-lg border border-gray-200 dark:border-gray-700
            overflow-hidden
          `}
        >
          {/* 预设范围 */}
          {showPresets && (
            <div className="p-3 border-b border-gray-100 dark:border-gray-700">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">快速选择</div>
              <div className="flex flex-wrap gap-2">
                {presets.map((preset) => (
                  <button
                    key={preset.key}
                    onClick={() => handlePresetClick(preset.key)}
                    className={`
                      px-3 py-1.5 text-xs font-medium rounded-md
                      transition-colors
                      ${
                        activePreset === preset.key
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                      }
                    `}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 自定义日期选择 */}
          <div className="p-3">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">自定义范围</div>
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                  开始日期
                </label>
                <input
                  type="date"
                  value={startInput}
                  onChange={handleStartInputChange}
                  max={endInput || formatDate(maxDate)}
                  min={formatDate(minDate)}
                  className={`
                    w-full px-2 py-1.5
                    text-sm
                    rounded-md border border-gray-200
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                    dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100
                  `}
                />
              </div>
              <div className="pt-5">
                <span className="text-gray-400">至</span>
              </div>
              <div className="flex-1">
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                  结束日期
                </label>
                <input
                  type="date"
                  value={endInput}
                  onChange={handleEndInputChange}
                  min={startInput || formatDate(minDate)}
                  max={formatDate(maxDate)}
                  className={`
                    w-full px-2 py-1.5
                    text-sm
                    rounded-md border border-gray-200
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                    dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100
                  `}
                />
              </div>
            </div>
          </div>

          {/* 底部操作 */}
          <div className="flex items-center justify-end gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-100 dark:border-gray-700">
            <button
              onClick={handleClear}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
            >
              清除
            </button>
            <button
              onClick={handleConfirm}
              className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              确定
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DateRangePicker;