/**
 * PageTransition 页面过渡动画组件
 * 提供流畅的页面切换动画效果
 */

import { ReactNode, useEffect, useRef, useState } from 'react';
import { useLocation, Outlet } from 'react-router-dom';
import { motion, AnimatePresence, type MotionProps, type Transition } from 'framer-motion';

/**
 * 页面过渡动画配置
 */
// eslint-disable-next-line react-refresh/only-export-components
export const pageTransitionConfig: Record<string, MotionProps> = {
  // 淡入淡出 + 轻微上移动画
  fadeUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 },
    transition: { duration: 0.3, ease: 'easeOut' } as Transition,
  },
  // 淡入动画
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.2, ease: 'easeOut' } as Transition,
  },
  // 缩放淡入动画
  scaleFade: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 1.02 },
    transition: { duration: 0.25, ease: 'easeOut' } as Transition,
  },
  // 左侧滑入动画
  slideLeft: {
    initial: { opacity: 0, x: 30 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
    transition: { duration: 0.3, ease: 'easeOut' } as Transition,
  },
  // 右侧滑入动画
  slideRight: {
    initial: { opacity: 0, x: -30 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 },
    transition: { duration: 0.3, ease: 'easeOut' } as Transition,
  },
};

/**
 * 默认使用的过渡动画类型
 */
type TransitionType = keyof typeof pageTransitionConfig;

interface PageTransitionProps {
  children: ReactNode;
  /**
   * 过渡动画类型
   * @default 'fadeUp'
   */
  type?: TransitionType;
  /**
   * 自定义动画属性，会覆盖 type 配置
   */
  custom?: MotionProps;
  /**
   * 是否启用动画
   * @default true
   */
  enabled?: boolean;
}

/**
 * 页面过渡动画包装组件
 */
export function PageTransition({
  children,
  type = 'fadeUp',
  custom,
  enabled = true,
}: PageTransitionProps): JSX.Element {
  const config = custom || pageTransitionConfig[type];

  if (!enabled) {
    return <>{children}</>;
  }

  return (
    <motion.div
      initial={config.initial}
      animate={config.animate}
      exit={config.exit}
      transition={config.transition}
    >
      {children}
    </motion.div>
  );
}

/**
 * 带路由过渡的页面容器
 * 自动根据路由变化触发动画
 */
interface AnimatedOutletProps {
  /**
   * 过渡动画类型
   * @default 'fadeUp'
   */
  type?: TransitionType;
  /**
   * 是否启用动画
   * @default true
   */
  enabled?: boolean;
}

/**
 * 带动画的 Outlet 组件
 * 用于替代 React Router 的 Outlet
 */
export function AnimatedOutlet({
  type = 'fadeUp',
  enabled = true,
}: AnimatedOutletProps): JSX.Element {
  const location = useLocation();
  const prevPathRef = useRef(location.pathname);

  // 跟踪路径变化
  useEffect(() => {
    prevPathRef.current = location.pathname;
  }, [location.pathname]);

  const config = pageTransitionConfig[type];

  if (!enabled) {
    return <Outlet />;
  }

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={location.pathname}
        initial={config.initial}
        animate={config.animate}
        exit={config.exit}
        transition={config.transition}
        className="w-full"
      >
        <Outlet />
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * 滚动到顶部组件
 * 页面切换时自动滚动到顶部
 */
interface ScrollToTopProps {
  /**
   * 是否在页面切换时滚动
   * @default true
   */
  enabled?: boolean;
  /**
   * 滚动行为
   * @default 'smooth'
   */
  behavior?: ScrollBehavior;
}

export function ScrollToTop({
  enabled = true,
  behavior = 'smooth',
}: ScrollToTopProps): JSX.Element | null {
  const { pathname } = useLocation();
  const prevPathRef = useRef(pathname);

  useEffect(() => {
    if (!enabled) return;

    // 只有路径变化时才滚动
    if (prevPathRef.current !== pathname) {
      window.scrollTo({
        top: 0,
        behavior,
      });
      prevPathRef.current = pathname;
    }
  }, [pathname, enabled, behavior]);

  return null;
}

/**
 * 滚动动画 Hook
 * 使用 Intersection Observer 实现元素进入视口时的动画
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useScrollAnimation<T extends HTMLElement>(
  options?: IntersectionObserverInit
): {
  ref: React.RefObject<T>;
  isInView: boolean;
} {
  const ref = useRef<T>(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        // 只在第一次进入时触发
        if (entry.isIntersecting && !isInView) {
          setIsInView(true);
        }
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px',
        ...options,
      }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [isInView, options]);

  return { ref, isInView };
}

/**
 * 带滚动动画的组件包装器
 */
interface ScrollRevealProps {
  children: ReactNode;
  /**
   * 动画方向
   * @default 'up'
   */
  direction?: 'up' | 'down' | 'left' | 'right' | 'none';
  /**
   * 延迟时间 (毫秒)
   * @default 0
   */
  delay?: number;
  /**
   * 动画持续时间
   * @default 0.5
   */
  duration?: number;
  /**
   * 触发视口阈值
   * @default 0.1
   */
  threshold?: number;
  /**
   * 是否禁用动画
   * @default false
   */
  disabled?: boolean;
}

/**
 * 滚动时自动显示的动画组件
 */
export function ScrollReveal({
  children,
  direction = 'up',
  delay = 0,
  duration = 0.5,
  threshold = 0.1,
  disabled = false,
}: ScrollRevealProps): JSX.Element {
  const [isInView, setIsInView] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (disabled) {
      setIsInView(true);
      return;
    }

    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [disabled, threshold]);

  // 方向映射
  const directionMap = {
    up: { y: 40, x: 0 },
    down: { y: -40, x: 0 },
    left: { y: 0, x: 40 },
    right: { y: 0, x: -40 },
    none: { y: 0, x: 0 },
  };

  const initial = directionMap[direction];

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, ...initial }}
      animate={isInView ? { opacity: 1, x: 0, y: 0 } : { opacity: 0, ...initial }}
      transition={{ duration, delay, ease: 'easeOut' } as Transition}
    >
      {children}
    </motion.div>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export { motion, AnimatePresence };
