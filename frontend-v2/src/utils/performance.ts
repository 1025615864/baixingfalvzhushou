/**
 * 性能监控工具
 * 
 * 功能：
 * - 页面加载时间监控
 * - 组件渲染性能监控
 * - 内存使用监控
 * - 网络请求性能监控
 * - 性能指标上报
 */

// ============================================
// 类型定义
// ============================================

interface LayoutShiftEntry extends PerformanceEntry {
  value: number;
  hadRecentInput: boolean;
}

interface PerformanceMemoryInfo {
  jsHeapSizeLimit: number;
  totalJSHeapSize: number;
  usedJSHeapSize: number;
}

interface NavigatorConnectionInfo {
  effectiveType: 'slow-2g' | '2g' | '3g' | '4g';
  rtt: number;
  downlink: number;
  saveData: boolean;
}

/**
 * 性能指标类型
 */
export interface PerformanceMetrics {
  /** 页面加载时间（毫秒） */
  pageLoadTime: number;
  /** 首次内容绘制（FCP，毫秒） */
  firstContentfulPaint: number;
  /** 最大内容绘制（LCP，毫秒） */
  largestContentfulPaint: number;
  /** 首次输入延迟（FID，毫秒） */
  firstInputDelay: number;
  /** 累积布局偏移（CLS） */
  cumulativeLayoutShift: number;
  /** 首次字节时间（TTFB，毫秒） */
  timeToFirstByte: number;
  /** DOM 交互时间（毫秒） */
  domInteractive: number;
  /** 页面完全加载时间（毫秒） */
  loadComplete: number;
  /** 内存使用情况（如果可用） */
  memory?: MemoryInfo;
  /** 网络信息（如果可用） */
  network?: NetworkInfo;
}

/**
 * 内存使用信息
 */
export interface MemoryInfo {
  /** JS 堆内存限制（字节） */
  jsHeapSizeLimit: number;
  /** 总 JS 堆内存（字节） */
  totalJSHeapSize: number;
  /** 已用 JS 堆内存（字节） */
  usedJSHeapSize: number;
}

/**
 * 网络信息
 */
export interface NetworkInfo {
  /** 有效连接类型 */
  effectiveType: 'slow-2g' | '2g' | '3g' | '4g';
  /** 往返时间（毫秒） */
  rtt: number;
  /** 下行带宽（Mbps） */
  downlink: number;
  /** 是否节省数据模式 */
  saveData: boolean;
}

/**
 * 组件渲染性能数据
 */
export interface ComponentRenderMetrics {
  /** 组件名称 */
  componentName: string;
  /** 渲染次数 */
  renderCount: number;
  /** 平均渲染时间（毫秒） */
  averageRenderTime: number;
  /** 最大渲染时间（毫秒） */
  maxRenderTime: number;
  /** 最近渲染时间（毫秒） */
  lastRenderTime: number;
  /** 是否有性能问题（渲染时间超过阈值） */
  hasPerformanceIssue: boolean;
}

/**
 * 网络请求性能数据
 */
export interface RequestPerformanceMetrics {
  /** 请求 URL */
  url: string;
  /** 请求方法 */
  method: string;
  /** 总耗时（毫秒） */
  duration: number;
  /** DNS 查询时间（毫秒） */
  dnsLookup: number;
  /** TCP 连接时间（毫秒） */
  tcpConnect: number;
  /** SSL 握手时间（毫秒） */
  sslHandshake: number;
  /** 请求发送时间（毫秒） */
  requestTime: number;
  /** 等待响应时间（TTFB，毫秒） */
  ttfb: number;
  /** 响应接收时间（毫秒） */
  responseTime: number;
  /** 传输大小（字节） */
  transferSize: number;
  /** 编码后大小（字节） */
  encodedBodySize: number;
  /** 解码后大小（字节） */
  decodedBodySize: number;
  /** 是否从缓存加载 */
  fromCache: boolean;
  /** 资源类型 */
  initiatorType: string;
}

/**
 * 性能监控配置
 */
export interface PerformanceMonitorConfig {
  /** 是否启用监控 */
  enabled: boolean;
  /** 是否上报到服务端 */
  reportToServer: boolean;
  /** 上报端点 */
  reportUrl: string;
  /** 采样率（0-1，1 表示 100%） */
  sampleRate: number;
  /** 渲染性能阈值（毫秒） */
  renderThreshold: number;
  /** 内存警告阈值（百分比） */
  memoryWarningThreshold: number;
  /** 上报间隔（毫秒） */
  reportInterval: number;
}

