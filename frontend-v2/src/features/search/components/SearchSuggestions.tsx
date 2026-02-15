/**
 * 搜索建议下拉组件
 */

import React from 'react';

export interface SearchSuggestionsProps {
  /** 建议列表 */
  suggestions: string[];
  /** 当前高亮索引 */
  highlightedIndex?: number;
  /** 点击建议的回调 */
  onSelect: (suggestion: string) => void;
  /** 是否显示 */
  visible?: boolean;
  /** 当前输入的关键词 */
  query?: string;
}

/**
 * 搜索建议组件
 */
export const SearchSuggestions: React.FC<SearchSuggestionsProps> = ({
  suggestions,
  highlightedIndex = -1,
  onSelect,
  visible = true,
  query = '',
}) => {
  if (!visible || suggestions.length === 0) {
    return null;
  }

  // 高亮匹配文本
  const highlightMatch = (text: string, query: string): React.ReactNode => {
    if (!query) return text;
    
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) => 
      part.toLowerCase() === query.toLowerCase() ? (
        <span key={index} className="text-blue-600 font-medium">{part}</span>
      ) : (
        part
      )
    );
  };

  return (
    <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-lg 
                    border border-gray-200 overflow-hidden z-50">
      <ul className="py-2">
        {suggestions.map((suggestion, index) => (
          <li
            key={index}
            onClick={() => onSelect(suggestion)}
            className={`
              flex items-center gap-3 px-4 py-2.5 cursor-pointer
              transition-colors duration-150
              ${index === highlightedIndex 
                ? 'bg-blue-50 text-blue-700' 
                : 'hover:bg-gray-50 text-gray-700'
              }
            `}
          >
            {/* 搜索图标 */}
            <svg
              className={`w-4 h-4 ${index === highlightedIndex ? 'text-blue-500' : 'text-gray-400'}`}
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
            
            {/* 建议文本 */}
            <span className="flex-1 text-sm">
              {highlightMatch(suggestion, query)}
            </span>

            {/* 箭头图标 */}
            {index === highlightedIndex && (
              <svg
                className="w-4 h-4 text-blue-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SearchSuggestions;