/**
 * 通知空状态组件
 */

import React from 'react';

export interface NotificationEmptyProps {
  /** 自定义标题 */
  title?: string;
  /** 自定义描述 */
  description?: string;
}

/**
 * 通知空状态组件
 */
export function NotificationEmpty({
  title = '暂无通知',
  description = '当有新消息时，会显示在这里',
}: NotificationEmptyProps): React.ReactElement {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      {/* 图标 */}
      <div className="w-16 h-16 mb-4 rounded-full bg-gray-100 flex items-center justify-center">
        <svg
          className="w-8 h-8 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
          />
        </svg>
      </div>

      {/* 标题 */}
      <h3 className="text-sm font-medium text-gray-900 mb-1">
        {title}
      </h3>

      {/* 描述 */}
      <p className="text-xs text-gray-500 max-w-[200px]">
        {description}
      </p>
    </div>
  );
}