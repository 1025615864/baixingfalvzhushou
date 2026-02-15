/**
 * Lawyer-Matching（律师匹配）模块 Query Keys
 * 用于 React Query 的缓存管理
 */

export const lawyerMatchingKeys = {
  // 所有律师匹配相关查询的根key
  all: ['lawyer-matching'] as const,

  // 推荐律师相关
  recommendations: () => [...lawyerMatchingKeys.all, 'recommendations'] as const,
  recommendationsByQuery: (query: string) =>
    [...lawyerMatchingKeys.recommendations(), 'query', query] as const,
  recommendationsByKeywords: (keywords: string[], domains: string[]) =>
    [...lawyerMatchingKeys.recommendations(), 'keywords', keywords, domains] as const,

  // 律师列表相关
  lawyers: () => [...lawyerMatchingKeys.all, 'lawyers'] as const,
  lawyerList: (filters: Record<string, unknown>) =>
    [...lawyerMatchingKeys.lawyers(), 'list', filters] as const,
  lawyerDetail: (lawyerId: string) =>
    [...lawyerMatchingKeys.lawyers(), 'detail', lawyerId] as const,
  lawyerSearch: (query: string, filters: Record<string, unknown>) =>
    [...lawyerMatchingKeys.lawyers(), 'search', query, filters] as const,

  // 律师可用时段
  lawyerSlots: (lawyerId: string, date: string) =>
    [...lawyerMatchingKeys.lawyers(), 'slots', lawyerId, date] as const,

  // 律师在线状态
  onlineStatus: () => [...lawyerMatchingKeys.all, 'online-status'] as const,
  onlineStatusByIds: (lawyerIds: string[]) =>
    [...lawyerMatchingKeys.onlineStatus(), 'batch', lawyerIds] as const,
  onlineStatusById: (lawyerId: string) =>
    [...lawyerMatchingKeys.onlineStatus(), 'single', lawyerId] as const,

  // 预约/咨询相关
  bookings: () => [...lawyerMatchingKeys.all, 'bookings'] as const,
  bookingList: (status?: string) =>
    [...lawyerMatchingKeys.bookings(), 'list', status] as const,
  bookingDetail: (bookingId: string) =>
    [...lawyerMatchingKeys.bookings(), 'detail', bookingId] as const,

  // 评价相关
  reviews: () => [...lawyerMatchingKeys.all, 'reviews'] as const,
  reviewList: (lawyerId: string, filters?: Record<string, unknown>) =>
    [...lawyerMatchingKeys.reviews(), 'list', lawyerId, filters] as const,
  reviewStats: (lawyerId: string) =>
    [...lawyerMatchingKeys.reviews(), 'stats', lawyerId] as const,
} as const;

// 导出默认对象便于使用
export default lawyerMatchingKeys;