// ============================================
// API 配置 - 适配微服务架构 v2
// ============================================

import { ServiceDiscovery } from './serviceDiscovery';

// API 版本
export const API_VERSION = 'v1';
export const API_BASE = `/api/${API_VERSION}`;

// 服务发现
function getServiceUrl(name: string, defaultPort: number): string {
  const envUrl = import.meta.env[`VITE_SERVICE_${name.toUpperCase()}`];
  if (envUrl) return envUrl;
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost';
  return `${base}:${defaultPort}`;
}

export const services = new ServiceDiscovery({
  auth: getServiceUrl('auth', 8000),
  user: getServiceUrl('user', 8000),
  payment: getServiceUrl('payment', 8000),
  accounting: getServiceUrl('accounting', 8000),
  legal: getServiceUrl('legal', 8000),
  ai: getServiceUrl('ai', 8005),
  news: getServiceUrl('news', 8000),
  community: getServiceUrl('community', 8000),
  points: getServiceUrl('points', 8000),
  notification: getServiceUrl('notification', 8000),
  recommendation: getServiceUrl('recommendation', 8000),
  search: getServiceUrl('search', 8000),
});

// API 基础配置
export const API_CONFIG = {
  baseURL: API_BASE,
  timeout: 30000,
  retry: 3,
  retryDelay: 1000,
};

// 请求头配置
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};

