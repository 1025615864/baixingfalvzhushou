/**
 * News Ingest Runs React Query Hooks
 */

import { useQuery } from '@tanstack/react-query';

import { apiGetNewsIngestRuns } from '../api';
import { NEWS_ADMIN_QUERY_KEYS } from '../api/queryKeys';
import type { GetIngestRunsRequest } from '../types';

/**
 * 获取抓取运行记录列表
 */
export function useNewsIngestRuns(filters: GetIngestRunsRequest) {
  return useQuery({
    queryKey: NEWS_ADMIN_QUERY_KEYS.ingestRuns.list(filters),
    queryFn: () => apiGetNewsIngestRuns(filters),
    staleTime: 30 * 1000, // 30秒
    placeholderData: (previousData) => previousData,
  });
}
