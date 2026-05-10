/**
 * 搜索页面
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import type { SearchType, SearchResults as SearchResultsType } from '../types';
import { SearchInput } from '../components/SearchInput';
import { SearchFilter, defaultFilterOptions } from '../components/SearchFilter';
import { SearchResults } from '../components/SearchResults';
import { SearchHistory } from '../components/SearchHistory';
import { SearchEmpty } from '../components/SearchEmpty';
import { SearchLoading } from '../components/SearchLoading';
import {
  useGlobalSearch,
  useSearchSuggestions,
  useHotKeywords,
  useSearchHistory,
  useClearSearchHistory,
} from '../hooks/useSearch';

/**
 * 搜索页面组件
 */
export const SearchPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // 从URL参数获取初始值
  const initialQuery = searchParams.get('q') || '';
  const initialType = (searchParams.get('type') as SearchType) || 'all';

  // 本地状态
  const [query, setQuery] = useState(initialQuery);
  const [activeType, setActiveType] = useState<SearchType>(initialType);
  const [hasSearched, setHasSearched] = useState(!!initialQuery);

  // React Query hooks
  const {
    data: searchResults,
    isLoading: isSearching,
    error: searchError,
  } = useGlobalSearch(
    { q: query, limit: 20 },
    hasSearched
  );

  const { data: suggestions = [], isLoading: isSuggestionsLoading } = useSearchSuggestions(
    query,
    !hasSearched || query !== initialQuery
  );

  const { data: hotKeywords = [] } = useHotKeywords();
  const { data: history = [] } = useSearchHistory();
  const clearHistoryMutation = useClearSearchHistory();

  // 更新URL参数
  useEffect(() => {
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    if (activeType !== 'all') params.set('type', activeType);
    setSearchParams(params, { replace: true });
  }, [query, activeType, setSearchParams]);

  // 处理搜索
  const handleSearch = useCallback((searchQuery: string) => {
    setQuery(searchQuery);
    setHasSearched(true);
  }, []);

  // 处理筛选切换
  const handleFilterChange = useCallback((type: SearchType) => {
    setActiveType(type);
  }, []);

  // 处理历史点击
  const handleHistoryClick = useCallback((item: string) => {
    setQuery(item);
    setHasSearched(true);
  }, []);

  // 处理清空历史
  const handleClearHistory = useCallback(() => {
    clearHistoryMutation.mutate();
  }, [clearHistoryMutation]);

  // 处理结果点击
  const handleResultClick = useCallback((type: string, id: number) => {
    const routes: Record<string, string> = {
      news: `/news/${id}`,
      post: `/forum/post/${id}`,
      lawyer: `/lawyer/${id}`,
      lawfirm: `/lawfirm/${id}`,
      knowledge: `/knowledge/${id}`,
    };
    
    const route = routes[type];
    if (route) {
      navigate(route);
    }
  }, [navigate]);

  // 获取筛选选项的计数
  const getFilterOptionsWithCount = useCallback(() => {
    if (!searchResults) return defaultFilterOptions;

    const counts: Record<SearchType, number> = {
      all:
        searchResults.news.length +
        searchResults.posts.length +
        searchResults.lawyers.length +
        searchResults.lawfirms.length +
        searchResults.knowledge.length,
      news: searchResults.news.length,
      post: searchResults.posts.length,
      lawyer: searchResults.lawyers.length,
      lawfirm: searchResults.lawfirms.length,
      knowledge: searchResults.knowledge.length,
    };

    return defaultFilterOptions.map((option) => ({
      ...option,
      count: counts[option.value] || 0,
    }));
  }, [searchResults]);

  // 判断是否无结果
  const hasNoResults = useCallback((results: SearchResultsType | undefined): boolean => {
    if (!results) return false;
    return (
      results.news.length === 0 &&
      results.posts.length === 0 &&
      results.lawyers.length === 0 &&
      results.lawfirms.length === 0 &&
      results.knowledge.length === 0
    );
  }, []);

  // 获取热门关键词文本
  const hotKeywordTexts = hotKeywords.map((k) => k.keyword);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">搜索</h1>
          <p className="text-gray-600">搜索帖子、资讯、律师、律所、法律知识</p>
        </div>

        {/* 搜索输入框 */}
        <div className="mb-6">
          <SearchInput
            value={query}
            onChange={setQuery}
            onSearch={handleSearch}
            suggestions={suggestions}
            placeholder="请输入搜索关键词..."
            autoFocus={!initialQuery}
            loading={isSuggestionsLoading}
          />
        </div>

        {/* 搜索历史 */}
        {!hasSearched && history.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm mb-6">
            <SearchHistory
              history={history}
              onItemClick={handleHistoryClick}
              onClear={handleClearHistory}
            />
          </div>
        )}

        {/* 搜索内容区域 */}
        {hasSearched && (
          <div className="bg-white rounded-lg shadow-sm">
            {/* 筛选器 */}
            <div className="px-4">
              <SearchFilter
                activeType={activeType}
                options={getFilterOptionsWithCount()}
                onChange={handleFilterChange}
              />
            </div>

            {/* 加载状态 */}
            {isSearching && <SearchLoading />}

            {/* 错误状态 */}
            {searchError && (
              <div className="py-12 text-center">
                <p className="text-red-500 mb-4">搜索出错：{searchError.message}</p>
                <button
                  onClick={() => handleSearch(query)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  重试
                </button>
              </div>
            )}

            {/* 搜索结果 */}
            {!isSearching && !searchError && searchResults && (
              <>
                {hasNoResults(searchResults) ? (
                  <SearchEmpty
                    query={query}
                    suggestions={hotKeywordTexts.slice(0, 5)}
                    onSuggestionClick={handleSearch}
                  />
                ) : (
                  <div className="px-4 pb-6">
                    <SearchResults
                      results={searchResults}
                      filterType={activeType}
                      onItemClick={handleResultClick}
                    />
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* 初始状态提示 */}
        {!hasSearched && (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">开始搜索</h3>
            <p className="text-gray-500 mb-6">输入关键词，发现你感兴趣的内容</p>

            {/* 热门搜索 */}
            {hotKeywordTexts.length > 0 && (
              <div>
                <p className="text-sm text-gray-600 mb-3">热门搜索</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {hotKeywordTexts.slice(0, 8).map((keyword) => (
                    <button
                      key={keyword}
                      onClick={() => handleSearch(keyword)}
                      className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 
                               rounded-full hover:bg-gray-50 hover:border-gray-400 transition-colors"
                    >
                      {keyword}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;