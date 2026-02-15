/**
 * FilterDropdown - 筛选下拉组件
 *
 * 支持多选、搜索、清除筛选等功能
 */

import React, { useState, useRef, useEffect, useMemo } from 'react';

/**
 * 筛选选项
 */
export interface FilterOption<T = string> {
  /** 选项值 */
  value: T;
  /** 选项标签 */
  label: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 图标（可选） */
  icon?: React.ReactNode;
}

/**
 * FilterDropdown 组件属性
 */
export interface FilterDropdownProps<T = string> {
  /** 筛选器标签 */
  label: string;
  /** 选项列表 */
  options: FilterOption<T>[];
  /** 当前选中值 */
  value: T[];
  /** 值变化回调 */
  onChange: (value: T[]) => void;
  /** 自定义类名 */
  className?: string;
  /** 占位符 */
  placeholder?: string;
  /** 是否允许多选 */
  multiple?: boolean;
  /** 是否显示搜索框 */
  searchable?: boolean;
  /** 是否显示清除按钮 */
  clearable?: boolean;
  /** 搜索占位符 */
  searchPlaceholder?: string;
  /** 最大选择数（多选时有效） */
  maxSelectCount?: number;
  /** 是否禁用 */
  disabled?: boolean;
  /** 自定义渲染选项 */
  renderOption?: (option: FilterOption<T>, isSelected: boolean) => React.ReactNode;
}

/**
 * 筛选下拉组件
 *
 * @example
 * ```tsx
 * // 单选
 * <FilterDropdown
 *   label="状态"
 *   options={[
 *     { value: 'active', label: '启用' },
 *     { value: 'inactive', label: '禁用' },
 *   ]}
 *   value={selectedStatus}
 *   onChange={setSelectedStatus}
 * />
 *
 * // 多选
 * <FilterDropdown
 *   label="类型"
 *   multiple
 *   searchable
 *   options={typeOptions}
 *   value={selectedTypes}
 *   onChange={setSelectedTypes}
 * />
 * ```
 */
