export interface PerformanceMetrics {
 FCP?: number;
  LCP?: number;
  FID?: number;
  CLS?: number;
  TTFB?: number;
  domContentLoaded?: number;
  load?: number;
}

export interface ResourceTiming {
  name: string;
  entryType: string;
  duration: number;
  size?: number;
  url?: string;
}

export interface PerformanceReport {
  metrics: PerformanceMetrics;
  resources: ResourceTiming[];
  timestamp: number;
  url: string;
  userAgent: string;
}

type PerformanceCallback = (report: PerformanceReport) => void;

class PerformanceMonitor {
  private callbacks: PerformanceCallback[] = [];
  private isMonitoring = false;

  start(): void {
    if (this.isMonitoring) return;
    this.isMonitoring = true;

    if (typeof window === 'undefined') return;

    const observer = new PerformanceObserver(this.handlePerformanceEntry.bind(this));
    observer.observe({ entryTypes: ['navigation', 'paint', 'resource', 'longtask'] });

    window.addEventListener('load', this.handleLoad.bind(this));
  }

  stop(): void {
    this.isMonitoring = false;
  }

  onReport(callback: PerformanceCallback): () => void {
    this.callbacks.push(callback);
    return () => {
      this.callbacks = this.callbacks.filter(cb => cb !== callback);
    };
  }

  private handlePerformanceEntry(list: PerformanceObserverEntryList): void {
    for (const entry of list.getEntries()) {
      if (entry.entryType === 'navigation') {
        const nav = entry as PerformanceNavigationTiming;
        this.reportMetrics({
          TTFB: nav.responseStart,
          domContentLoaded: nav.domContentLoadedEventEnd,
          load: nav.loadEventEnd,
        });
      }
      if (entry.entryType === 'paint') {
        const paint = entry as PerformancePaintTiming;
        if (paint.name === 'first-contentful-paint') {
          this.reportMetrics({ FCP: paint.startTime });
        }
      }
    }
  }

  private handleLoad(): void {
    this.collectResourceTiming();
  }

  private reportMetrics(metrics: Partial<PerformanceMetrics>): void {
    const report = this.createReport(metrics);
    this.callbacks.forEach(cb => cb(report));
  }

  private createReport(additionalMetrics: Partial<PerformanceMetrics>): PerformanceReport {
    return {
      metrics: {
        ...this.getCurrentMetrics(),
        ...additionalMetrics,
      },
      resources: this.collectResourceTiming(),
      timestamp: Date.now(),
      url: typeof window !== 'undefined' ? window.location.href : '',
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
    };
  }

  private getCurrentMetrics(): PerformanceMetrics {
    if (typeof window === 'undefined' || !performance) {
      return {};
    }

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
    const paint = performance.getEntriesByType('paint');

    const metrics: PerformanceMetrics = {};

    if (navigation) {
      metrics.TTFB = navigation.responseStart;
      metrics.domContentLoaded = navigation.domContentLoadedEventEnd;
      metrics.load = navigation.loadEventEnd;
    }

    const fcp = paint.find(p => p.name === 'first-contentful-paint');
    if (fcp) {
      metrics.FCP = fcp.startTime;
    }

    return metrics;
  }

  private collectResourceTiming(): ResourceTiming[] {
    if (typeof performance === 'undefined') {
      return [];
    }

    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];

    return resources.map(entry => ({
      name: entry.name,
      entryType: entry.entryType,
      duration: entry.duration,
      size: entry.transferSize,
      url: entry.name,
    }));
  }

  measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    return fn().finally(() => {
      const duration = performance.now() - start;
      console.log(`[Performance] ${name} took ${duration.toFixed(2)}ms`);
    });
  }

  measureSync<T>(name: string, fn: () => T): T {
    const start = performance.now();
    const result = fn();
    const duration = performance.now() - start;
    console.log(`[Performance] ${name} took ${duration.toFixed(2)}ms`);
    return result;
  }
}

export const performanceMonitor = new PerformanceMonitor();

export function reportWebVitals(): void {
  if (typeof window === 'undefined') return;

  import('web-vitals').then(({ onCLS, onFCP, onLCP, onFID, onTTFB }) => {
    onCLS(metric => {
      console.log('[Web Vitals] CLS:', metric.value);
    });
    onFCP(metric => {
      console.log('[Web Vitals] FCP:', metric.value);
    });
    onLCP(metric => {
      console.log('[Web Vitals] LCP:', metric.value);
    });
    onFID(metric => {
      console.log('[Web Vitals] FID:', metric.value);
    });
    onTTFB(metric => {
      console.log('[Web Vitals] TTFB:', metric.value);
    });
  }).catch(() => {
    console.warn('Web Vitals library not available');
  });
}
