/**
 * 搜索加载状态组件
 */

import React from 'react';

export interface SearchLoadingProps {
  /** 加载提示文本 */
  text?: string;
}

/**
 * 搜索加载状态
 */
export const SearchLoading: React.FC<SearchLoadingProps> = ({
  text = '搜索中...',
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="relative">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
        <div className="absolute inset-0 h-12 w-12 animate-pulse rounded-full bg-blue-100 opacity-20" />
      </div>
      <p className="mt-4 text-sm text-gray-500">{text}</p>
    </div>
  );
};

export default SearchLoading;