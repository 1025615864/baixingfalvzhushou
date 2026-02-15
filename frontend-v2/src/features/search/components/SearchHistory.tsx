/**
 * 搜索历史组件
 */

import React from 'react';

export interface SearchHistoryProps {
  /** 搜索历史列表 */
  history: string[];
  /** 点击历史项的回调 */
  onItemClick: (item: string) => void;
  /** 删除单个历史项的回调 */
  onItemDelete?: (item: string) => void;
  /** 清空历史的回调 */
  onClear?: () => void;
  /** 是否显示标题 */
  showTitle?: boolean;
  /** 最大显示数量 */
  maxItems?: number;
}

/**
 * 搜索历史组件
 */
export const SearchHistory: React.FC<SearchHistoryProps> = ({
  history,
  onItemClick,
  onItemDelete,
  onClear,
  showTitle = true,
  maxItems = 10,
}) => {
  const displayHistory = history.slice(0, maxItems);

  if (history.length === 0) {
    return null;
  }

  return (
    <div className="py-3">
      {showTitle && (
        <div className="flex items-center justify-between mb-3 px-4">
          <h3 className="text-sm font-medium text-gray-700">搜索历史</h3>
          {onClear && (
            <button
              onClick={onClear}
              className="text-xs text-gray-500 hover:text-red-500 transition-colors"
            >
              清空
            </button>
          )}
        </div>
      )}

      <div className="flex flex-wrap gap-2 px-4">
        {displayHistory.map((item, index) => (
          <div
            key={`${item}-${index}`}
            className="group flex items-center gap-1 px-3 py-1.5 
                     bg-gray-100 hover:bg-gray-200 rounded-full
                     transition-colors duration-200"
          >
            <button
              onClick={() => onItemClick(item)}
              className="text-sm text-gray-700 hover:text-gray-900"
            >
              {item}
            </button>
            {onItemDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onItemDelete(item);
                }}
                className="opacity-0 group-hover:opacity-100 text-gray-400 
                         hover:text-red-500 transition-opacity duration-200"
                aria-label={`删除 ${item}`}
              >
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchHistory;