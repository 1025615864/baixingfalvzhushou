/**
 * User（用户管理）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 用户模块的基础 query key
 */
export const userKeys = {
  all: ['user'] as const,

  /** 当前用户信息 */
  me: () => [...userKeys.all, 'me'] as const,

  /** 用户配额 */
  quotas: () => [...userKeys.all, 'quotas'] as const,
  quotaUsage: (days?: number) => [...userKeys.quotas(), 'usage', days] as const,

  /** 用户统计数据 */
  stats: () => [...userKeys.all, 'stats'] as const,

  /** 用户详情 */
  detail: (userId: string) => [...userKeys.all, 'detail', userId] as const,

  /** 邮箱验证状态 */
  emailVerification: () => [...userKeys.all, 'email-verification'] as const,

  /** 用户列表（管理员） */
  list: () => [...userKeys.all, 'list'] as const,
  userList: (page?: number, pageSize?: number, keyword?: string) =>
    [...userKeys.list(), { page, pageSize, keyword }] as const,

  /** 活跃Token */
  activeTokens: () => [...userKeys.all, 'active-tokens'] as const,
} as const;

export default userKeys;