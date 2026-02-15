/**
 * 搜索功能类型定义
 */

/** 搜索类型 */
export type SearchType = 'all' | 'news' | 'post' | 'lawfirm' | 'lawyer' | 'knowledge';

/** 新闻搜索项 */
export interface NewsSearchItem {
  id: number;
  title: string;
  summary: string | null;
  snippet: string | null;
  type: 'news';
}

/** 帖子搜索项 */
export interface PostSearchItem {
  id: number;
  title: string;
  content: string;
  type: 'post';
}

/** 律所搜索项 */
export interface LawFirmSearchItem {
  id: number;
  name: string;
  address: string | null;
  type: 'lawfirm';
}

/** 律师搜索项 */
export interface LawyerSearchItem {
  id: number;
  name: string;
  specialties: string | null;
  type: 'lawyer';
}

/** 法律知识搜索项 */
export interface KnowledgeSearchItem {
  id: number;
  title: string;
  category: string | null;
  type: 'knowledge';
}

/** 搜索结果 */
export interface SearchResults {
  news: NewsSearchItem[];
  posts: PostSearchItem[];
  lawfirms: LawFirmSearchItem[];
  lawyers: LawyerSearchItem[];
  knowledge: KnowledgeSearchItem[];
}

/** 热门关键词 */
export interface HotKeyword {
  keyword: string;
  count: number;
}

/** 搜索建议响应 */
export interface SearchSuggestionsResponse {
  suggestions: string[];
}

/** 热门搜索响应 */
export interface HotKeywordsResponse {
  keywords: HotKeyword[];
}

/** 搜索历史响应 */
export interface SearchHistoryResponse {
  history: string[];
}

/** 搜索请求参数 */
export interface SearchParams {
  q: string;
  type?: SearchType;
  page?: number;
  limit?: number;
}

/** 搜索筛选器选项 */
export interface SearchFilterOption {
  value: SearchType;
  label: string;
  icon?: string;
}

/** 搜索状态 */
export interface SearchState {
  query: string;
  type: SearchType;
  isLoading: boolean;
  results: SearchResults | null;
  suggestions: string[];
  history: string[];
  hotKeywords: HotKeyword[];
  error: string | null;
}