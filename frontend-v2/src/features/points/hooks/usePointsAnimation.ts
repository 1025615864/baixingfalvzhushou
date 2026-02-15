/**
 * usePointsAnimation - 积分动画控制 Hook
 */

import { useState, useCallback, useRef, useEffect } from 'react';

interface PointsAnimationState {
  isAnimating: boolean;
  points: number;
  position?: { x: number; y: number };
}

interface UsePointsAnimationReturn {
  /** 当前动画状态 */
  state: PointsAnimationState;
  /** 触发动画 */
  trigger: (points: number, element?: HTMLElement | null) => void;
  /** 停止动画 */
  stop: () => void;
  /** 动画完成回调 */
  onComplete: () => void;
}

/**
 * 积分动画控制 Hook
 */
export function usePointsAnimation(): UsePointsAnimationReturn {
  const [state, setState] = useState<PointsAnimationState>({
    isAnimating: false,
    points: 0,
  });

  const completeCallbackRef = useRef<(() => void) | undefined>();

  /**
   * 触发动画
   */
  const trigger = useCallback((points: number, element?: HTMLElement | null) => {
    let position: { x: number; y: number } | undefined;

    if (element) {
      const rect = element.getBoundingClientRect();
      position = {
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      };
    }

    setState({
      isAnimating: true,
      points,
      position,
    });
  }, []);

  /**
   * 停止动画
   */
  const stop = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isAnimating: false,
    }));
  }, []);

  /**
   * 动画完成处理
   */
  const onComplete = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isAnimating: false,
    }));
    completeCallbackRef.current?.();
  }, []);

  return {
    state,
    trigger,
    stop,
    onComplete,
  };
}

/**
 * 批量积分动画 Hook
 * 用于连续触发多个积分获得动画
 */
export function useBatchPointsAnimation() {
  const [queue, setQueue] = useState<Array<{ id: number; points: number }>>([]);
  const [currentAnimation, setCurrentAnimation] = useState<{
    id: number;
    points: number;
  } | null>(null);
  const idCounterRef = useRef(0);

  /**
   * 添加动画到队列
   */
  const addAnimation = useCallback((points: number) => {
    const id = ++idCounterRef.current;
    setQueue((prev) => [...prev, { id, points }]);
    return id;
  }, []);

  /**
   * 处理动画完成
   */
  const handleAnimationComplete = useCallback(() => {
    setCurrentAnimation(null);
    
    // 开始下一个动画
    setQueue((prev) => {
      if (prev.length > 0) {
        const [next, ...rest] = prev;
        setTimeout(() => setCurrentAnimation(next), 200);
        return rest;
      }
      return prev;
    });
  }, []);

  /**
   * 清空队列
   */
  const clearQueue = useCallback(() => {
    setQueue([]);
    setCurrentAnimation(null);
  }, []);

  return {
    currentAnimation,
    queue,
    addAnimation,
    handleAnimationComplete,
    clearQueue,
  };
}

/**
 * 积分增加提示 Hook
 * 用于显示积分增加的 Toast 提示
 */
export function usePointsToast() {
  const [toasts, setToasts] = useState<Array<{
    id: number;
    points: number;
    message: string;
  }>>([]);
  const idCounterRef = useRef(0);
  // 用于存储所有 timeout ID，以便清理
  const timeoutsRef = useRef<Set<NodeJS.Timeout>>(new Set());

  /**
   * 显示积分增加提示
   */
  const showPointsToast = useCallback((points: number, customMessage?: string) => {
    const id = ++idCounterRef.current;
    const message = customMessage || `获得 ${points} 积分`;
    
    setToasts((prev) => [...prev, { id, points, message }]);

    // 3秒后自动移除
    const timeoutId = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
      // 清理已完成的 timeout
      timeoutsRef.current.delete(timeoutId);
    }, 3000);
    
    // 保存 timeout ID
    timeoutsRef.current.add(timeoutId);

    return id;
  }, []);

  /**
   * 移除指定提示
   */
  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  /**
   * 清空所有提示
   */
  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  // 组件卸载时清理所有 timeout
  useEffect(() => {
    const timeouts = timeoutsRef.current;
    return () => {
      // 清理所有未完成的 timeout
      timeouts.forEach((timeoutId) => {
        clearTimeout(timeoutId);
      });
      timeouts.clear();
    };
  }, []);

  return {
    toasts,
    showPointsToast,
    removeToast,
    clearToasts,
  };
}