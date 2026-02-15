/**
 * Consultation（咨询预约）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 咨询模块的基础 query key
 */
export const consultationKeys = {
  all: ['consultations'] as const,
  
  /** 咨询列表 */
  lists: () => [...consultationKeys.all, 'list'] as const,
  list: (filters: { status?: string; page?: number; pageSize?: number } = {}) => 
    [...consultationKeys.lists(), filters] as const,
  
  /** 单个咨询详情 */
  details: () => [...consultationKeys.all, 'detail'] as const,
  detail: (consultationId: string | number) => [...consultationKeys.details(), consultationId] as const,
  
  /** 咨询消息 */
  messages: (consultationId: string | number) => 
    [...consultationKeys.detail(consultationId), 'messages'] as const,
  
  /** 待处理咨询 */
  pending: () => [...consultationKeys.all, 'pending'] as const,
  
  /** 已完成咨询 */
  completed: () => [...consultationKeys.all, 'completed'] as const,
  
  /** 按状态筛选 */
  byStatus: (status: string) => [...consultationKeys.all, 'by-status', status] as const,
} as const;

export default consultationKeys;