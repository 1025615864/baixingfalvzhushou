/**
 * 搜索功能 React Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import type { SearchParams, SearchResults, HotKeyword } from '../types';
import searchApi from '../api';

/** Query keys for search */
export const searchQueryKeys = {
  all: ['search'] as const,
  results: (params: SearchParams) => [...searchQueryKeys.all, 'results', params] as const,
  suggestions: (query: string) => [...searchQueryKeys.all, 'suggestions', query] as const,
  hotKeywords: () => [...searchQueryKeys.all, 'hotKeywords'] as const,
  history: () => [...searchQueryKeys.all, 'history'] as const,
};

/**
 * 全局搜索 Hook
 * @param params 搜索参数
 * @param enabled 是否启用查询
 */
export function useGlobalSearch(params: SearchParams, enabled: boolean = true) {
  return useQuery<SearchResults, Error>({
    queryKey: searchQueryKeys.results(params),
    queryFn: () => searchApi.globalSearch(params),
    enabled: enabled && params.q.length >= 2,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 搜索建议 Hook
 * @param query 搜索关键词
 * @param enabled 是否启用查询
 */
export function useSearchSuggestions(query: string, enabled: boolean = true) {
  return useQuery<string[], Error>({
    queryKey: searchQueryKeys.suggestions(query),
    queryFn: () => searchApi.getSearchSuggestions(query),
    enabled: enabled && query.length >= 1,
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 热门搜索 Hook
 */
export function useHotKeywords() {
  return useQuery<HotKeyword[], Error>({
    queryKey: searchQueryKeys.hotKeywords(),
    queryFn: async () => {
      const response = await searchApi.getHotKeywords();
      return response.keywords;
    },
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

/**
 * 搜索历史 Hook
 */
export function useSearchHistory() {
  return useQuery<string[], Error>({
    queryKey: searchQueryKeys.history(),
    queryFn: () => searchApi.getSearchHistory(),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

/**
 * 清空搜索历史 Hook
 */
export function useClearSearchHistory() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, void>({
    mutationFn: () => searchApi.clearSearchHistory(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: searchQueryKeys.history() });
    },
  });
}

/**
 * 综合搜索 Hook
 * 包含搜索、建议、历史等功能的组合
 */
export function useSearch() {
  const queryClient = useQueryClient();

  const prefetchSuggestions = useCallback(
    (query: string) => {
      if (query.length >= 1) {
        void queryClient.prefetchQuery({
          queryKey: searchQueryKeys.suggestions(query),
          queryFn: () => searchApi.getSearchSuggestions(query),
          staleTime: 60 * 1000,
        });
      }
    },
    [queryClient]
  );

  const invalidateSearchResults = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: searchQueryKeys.all });
  }, [queryClient]);

  return {
    prefetchSuggestions,
    invalidateSearchResults,
  };
}