/**
 * Points（积分系统）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 积分模块的基础 query key
 */
export const pointsKeys = {
  all: ['points'] as const,
  
  /** 积分余额 */
  balance: () => [...pointsKeys.all, 'balance'] as const,
  
  /** 积分历史 */
  history: () => [...pointsKeys.all, 'history'] as const,
  historyList: (filters: { limit?: number; offset?: number; actionTypes?: string[]; startDate?: string; endDate?: string } = {}) => 
    [...pointsKeys.history(), filters] as const,
  
  /** 积分商品 */
  products: () => [...pointsKeys.all, 'products'] as const,
  productList: (productType?: string) => 
    [...pointsKeys.products(), 'list', productType] as const,
  productDetail: (productId: string) => 
    [...pointsKeys.products(), 'detail', productId] as const,
  
  /** 每日统计 */
  dailyStats: () => [...pointsKeys.all, 'daily-stats'] as const,
  
  /** 积分规则 */
  rules: () => [...pointsKeys.all, 'rules'] as const,
  
  /** 排行榜 */
  leaderboard: (topK?: number) => 
    [...pointsKeys.all, 'leaderboard', topK] as const,
  
  /** 兑换订单 */
  orders: () => [...pointsKeys.all, 'orders'] as const,
  orderList: (status?: string, limit?: number) => 
    [...pointsKeys.orders(), 'list', status, limit] as const,
  
  /** 签到状态 */
  checkIn: () => [...pointsKeys.all, 'check-in'] as const,
} as const;

export default pointsKeys;