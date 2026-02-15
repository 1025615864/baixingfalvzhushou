/**
 * React Query Keys 统一管理
 * 按照功能模块组织，便于缓存管理和失效
 */

export const queryKeys = {
  // ==================== 用户相关 ====================
  user: {
    me: ['user', 'me'] as const,
    quotas: ['user', 'quotas'] as const,
    profile: (userId: string) => ['user', 'profile', userId] as const,
  },

  // ==================== AI 相关 ====================
  ai: {
    sessions: ['ai', 'sessions'] as const,
    session: (id: string) => ['ai', 'sessions', id] as const,
    history: (sessionId: string) => ['ai', 'history', sessionId] as const,
    analysis: (id: string) => ['ai', 'analysis', id] as const,
  },

  // ==================== 企业服务相关 ====================
  enterprise: {
    info: (accountId: number) => ['enterprise', 'info', accountId] as const,
    members: (accountId: number, params?: object) => 
      ['enterprise', 'members', accountId, params] as const,
    orders: (accountId: number, params?: object) => 
      ['enterprise', 'orders', accountId, params] as const,
    contracts: (accountId: number) => ['enterprise', 'contracts', accountId] as const,
    templates: (category?: string) => ['enterprise', 'templates', category] as const,
    permissions: ['enterprise', 'permissions'] as const,
    rolePermissions: (accountId: number) => ['enterprise', 'role-permissions', accountId] as const,
  },

  // ==================== 律师相关 ====================
  lawyers: {
    list: (params?: object) => ['lawyers', 'list', params] as const,
    detail: (id: string) => ['lawyers', 'detail', id] as const,
    reviews: (id: string, params?: object) => ['lawyers', 'reviews', id, params] as const,
    schedules: (id: string) => ['lawyers', 'schedules', id] as const,
    recommendations: (query: string, criteria?: object) => 
      ['lawyers', 'recommendations', query, criteria] as const,
    search: (params: object) => ['lawyers', 'search', params] as const,
    onlineStatus: (ids: string[]) => ['lawyers', 'online-status', ids] as const,
  },

  // ==================== 预约相关 ====================
  bookings: {
    list: (params?: object) => ['bookings', 'list', params] as const,
    detail: (id: string) => ['bookings', 'detail', id] as const,
  },

  // ==================== 论坛相关 ====================
  forum: {
    posts: (params?: object) => ['forum', 'posts', params] as const,
    post: (id: string) => ['forum', 'posts', id] as const,
    comments: (postId: string) => ['forum', 'comments', postId] as const,
    favorites: ['forum', 'favorites'] as const,
    invitations: (postId?: string) => ['forum', 'invitations', postId] as const,
  },

  // ==================== 新闻相关 ====================
  news: {
    list: (params?: object) => ['news', 'list', params] as const,
    detail: (id: string) => ['news', 'detail', id] as const,
    comments: (newsId: string) => ['news', 'comments', newsId] as const,
    subscriptions: ['news', 'subscriptions'] as const,
    topics: ['news', 'topics'] as const,
  },

  // ==================== 积分相关 ====================
  points: {
    balance: ['points', 'balance'] as const,
    transactions: ['points', 'transactions'] as const,
    products: ['points', 'products'] as const,
    tasks: ['points', 'tasks'] as const,
  },

  // ==================== 渠道相关 ====================
  channels: {
    list: ['channels'] as const,
    detail: (id: string) => ['channels', id] as const,
    analytics: (id?: string) => ['channels', 'analytics', id] as const,
    stats: ['channels', 'stats'] as const,
  },

  // ==================== 数据分析相关 ====================
  analytics: {
    dashboard: ['analytics', 'dashboard'] as const,
    metrics: ['analytics', 'metrics'] as const,
    revenue: (params?: object) => ['analytics', 'revenue', params] as const,
    funnel: (params?: object) => ['analytics', 'funnel', params] as const,
    retention: (params?: object) => ['analytics', 'retention', params] as const,
    behavior: (params?: object) => ['analytics', 'behavior', params] as const,
  },

  // ==================== 支付相关 ====================
  payment: {
    orders: ['payment', 'orders'] as const,
    order: (id: string) => ['payment', 'orders', id] as const,
    cards: ['payment', 'cards'] as const,
  },

  // ==================== 结算相关 ====================
  settlement: {
    wallet: ['settlement', 'wallet'] as const,
    income: (params?: object) => ['settlement', 'income', params] as const,
    withdrawals: ['settlement', 'withdrawals'] as const,
  },

  // ==================== 通知相关 ====================
  notifications: {
    list: ['notifications', 'list'] as const,
    unread: ['notifications', 'unread'] as const,
    preferences: ['notifications', 'preferences'] as const,
  },

  // ==================== 搜索相关 ====================
  search: {
    suggestions: (query: string) => ['search', 'suggestions', query] as const,
    results: (params: object) => ['search', 'results', params] as const,
    history: ['search', 'history'] as const,
  },

  // ==================== 知识库相关 ====================
  knowledge: {
    categories: ['knowledge', 'categories'] as const,
    articles: (params?: object) => ['knowledge', 'articles', params] as const,
    article: (id: string) => ['knowledge', 'articles', id] as const,
  },

  // ==================== 合同相关 ====================
  contracts: {
    templates: ['contracts', 'templates'] as const,
    reviews: ['contracts', 'reviews'] as const,
    history: (contractId: string) => ['contracts', 'history', contractId] as const,
  },

  // ==================== 会员相关 ====================
  membership: {
    plans: ['membership', 'plans'] as const,
    current: ['membersship', 'current'] as const,
    benefits: ['membership', 'benefits'] as const,
  },
} as const;

export default queryKeys;