export function FilterDropdown<T = string>({
  label,
  options,
  value,
  onChange,
  className = '',
  placeholder = '请选择',
  multiple = false,
  searchable = false,
  clearable = true,
  searchPlaceholder = '搜索...',
  maxSelectCount,
  disabled = false,
  renderOption,
}: FilterDropdownProps<T>): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // 过滤选项
  const filteredOptions = useMemo(() => {
    if (!searchQuery.trim()) return options;
    const query = searchQuery.toLowerCase();
    return options.filter(
      (option) =>
        option.label.toLowerCase().includes(query) ||
        String(option.value).toLowerCase().includes(query)
    );
  }, [options, searchQuery]);

  // 处理点击外部关闭
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 打开时聚焦搜索框
  useEffect(() => {
    if (isOpen && searchable) {
      setTimeout(() => searchInputRef.current?.focus(), 0);
    }
  }, [isOpen, searchable]);

  // 处理选项选择
  const handleSelect = (optionValue: T, optionDisabled?: boolean): void => {
    if (optionDisabled) return;

    if (multiple) {
      const currentIndex = value.indexOf(optionValue);
      let newValue: T[];

      if (currentIndex > -1) {
        // 取消选择
        newValue = value.filter((v) => v !== optionValue);
      } else {
        // 检查是否超过最大选择数
        if (maxSelectCount && value.length >= maxSelectCount) {
          return;
        }
        newValue = [...value, optionValue];
      }

      onChange(newValue);
    } else {
      onChange([optionValue]);
      setIsOpen(false);
      setSearchQuery('');
    }
  };

  // 清除所有选择
  const handleClear = (e: React.MouseEvent): void => {
    e.stopPropagation();
    onChange([]);
    setSearchQuery('');
  };

  // 清除单个选择
  const handleRemoveValue = (e: React.MouseEvent, valueToRemove: T): void => {
    e.stopPropagation();
    onChange(value.filter((v) => v !== valueToRemove));
  };

  // 全选/取消全选
  const handleToggleAll = (): void => {
    if (value.length === filteredOptions.length) {
      // 取消全选
      const filteredValues = filteredOptions.map((o) => o.value);
      onChange(value.filter((v) => !filteredValues.includes(v)));
    } else {
      // 全选
      const newValues = filteredOptions.filter((o) => !o.disabled).map((o) => o.value);
      const combined = Array.from(new Set([...value, ...newValues]));
      onChange(maxSelectCount ? combined.slice(0, maxSelectCount) : combined);
    }
  };

  // 获取显示文本
  const displayText = useMemo(() => {
    if (value.length === 0) return placeholder;
    if (value.length === 1) {
      const option = options.find((o) => o.value === value[0]);
      return option?.label || String(value[0]);
    }
    return `已选择 ${value.length} 项`;
  }, [value, options, placeholder]);

  // 判断选项是否选中
  const isSelected = (optionValue: T): boolean => value.includes(optionValue);

  // 是否有选中值
  const hasValue = value.length > 0;

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      {/* 触发按钮 */}
      <button
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full flex items-center justify-between
          px-3 py-2
          text-sm font-medium
          rounded-lg border
          transition-colors
          ${
            disabled
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed border-gray-200 dark:bg-gray-800 dark:border-gray-700'
              : hasValue
                ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300'
                : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:border-gray-600'
          }
        `}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="text-gray-500 dark:text-gray-400 shrink-0">{label}</span>
          <span className="truncate">
            {hasValue ? (
              <span className="text-inherit">{displayText}</span>
            ) : (
              <span className="text-gray-400 dark:text-gray-500">{placeholder}</span>
            )}
          </span>
        </div>

        <div className="flex items-center gap-1 shrink-0 ml-2">
          {/* 清除按钮 */}
          {clearable && hasValue && !disabled && (
            <span
              onClick={handleClear}
              className="p-0.5 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
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
            className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* 下拉面板 */}
      {isOpen && (
        <div
          className={`
            absolute z-50 mt-1 right-0
            min-w-[200px] max-w-[300px]
            bg-white dark:bg-gray-800
            rounded-lg shadow-lg border border-gray-200 dark:border-gray-700
            overflow-hidden
          `}
        >
          {/* 搜索框 */}
          {searchable && (
            <div className="p-2 border-b border-gray-100 dark:border-gray-700">
              <div className="relative">
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={searchPlaceholder}
                  className={`
                    w-full pl-8 pr-3 py-1.5
                    text-sm
                    rounded-md border border-gray-200
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                    dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100
                  `}
                />
                <svg
                  className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* 多选时的全选按钮 */}
          {multiple && filteredOptions.length > 0 && (
            <div className="px-2 py-1.5 border-b border-gray-100 dark:border-gray-700">
              <button
                onClick={handleToggleAll}
                className="w-full text-left px-2 py-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                {value.length === filteredOptions.length ? '取消全选' : '全选'}
              </button>
            </div>
          )}

          {/* 选项列表 */}
          <div className="max-h-[240px] overflow-y-auto">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                暂无匹配选项
              </div>
            ) : (
              filteredOptions.map((option) => {
                const selected = isSelected(option.value);
                const optionContent = renderOption ? (
                  renderOption(option, selected)
                ) : (
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {multiple && (
                      <div
                        className={`
                          w-4 h-4 rounded border flex items-center justify-center
                          ${selected
                            ? 'bg-blue-600 border-blue-600 text-white'
                            : 'border-gray-300 dark:border-gray-600'
                          }
                        `}
                      >
                        {selected && (
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </div>
                    )}
                    {option.icon && <span className="shrink-0">{option.icon}</span>}
                    <span className="truncate">{option.label}</span>
                  </div>
                );

                return (
                  <button
                    key={String(option.value)}
                    onClick={() => handleSelect(option.value, option.disabled)}
                    disabled={option.disabled}
                    className={`
                      w-full flex items-center gap-2
                      px-3 py-2
                      text-sm
                      transition-colors
                      ${selected
                        ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                        : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700'
                      }
                      ${option.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    {optionContent}
                  </button>
                );
              })
            )}
          </div>

          {/* 底部选中项显示（多选时） */}
          {multiple && hasValue && (
            <div className="px-3 py-2 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-100 dark:border-gray-700">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">已选择:</div>
              <div className="flex flex-wrap gap-1">
                {value.map((v) => {
                  const option = options.find((o) => o.value === v);
                  return (
                    <span
                      key={String(v)}
                      className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full dark:bg-blue-900/50 dark:text-blue-300"
                    >
                      {option?.label || String(v)}
                      <button
                        onClick={(e) => handleRemoveValue(e, v)}
                        className="hover:text-blue-900 dark:hover:text-blue-100"
                      >
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </button>
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default FilterDropdown;