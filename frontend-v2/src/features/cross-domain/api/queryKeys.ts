/**
 * Cross-Domain（跨域功能）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 跨域模块的基础 query key
 */
export const crossDomainKeys = {
  all: ['cross-domain'] as const,

  /** 域名列表 */
  lists: () => [...crossDomainKeys.all, 'list'] as const,
  list: (params?: { status?: string; search?: string; limit?: number; offset?: number }) =>
    [...crossDomainKeys.lists(), params] as const,

  /** 域名详情 */
  detail: (domainId: number) => [...crossDomainKeys.all, 'detail', domainId] as const,

  /** 跨域规则 */
  rules: (domainId: number) => [...crossDomainKeys.all, 'rules', domainId] as const,

  /** 域名验证状态 */
  verification: (domainId: number) => [...crossDomainKeys.all, 'verification', domainId] as const,
} as const;

export default crossDomainKeys;