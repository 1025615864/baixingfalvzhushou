/**
 * Search（搜索功能）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/search 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  SearchResults,
  SearchParams,
  HotKeywordsResponse,
  HotKeyword,
} from '../types';


// API 基础路径
const API_BASE = '/search';

// ==================== 后端响应类型定义 ====================

/** 后端搜索结果响应 */
interface BackendSearchResponse {
  news: Array<{
    id: number;
    title: string;
    summary: string | null;
    snippet: string | null;
    type: 'news';
  }>;
  posts: Array<{
    id: number;
    title: string;
    content: string;
    type: 'post';
  }>;
  lawfirms: Array<{
    id: number;
    name: string;
    address: string | null;
    type: 'lawfirm';
  }>;
  lawyers: Array<{
    id: number;
    name: string;
    specialties: string | null;
    type: 'lawyer';
  }>;
  knowledge: Array<{
    id: number;
    title: string;
    category: string | null;
    type: 'knowledge';
  }>;
}

/** 后端搜索建议响应 */
interface BackendSuggestionsResponse {
  suggestions: string[];
}

/** 后端热门关键词项 */
interface BackendHotKeyword {
  keyword: string;
  count: number;
}

/** 后端热门搜索响应 */
interface BackendHotKeywordsResponse {
  keywords: BackendHotKeyword[];
}

/** 后端搜索历史响应 */
interface BackendSearchHistoryResponse {
  history: string[];
}

// ==================== 转换函数 ====================

/**
 * 转换后端热门关键词到前端格式
 */
function mapBackendToHotKeyword(data: BackendHotKeyword): HotKeyword {
  return {
    keyword: data.keyword,
    count: data.count,
  };
}

// ==================== 全文搜索 API ====================

/**
 * 全局搜索
 */
export async function apiGlobalSearch(params: SearchParams): Promise<SearchResults> {
  const { q, limit = 10 } = params;
  const response = await apiClient.get<BackendSearchResponse>(API_BASE, {
    params: {
      q,
      limit,
    },
  });

  return {
    news: response.data.news,
    posts: response.data.posts,
    lawfirms: response.data.lawfirms,
    lawyers: response.data.lawyers,
    knowledge: response.data.knowledge,
  };
}

// ==================== 搜索建议 API ====================

/**
 * 获取搜索建议
 */
export async function apiGetSearchSuggestions(
  query: string,
  limit: number = 5
): Promise<string[]> {
  const response = await apiClient.get<BackendSuggestionsResponse>(
    `${API_BASE}/suggestions`,
    {
      params: {
        q: query,
        limit,
      },
    }
  );
  return response.data.suggestions;
}

// ==================== 热门搜索 API ====================

/**
 * 获取热门搜索关键词
 */
export async function apiGetHotKeywords(limit: number = 10): Promise<HotKeywordsResponse> {
  const response = await apiClient.get<BackendHotKeywordsResponse>(`${API_BASE}/hot`, {
    params: {
      limit,
    },
  });

  return {
    keywords: response.data.keywords.map(mapBackendToHotKeyword),
  };
}

// ==================== 搜索历史 API ====================

/**
 * 获取用户搜索历史
 */
export async function apiGetSearchHistory(limit: number = 10): Promise<string[]> {
  const response = await apiClient.get<BackendSearchHistoryResponse>(
    `${API_BASE}/history`,
    {
      params: {
        limit,
      },
    }
  );
  return response.data.history;
}

/**
 * 清空搜索历史
 */
export async function apiClearSearchHistory(): Promise<{ message: string }> {
  const response = await apiClient.delete<{ message: string }>(
    `${API_BASE}/history`
  );
  return response.data;
}

// ==================== 统一导出 ====================

/**
 * Search API 统一导出对象
 */
export const searchApi = {
  // 全文搜索
  globalSearch: apiGlobalSearch,

  // 搜索建议
  getSearchSuggestions: apiGetSearchSuggestions,

  // 热门搜索
  getHotKeywords: apiGetHotKeywords,

  // 搜索历史
  getSearchHistory: apiGetSearchHistory,
  clearSearchHistory: apiClearSearchHistory,
} as const;

export default searchApi;