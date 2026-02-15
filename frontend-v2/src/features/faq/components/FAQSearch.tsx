/**
 * FAQSearch - FAQ搜索组件
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Search, X } from 'lucide-react';

import type { FAQSearchProps } from '../types';

/**
 * FAQ搜索组件
 */
export const FAQSearch: React.FC<FAQSearchProps> = ({
  keyword = '',
  category = '',
  categories = [],
  onSearch,
  onCategoryChange,
  placeholder = '搜索常见问题...',
}) => {
  const [searchValue, setSearchValue] = useState(keyword);

  // 同步外部keyword变化
  useEffect(() => {
    setSearchValue(keyword);
  }, [keyword]);

  // 处理搜索提交
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    onSearch?.(searchValue);
  }, [searchValue, onSearch]);

  // 处理清除搜索
  const handleClear = useCallback(() => {
    setSearchValue('');
    onSearch?.('');
  }, [onSearch]);

  return (
    <div className="space-y-4">
      {/* 搜索输入框 */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          <Search className="absolute left-3 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder={placeholder}
            className="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-10 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            aria-label="搜索FAQ"
          />
          {searchValue && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              aria-label="清除搜索"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </form>

      {/* 分类筛选 */}
      {categories.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-gray-500">分类：</span>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onCategoryChange?.('')}
              className={`rounded-full px-3 py-1 text-sm transition-colors ${
                category === ''
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              全部
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => onCategoryChange?.(cat)}
                className={`rounded-full px-3 py-1 text-sm transition-colors ${
                  category === cat
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 当前筛选状态 */}
      {(keyword || category) && (
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>当前筛选：</span>
          {keyword && (
            <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-blue-700">
              关键词: {keyword}
              <button
                type="button"
                onClick={() => onSearch?.('')}
                className="rounded-full p-0.5 hover:bg-blue-100"
                aria-label="清除关键词筛选"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
          {category && (
            <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-green-700">
              分类: {category}
              <button
                type="button"
                onClick={() => onCategoryChange?.('')}
                className="rounded-full p-0.5 hover:bg-green-100"
                aria-label="清除分类筛选"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
};

FAQSearch.displayName = 'FAQSearch';