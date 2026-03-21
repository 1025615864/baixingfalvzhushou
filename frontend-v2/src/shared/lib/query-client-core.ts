import { QueryClient } from '@tanstack/react-query';

/**
 * 缓存时间配置（毫秒）
 */
export const CACHE_TIMINGS = {
  /** 即时数据 - 几乎不过期（如用户配置） */
  IMMEDIATE: 0,
  /** 短期缓存 - 30 秒（如实时通知、聊天消息） */
  SHORT: 30 * 1000,
  /** 中期缓存 - 2 分钟（如列表数据、搜索结果） */
  MEDIUM: 2 * 60 * 1000,
  /** 长期缓存 - 10 分钟（如用户资料、设置） */
  LONG: 10 * 60 * 1000,
  /** 持久缓存 - 30 分钟（如静态数据、配置项） */
  PERSISTENT: 30 * 60 * 1000,
  /** 永久缓存 - 1 小时（如字典数据、选项列表） */
  PERMANENT: 60 * 60 * 1000,
} as const;

/**
 * 垃圾回收时间配置（毫秒）
 * 定义查询数据在缓存中保留的时间
 */
export const GC_TIMINGS = {
  /** 快速回收 - 1 分钟（临时数据） */
  FAST: 60 * 1000,
  /** 标准回收 - 5 分钟（一般数据） */
  STANDARD: 5 * 60 * 1000,
  /** 延迟回收 - 15 分钟（重要数据） */
  DELAYED: 15 * 60 * 1000,
  /** 持久保留 - 30 分钟（常用数据） */
  PERSISTENT: 30 * 60 * 1000,
} as const;

/**
 * React Query 客户端配置
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: CACHE_TIMINGS.MEDIUM,
      gcTime: GC_TIMINGS.PERSISTENT,
      retry: (failureCount, error) => {
        const maybeCode =
          typeof error === 'object' &&
          error !== null &&
          'code' in error &&
          typeof (error as { code?: unknown }).code === 'number'
            ? (error as { code: number }).code
            : undefined;

        if (typeof maybeCode === 'number' && maybeCode >= 400 && maybeCode < 500) {
          return false;
        }
        if (maybeCode === 0) {
          return failureCount < 3;
        }
        if (typeof maybeCode === 'number' && maybeCode >= 500) {
          return failureCount < 2;
        }
        return failureCount < 3;
      },
      retryDelay: (attemptIndex) => {
        const baseDelay = Math.min(1000 * 2 ** attemptIndex, 30000);
        const jitter = baseDelay * 0.2 * Math.random();
        return baseDelay + jitter;
      },
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      refetchOnMount: (query) => {
        return query.state.data === undefined || query.isStale();
      },
      structuralSharing: true,
      placeholderData: <TQueryData>(previousData: TQueryData | undefined) => previousData,
    },
    mutations: {
      retry: false,
      networkMode: 'offlineFirst',
    },
  },
});

export default queryClient;
