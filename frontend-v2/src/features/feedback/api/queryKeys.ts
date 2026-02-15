/**
 * Feedback（用户反馈）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 反馈模块的基础 query key
 */
export const feedbackKeys = {
  all: ['feedback'] as const,

  /** 反馈列表 */
  lists: () => [...feedbackKeys.all, 'list'] as const,
  list: (params?: { page?: number; pageSize?: number; status?: string; keyword?: string }) =>
    [...feedbackKeys.lists(), params] as const,

  /** 我的反馈列表 */
  myLists: () => [...feedbackKeys.all, 'my-list'] as const,
  myList: (params?: { page?: number; pageSize?: number }) =>
    [...feedbackKeys.myLists(), params] as const,

  /** 我的反馈列表（兼容旧代码） */
  myListPaginated: (page?: number, pageSize?: number) =>
    [...feedbackKeys.myLists(), { page, pageSize }] as const,

  /** 管理员反馈列表（兼容旧代码） */
  adminList: () => [...feedbackKeys.all, 'admin-list'] as const,
  adminListPaginated: (page?: number, pageSize?: number, status?: string, keyword?: string) =>
    [...feedbackKeys.adminList(), { page, pageSize, status, keyword }] as const,

  /** 反馈统计（管理员） */
  stats: () => [...feedbackKeys.all, 'stats'] as const,

  /** 反馈详情 */
  detail: (ticketId: number) => [...feedbackKeys.all, 'detail', ticketId] as const,
} as const;

export default feedbackKeys;