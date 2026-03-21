import { useQuery, useQueryClient, QueryKey } from '@tanstack/react-query';

export interface UseDataLoaderOptions<T> {
  queryKey: QueryKey;
  queryFn: () => Promise<T>;
  enabled?: boolean;
  staleTime?: number;
  cacheTime?: number;
  refetchOnWindowFocus?: boolean;
  refetchOnMount?: boolean;
  retry?: number | boolean;
}

export function useDataLoader<T>({
  queryKey,
  queryFn,
  enabled = true,
  staleTime = 1000 * 60 * 5,
  cacheTime = 1000 * 60 * 10,
  refetchOnWindowFocus = false,
  refetchOnMount = false,
  retry = 1,
}: UseDataLoaderOptions<T>) {
  return useQuery<T, Error>({
    queryKey,
    queryFn,
    enabled,
    staleTime,
    cacheTime,
    refetchOnWindowFocus,
    refetchOnMount,
    retry,
  });
}

export function usePrefetchData<T>(
  queryKey: QueryKey,
  queryFn: () => Promise<T>,
  options?: {
    staleTime?: number;
  }
) {
  const queryClient = useQueryClient();

  return () => {
    queryClient.prefetchQuery({
      queryKey,
      queryFn,
      staleTime: options?.staleTime ?? 1000 * 60 * 5,
    });
  };
}

export function useInvalidateData() {
  const queryClient = useQueryClient();

  return (queryKey: QueryKey) => {
    queryClient.invalidateQueries({ queryKey });
  };
}

export function useResetData() {
  const queryClient = useQueryClient();

  return (queryKey: QueryKey) => {
    queryClient.resetQueries({ queryKey });
  };
}
