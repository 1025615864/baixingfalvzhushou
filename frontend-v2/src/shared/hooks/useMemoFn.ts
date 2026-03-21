import { useState, useEffect, useRef, useCallback } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function useDebouncedCallback<T extends (...args: unknown[]) => unknown>(
  callback: T,
  delay: number
): T {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  return useCallback(
    ((...args) => {
      const handler = setTimeout(() => {
        callbackRef.current(...args);
      }, delay);
      return () => clearTimeout(handler);
    }) as T,
    [delay]
  );
}

export function useThrottle<T>(value: T, interval: number): T {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  const lastExecuted = useRef<number>(Date.now());

  useEffect(() => {
    const now = Date.now();
    const timeSinceLastExecution = now - lastExecuted.current;

    if (timeSinceLastExecution >= interval) {
      lastExecuted.current = now;
      setThrottledValue(value);
    } else {
      const timerId = setTimeout(() => {
        lastExecuted.current = Date.now();
        setThrottledValue(value);
      }, interval - timeSinceLastExecution);

      return () => clearTimeout(timerId);
    }
  }, [value, interval]);

  return throttledValue;
}

export function useThrottledCallback<T extends (...args: unknown[]) => unknown>(
  callback: T,
  interval: number
): T {
  const callbackRef = useRef(callback);
  const lastExecuted = useRef<number>(0);
  callbackRef.current = callback;

  return useCallback(
    ((...args) => {
      const now = Date.now();
      if (now - lastExecuted.current >= interval) {
        lastExecuted.current = now;
        callbackRef.current(...args);
      }
    }) as T,
    [interval]
  );
}

export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}

export function useFirstMount(): boolean {
  const isFirst = useRef(true);

  if (isFirst.current) {
    isFirst.current = false;
    return true;
  }

  return false;
}

export function useUpdateEffect(effect: React.EffectCallback, deps?: React.DependencyList): void {
  const isFirst = useRef(true);

  useEffect(() => {
    if (!isFirst.current) {
      return effect();
    }
    isFirst.current = false;
  }, deps);
}
