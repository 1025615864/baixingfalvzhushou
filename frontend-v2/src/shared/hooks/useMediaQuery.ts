// ============================================
// 响应式媒体查询 Hook
// ============================================

import { useState, useEffect } from 'react';

// Tailwind 默认断点
const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;

type Breakpoint = keyof typeof breakpoints;

/**
 * 使用媒体查询
 * @param query 媒体查询字符串
 * @returns 是否匹配
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const media = window.matchMedia(query);
    
    // 初始检查
    setMatches(media.matches);

    // 监听变化
    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    media.addEventListener('change', listener);
    
    return () => {
      media.removeEventListener('change', listener);
    };
  }, [query]);

  return matches;
}

/**
 * 使用断点
 * @param breakpoint 断点名称
 * @returns 是否匹配（大于等于该断点）
 */
export function useBreakpoint(breakpoint: Breakpoint): boolean {
  const query = `(min-width: ${breakpoints[breakpoint]}px)`;
  return useMediaQuery(query);
}

/**
 * 使用移动设备检测
 * @returns 是否为移动设备（小于 md 断点）
 */
export function useIsMobile(): boolean {
  return !useBreakpoint('md');
}

/**
 * 使用平板设备检测
 * @returns 是否为平板设备（md 到 lg 之间）
 */
export function useIsTablet(): boolean {
  const isMd = useBreakpoint('md');
  const isLg = useBreakpoint('lg');
  return isMd && !isLg;
}

/**
 * 使用桌面设备检测
 * @returns 是否为桌面设备（大于等于 lg 断点）
 */
export function useIsDesktop(): boolean {
  return useBreakpoint('lg');
}

/**
 * 使用视口尺寸
 * @returns 视口宽度和高度
 */
export function useViewportSize(): { width: number; height: number } {
  const [size, setSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return size;
}

/**
 * 使用设备方向
 * @returns 是否为横向
 */
export function useOrientation(): 'portrait' | 'landscape' {
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>(
    typeof window !== 'undefined' && window.innerWidth > window.innerHeight ? 'landscape' : 'portrait'
  );

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleResize = () => {
      setOrientation(
        window.innerWidth > window.innerHeight ? 'landscape' : 'portrait'
      );
    };

    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return orientation;
}

/**
 * 使用响应式值
 * 根据断点返回不同的值
 */
export function useResponsiveValue<T>(values: {
  default: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
  '2xl'?: T;
}): T {
  const isSm = useBreakpoint('sm');
  const isMd = useBreakpoint('md');
  const isLg = useBreakpoint('lg');
  const isXl = useBreakpoint('xl');
  const is2Xl = useBreakpoint('2xl');

  if (is2Xl && values['2xl'] !== undefined) return values['2xl'];
  if (isXl && values.xl !== undefined) return values.xl;
  if (isLg && values.lg !== undefined) return values.lg;
  if (isMd && values.md !== undefined) return values.md;
  if (isSm && values.sm !== undefined) return values.sm;
  
  return values.default;
}