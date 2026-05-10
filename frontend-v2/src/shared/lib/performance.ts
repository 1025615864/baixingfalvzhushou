// ============================================
// 性能监控工具
// ============================================

import { logger } from './logger';

// Layout Shift 条目类型
interface LayoutShiftEntry extends PerformanceEntry {
  value: number;
  hadRecentInput: boolean;
}

// First Input 条目类型
interface FirstInputEntry extends PerformanceEntry {
  processingStart: number;
}

/**
 * 性能指标类型
 */
export interface PerformanceMetrics {
  /** 首次内容绘制 */
  fcp: number;
  /** 最大内容绘制 */
  lcp: number;
  /** 首次输入延迟 */
  fid: number;
  /** 累积布局偏移 */
  cls: number;
  /** 首次字节时间 */
  ttfb: number;
  /** 页面加载时间 */
  loadTime: number;
  /** DOM 可交互时间 */
  domInteractive: number;
}

/**
 * 性能监控配置
 */
const PERFORMANCE_CONFIG = {
  /** 是否启用性能监控 */
  enabled: import.meta.env.PROD,
  /** 报告阈值 (ms) */
  thresholds: {
    fcp: 1800,
    lcp: 2500,
    fid: 100,
    cls: 0.1,
    ttfb: 600,
    loadTime: 3000,
  },
};

/**
 * 获取性能指标
 */
export function getPerformanceMetrics(): Partial<PerformanceMetrics> {
  if (typeof window === 'undefined' || !window.performance) {
    return {};
  }

  const navigation = performance.getEntriesByType(
    'navigation'
  )[0] as PerformanceNavigationTiming;
  const paint = performance.getEntriesByType('paint');

  const metrics: Partial<PerformanceMetrics> = {};

  // 页面加载时间
  if (navigation) {
    metrics.loadTime = navigation.loadEventEnd - navigation.startTime;
    metrics.domInteractive =
      navigation.domInteractive - navigation.startTime;
    metrics.ttfb = navigation.responseStart - navigation.startTime;
  }

  // 绘制指标
  paint.forEach((entry) => {
    if (entry.name === 'first-contentful-paint') {
      metrics.fcp = entry.startTime;
    }
  });

  return metrics;
}

/**
 * 观察 LCP (最大内容绘制)
 */
export function observeLCP(
  callback: (metric: number) => void
): () => void {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
    return () => {};
  }

  const observer = new PerformanceObserver((list) => {
    const entries = list.getEntries();
    const lastEntry = entries[entries.length - 1];
    if (lastEntry) {
      callback(lastEntry.startTime);
    }
  });

  observer.observe({ entryTypes: ['largest-contentful-paint'] });

  return () => observer.disconnect();
}

/**
 * 观察 CLS (累积布局偏移)
 */
export function observeCLS(
  callback: (metric: number) => void
): () => void {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
    return () => {};
  }

  let clsValue = 0;

  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      const layoutShift = entry as LayoutShiftEntry;
      if (!layoutShift.hadRecentInput) {
        clsValue += layoutShift.value;
      }
    }
    callback(clsValue);
  });

  observer.observe({ entryTypes: ['layout-shift'] });

  return () => observer.disconnect();
}

/**
 * 观察 FID (首次输入延迟)
 */
export function observeFID(
  callback: (metric: number) => void
): () => void {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
    return () => {};
  }

  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      const firstInput = entry as FirstInputEntry;
      const fid = firstInput.processingStart - entry.startTime;
      callback(fid);
    }
  });

  observer.observe({ entryTypes: ['first-input'] });

  return () => observer.disconnect();
}

/**
 * 报告性能指标
 */
export function reportPerformanceMetrics(
  metrics: Partial<PerformanceMetrics>
): void {
  if (!PERFORMANCE_CONFIG.enabled) {
    return;
  }

  // 检查是否超过阈值
  const warnings: string[] = [];
  const { thresholds } = PERFORMANCE_CONFIG;

  if (metrics.fcp && metrics.fcp > thresholds.fcp) {
    warnings.push(`FCP 超过阈值: ${metrics.fcp.toFixed(0)}ms`);
  }
  if (metrics.lcp && metrics.lcp > thresholds.lcp) {
    warnings.push(`LCP 超过阈值: ${metrics.lcp.toFixed(0)}ms`);
  }
  if (metrics.fid && metrics.fid > thresholds.fid) {
    warnings.push(`FID 超过阈值: ${metrics.fid.toFixed(0)}ms`);
  }
  if (metrics.cls && metrics.cls > thresholds.cls) {
    warnings.push(`CLS 超过阈值: ${metrics.cls.toFixed(3)}`);
  }
  if (metrics.ttfb && metrics.ttfb > thresholds.ttfb) {
    warnings.push(`TTFB 超过阈值: ${metrics.ttfb.toFixed(0)}ms`);
  }

  // 输出警告
  if (warnings.length > 0) {
    logger.warn('性能指标警告:', warnings);
  }

  // 发送到分析服务（如果有）
  const analyticsEndpoint = import.meta.env.VITE_ANALYTICS_ENDPOINT as
    | string
    | undefined;
  if (analyticsEndpoint && typeof window !== 'undefined') {
    fetch(analyticsEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'performance',
        metrics,
        url: window.location.href,
        timestamp: Date.now(),
      }),
      keepalive: true,
    }).catch(() => {
      // 静默失败，不影响用户体验
    });
  }
}

/**
 * 初始化性能监控
 */
export function initPerformanceMonitoring(): void {
  if (typeof window === 'undefined') {
    return;
  }

  // 页面加载完成后报告指标
  window.addEventListener('load', () => {
    // 延迟执行，确保所有指标都已收集
    setTimeout(() => {
      const metrics = getPerformanceMetrics();
      reportPerformanceMetrics(metrics);
    }, 0);
  });

  // 监听 LCP
  observeLCP((lcp) => {
    reportPerformanceMetrics({ lcp });
  });

  // 监听 CLS
  observeCLS((cls) => {
    reportPerformanceMetrics({ cls });
  });

  // 监听 FID
  observeFID((fid) => {
    reportPerformanceMetrics({ fid });
  });
}

/**
 * 测量函数执行时间
 */
export function measurePerformance<T extends (...args: unknown[]) => unknown>(
  fn: T,
  name: string
): T {
  return function (...args: Parameters<T>): ReturnType<T> {
    const start = performance.now();
    const result = fn(...args);
    const end = performance.now();

    logger.info(`${name} 执行时间: ${(end - start).toFixed(2)}ms`);

    return result as ReturnType<T>;
  } as T;
}

/**
 * 创建性能标记
 */
export function markPerformance(markName: string): void {
  if (typeof window !== 'undefined' && window.performance) {
    performance.mark(markName);
  }
}

/**
 * 测量性能标记之间的时间
 */
export function measurePerformanceMark(
  measureName: string,
  startMark: string,
  endMark?: string
): number | null {
  if (typeof window === 'undefined' || !window.performance) {
    return null;
  }

  try {
    performance.measure(measureName, startMark, endMark);
    const entries = performance.getEntriesByName(measureName);
    const duration = entries[entries.length - 1]?.duration;
    return duration ?? null;
  } catch {
    return null;
  }
}