/**
 * Contract（合同审查）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 合同审查模块的基础 query key
 */
export const contractKeys = {
  all: ['contracts'] as const,

  /** 审查历史列表 */
  lists: () => [...contractKeys.all, 'list'] as const,
  list: (filters: {
    page?: number;
    pageSize?: number;
  } = {}) => [...contractKeys.lists(), filters] as const,

  /** 单个审查详情 */
  details: () => [...contractKeys.all, 'detail'] as const,
  detail: (reviewId: string) => [...contractKeys.details(), reviewId] as const,

  /** 比对结果 */
  comparison: () => [...contractKeys.all, 'comparison'] as const,

  /** 导出报告 */
  export: () => [...contractKeys.all, 'export'] as const,
} as const;

export default contractKeys;