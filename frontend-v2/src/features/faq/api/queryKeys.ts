/**
 * FAQ（常见问题）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * FAQ模块的基础 query key
 */
export const faqKeys = {
  all: ['faq'] as const,

  /** FAQ列表 */
  lists: () => [...faqKeys.all, 'list'] as const,
  list: (params?: { keyword?: string; category?: string; page?: number; pageSize?: number }) =>
    [...faqKeys.lists(), params] as const,

  /** FAQ分类 */
  categories: () => [...faqKeys.all, 'categories'] as const,

  /** 热门FAQ */
  popular: () => [...faqKeys.all, 'popular'] as const,
  popularByCategory: (category?: string, limit?: number) =>
    [...faqKeys.popular(), { category, limit }] as const,

  /** FAQ详情 */
  detail: (id: number) => [...faqKeys.all, 'detail', id] as const,

  /** FAQ智能搜索 */
  smartSearch: () => [...faqKeys.all, 'smart-search'] as const,

  /** 管理员FAQ列表 */
  adminLists: () => [...faqKeys.all, 'admin-list'] as const,
  adminList: (params?: { keyword?: string; category?: string; page?: number; pageSize?: number }) =>
    [...faqKeys.adminLists(), params] as const,
} as const;

export default faqKeys;