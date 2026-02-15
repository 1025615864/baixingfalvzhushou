/**
 * 搜索功能模块入口
 */

// 类型导出
export type {
  SearchType,
  SearchResults as SearchResultsData,
  NewsSearchItem,
  PostSearchItem,
  LawyerSearchItem,
  LawFirmSearchItem,
  KnowledgeSearchItem,
  HotKeyword,
  SearchSuggestionsResponse,
  HotKeywordsResponse,
  SearchHistoryResponse,
  SearchParams,
  SearchFilterOption,
  SearchState,
} from './types';

// API导出
export { searchApi } from './api';
export { default as searchApiDefault } from './api';

// Hooks导出
export {
  useGlobalSearch,
  useSearchSuggestions,
  useHotKeywords,
  useSearchHistory,
  useClearSearchHistory,
  useSearch,
  searchQueryKeys,
} from './hooks/useSearch';

// 组件导出
export { SearchInput } from './components/SearchInput';
export { SearchSuggestions } from './components/SearchSuggestions';
export { SearchResults } from './components/SearchResults';
export { SearchFilter, defaultFilterOptions } from './components/SearchFilter';
export { SearchHistory } from './components/SearchHistory';
export { SearchEmpty } from './components/SearchEmpty';
export { SearchLoading } from './components/SearchLoading';

// 页面导出
export { SearchPage } from './pages/SearchPage';