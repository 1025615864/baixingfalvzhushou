/**
 * 搜索无结果状态组件
 */

import React from 'react';

export interface SearchEmptyProps {
  /** 搜索关键词 */
  query?: string;
  /** 自定义提示文本 */
  message?: string;
  /** 是否显示建议 */
  showSuggestions?: boolean;
  /** 建议关键词列表 */
  suggestions?: string[];
  /** 点击建议的回调 */
  onSuggestionClick?: (suggestion: string) => void;
}

/**
 * 搜索无结果状态
 */
export const SearchEmpty: React.FC<SearchEmptyProps> = ({
  query,
  message,
  showSuggestions = true,
  suggestions = [],
  onSuggestionClick,
}) => {
  const defaultMessage = query 
    ? `未找到与"${query}"相关的内容` 
    : '请输入搜索关键词';

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {/* 图标 */}
      <div className="mb-6">
        <svg
          className="w-20 h-20 text-gray-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      {/* 提示文本 */}
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {message || defaultMessage}
      </h3>
      
      <p className="text-sm text-gray-500 text-center max-w-md mb-6">
        建议检查输入是否正确，或尝试使用其他关键词进行搜索
      </p>

      {/* 建议关键词 */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="w-full max-w-md">
          <p className="text-sm text-gray-600 mb-3 text-center">热门搜索：</p>
          <div className="flex flex-wrap justify-center gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => onSuggestionClick?.(suggestion)}
                className="px-4 py-2 text-sm text-blue-600 bg-blue-50 rounded-full 
                         hover:bg-blue-100 transition-colors duration-200"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 搜索技巧 */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg max-w-md w-full">
        <h4 className="text-sm font-medium text-gray-700 mb-2">搜索技巧：</h4>
        <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
          <li>使用更简短的关键词</li>
          <li>尝试使用同义词或相关词</li>
          <li>检查是否有错别字</li>
          <li>使用空格分隔多个关键词</li>
        </ul>
      </div>
    </div>
  );
};

export default SearchEmpty;