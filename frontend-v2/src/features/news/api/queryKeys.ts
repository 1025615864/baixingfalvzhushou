/**
 * News（新闻资讯）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 新闻资讯模块的基础 query key
 */
export const newsKeys = {
  all: ['news'] as const,

  /** 新闻列表 */
  lists: () => [...newsKeys.all, 'list'] as const,
  list: (filters: {
    page?: number;
    pageSize?: number;
    categoryId?: string;
    keyword?: string;
    source?: string;
    sortBy?: 'newest' | 'hottest' | 'relevant';
  } = {}) => [...newsKeys.lists(), filters] as const,

  /** 单个新闻详情 */
  details: () => [...newsKeys.all, 'detail'] as const,
  detail: (newsId: string) => [...newsKeys.details(), newsId] as const,

  /** 推荐新闻 */
  recommended: (filters: {
    page?: number;
    pageSize?: number;
  } = {}) => [...newsKeys.all, 'recommended', filters] as const,

  /** 热门新闻 */
  hot: (filters: {
    page?: number;
    pageSize?: number;
    period?: 'day' | 'week' | 'month';
  } = {}) => [...newsKeys.all, 'hot', filters] as const,

  /** 置顶新闻 */
  top: () => [...newsKeys.all, 'top'] as const,

  /** 相关新闻 */
  related: (newsId: string) => [...newsKeys.all, 'related', newsId] as const,

  /** 新闻评论 */
  comments: (newsId: string) => [...newsKeys.all, 'comments', newsId] as const,

  /** 分类列表 */
  categories: () => [...newsKeys.all, 'categories'] as const,

  /** 用户订阅 */
  subscriptions: () => [...newsKeys.all, 'subscriptions'] as const,

  /** 用户收藏 */
  favorites: () => [...newsKeys.all, 'favorites'] as const,

  /** 搜索结果 */
  search: (filters: {
    keyword: string;
    page?: number;
    pageSize?: number;
    categoryId?: string;
  }) => [...newsKeys.all, 'search', filters] as const,
} as const;

export default newsKeys;