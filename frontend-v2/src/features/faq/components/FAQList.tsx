/**
 * FAQList - FAQ列表组件
 */

import React from 'react';
import { ChevronRight, Eye, CircleHelp } from 'lucide-react';

import type { FAQListProps, FAQItem } from '../types';

/**
 * 格式化浏览次数
 */
function formatViewCount(count: number): string {
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万`;
  }
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`;
  }
  return count.toString();
}

/**
 * 获取分类颜色
 */
function getCategoryColor(category: string | null): string {
  if (!category) return 'bg-gray-100 text-gray-700';
  
  const colors: Record<string, string> = {
    '账户': 'bg-blue-100 text-blue-700',
    '支付': 'bg-green-100 text-green-700',
    '咨询': 'bg-purple-100 text-purple-700',
    '合同': 'bg-orange-100 text-orange-700',
    '投诉': 'bg-red-100 text-red-700',
    '其他': 'bg-gray-100 text-gray-700',
  };
  
  return colors[category] || 'bg-gray-100 text-gray-700';
}

/**
 * FAQ列表项组件
 */
interface FAQListItemProps {
  item: FAQItem;
  onClick?: (item: FAQItem) => void;
}

const FAQListItem: React.FC<FAQListItemProps> = ({ item, onClick }) => {
  const handleClick = React.useCallback(() => {
    onClick?.(item);
  }, [item, onClick]);

  return (
    <div
      onClick={handleClick}
      className="group flex cursor-pointer items-start gap-3 rounded-lg border border-gray-200 bg-white p-4 transition-all hover:border-blue-300 hover:shadow-sm"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      <div className="mt-0.5 flex-shrink-0">
        <CircleHelp className="h-5 w-5 text-blue-500" />
      </div>
      
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-base font-medium text-gray-900 group-hover:text-blue-600">
            {item.question}
          </h3>
          <ChevronRight className="h-5 w-5 flex-shrink-0 text-gray-400 transition-transform group-hover:translate-x-1 group-hover:text-blue-500" />
        </div>
        
        <div className="mt-2 flex items-center gap-3 text-sm text-gray-500">
          {item.category && (
            <span className={`rounded-full px-2 py-0.5 text-xs ${getCategoryColor(item.category)}`}>
              {item.category}
            </span>
          )}
          
          <span className="flex items-center gap-1">
            <Eye className="h-3.5 w-3.5" />
            {formatViewCount(item.viewCount)}
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * FAQ列表组件
 */
export const FAQList: React.FC<FAQListProps> = ({
  items,
  loading = false,
  onItemClick,
  emptyText = '暂无相关FAQ',
}) => {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, index) => (
          <div
            key={index}
            className="rounded-lg border border-gray-200 bg-white p-4"
          >
            <div className="flex items-start gap-3">
              <div className="h-5 w-5 flex-shrink-0 animate-pulse rounded bg-gray-200" />
              <div className="flex-1 space-y-2">
                <div className="h-5 w-3/4 animate-pulse rounded bg-gray-200" />
                <div className="h-4 w-1/3 animate-pulse rounded bg-gray-200" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 bg-gray-50 py-12">
        <CircleHelp className="h-12 w-12 text-gray-300" />
        <p className="mt-3 text-gray-500">{emptyText}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <FAQListItem
          key={item.id}
          item={item}
          onClick={onItemClick}
        />
      ))}
    </div>
  );
};

FAQList.displayName = 'FAQList';