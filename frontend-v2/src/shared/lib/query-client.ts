import { QueryKey } from '@tanstack/react-query';
import { logger } from './logger';

export {
  CACHE_TIMINGS,
  GC_TIMINGS,
  queryClient,
} from './query-client-core';

import {
  CACHE_TIMINGS,
  GC_TIMINGS,
  queryClient,
} from './query-client-core';

/**
 * 根据查询键获取定制的 staleTime
 * 基于查询类型提供不同的缓存策略
 */
export function getStaleTime(queryKey: QueryKey): number {
  const keyPath = queryKey.join('/');

  if (keyPath.includes('notifications') || keyPath.includes('messages') || keyPath.includes('chat')) {
    return CACHE_TIMINGS.SHORT;
  }

  if (keyPath.includes('user') || keyPath.includes('profile') || keyPath.includes('settings')) {
    return CACHE_TIMINGS.LONG;
  }

  if (keyPath.includes('list') || keyPath.includes('search') || keyPath.includes('query')) {
    return CACHE_TIMINGS.MEDIUM;
  }

  if (keyPath.includes('config') || keyPath.includes('options') || keyPath.includes('dictionary')) {
    return CACHE_TIMINGS.PERMANENT;
  }

  if (keyPath.includes('stats') || keyPath.includes('analytics') || keyPath.includes('dashboard')) {
    return CACHE_TIMINGS.SHORT;
  }

  return CACHE_TIMINGS.MEDIUM;
}

/**
 * 根据查询键获取定制的 gcTime
 */
export function getGcTime(queryKey: QueryKey): number {
  const keyPath = queryKey.join('/');

  if (keyPath.includes('temp') || keyPath.includes('preview')) {
    return GC_TIMINGS.FAST;
  }

  if (keyPath.includes('user') || keyPath.includes('auth') || keyPath.includes('security')) {
    return GC_TIMINGS.STANDARD;
  }

  if (keyPath.includes('config') || keyPath.includes('settings')) {
    return GC_TIMINGS.DELAYED;
  }

  return GC_TIMINGS.PERSISTENT;
}

export interface PrefetchConfig {
  staleTime?: number;
  timeout?: number;
}

export async function prefetchQuery<TData = unknown>(
  queryKey: QueryKey,
  queryFn: () => Promise<TData>,
  config: PrefetchConfig = {}
): Promise<void> {
  const { staleTime = CACHE_TIMINGS.SHORT, timeout = 5000 } = config;

  try {
    const query = queryClient.getQueryData(queryKey);
    if (query !== undefined) {
      return;
    }

    await Promise.race([
      queryClient.prefetchQuery({
        queryKey,
        queryFn,
        staleTime,
        gcTime: GC_TIMINGS.STANDARD,
      }),
      new Promise<void>((_, reject) => setTimeout(() => reject(new Error('Prefetch timeout')), timeout)),
    ]);
  } catch (error) {
    logger.warn(`Prefetch failed for ${JSON.stringify(queryKey)}:`, error);
  }
}

export async function prefetchQueries(
  queries: Array<{
    queryKey: QueryKey;
    queryFn: () => Promise<unknown>;
    config?: PrefetchConfig;
  }>
): Promise<void> {
  try {
    await Promise.all(queries.map(({ queryKey, queryFn, config }) => prefetchQuery(queryKey, queryFn, config)));
  } catch (error) {
    logger.warn('Some prefetch operations failed:', error);
  }
}

export async function prefetchInfiniteQuery<TData extends { hasNext?: boolean; nextPage?: number } = { hasNext?: boolean; nextPage?: number }>(
  queryKey: QueryKey,
  queryFn: (pageParam: number) => Promise<TData>,
  config: PrefetchConfig & { initialPageParam?: number } = {}
): Promise<void> {
  const { staleTime = CACHE_TIMINGS.SHORT, timeout = 5000, initialPageParam = 0 } = config;

  try {
    await Promise.race([
      queryClient.prefetchInfiniteQuery({
        queryKey,
        queryFn: ({ pageParam }) => queryFn(pageParam),
        staleTime,
        gcTime: GC_TIMINGS.STANDARD,
        initialPageParam,
        getNextPageParam: (lastPage: TData & { hasNext?: boolean; nextPage?: number }) =>
          lastPage?.hasNext ? lastPage.nextPage : undefined,
      }),
      new Promise<void>((_, reject) => setTimeout(() => reject(new Error('Prefetch timeout')), timeout)),
    ]);
  } catch (error) {
    logger.warn(`Infinite prefetch failed for ${JSON.stringify(queryKey)}:`, error);
  }
}

export const smartPrefetch = {
  onMouseEnter: (queryKey: QueryKey, queryFn: () => Promise<unknown>) => {
    const timeoutId = setTimeout(() => {
      void prefetchQuery(queryKey, queryFn, { staleTime: CACHE_TIMINGS.SHORT });
    }, 100);
    return () => clearTimeout(timeoutId);
  },

  onScrollNearEnd: <TData extends { hasNext?: boolean; nextPage?: number }>(
    queryKey: QueryKey,
    queryFn: (page: number) => Promise<TData>,
    currentPage: number
  ) => {
    void prefetchInfiniteQuery(queryKey, queryFn, {
      staleTime: CACHE_TIMINGS.SHORT,
      initialPageParam: currentPage + 1,
    });
  },

  onRouteChange: (queryKey: QueryKey, queryFn: () => Promise<unknown>) => {
    void prefetchQuery(queryKey, queryFn, { staleTime: CACHE_TIMINGS.MEDIUM });
  },
};

export default queryClient;