// ============================================
// API 端点配置 - 与后端 services 匹配
// ============================================
export const ENDPOINTS = {
  // ==================== 认证服务 (8001) ====================
  auth: {
    login: `${API_BASE}/auth/login`,
    register: `${API_BASE}/auth/register`,
    refresh: `${API_BASE}/auth/refresh`,
    logout: `${API_BASE}/auth/logout`,
    me: `${API_BASE}/users/me`,
  },

  // ==================== 用户服务 (8001) ====================
  user: {
    profile: `${API_BASE}/users/me`,
    updateProfile: `${API_BASE}/users/me`,
    changePassword: `${API_BASE}/users/me/password`,
    quotas: `${API_BASE}/users/me/quotas`,
    avatar: `${API_BASE}/users/me/avatar`,
    stats: `${API_BASE}/users/me/stats`,
    membership: `${API_BASE}/membership/current`,
    list: `${API_BASE}/users`,
    admin: {
      list: `${API_BASE}/users`,
      toggleActive: (id: number) => `${API_BASE}/users/${id}/toggle-active`,
      updateRole: (id: number) => `${API_BASE}/users/${id}/role`,
    },
  },

  // ==================== 支付通道服务 (8002) ====================
  payment: {
    orders: `${API_BASE}/payment/orders`,
    order: (id: string) => `${API_BASE}/payment/orders/${id}`,
    pay: (id: string) => `${API_BASE}/payment/orders/${id}/pay`,
    createOrder: `${API_BASE}/payment/orders`,
    refund: `${API_BASE}/payment/refunds`,
    refundStatus: (id: string) => `${API_BASE}/payment/refunds/${id}`,
    balance: `${API_BASE}/balance`,
    balanceHistory: `${API_BASE}/balance/history`,
    wallet: `${API_BASE}/settlement/wallet`,
    withdraw: `${API_BASE}/settlement/withdraw`,
    settlementRecords: `${API_BASE}/settlement/records`,
  },

  // ==================== 法律服务 (8004) ====================
  legal: {
    consultations: `${API_BASE}/legal/consultations`,
    consultation: (id: string) => `${API_BASE}/legal/consultations/${id}`,
    consultationMessages: (id: string) => `${API_BASE}/legal/consultations/${id}/messages`,
    lawyers: `${API_BASE}/legal/lawyers`,
    lawyer: (id: string) => `${API_BASE}/legal/lawyers/${id}`,
    lawyerVerify: (id: string) => `${API_BASE}/legal/lawyers/${id}/verify`,
    firms: `${API_BASE}/legal/firms`,
    firm: (id: string) => `${API_BASE}/legal/firms/${id}`,
    appointments: `${API_BASE}/legal/appointments`,
    contracts: {
      review: `${API_BASE}/legal/contracts/review`,
    },
    documents: {
      templates: `${API_BASE}/legal/documents/templates`,
      generate: `${API_BASE}/legal/documents/generate`,
    },
    knowledge: `${API_BASE}/legal/knowledge`,
    knowledgeDetail: (id: string) => `${API_BASE}/legal/knowledge/${id}`,
  },

  // ==================== AI服务 (8005) ====================
  ai: {
    chat: `${API_BASE}/ai/chat`,
    sessions: `${API_BASE}/ai/sessions`,
    session: (id: string) => `${API_BASE}/ai/sessions/${id}`,
    sessionHistory: (id: string) => `${API_BASE}/ai/sessions/${id}/history`,
    feedback: (id: string) => `${API_BASE}/ai/sessions/${id}/feedback`,
    admin: {
      config: `${API_BASE}/ai/admin/config`,
      prompts: `${API_BASE}/ai/admin/prompts`,
      prompt: (id: string) => `${API_BASE}/ai/admin/prompts/${id}`,
      metrics: `${API_BASE}/ai/admin/metrics`,
      agents: `${API_BASE}/ai/admin/agents`,
      agent: (id: string) => `${API_BASE}/ai/admin/agents/${id}`,
    },
  },

  // ==================== 新闻服务 (8006) ====================
  news: {
    list: `${API_BASE}/news`,
    detail: (id: string) => `${API_BASE}/news/${id}`,
    comments: (id: string) => `${API_BASE}/news/${id}/comments`,
    createComment: (id: string) => `${API_BASE}/news/${id}/comments`,
    subscriptions: `${API_BASE}/news/subscriptions`,
    topics: `${API_BASE}/news/topics`,
    topic: (id: string) => `${API_BASE}/news/topics/${id}`,
    admin: {
      create: `${API_BASE}/news`,
      update: (id: string) => `${API_BASE}/news/${id}`,
      delete: (id: string) => `${API_BASE}/news/${id}`,
      publish: (id: string) => `${API_BASE}/news/${id}/publish`,
      recall: (id: string) => `${API_BASE}/news/${id}/recall`,
      drafts: `${API_BASE}/news/drafts`,
      review: `${API_BASE}/news/review`,
      approve: (id: string) => `${API_BASE}/news/review/${id}/approve`,
      reject: (id: string) => `${API_BASE}/news/review/${id}/reject`,
      stats: `${API_BASE}/news/stats`,
    },
  },

  // ==================== 社区服务 (8007) ====================
  community: {
    posts: `${API_BASE}/community/posts`,
    post: (id: string) => `${API_BASE}/community/posts/${id}`,
    postComments: (id: string) => `${API_BASE}/community/posts/${id}/comments`,
    createPost: `${API_BASE}/community/posts`,
    createComment: (id: string) => `${API_BASE}/community/posts/${id}/comments`,
    favorite: (id: string) => `${API_BASE}/community/posts/${id}/favorite`,
    react: (id: string) => `${API_BASE}/community/posts/${id}/react`,
    userPosts: (userId: string) => `${API_BASE}/community/users/${userId}/posts`,
    lawyers: {
      invitations: `${API_BASE}/community/lawyers/invitations`,
      verify: `${API_BASE}/community/lawyers/verify`,
      profile: `${API_BASE}/community/lawyers/profile`,
    },
    moderation: {
      tasks: `${API_BASE}/community/moderation/tasks`,
      deletePost: (id: string) => `${API_BASE}/community/moderation/posts/${id}/delete`,
      hidePost: (id: string) => `${API_BASE}/community/moderation/posts/${id}/hide`,
      pinPost: (id: string) => `${API_BASE}/community/moderation/posts/${id}/pin`,
      essencePost: (id: string) => `${API_BASE}/community/moderation/posts/${id}/essence`,
      banUser: (id: string) => `${API_BASE}/community/moderation/users/${id}/ban`,
      unbanUser: (id: string) => `${API_BASE}/community/moderation/users/${id}/unban`,
      appeal: (id: string) => `${API_BASE}/community/moderation/appeals/${id}`,
      stats: `${API_BASE}/community/stats`,
    },
    sections: `${API_BASE}/community/sections`,
    section: (id: string) => `${API_BASE}/community/sections/${id}`,
  },

  // ==================== 积分服务 (8008) ====================
  points: {
    balance: (userId: string) => `${API_BASE}/points/${userId}`,
    history: (userId: string) => `${API_BASE}/points/${userId}/history`,
    exchange: `${API_BASE}/points/exchange`,
    products: `${API_BASE}/points/products`,
    orders: `${API_BASE}/points/orders`,
  },

  // ==================== 通知服务 (8009) ====================
  notification: {
    list: `${API_BASE}/notifications`,
    markRead: (id: string) => `${API_BASE}/notifications/${id}/read`,
    settings: `${API_BASE}/notifications/settings`,
  },

  // ==================== 推荐服务 (8010) ====================
  recommendation: {
    lawyers: `${API_BASE}/recommendations/lawyers`,
    news: `${API_BASE}/recommendations/news`,
    posts: `${API_BASE}/recommendations/posts`,
  },

  // ==================== 搜索服务 (8011) ====================
  search: {
    global: `${API_BASE}/search`,
    suggestions: `${API_BASE}/search/suggestions`,
    hot: `${API_BASE}/search/hot`,
  },

  // ==================== 知识库 (与法律服务共用 8004) ====================
  knowledge: {
    list: `${API_BASE}/knowledge`,
    detail: (id: string) => `${API_BASE}/knowledge/${id}`,
    categories: `${API_BASE}/knowledge/categories`,
    search: `${API_BASE}/knowledge/search`,
  },

  // ==================== 文档相关 ====================
  document: {
    list: `${API_BASE}/documents`,
    detail: (id: string) => `${API_BASE}/documents/${id}`,
    upload: `${API_BASE}/documents/upload`,
    templates: `${API_BASE}/document-templates`,
  },

  contract: {
    review: `${API_BASE}/contracts/review`,
    history: `${API_BASE}/contracts/history`,
    detail: (id: string) => `${API_BASE}/contracts/${id}`,
  },

  // ==================== 日历 ====================
  calendar: {
    events: `${API_BASE}/calendar/events`,
    event: (id: string) => `${API_BASE}/calendar/events/${id}`,
  },

  // ==================== 上传 ====================
  upload: {
    file: `${API_BASE}/upload`,
    image: `${API_BASE}/upload/image`,
  },

  // ==================== 管理后台 ====================
  admin: {
    dashboard: `${API_BASE}/admin/dashboard`,
    stats: `${API_BASE}/admin/stats`,
    moderation: `${API_BASE}/moderation/pending`,
  },
} as const;

// 导出端点类型
export type Endpoints = typeof ENDPOINTS;
