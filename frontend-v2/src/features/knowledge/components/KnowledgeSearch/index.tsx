/**
 * 知识搜索组件
 * 支持关键词搜索和高级筛选
 */

import { useState, useCallback, useEffect } from 'react';

interface KnowledgeSearchProps {
  onSearch: (keyword: string) => void;
  onClear?: () => void;
  placeholder?: string;
  initialValue?: string;
  loading?: boolean;
}

/**
 * 知识搜索组件
 */
export function KnowledgeSearch({
  onSearch,
  onClear,
  placeholder = '搜索法律知识...',
  initialValue = '',
  loading = false,
}: KnowledgeSearchProps): JSX.Element {
  const [keyword, setKeyword] = useState(initialValue);

  // 同步外部 initialValue 变化
  useEffect(() => {
    setKeyword(initialValue);
  }, [initialValue]);

  // 处理搜索提交
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    const trimmedKeyword = keyword.trim();
    onSearch(trimmedKeyword);
  }, [keyword, onSearch]);

  // 处理清空
  const handleClear = useCallback(() => {
    setKeyword('');
    onClear?.();
  }, [onClear]);

  // 处理输入变化
  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setKeyword(e.target.value);
  }, []);

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        {/* 搜索图标 */}
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg
            className="h-5 w-5 text-gray-400"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
              clipRule="evenodd"
            />
          </svg>
        </div>

        {/* 输入框 */}
        <input
          type="text"
          value={keyword}
          onChange={handleChange}
          className="block w-full pl-10 pr-20 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm transition-shadow"
          placeholder={placeholder}
          aria-label="搜索法律知识"
        />

        {/* 右侧操作按钮 */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-2">
          {/* 清空按钮 */}
          {keyword && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none"
              aria-label="清空搜索"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}

          {/* 搜索按钮 */}
          <button
            type="submit"
            disabled={loading}
            className="ml-2 px-4 py-1.5 bg-primary-600 text-white text-sm font-medium rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              '搜索'
            )}
          </button>
        </div>
      </div>

      {/* 搜索提示 */}
      <p className="mt-2 text-xs text-gray-500">
        支持搜索标题、内容、关键词
      </p>
    </form>
  );
}