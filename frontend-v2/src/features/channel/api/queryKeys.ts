/**
 * Channel（渠道管理）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 渠道模块的基础 query key
 */
export const channelKeys = {
  all: ['channels'] as const,
  
  /** 渠道列表 */
  lists: () => [...channelKeys.all, 'list'] as const,
  list: (filters: { status?: string; type?: string; page?: number; pageSize?: number } = {}) => 
    [...channelKeys.lists(), filters] as const,
  
  /** 单个渠道详情 */
  details: () => [...channelKeys.all, 'detail'] as const,
  detail: (channelId: string | number) => [...channelKeys.details(), channelId] as const,
  
  /** 通过 code 获取渠道 */
  byCode: (code: string) => [...channelKeys.all, 'by-code', code] as const,
  
  /** 渠道分析数据 */
  analytics: () => [...channelKeys.all, 'analytics'] as const,
  analyticsList: (filters: { channelIds?: string[]; startDate?: string; endDate?: string } = {}) => 
    [...channelKeys.analytics(), 'list', filters] as const,
  analyticsDetail: (channelId: string | number, filters: { startDate?: string; endDate?: string } = {}) => 
    [...channelKeys.analytics(), 'detail', channelId, filters] as const,
  
  /** 渠道对比 */
  comparison: (channelIds: string[], filters: { startDate?: string; endDate?: string } = {}) => 
    [...channelKeys.analytics(), 'compare', channelIds, filters] as const,
  
  /** 渠道统计汇总 */
  stats: () => [...channelKeys.all, 'stats'] as const,
} as const;

export default channelKeys;