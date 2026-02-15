/**
 * 搜索筛选器组件
 */
/* eslint-disable react-refresh/only-export-components */

import React from 'react';

import type { SearchType } from '../types';

/** 筛选选项配置 */
export interface FilterOption {
  value: SearchType;
  label: string;
  icon?: React.ReactNode;
  count?: number;
}

export interface SearchFilterProps {
  /** 当前选中的类型 */
  activeType: SearchType;
  /** 筛选选项 */
  options: FilterOption[];
  /** 切换筛选的回调 */
  onChange: (type: SearchType) => void;
  /** 是否显示数量 */
  showCount?: boolean;
}

/**
 * 搜索筛选器组件
 */
export const SearchFilter: React.FC<SearchFilterProps> = ({
  activeType,
  options,
  onChange,
  showCount = true,
}) => {
  return (
    <div className="flex flex-wrap gap-2 py-3 border-b border-gray-200">
      {options.map((option) => {
        const isActive = activeType === option.value;
        
        return (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`
              flex items-center gap-1.5 px-4 py-2 rounded-full text-sm
              transition-all duration-200
              ${isActive 
                ? 'bg-blue-600 text-white shadow-md' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            {option.icon && (
              <span className={isActive ? 'text-white' : 'text-gray-500'}>
                {option.icon}
              </span>
            )}
            <span>{option.label}</span>
            {showCount && option.count !== undefined && option.count > 0 && (
              <span
                className={`
                  ml-1 px-1.5 py-0.5 text-xs rounded-full
                  ${isActive ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'}
                `}
              >
                {option.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};

/** 默认筛选选项 */
export const defaultFilterOptions: FilterOption[] = [
  { value: 'all', label: '全部' },
  { value: 'news', label: '资讯' },
  { value: 'post', label: '帖子' },
  { value: 'lawyer', label: '律师' },
  { value: 'lawfirm', label: '律所' },
  { value: 'knowledge', label: '知识' },
];

export default SearchFilter;