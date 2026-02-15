/**
 * Order（订单管理）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 订单模块的基础 query key
 */
export const orderKeys = {
  all: ['orders'] as const,

  /** 订单列表 */
  lists: () => [...orderKeys.all, 'list'] as const,
  list: (filters: { status?: string; page?: number; pageSize?: number } = {}) =>
    [...orderKeys.lists(), filters] as const,

  /** 单个订单详情 */
  details: () => [...orderKeys.all, 'detail'] as const,
  detail: (orderNo: string) => [...orderKeys.details(), orderNo] as const,

  /** 订单统计 */
  stats: () => [...orderKeys.all, 'stats'] as const,
} as const;

export default orderKeys;