/**
 * React Query 缓存工具函数
 * 提供统一的缓存时间常量、缓存键生成器和缓存失效策略
 */

import { queryClient } from './query-client';

// ============================================================
// 缓存时间常量
// ============================================================

/**
 * 缓存时间常量
 * 根据数据更新频率选择合适的缓存时间
 */
export const CACHE_TIMES = {
  /** 短缓存：1分钟 - 适用于频繁变化的数据（如实时状态、在线状态） */
  SHORT: 1 * 60 * 1000,
  /** 中等缓存：5分钟 - 适用于常规数据（如列表、详情） */
  MEDIUM: 5 * 60 * 1000,
  /** 长缓存：30分钟 - 适用于相对稳定的数据（如配置、分类） */
  LONG: 30 * 60 * 1000,
  /** 超长缓存：1小时 - 适用于很少变化的数据（如静态内容、法律条文） */
  VERY_LONG: 60 * 60 * 1000,
} as const;

// ============================================================
// 缓存键生成器
// ============================================================

/**
 * 缓存键生成器
 * 提供类型安全的缓存键生成方法
 */
export const createCacheKeys = {
  // 用户相关
  user: {
    profile: (userId: number) => ['user', 'profile', userId] as const,
    settings: (userId: number) => ['user', 'settings', userId] as const,
    list: (params?: Record<string, unknown>) => ['user', 'list', params] as const,
  },

  // 会员相关
  membership: {
    current: () => ['membership', 'current'] as const,
    plans: () => ['membership', 'plans'] as const,
    history: (userId: number) => ['membership', 'history', userId] as const,
  },

  // 视频咨询相关
  videoConsultation: {
    detail: (id: number) => ['videoConsultation', 'detail', id] as const,
    list: (params?: Record<string, unknown>) => ['videoConsultation', 'list', params] as const,
    schedule: (lawyerId: number) => ['videoConsultation', 'schedule', lawyerId] as const,
  },

  // 法律文档相关
  legalDocument: {
    detail: (id: number) => ['legalDocument', 'detail', id] as const,
    list: (params?: Record<string, unknown>) => ['legalDocument', 'list', params] as const,
    categories: () => ['legalDocument', 'categories'] as const,
  },

  // 咨询相关
  consultation: {
    detail: (id: number) => ['consultation', 'detail', id] as const,
    list: (params?: Record<string, unknown>) => ['consultation', 'list', params] as const,
    history: (userId: number) => ['consultation', 'history', userId] as const,
  },

  // 合同相关
  contract: {
    detail: (id: number) => ['contract', 'detail', id] as const,
    list: (params?: Record<string, unknown>) => ['contract', 'list', params] as const,
    templates: () => ['contract', 'templates'] as const,
  },

  // 知识库相关
  knowledge: {
    detail: (id: number) => ['knowledge', 'detail', id] as const,
    list: (params?: Record<string, unknown>) => ['knowledge', 'list', params] as const,
    categories: () => ['knowledge', 'categories'] as const,
    search: (query: string) => ['knowledge', 'search', query] as const,
  },

  // 律师相关
  lawyer: {
    detail: (id: number) => ['lawyer', 'detail', id] as const,
    list: (params?: Record<string, unknown>) => ['lawyer', 'list', params] as const,
    schedule: (lawyerId: number) => ['lawyer', 'schedule', lawyerId] as const,
    reviews: (lawyerId: number) => ['lawyer', 'reviews', lawyerId] as const,
  },

  // 积分相关
  points: {
    balance: () => ['points', 'balance'] as const,
    history: (params?: Record<string, unknown>) => ['points', 'history', params] as const,
    tasks: () => ['points', 'tasks'] as const,
    products: (params?: Record<string, unknown>) => ['points', 'products', params] as const,
  },

  // 订单相关
  order: {
    detail: (id: string) => ['order', 'detail', id] as const,
    list: (params?: Record<string, unknown>) => ['order', 'list', params] as const,
  },

  // 通知相关
  notification: {
    list: (params?: Record<string, unknown>) => ['notification', 'list', params] as const,
    unreadCount: () => ['notification', 'unreadCount'] as const,
    settings: () => ['notification', 'settings'] as const,
  },

  // 论坛相关
  forum: {
    posts: (params?: Record<string, unknown>) => ['forum', 'posts', params] as const,
    postDetail: (id: number) => ['forum', 'post', id] as const,
    comments: (postId: number) => ['forum', 'comments', postId] as const,
    favorites: (userId: number) => ['forum', 'favorites', userId] as const,
  },

  // 新闻相关
  news: {
    list: (params?: Record<string, unknown>) => ['news', 'list', params] as const,
    detail: (id: number) => ['news', 'detail', id] as const,
    topics: () => ['news', 'topics'] as const,
  },

  // 搜索相关
  search: {
    results: (query: string, params?: Record<string, unknown>) => ['search', 'results', query, params] as const,
    suggestions: (query: string) => ['search', 'suggestions', query] as const,
    history: () => ['search', 'history'] as const,
  },

  // 推广相关
  promotion: {
    stats: (promotionId: string) => ['promotion', 'stats', promotionId] as const,
    links: (userId: number) => ['promotion', 'links', userId] as const,
    commissions: (userId: number) => ['promotion', 'commissions', userId] as const,
  },
} as const;