// ============================================
// 默认配置
// ============================================

const DEFAULT_CONFIG: PerformanceMonitorConfig = {
  enabled: true,
  reportToServer: false,
  reportUrl: '/api/performance/metrics',
  sampleRate: 0.1, // 默认 10% 采样
  renderThreshold: 16, // 60fps 对应的帧时间
  memoryWarningThreshold: 0.8, // 80% 内存使用率警告
  reportInterval: 30000, // 30 秒上报一次
};

// ============================================
// 性能监控类
// ============================================

/**
 * 性能监控器
 */
class PerformanceMonitorClass {
  private config: PerformanceMonitorConfig;
  private metricsQueue: PerformanceMetrics[] = [];
  private renderMetrics: Map<string, ComponentRenderMetrics> = new Map();
  private requestMetrics: RequestPerformanceMetrics[] = [];
  private reportTimer: ReturnType<typeof setInterval> | null = null;
  private observer: PerformanceObserver | null = null;
  private lcpValue = 0;
  private fidValue = 0;
  private clsValue = 0;

  constructor() {
    this.config = { ...DEFAULT_CONFIG };
  }

  /**
   * 初始化性能监控
   */
  init(config?: Partial<PerformanceMonitorConfig>): void {
    if (config) {
      this.config = { ...this.config, ...config };
    }

    if (!this.config.enabled) {
      return;
    }

    // 监听页面加载完成
    if (document.readyState === 'complete') {
      this.collectPageLoadMetrics();
    } else {
      window.addEventListener('load', () => this.collectPageLoadMetrics());
    }

    // 启动性能观察器
    this.startObservers();

    // 启动定时上报
    this.startReportTimer();

    // 监听页面可见性变化
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.reportMetrics();
      }
    });
  }

  /**
   * 收集页面加载性能指标
   */
  private collectPageLoadMetrics(): void {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (!navigation) return;

    const now = Date.now();
    
    // 计算各项时间
    const pageLoadTime = now - navigation.startTime;
    const firstContentfulPaint = this.getFCP();
    const timeToFirstByte = navigation.responseStart - navigation.requestStart;
    const domInteractive = navigation.domInteractive - navigation.domContentLoadedEventStart;
    const loadComplete = navigation.loadEventEnd - navigation.startTime;

    // 获取内存信息
    const memory = this.getMemoryInfo();
    
    // 获取网络信息
    const network = this.getNetworkInfo();

    const metrics: PerformanceMetrics = {
      pageLoadTime,
      firstContentfulPaint,
      largestContentfulPaint: this.lcpValue,
      firstInputDelay: this.fidValue,
      cumulativeLayoutShift: this.clsValue,
      timeToFirstByte,
      domInteractive,
      loadComplete,
      memory,
      network,
    };

    this.metricsQueue.push(metrics);

    // 如果启用上报且命中采样，立即上报
    if (this.config.reportToServer && this.shouldSample()) {
      this.reportMetrics();
    }

    // 开发环境下输出到控制台
    if (import.meta.env.DEV) {
      // 开发环境保留分支，避免影响指标采集主流程
    }
  }

  /**
   * 获取 FCP 时间
   */
  private getFCP(): number {
    const entries = performance.getEntriesByName('first-contentful-paint');
    if (entries.length > 0) {
      return entries[0].startTime;
    }
    return 0;
  }

  /**
   * 获取内存信息
   */
  private getMemoryInfo(): MemoryInfo | undefined {
    const memory = (performance as Performance & { memory?: PerformanceMemoryInfo }).memory;
    if (memory) {
      const { jsHeapSizeLimit, totalJSHeapSize, usedJSHeapSize } = memory;
      return { jsHeapSizeLimit, totalJSHeapSize, usedJSHeapSize };
    }
    return undefined;
  }

  /**
   * 获取网络信息
   */
  private getNetworkInfo(): NetworkInfo | undefined {
    const connection = (navigator as Navigator & { connection?: NavigatorConnectionInfo }).connection;
    if (connection) {
      const { effectiveType, rtt, downlink, saveData } = connection;
      return { effectiveType, rtt, downlink, saveData };
    }
    return undefined;
  }

  /**
   * 启动性能观察器
   */
  private startObservers(): void {
    // LCP 观察器
    try {
      const lcpObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.lcpValue = lastEntry.startTime;
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (e) {
      // LCP 不支持
    }

    // FID 观察器
    try {
      const fidObserver = new PerformanceObserver((entryList) => {
        entryList.getEntries().forEach((entry) => {
          this.fidValue = (entry as PerformanceEventTiming).processingStart - (entry as PerformanceEventTiming).startTime;
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });
    } catch (e) {
      // FID 不支持
    }

    // CLS 观察器
    try {
      const clsObserver = new PerformanceObserver((entryList) => {
        entryList.getEntries().forEach((entry) => {
          if (!(entry as LayoutShiftEntry).hadRecentInput) {
            this.clsValue += (entry as LayoutShiftEntry).value;
          }
        });
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    } catch (e) {
      // CLS 不支持
    }

    // 资源观察器 - 监控网络请求
    try {
      const resourceObserver = new PerformanceObserver((entryList) => {
        entryList.getEntries().forEach((entry) => {
          if (entry.entryType === 'resource') {
            this.collectRequestMetrics(entry as PerformanceResourceTiming);
          }
        });
      });
      resourceObserver.observe({ entryTypes: ['resource'] });
    } catch (e) {
      // 资源观察器不支持
    }
  }

  /**
   * 收集网络请求性能数据
   */
  private collectRequestMetrics(entry: PerformanceResourceTiming): void {
    const metrics: RequestPerformanceMetrics = {
      url: entry.name,
      method: 'GET', // 从 PerformanceResourceTiming 无法直接获取方法
      duration: entry.duration,
      dnsLookup: entry.domainLookupEnd - entry.domainLookupStart,
      tcpConnect: entry.connectEnd - entry.connectStart,
      sslHandshake: entry.secureConnectionStart ? entry.connectEnd - entry.secureConnectionStart : 0,
      requestTime: entry.requestStart - entry.connectEnd,
      ttfb: entry.responseStart - entry.requestStart,
      responseTime: entry.responseEnd - entry.responseStart,
      transferSize: entry.transferSize,
      encodedBodySize: entry.encodedBodySize,
      decodedBodySize: entry.decodedBodySize,
      fromCache: entry.transferSize === 0 && entry.encodedBodySize > 0,
      initiatorType: entry.initiatorType,
    };

    this.requestMetrics.push(metrics);

    // 限制队列大小
    if (this.requestMetrics.length > 100) {
      this.requestMetrics.shift();
    }
  }

  /**
   * 启动定时上报
   */
  private startReportTimer(): void {
    if (this.reportTimer) {
      clearInterval(this.reportTimer);
    }

    this.reportTimer = setInterval(() => {
      if (this.config.reportToServer && this.metricsQueue.length > 0) {
        this.reportMetrics();
      }
    }, this.config.reportInterval);
  }

  /**
   * 上报性能指标
   */
  private reportMetrics(): void {
    if (this.metricsQueue.length === 0 && this.requestMetrics.length === 0) {
      return;
    }

    const payload = {
      pageMetrics: [...this.metricsQueue],
      requestMetrics: [...this.requestMetrics],
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    // 使用 sendBeacon 发送（不会阻塞页面）
    if ('sendBeacon' in navigator) {
      navigator.sendBeacon(
        this.config.reportUrl,
        JSON.stringify(payload)
      );
    } else {
      // 降级为 fetch
      fetch(this.config.reportUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        keepalive: true,
      }).catch(() => {
        // 上报失败静默处理
      });
    }

    // 清空队列
    this.metricsQueue = [];
    this.requestMetrics = [];
  }

  /**
   * 判断是否应该采样
   */
  private shouldSample(): boolean {
    return Math.random() < this.config.sampleRate;
  }

  /**
   * 记录组件渲染性能
   * @param componentName 组件名称
   * @param renderTime 渲染时间（毫秒）
   */
  recordComponentRender(componentName: string, renderTime: number): void {
    const existing = this.renderMetrics.get(componentName);
    
    if (existing) {
      existing.renderCount++;
      existing.lastRenderTime = renderTime;
      existing.averageRenderTime = 
        (existing.averageRenderTime * (existing.renderCount - 1) + renderTime) / existing.renderCount;
      existing.maxRenderTime = Math.max(existing.maxRenderTime, renderTime);
      existing.hasPerformanceIssue = renderTime > this.config.renderThreshold;
    } else {
      this.renderMetrics.set(componentName, {
        componentName,
        renderCount: 1,
        averageRenderTime: renderTime,
        maxRenderTime: renderTime,
        lastRenderTime: renderTime,
        hasPerformanceIssue: renderTime > this.config.renderThreshold,
      });
    }

    // 开发环境下输出警告
    if (import.meta.env.DEV && renderTime > this.config.renderThreshold) {
      // 开发环境保留分支，避免影响性能记录主流程
    }
  }

  /**
   * 获取组件渲染性能数据
   * @param componentName 组件名称
   */
  getComponentRenderMetrics(componentName?: string): ComponentRenderMetrics[] | ComponentRenderMetrics | null {
    if (componentName) {
      return this.renderMetrics.get(componentName) || null;
    }
    return Array.from(this.renderMetrics.values());
  }

  /**
   * 获取网络请求性能数据
   * @param urlFilter 可选的 URL 过滤器
   */
  getRequestMetrics(urlFilter?: string): RequestPerformanceMetrics[] {
    if (urlFilter) {
      return this.requestMetrics.filter((m) => m.url.includes(urlFilter));
    }
    return [...this.requestMetrics];
  }

  /**
   * 获取页面加载性能数据
   */
  getPageMetrics(): PerformanceMetrics[] {
    return [...this.metricsQueue];
  }

  /**
   * 获取 Core Web Vitals 数据
   */
  getCoreWebVitals(): {
    lcp: number;
    fid: number;
    cls: number;
  } {
    return {
      lcp: this.lcpValue,
      fid: this.fidValue,
      cls: this.clsValue,
    };
  }

  /**
   * 检查内存使用情况
   * @returns 内存使用率（0-1）或 null（如果不支持）
   */
  checkMemoryUsage(): number | null {
    const memory = this.getMemoryInfo();
    if (!memory) return null;
    return memory.usedJSHeapSize / memory.jsHeapSizeLimit;
  }

  /**
   * 获取性能报告
   */
  getPerformanceReport(): {
    coreWebVitals: {
      lcp: number;
      fid: number;
      cls: number;
      lcpRating: 'good' | 'needs-improvement' | 'poor';
      fidRating: 'good' | 'needs-improvement' | 'poor';
      clsRating: 'good' | 'needs-improvement' | 'poor';
    };
    slowComponents: Array<{ name: string; avgTime: number; maxTime: number }>;
    slowRequests: Array<{ url: string; duration: number }>;
    memoryUsage: number | null;
  } {
    // Core Web Vitals 评级标准
    const lcpRating = this.lcpValue < 2500 ? 'good' : this.lcpValue < 4000 ? 'needs-improvement' : 'poor';
    const fidRating = this.fidValue < 100 ? 'good' : this.fidValue < 300 ? 'needs-improvement' : 'poor';
    const clsRating = this.clsValue < 0.1 ? 'good' : this.clsValue < 0.25 ? 'needs-improvement' : 'poor';

    // 慢组件
    const slowComponents = Array.from(this.renderMetrics.entries())
      .filter(([, metrics]) => metrics.hasPerformanceIssue)
      .map(([name, metrics]) => ({
        name,
        avgTime: metrics.averageRenderTime,
        maxTime: metrics.maxRenderTime,
      }))
      .sort((a, b) => b.maxTime - a.maxTime)
      .slice(0, 10);

    // 慢请求
    const slowRequests = this.requestMetrics
      .filter((m) => m.duration > 1000)
      .map((m) => ({ url: m.url, duration: m.duration }))
      .sort((a, b) => b.duration - a.duration)
      .slice(0, 10);

    return {
      coreWebVitals: {
        lcp: this.lcpValue,
        fid: this.fidValue,
        cls: this.clsValue,
        lcpRating,
        fidRating,
        clsRating,
      },
      slowComponents,
      slowRequests,
      memoryUsage: this.checkMemoryUsage(),
    };
  }

  /**
   * 销毁监控器
   */
  destroy(): void {
    if (this.reportTimer) {
      clearInterval(this.reportTimer);
      this.reportTimer = null;
    }

    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }

    this.metricsQueue = [];
    this.renderMetrics.clear();
    this.requestMetrics = [];
  }
}

// ============================================
// 导出单例
// ============================================

export const PerformanceMonitor = new PerformanceMonitorClass();

// ============================================
// React Hook - usePerformanceMonitor
// ============================================

import { useEffect, useRef, useCallback } from 'react';

/**
 * React Hook - 监控组件渲染性能
 * 
 * @param componentName 组件名称
 * @param deps 依赖项（用于判断是否需要重新渲染）
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { renderTime } = usePerformanceMonitor('MyComponent');
 *   
 *   return <div>Render time: {renderTime}ms</div>;
 * }
 * ```
 */
export function usePerformanceMonitor(
  componentName: string,
  deps?: unknown[]
): {
  renderTime: number;
  renderCount: number;
  hasPerformanceIssue: boolean;
} {
  const renderStartRef = useRef<number>(0);
  const renderCountRef = useRef(0);
  const lastRenderTimeRef = useRef(0);

  // 记录渲染开始
  useEffect(() => {
    renderStartRef.current = performance.now();
  });

  // 记录渲染结束
  useEffect(() => {
    const renderTime = performance.now() - renderStartRef.current;
    lastRenderTimeRef.current = renderTime;
    renderCountRef.current++;

    PerformanceMonitor.recordComponentRender(componentName, renderTime);
  }, [componentName, deps]);

  const metrics = PerformanceMonitor.getComponentRenderMetrics(componentName) as ComponentRenderMetrics | null;

  return {
    renderTime: lastRenderTimeRef.current,
    renderCount: renderCountRef.current,
    hasPerformanceIssue: metrics?.hasPerformanceIssue || false,
  };
}

/**
 * React Hook - 监控异步操作性能
 * 
 * @param operationName 操作名称
 * 
 * @example
 * ```tsx
 * function DataFetcher() {
 *   const { measure, isLoading } = useAsyncMeasure('fetchData');
 *   
 *   const fetchData = async () => {
 *     const end = measure();
 *     const data = await api.getData();
 *     end();
 *   };
 * }
 * ```
 */
export function useAsyncMeasure(operationName: string): {
  measure: () => () => void;
  isLoading: boolean;
  lastDuration: number | null;
} {
  const startTimeRef = useRef<number | null>(null);
  const lastDurationRef = useRef<number | null>(null);
  const isLoadingRef = useRef(false);

  const measure = useCallback(() => {
    startTimeRef.current = performance.now();
    isLoadingRef.current = true;

    return () => {
      if (startTimeRef.current !== null) {
        const duration = performance.now() - startTimeRef.current;
        lastDurationRef.current = duration;
        isLoadingRef.current = false;

        PerformanceMonitor.recordComponentRender(operationName, duration);
      }
    };
  }, [operationName]);

  return {
    measure,
    isLoading: isLoadingRef.current,
    lastDuration: lastDurationRef.current,
  };
}

// ============================================
// 工具函数
// ============================================

/**
 * 获取当前内存使用率（百分比）
 */
export function getMemoryUsagePercent(): number | null {
  return PerformanceMonitor.checkMemoryUsage();
}

/**
 * 获取性能报告
 */
export function getPerformanceReport(): ReturnType<typeof PerformanceMonitor.getPerformanceReport> {
  return PerformanceMonitor.getPerformanceReport();
}

/**
 * 记录自定义性能指标
 */
export function recordCustomMetric(name: string, value: number, unit = 'ms'): void {
  if (import.meta.env.DEV) {
    void name;
    void value;
    void unit;
  }
}

/**
 * 性能标记 - 用于标记特定时间点
 */
export function markPerformancePoint(name: string): void {
  performance.mark(name);
}

/**
 * 测量两个标记点之间的时间
 */
export function measureBetweenMarks(startMark: string, endMark: string, measureName?: string): number {
  try {
    performance.measure(measureName || `${startMark}-to-${endMark}`, startMark, endMark);
    const measure = performance.getEntriesByName(measureName || `${startMark}-to-${endMark}`)[0];
    return measure ? measure.duration : 0;
  } catch (e) {
    return 0;
  }
}

export default PerformanceMonitor;