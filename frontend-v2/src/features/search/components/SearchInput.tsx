/**
 * 搜索输入框组件（带自动完成）
 */

import React, { useState, useCallback, useEffect, useRef, KeyboardEvent } from 'react';

import { SearchSuggestions } from './SearchSuggestions';

export interface SearchInputProps {
  /** 输入值 */
  value: string;
  /** 值变化回调 */
  onChange: (value: string) => void;
  /** 搜索回调 */
  onSearch: (value: string) => void;
  /** 搜索建议 */
  suggestions?: string[];
  /** 占位符文本 */
  placeholder?: string;
  /** 是否自动聚焦 */
  autoFocus?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否显示加载状态 */
  loading?: boolean;
  /** 是否显示清除按钮 */
  showClear?: boolean;
  /** 自定义样式类名 */
  className?: string;
}

/**
 * 搜索输入框组件
 */
export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  onSearch,
  suggestions = [],
  placeholder = '搜索帖子、新闻、律师、法律知识...',
  autoFocus = false,
  disabled = false,
  loading = false,
  showClear = true,
  className = '',
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 是否显示建议下拉框
  const showSuggestions = isFocused && suggestions.length > 0 && value.length > 0;

  // 处理输入变化
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    setHighlightedIndex(-1);
  }, [onChange]);

  // 处理搜索提交
  const handleSubmit = useCallback(() => {
    if (value.trim()) {
      onSearch(value.trim());
      setIsFocused(false);
    }
  }, [value, onSearch]);

  // 处理清除
  const handleClear = useCallback(() => {
    onChange('');
    setHighlightedIndex(-1);
    inputRef.current?.focus();
  }, [onChange]);

  // 处理建议选中
  const handleSuggestionSelect = useCallback((suggestion: string) => {
    onChange(suggestion);
    onSearch(suggestion);
    setIsFocused(false);
  }, [onChange, onSearch]);

  // 键盘事件处理
  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLInputElement>) => {
    switch (e.key) {
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && suggestions[highlightedIndex]) {
          handleSuggestionSelect(suggestions[highlightedIndex]);
        } else {
          handleSubmit();
        }
        break;

      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex((prev) => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;

      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;

      case 'Escape':
        e.preventDefault();
        setIsFocused(false);
        setHighlightedIndex(-1);
        break;

      default:
        break;
    }
  }, [highlightedIndex, suggestions, handleSuggestionSelect, handleSubmit]);

  // 点击外部关闭建议
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 自动聚焦
  useEffect(() => {
    if (autoFocus) {
      inputRef.current?.focus();
    }
  }, [autoFocus]);

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* 输入框容器 */}
      <div
        className={`
          flex items-center gap-2 px-4 py-3 
          bg-white border rounded-lg shadow-sm
          transition-all duration-200
          ${isFocused 
            ? 'border-blue-500 ring-2 ring-blue-100' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}
        `}
      >
        {/* 搜索图标 */}
        <svg
          className="w-5 h-5 text-gray-400 flex-shrink-0"
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

        {/* 输入框 */}
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={handleInputChange}
          onFocus={() => setIsFocused(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="
            flex-1 bg-transparent border-none outline-none
            text-gray-900 placeholder-gray-400
            text-base
          "
          aria-label="搜索"
          aria-autocomplete="list"
          aria-controls="search-suggestions"
          aria-activedescendant={
            highlightedIndex >= 0 ? `suggestion-${highlightedIndex}` : undefined
          }
        />

        {/* 加载状态 */}
        {loading && (
          <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
        )}

        {/* 清除按钮 */}
        {showClear && value && !loading && (
          <button
            onClick={handleClear}
            className="
              p-1 rounded-full text-gray-400 hover:text-gray-600 
              hover:bg-gray-100 transition-colors duration-200
            "
            aria-label="清除搜索"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}

        {/* 搜索按钮 */}
        <button
          onClick={handleSubmit}
          disabled={!value.trim() || disabled}
          className={`
            px-4 py-1.5 rounded-md text-sm font-medium
            transition-colors duration-200
            ${value.trim() && !disabled
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }
          `}
        >
          搜索
        </button>
      </div>

      {/* 搜索建议下拉框 */}
      <SearchSuggestions
        suggestions={suggestions}
        highlightedIndex={highlightedIndex}
        onSelect={handleSuggestionSelect}
        visible={showSuggestions}
        query={value}
      />
    </div>
  );
};

export default SearchInput;