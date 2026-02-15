// ============================================
// 响应式容器组件
// ============================================

import type { ReactNode } from 'react';

interface ResponsiveContainerProps {
  children: ReactNode;
  className?: string;
  /** 是否限制最大宽度 */
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  /** 内边距 */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** 居中对齐 */
  centered?: boolean;
}

/**
 * 响应式容器
 * 提供一致的布局约束和响应式内边距
 */
export function ResponsiveContainer({
  children,
  className = '',
  maxWidth = '2xl',
  padding = 'md',
  centered = true,
}: ResponsiveContainerProps): JSX.Element {
  // 最大宽度映射
  const maxWidthClasses = {
    sm: 'max-w-screen-sm',
    md: 'max-w-screen-md',
    lg: 'max-w-screen-lg',
    xl: 'max-w-screen-xl',
    '2xl': 'max-w-screen-2xl',
    full: 'max-w-full',
  };

  // 内边距映射（响应式）
  const paddingClasses = {
    none: '',
    sm: 'px-4 sm:px-6',
    md: 'px-4 sm:px-6 lg:px-8',
    lg: 'px-4 sm:px-8 lg:px-12',
  };

  return (
    <div
      className={`
        w-full
        ${maxWidthClasses[maxWidth]}
        ${paddingClasses[padding]}
        ${centered ? 'mx-auto' : ''}
        ${className}
      `.trim()}
    >
      {children}
    </div>
  );
}