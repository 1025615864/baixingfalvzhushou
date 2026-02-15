/**
 * News-Admin API 类型定义
 * 后端原始类型 (snake_case)，用于 API 请求/响应
 */

// ==================== 后端原始类型 ====================

/** 后端新闻来源类型 */
export interface NewsSourceBackend {
  id: number;
  name: string;
  source_type: string;
  feed_url: string;
  site: string | null;
  category: string | null;
  is_enabled: boolean;
  fetch_timeout_seconds: number;
  max_items_per_feed: number;
  last_run_at: string | null;
  last_success_at: string | null;
  last_error: string | null;
  last_error_at: string | null;
  created_at: string;
  updated_at: string;
}

/** 后端抓取运行记录类型 */
export interface NewsIngestRunBackend {
  id: number;
  source_id: number | null;
  source_name: string | null;
  feed_url: string | null;
  status: 'running' | 'success' | 'failed';
  fetched: number;
  inserted: number;
  skipped: number;
  errors: number;
  last_error: string | null;
  started_at: string;
  finished_at: string | null;
  created_at: string;
}

/** 后端新闻文章类型 */
export interface NewsArticleBackend {
  id: number;
  title: string;
  summary: string | null;
  content: string;
  cover_image: string | null;
  category: string;
  source: string | null;
  source_url: string | null;
  source_site: string | null;
  author: string | null;
  view_count: number;
  favorite_count: number;
  is_favorited: boolean;
  ai_risk_level: string | null;
  ai_keywords: string[] | null;
  is_top: boolean;
  is_published: boolean;
  review_status: string | null;
  review_reason: string | null;
  reviewed_at: string | null;
  published_at: string | null;
  scheduled_publish_at: string | null;
  scheduled_unpublish_at: string | null;
  created_at: string;
  updated_at: string;
}

/** 后端 AI 标注类型 */
export interface AIAnnotationBackend {
  summary: string | null;
  risk_level: string;
  sensitive_words: string[];
  highlights: string[];
  keywords: string[];
  duplicate_of_news_id: number | null;
  processed_at: string | null;
}

/** 后端评论类型 */
export interface NewsCommentBackend {
  id: number;
  news_id: number;
  user_id: number;
  content: string;
  review_status: string | null;
  review_reason: string | null;
  reviewed_at: string | null;
  created_at: string;
  is_deleted: boolean;
  author: {
    id: number;
    username: string;
    nickname: string | null;
    avatar: string | null;
  } | null;
  news: {
    id: number;
    title: string;
  } | null;
}

/** 后端专题类型 */
export interface NewsTopicBackend {
  id: number;
  title: string;
  description: string | null;
  cover_image: string | null;
  is_active: boolean;
  sort_order: number;
  auto_category: string | null;
  auto_keyword: string | null;
  auto_limit: number;
  created_at: string;
  updated_at: string;
}

/** 后端来源健康状态类型 */
export interface NewsSourceHealthBackend {
  source_id: number;
  recent_total: number;
  recent_failed: number;
  failure_rate: number;
  last_status: string | null;
  last_run_at: string | null;
  last_success_at: string | null;
  last_error: string | null;
  last_error_at: string | null;
}

// ==================== API 响应类型 ====================

/** 分页响应 */
export interface PaginatedResponseBackend<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** 新闻列表响应 */
export type NewsListResponseBackend = PaginatedResponseBackend<NewsArticleBackend>;

/** 抓取记录列表响应 */
export type NewsIngestRunListResponseBackend = PaginatedResponseBackend<NewsIngestRunBackend>;

/** 评论列表响应 */
export type NewsCommentListResponseBackend = PaginatedResponseBackend<NewsCommentBackend>;

/** 来源列表响应 */
export interface NewsSourceListResponseBackend {
  items: NewsSourceBackend[];
}

/** 来源健康状态响应 */
export interface NewsSourceHealthListResponseBackend {
  limit_per_source: number;
  items: NewsSourceHealthBackend[];
}

/** 专题列表响应 */
export interface NewsTopicListResponseBackend {
  items: NewsTopicBackend[];
}

/** 分类统计响应 */
export interface CategoryStatsResponseBackend {
  categories: Array<{
    category: string;
    count: number;
  }>;
}

/** 新闻统计响应 */
export interface NewsStatsResponseBackend {
  stats: {
    total_articles: number;
    published_articles: number;
    pending_review: number;
    rejected_articles: number;
    top_articles: number;
    total_views: number;
    today_views: number;
  };
}
