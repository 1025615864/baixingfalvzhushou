/**
 * News-Admin Query Keys
 * 统一管理 React Query 的缓存键
 */

import type { GetNewsListRequest, GetCommentsRequest, GetIngestRunsRequest } from '../types';

export const NEWS_ADMIN_QUERY_KEYS = {
  all: ['news-admin'] as const,

  // 新闻文章
  articles: {
    all: () => [...NEWS_ADMIN_QUERY_KEYS.all, 'articles'] as const,
    list: (filters: GetNewsListRequest) =>
      [...NEWS_ADMIN_QUERY_KEYS.articles.all(), 'list', filters] as const,
    detail: (id: number) => [...NEWS_ADMIN_QUERY_KEYS.articles.all(), 'detail', id] as const,
  },

  // 新闻评论
  comments: {
    all: () => [...NEWS_ADMIN_QUERY_KEYS.all, 'comments'] as const,
    list: (filters: GetCommentsRequest) =>
      [...NEWS_ADMIN_QUERY_KEYS.comments.all(), 'list', filters] as const,
  },

  // 新闻专题
  topics: {
    all: () => [...NEWS_ADMIN_QUERY_KEYS.all, 'topics'] as const,
    list: () => [...NEWS_ADMIN_QUERY_KEYS.topics.all(), 'list'] as const,
    detail: (id: number) => [...NEWS_ADMIN_QUERY_KEYS.topics.all(), 'detail', id] as const,
    report: () => [...NEWS_ADMIN_QUERY_KEYS.topics.all(), 'report'] as const,
  },

  // 新闻来源
  sources: {
    all: () => [...NEWS_ADMIN_QUERY_KEYS.all, 'sources'] as const,
    list: () => [...NEWS_ADMIN_QUERY_KEYS.sources.all(), 'list'] as const,
    health: () => [...NEWS_ADMIN_QUERY_KEYS.sources.all(), 'health'] as const,
  },

  // 抓取运行记录
  ingestRuns: {
    all: () => [...NEWS_ADMIN_QUERY_KEYS.all, 'ingest-runs'] as const,
    list: (filters: GetIngestRunsRequest) =>
      [...NEWS_ADMIN_QUERY_KEYS.ingestRuns.all(), 'list', filters] as const,
  },

  // 分类统计
  categories: {
    all: () => [...NEWS_ADMIN_QUERY_KEYS.all, 'categories'] as const,
    stats: () => [...NEWS_ADMIN_QUERY_KEYS.categories.all(), 'stats'] as const,
  },

  // 新闻统计
  stats: {
    all: () => [...NEWS_ADMIN_QUERY_KEYS.all, 'stats'] as const,
    overview: () => [...NEWS_ADMIN_QUERY_KEYS.stats.all(), 'overview'] as const,
  },

  // 版本历史
  versions: {
    all: () => [...NEWS_ADMIN_QUERY_KEYS.all, 'versions'] as const,
    list: (newsId: number) => [...NEWS_ADMIN_QUERY_KEYS.versions.all(), 'list', newsId] as const,
  },

  // AI 生成
  aiGenerations: {
    all: () => [...NEWS_ADMIN_QUERY_KEYS.all, 'ai-generations'] as const,
    list: () => [...NEWS_ADMIN_QUERY_KEYS.aiGenerations.all(), 'list'] as const,
  },

  // 定时发布
  scheduled: {
    all: () => [...NEWS_ADMIN_QUERY_KEYS.all, 'scheduled'] as const,
    list: () => [...NEWS_ADMIN_QUERY_KEYS.scheduled.all(), 'list'] as const,
  },
} as const;
