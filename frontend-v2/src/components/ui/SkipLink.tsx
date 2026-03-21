/**
 * SkipLink - 无障碍跳转链接组件
 * 
 * 允许键盘用户快速跳过导航直接到达主内容区域
 * 符合 WCAG 2.1 无障碍标准
 */

import React from 'react';

export interface SkipLinkProps {
  /** 跳转目标元素的 ID，默认为 'main-content' */
  targetId?: string;
  /** 链接文本，默认为 '跳转到主内容' */
  label?: string;
  /** 自定义类名 */
  className?: string;
}

/**
 * 无障碍跳转链接组件
 * 
 * @example
 * ```tsx
 * // 在布局中使用
 * <SkipLink />
 * 
 * // 自定义目标
 * <SkipLink targetId="content" label="跳转到内容" />
 * ```
 * 
 * 使用说明：
 * 1. 在页面顶部放置 SkipLink 组件
 * 2. 确保主内容区域有对应的 ID：
 *    <main id="main-content">...</main>
 */
export function SkipLink({
  targetId = 'main-content',
  label = '跳转到主内容',
  className = '',
}: SkipLinkProps): JSX.Element {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <a
      href={`#${targetId}`}
      onClick={handleClick}
      className={`
        sr-only focus:not-sr-only
        focus:absolute focus:top-4 focus:left-4 focus:z-[9999]
        focus:px-4 focus:py-2.5
        focus:bg-primary-600 focus:text-white
        focus:rounded-lg focus:shadow-lg
        focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2
        transition-all duration-200
        ${className}
      `}
    >
      {label}
    </a>
  );
}

/**
 * SkipLinkContainer - 多个跳转链接的容器
 * 
 * @example
 * ```tsx
 * <SkipLinkContainer
 *   links={[
 *     { targetId: 'main-content', label: '跳转到主内容' },
 *     { targetId: 'sidebar', label: '跳转到侧边栏' },
 *   ]}
 * />
 * ```
 */
export interface SkipLinkItem {
  targetId: string;
  label: string;
}

export interface SkipLinkContainerProps {
  /** 跳转链接配置 */
  links: SkipLinkItem[];
  /** 容器类名 */
  className?: string;
}

export function SkipLinkContainer({
  links,
  className = '',
}: SkipLinkContainerProps): JSX.Element {
  return (
    <div
      className={`
        sr-only focus-within:not-sr-only
        focus-within:absolute focus-within:top-4 focus-within:left-4 focus-within:z-[9999]
        focus-within:bg-white focus-within:rounded-lg focus-within:shadow-lg
        focus-within:p-2
        ${className}
      `}
    >
      {links.map((link, index) => (
        <a
          key={link.targetId}
          href={`#${link.targetId}`}
          onClick={(e) => {
            e.preventDefault();
            const target = document.getElementById(link.targetId);
            if (target) {
              target.focus();
              target.scrollIntoView({ behavior: 'smooth' });
            }
          }}
          className={`
            block px-4 py-2.5
            ${index > 0 ? 'mt-1' : ''}
            bg-primary-600 text-white
            rounded-lg
            hover:bg-primary-700
            focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2
            transition-colors duration-200
          `}
        >
          {link.label}
        </a>
      ))}
    </div>
  );
}

export default SkipLink;