/**
 * 通知骨架屏组件
 */

import React from 'react';

export interface NotificationSkeletonProps {
  /** 骨架屏数量 */
  count?: number;
}

/**
 * 单个骨架屏项
 */
function SkeletonItem(): React.ReactElement {
  return (
    <div className="flex items-start gap-3 p-4 border-b border-gray-100 last:border-b-0">
      {/* 图标骨架 */}
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-200 animate-pulse" />
      
      {/* 内容骨架 */}
      <div className="flex-1 space-y-2">
        {/* 标题骨架 */}
        <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse" />
        {/* 内容骨架 */}
        <div className="h-3 bg-gray-200 rounded w-full animate-pulse" />
        <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse" />
        {/* 时间骨架 */}
        <div className="h-3 bg-gray-200 rounded w-24 animate-pulse" />
      </div>
    </div>
  );
}

/**
 * 通知骨架屏组件
 */
export function NotificationSkeleton({ count = 3 }: NotificationSkeletonProps): React.ReactElement {
  return (
    <div className="py-2">
      {Array.from({ length: count }).map((_, index) => (
        <SkeletonItem key={index} />
      ))}
    </div>
  );
}