/**
 * EmptyState - 空状态展示组件
 * 
 * 用于在数据为空时显示友好的提示信息
 */

import React from 'react';

/**
 * 预设图标类型
 */
export type EmptyIconType = 
  | 'default'
  | 'search'
  | 'box'
  | 'document'
  | 'message'
  | 'notification'
  | 'cart'
  | 'network'
  | 'error'
  | 'custom';

/**
 * EmptyState组件属性
 */
export interface EmptyStateProps {
  /** 标题 */
  title?: string;
  /** 描述文本 */
  description?: string;
  /** 图标类型 */
  icon?: EmptyIconType;
  /** 自定义图标 */
  customIcon?: React.ReactNode;
  /** 操作按钮 */
  action?: React.ReactNode;
  /** 自定义类名 */
  className?: string;
  /** 尺寸：sm | md | lg */
  size?: 'sm' | 'md' | 'lg';
  /** 是否紧凑模式（减少内边距） */
  compact?: boolean;
  /** 测试ID */
  'data-testid'?: string;
}

/**
 * 图标尺寸映射
 */
const iconSizeMap = {
  sm: 'w-10 h-10',
  md: 'w-16 h-16',
  lg: 'w-24 h-24',
};

/**
 * 容器内边距映射
 */
const paddingMap = {
  sm: 'p-4',
  md: 'p-8',
  lg: 'p-12',
};

/**
 * 标题尺寸映射
 */
const titleSizeMap = {
  sm: 'text-base',
  md: 'text-lg',
  lg: 'text-xl',
};

/**
 * 描述尺寸映射
 */
const descSizeMap = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
};

/**
 * 获取预设图标
 */
function getPresetIcon(type: EmptyIconType): React.ReactNode {
  const icons: Record<string, React.ReactNode> = {
    default: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
        />
      </svg>
    ),
    search: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
    ),
    box: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
        />
      </svg>
    ),
    document: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
    ),
    message: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
    ),
    notification: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
    ),
    cart: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
        />
      </svg>
    ),
    network: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
    error: (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  };

  return icons[type] || icons.default;
}

/**
 * 空状态展示组件
 * 
 * @example
 * ```tsx
 * // 基本使用
 * <EmptyState title="暂无数据" description="数据加载中..." />
 * 
 * // 带操作按钮
 * <EmptyState
 *   title="购物车为空"
 *   description="快去选购心仪的商品吧"
 *   icon="cart"
 *   action={<Button>去购物</Button>}
 * />
 * 
 * // 搜索为空
 * <EmptyState
 *   title="未找到相关结果"
 *   description="请尝试其他关键词"
 *   icon="search"
 *   size="sm"
 * />
 * ```
 */
export function EmptyState({
  title = '暂无数据',
  description,
  icon = 'default',
  customIcon,
  action,
  className = '',
  size = 'md',
  compact = false,
  'data-testid': dataTestId,
}: EmptyStateProps): JSX.Element {
  const iconContent = customIcon || getPresetIcon(icon);

  return (
    <div
      className={`
        flex flex-col items-center justify-center text-center
        ${compact ? 'p-4' : paddingMap[size]}
        ${className}
      `}
      data-testid={dataTestId}
    >
      {/* 图标 */}
      <div
        className={`
          ${iconSizeMap[size]}
          text-gray-300 dark:text-gray-600 mb-4
        `}
      >
        {iconContent}
      </div>

      {/* 标题 */}
      <h3
        className={`
          ${titleSizeMap[size]}
          font-medium text-gray-900 dark:text-gray-100
          ${compact ? 'mb-1' : 'mb-2'}
        `}
      >
        {title}
      </h3>

      {/* 描述 */}
      {description && (
        <p
          className={`
            ${descSizeMap[size]}
            text-gray-500 dark:text-gray-400
            max-w-md
            ${compact ? 'mb-3' : 'mb-4'}
          `}
        >
          {description}
        </p>
      )}

      {/* 操作按钮 */}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

/**
 * 搜索结果为空
 */
export function EmptySearch({
  keyword,
  onClear,
  className = '',
}: {
  keyword?: string;
  onClear?: () => void;
  className?: string;
}): JSX.Element {
  return (
    <EmptyState
      icon="search"
      title={keyword ? `未找到"${keyword}"相关结果` : '请输入搜索关键词'}
      description={keyword ? '请尝试其他关键词或筛选条件' : '输入关键词开始搜索'}
      action={
        onClear && keyword ? (
          <button
            onClick={onClear}
            className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
          >
            清除搜索
          </button>
        ) : undefined
      }
      className={className}
    />
  );
}

/**
 * 网络错误状态
 */
export function EmptyNetwork({
  onRetry,
  className = '',
}: {
  onRetry?: () => void;
  className?: string;
}): JSX.Element {
  return (
    <EmptyState
      icon="network"
      title="网络连接失败"
      description="请检查网络连接后重试"
      action={
        onRetry ? (
          <button
            onClick={onRetry}
            className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            重试
          </button>
        ) : undefined
      }
      className={className}
    />
  );
}

/**
 * 错误状态
 */
export function EmptyError({
  title = '出错了',
  description = '加载数据时发生错误，请稍后重试',
  onRetry,
  className = '',
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}): JSX.Element {
  return (
    <EmptyState
      icon="error"
      title={title}
      description={description}
      action={
        onRetry ? (
          <button
            onClick={onRetry}
            className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
          >
            重新加载
          </button>
        ) : undefined
      }
      className={className}
    />
  );
}

export default EmptyState;