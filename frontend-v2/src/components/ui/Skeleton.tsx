/**
 * Skeleton - 通用骨架屏组件
 * 
 * 用于在数据加载时显示占位符，提供良好的加载体验
 */

import React from 'react';

/**
 * Skeleton组件属性
 */
export interface SkeletonProps {
  /** 自定义类名 */
  className?: string;
  /** 宽度，可以是数字(像素)或字符串(如'100%', '4rem') */
  width?: number | string;
  /** 高度，可以是数字(像素)或字符串 */
  height?: number | string;
  /** 圆角大小，可选 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'full' */
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  /** 是否显示动画 */
  animate?: boolean;
  /** 子元素，用于自定义骨架屏内容 */
  children?: React.ReactNode;
  /** 测试ID */
  'data-testid'?: string;
}

/**
 * 圆角样式映射
 */
const roundedMap = {
  none: 'rounded-none',
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  full: 'rounded-full',
};

/**
 * 通用骨架屏组件
 * 
 * @example
 * ```tsx
 * // 基本使用
 * <Skeleton width={200} height={24} />
 * 
 * // 圆形头像骨架
 * <Skeleton width={40} height={40} rounded="full" />
 * 
 * // 卡片骨架
 * <Skeleton className="w-full h-32" rounded="lg" />
 * 
 * // 自定义内容
 * <Skeleton className="p-4 space-y-3">
 *   <Skeleton width="100%" height={20} />
 *   <Skeleton width="80%" height={16} />
 * </Skeleton>
 * ```
 */
export function Skeleton({
  className = '',
  width,
  height,
  rounded = 'md',
  animate = true,
  children,
  'data-testid': dataTestId,
}: SkeletonProps): JSX.Element {
  // 处理宽度样式
  const widthStyle = width !== undefined
    ? typeof width === 'number' ? `${width}px` : width
    : undefined;

  // 处理高度样式
  const heightStyle = height !== undefined
    ? typeof height === 'number' ? `${height}px` : height
    : undefined;

  const style: React.CSSProperties = {
    width: widthStyle,
    height: heightStyle,
  };

  return (
    <div
      className={`
        bg-gray-200 dark:bg-gray-700
        ${roundedMap[rounded]}
        ${animate ? 'animate-pulse' : ''}
        ${className}
      `}
      style={style}
      data-testid={dataTestId}
    >
      {children}
    </div>
  );
}

/**
 * 文本骨架屏 - 专为文本内容优化
 */
export function TextSkeleton({
  lines = 1,
  className = '',
  lastLineWidth = '80%',
  'data-testid': dataTestId,
}: {
  lines?: number;
  className?: string;
  lastLineWidth?: string;
  'data-testid'?: string;
}): JSX.Element {
  return (
    <div className={`space-y-2 ${className}`} data-testid={dataTestId}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          width={index === lines - 1 ? lastLineWidth : '100%'}
          height={16}
          rounded="sm"
        />
      ))}
    </div>
  );
}

/**
 * 卡片骨架屏 - 用于卡片式布局
 */
export function CardSkeleton({
  hasImage = true,
  lines = 2,
  className = '',
  'data-testid': dataTestId,
}: {
  hasImage?: boolean;
  lines?: number;
  className?: string;
  'data-testid'?: string;
}): JSX.Element {
  return (
    <div className={`p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 ${className}`} data-testid={dataTestId}>
      {hasImage && (
        <Skeleton className="w-full h-40 mb-4" rounded="lg" />
      )}
      <Skeleton width="70%" height={20} className="mb-2" />
      <TextSkeleton lines={lines} lastLineWidth="60%" />
    </div>
  );
}

/**
 * 列表项骨架屏 - 用于列表布局
 */
export function ListItemSkeleton({
  avatar = true,
  lines = 2,
  className = '',
  'data-testid': dataTestId,
}: {
  avatar?: boolean;
  lines?: number;
  className?: string;
  'data-testid'?: string;
}): JSX.Element {
  return (
    <div className={`flex items-center gap-4 p-4 ${className}`} data-testid={dataTestId}>
      {avatar && (
        <Skeleton width={48} height={48} rounded="full" />
      )}
      <div className="flex-1">
        <Skeleton width="40%" height={18} className="mb-2" />
        {lines > 0 && <TextSkeleton lines={lines} lastLineWidth="70%" />}
      </div>
    </div>
  );
}

/**
 * 统计卡片骨架屏
 */
export function StatCardSkeleton({
  count = 4,
  className = '',
  'data-testid': dataTestId,
}: {
  count?: number;
  className?: string;
  'data-testid'?: string;
}): JSX.Element {
  return (
    <div className={`grid grid-cols-2 md:grid-cols-${Math.min(count, 4)} gap-4 ${className}`} data-testid={dataTestId}>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Skeleton width={60} height={14} className="mb-2" />
          <Skeleton width="50%" height={28} />
        </div>
      ))}
    </div>
  );
}

/**
 * 表格骨架屏
 */
export function TableSkeleton({
  rows = 5,
  columns = 4,
  className = '',
  'data-testid': dataTestId,
}: {
  rows?: number;
  columns?: number;
  className?: string;
  'data-testid'?: string;
}): JSX.Element {
  return (
    <div className={`w-full ${className}`} data-testid={dataTestId}>
      {/* 表头 */}
      <div className="flex gap-4 p-4 border-b border-gray-200 dark:border-gray-700">
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton
            key={`header-${index}`}
            width={`${100 / columns}%`}
            height={16}
            rounded="sm"
          />
        ))}
      </div>
      {/* 行 */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={`row-${rowIndex}`}
          className="flex gap-4 p-4 border-b border-gray-100 dark:border-gray-800"
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton
              key={`cell-${rowIndex}-${colIndex}`}
              width={`${90 / columns}%`}
              height={14}
              rounded="sm"
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export default Skeleton;