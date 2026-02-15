/**
 * Search（搜索功能）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 搜索模块的基础 query key
 */
export const searchKeys = {
  all: ['search'] as const,

  /** 搜索结果 */
  results: () => [...searchKeys.all, 'results'] as const,
  searchQuery: (query: string, limit?: number) =>
    [...searchKeys.results(), { q: query, limit }] as const,

  /** 搜索建议 */
  suggestions: () => [...searchKeys.all, 'suggestions'] as const,
  suggestionList: (query: string, limit?: number) =>
    [...searchKeys.suggestions(), { q: query, limit }] as const,

  /** 热门搜索 */
  hotKeywords: () => [...searchKeys.all, 'hot-keywords'] as const,
  hotKeywordsList: (limit?: number) =>
    [...searchKeys.hotKeywords(), limit] as const,

  /** 搜索历史 */
  history: () => [...searchKeys.all, 'history'] as const,
  historyList: (limit?: number) =>
    [...searchKeys.history(), limit] as const,
} as const;

export default searchKeys;