// ============================================================
// 缓存失效策略
// ============================================================

/**
 * 缓存失效策略
 * 在变更操作后使相关缓存失效
 */
export const invalidateOnMutation = {
  // 用户相关
  user: {
    all: () => queryClient.invalidateQueries({ queryKey: ['user'] }),
    profile: (userId: number) => queryClient.invalidateQueries({ queryKey: ['user', 'profile', userId] }),
    settings: (userId: number) => queryClient.invalidateQueries({ queryKey: ['user', 'settings', userId] }),
    list: () => queryClient.invalidateQueries({ queryKey: ['user', 'list'] }),
  },

  // 会员相关
  membership: {
    all: () => queryClient.invalidateQueries({ queryKey: ['membership'] }),
    current: () => queryClient.invalidateQueries({ queryKey: ['membership', 'current'] }),
    plans: () => queryClient.invalidateQueries({ queryKey: ['membership', 'plans'] }),
  },

  // 视频咨询相关
  videoConsultation: {
    all: () => queryClient.invalidateQueries({ queryKey: ['videoConsultation'] }),
    detail: (id: number) => queryClient.invalidateQueries({ queryKey: ['videoConsultation', 'detail', id] }),
    list: () => queryClient.invalidateQueries({ queryKey: ['videoConsultation', 'list'] }),
    schedule: (lawyerId: number) => queryClient.invalidateQueries({ queryKey: ['videoConsultation', 'schedule', lawyerId] }),
  },

  // 法律文档相关
  legalDocument: {
    all: () => queryClient.invalidateQueries({ queryKey: ['legalDocument'] }),
    detail: (id: number) => queryClient.invalidateQueries({ queryKey: ['legalDocument', 'detail', id] }),
    list: () => queryClient.invalidateQueries({ queryKey: ['legalDocument', 'list'] }),
  },

  // 咨询相关
  consultation: {
    all: () => queryClient.invalidateQueries({ queryKey: ['consultation'] }),
    detail: (id: number) => queryClient.invalidateQueries({ queryKey: ['consultation', 'detail', id] }),
    list: () => queryClient.invalidateQueries({ queryKey: ['consultation', 'list'] }),
    history: (userId: number) => queryClient.invalidateQueries({ queryKey: ['consultation', 'history', userId] }),
  },

  // 合同相关
  contract: {
    all: () => queryClient.invalidateQueries({ queryKey: ['contract'] }),
    detail: (id: number) => queryClient.invalidateQueries({ queryKey: ['contract', 'detail', id] }),
    list: () => queryClient.invalidateQueries({ queryKey: ['contract', 'list'] }),
  },

  // 知识库相关
  knowledge: {
    all: () => queryClient.invalidateQueries({ queryKey: ['knowledge'] }),
    detail: (id: number) => queryClient.invalidateQueries({ queryKey: ['knowledge', 'detail', id] }),
    list: () => queryClient.invalidateQueries({ queryKey: ['knowledge', 'list'] }),
    categories: () => queryClient.invalidateQueries({ queryKey: ['knowledge', 'categories'] }),
  },

  // 律师相关
  lawyer: {
    all: () => queryClient.invalidateQueries({ queryKey: ['lawyer'] }),
    detail: (id: number) => queryClient.invalidateQueries({ queryKey: ['lawyer', 'detail', id] }),
    list: () => queryClient.invalidateQueries({ queryKey: ['lawyer', 'list'] }),
    reviews: (lawyerId: number) => queryClient.invalidateQueries({ queryKey: ['lawyer', 'reviews', lawyerId] }),
  },

  // 积分相关
  points: {
    all: () => queryClient.invalidateQueries({ queryKey: ['points'] }),
    balance: () => queryClient.invalidateQueries({ queryKey: ['points', 'balance'] }),
    history: () => queryClient.invalidateQueries({ queryKey: ['points', 'history'] }),
    tasks: () => queryClient.invalidateQueries({ queryKey: ['points', 'tasks'] }),
  },

  // 订单相关
  order: {
    all: () => queryClient.invalidateQueries({ queryKey: ['order'] }),
    detail: (id: string) => queryClient.invalidateQueries({ queryKey: ['order', 'detail', id] }),
    list: () => queryClient.invalidateQueries({ queryKey: ['order', 'list'] }),
  },

  // 通知相关
  notification: {
    all: () => queryClient.invalidateQueries({ queryKey: ['notification'] }),
    list: () => queryClient.invalidateQueries({ queryKey: ['notification', 'list'] }),
    unreadCount: () => queryClient.invalidateQueries({ queryKey: ['notification', 'unreadCount'] }),
    settings: () => queryClient.invalidateQueries({ queryKey: ['notification', 'settings'] }),
  },

  // 论坛相关
  forum: {
    all: () => queryClient.invalidateQueries({ queryKey: ['forum'] }),
    posts: () => queryClient.invalidateQueries({ queryKey: ['forum', 'posts'] }),
    postDetail: (id: number) => queryClient.invalidateQueries({ queryKey: ['forum', 'post', id] }),
    comments: (postId: number) => queryClient.invalidateQueries({ queryKey: ['forum', 'comments', postId] }),
    favorites: (userId: number) => queryClient.invalidateQueries({ queryKey: ['forum', 'favorites', userId] }),
  },

  // 新闻相关
  news: {
    all: () => queryClient.invalidateQueries({ queryKey: ['news'] }),
    list: () => queryClient.invalidateQueries({ queryKey: ['news', 'list'] }),
    detail: (id: number) => queryClient.invalidateQueries({ queryKey: ['news', 'detail', id] }),
  },

  // 搜索相关
  search: {
    all: () => queryClient.invalidateQueries({ queryKey: ['search'] }),
    history: () => queryClient.invalidateQueries({ queryKey: ['search', 'history'] }),
  },

  // 推广相关
  promotion: {
    all: () => queryClient.invalidateQueries({ queryKey: ['promotion'] }),
    stats: (promotionId: string) => queryClient.invalidateQueries({ queryKey: ['promotion', 'stats', promotionId] }),
    links: (userId: number) => queryClient.invalidateQueries({ queryKey: ['promotion', 'links', userId] }),
    commissions: (userId: number) => queryClient.invalidateQueries({ queryKey: ['promotion', 'commissions', userId] }),
  },
} as const;

