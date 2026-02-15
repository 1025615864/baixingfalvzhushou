/**
 * Calendar（法律日历）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 日历模块的基础 query key
 */
export const calendarKeys = {
  all: ['calendar'] as const,
  
  /** 提醒列表 */
  lists: () => [...calendarKeys.all, 'reminders', 'list'] as const,
  list: (filters: { done?: boolean | null; fromAt?: string; toAt?: string; page?: number; pageSize?: number } = {}) => 
    [...calendarKeys.lists(), filters] as const,
  /** 别名：提醒列表 */
  remindersList: (filters: { done?: boolean | null; fromAt?: string; toAt?: string; page?: number; pageSize?: number } = {}) => 
    [...calendarKeys.lists(), filters] as const,
  
  /** 单个提醒详情 */
  details: () => [...calendarKeys.all, 'reminders', 'detail'] as const,
  detail: (reminderId: number) => [...calendarKeys.details(), reminderId] as const,
  /** 别名：单个提醒 */
  reminder: (reminderId: number) => [...calendarKeys.details(), reminderId] as const,
  
  /** 按日期范围查询 */
  byDateRange: (fromAt: string, toAt: string) => 
    [...calendarKeys.all, 'reminders', 'by-date', { fromAt, toAt }] as const,
  /** 别名：按日期范围查询 */
  remindersByDate: (params: { fromAt: string; toAt: string }) => 
    [...calendarKeys.all, 'reminders', 'by-date', params] as const,
  
  /** 已完成提醒 */
  completed: () => [...calendarKeys.all, 'reminders', 'completed'] as const,
  
  /** 待处理提醒 */
  pending: () => [...calendarKeys.all, 'reminders', 'pending'] as const,
  
  /** 所有提醒（用于invalidate） */
  reminders: () => [...calendarKeys.all, 'reminders'] as const,
} as const;

export default calendarKeys;