// ============================================================
// 缓存操作工具
// ============================================================

/**
 * 缓存操作工具函数
 */
export const cacheUtils = {
  /**
   * 设置缓存数据
   */
  setQueryData: <T>(queryKey: readonly unknown[], data: T) => {
    queryClient.setQueryData(queryKey, data);
  },

  /**
   * 获取缓存数据
   */
  getQueryData: <T>(queryKey: readonly unknown[]): T | undefined => {
    return queryClient.getQueryData<T>(queryKey);
  },

  /**
   * 移除指定缓存
   */
  removeQuery: (queryKey: readonly unknown[]) => {
    queryClient.removeQueries({ queryKey });
  },

  /**
   * 重置指定缓存
   */
  resetQuery: (queryKey: readonly unknown[]) => {
    void queryClient.resetQueries({ queryKey });
  },

  /**
   * 取消正在进行的请求
   */
  cancelQuery: async (queryKey: readonly unknown[]) => {
    await queryClient.cancelQueries({ queryKey });
  },

  /**
   * 清除所有缓存
   */
  clearAll: () => {
    queryClient.clear();
  },
};

// ============================================================
// 类型导出
// ============================================================

export type CacheTimeKey = keyof typeof CACHE_TIMES;
export type CacheKeys = typeof createCacheKeys;