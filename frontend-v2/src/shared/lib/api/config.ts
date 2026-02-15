// ============================================
// API 配置 - 修复与后端接口匹配
// ============================================

// API 基础配置
export const API_CONFIG = {
  // 基础 URL - 修复为与后端一致 (/api)
  baseURL: (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api',
  
  // 请求超时时间（毫秒）
  timeout: 30000,
  
  // 重试次数
  retry: 3,
  
  // 重试延迟（毫秒）
  retryDelay: 1000,
};

// 请求头配置
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};

// ============================================
// API 端点配置 - 与 backend/app/routers/user.py 匹配
// ============================================
export const ENDPOINTS = {
  // 认证相关 - 使用 /user 前缀
  auth: {
    login: '/user/login',           // POST /user/login
    register: '/user/register',     // POST /user/register
    logout: '/user/logout',         // POST /user/logout
    refresh: '/user/auth/refresh',  // POST /user/auth/refresh
    me: '/user/me',                 // GET /user/me
    profile: '/user/me',            // PUT /user/me
    password: '/user/me/password',  // PUT /user/me/password
    avatar: '/user/avatar',         // POST /user/avatar (假设)
    csrf: '/user/csrf-token',       // GET /user/csrf-token
  },
  
  // 用户相关 - 使用 /user 前缀
  user: {
    profile: '/user/me',                    // GET /user/me
    update: '/user/me',                     // PUT /user/me
    password: '/user/me/password',          // PUT /user/me/password
    avatar: '/user/avatar',                 // POST /user/avatar
    quotas: '/user/me/quotas',              // GET /user/me/quotas
    stats: '/user/me/stats',                // GET /user/me/stats
    list: '/user/admin/list',               // GET /user/admin/list (管理员)
    toggleActive: (id: number) => `/user/admin/${id}/toggle-active`,
    updateRole: (id: number) => `/user/admin/${id}/role`,
  },
  
  // AI 对话相关 - 需要检查 backend/app/routers/ai.py
  ai: {
    chat: '/ai/chat',               // POST /ai/chat
    history: '/ai/history',         // GET /ai/history
    sessions: '/ai/sessions',       // GET/POST /ai/sessions
    session: (id: string) => `/ai/sessions/${id}`,
  },
  
  // 咨询相关 - 需要检查 backend/app/routers/lawfirm/consultations.py
  consultation: {
    list: '/lawfirm/consultations',           // GET /lawfirm/consultations
    detail: (id: string) => `/lawfirm/consultations/${id}`,
    create: '/lawfirm/consultations',         // POST /lawfirm/consultations
    messages: (id: string) => `/lawfirm/consultations/${id}/messages`,
  },
  
  // 律师相关 - 需要检查 backend/app/routers/lawfirm/lawyers.py
  lawyer: {
    list: '/lawfirm/lawyers',                 // GET /lawfirm/lawyers
    detail: (id: string) => `/lawfirm/lawyers/${id}`,
    reviews: (id: string) => `/lawfirm/lawyers/${id}/reviews`,
  },
  
  // 知识库相关 - 检查 backend/app/routers/knowledge.py
  knowledge: {
    list: '/knowledge',               // GET /knowledge
    detail: (id: string) => `/knowledge/${id}`,
    categories: '/knowledge/categories',
    search: '/knowledge/search',
  },
  
  // 资讯相关 - 检查 backend/app/routers/news.py
  news: {
    list: '/news',                    // GET /news
    detail: (id: string) => `/news/${id}`,
    categories: '/news/categories',
  },
  
  // 论坛相关 - 检查 backend/app/routers/forum/posts.py
  forum: {
    posts: '/forum/posts',            // GET /forum/posts
    post: (id: string) => `/forum/posts/${id}`,
    comments: (id: string) => `/forum/posts/${id}/comments`,
    categories: '/forum/categories',
  },
  
  // 支付相关 - 检查 backend/app/routers/payment/
  payment: {
    orders: '/payments/orders',       // GET /payments/orders
    create: '/payments/orders',       // POST /payments/orders
    pay: '/payments/pay',             // POST /payments/pay
    history: '/payments/history',     // GET /payments/history
    methods: '/payments/methods',     // GET /payments/methods
  },
  
  // 结算相关 - 检查 backend/app/routers/settlement/
  settlement: {
    wallet: '/settlement/wallet',           // GET /settlement/wallet
    income: '/settlement/income',           // GET /settlement/income
    withdrawals: '/settlement/withdrawals', // GET /settlement/withdrawals
    bankAccounts: '/settlement/bank-accounts',
  },
  
  // 日历相关 - 检查 backend/app/routers/calendar.py
  calendar: {
    events: '/calendar/events',       // GET/POST /calendar/events
    event: (id: string) => `/calendar/events/${id}`,
  },
  
  // 通知相关 - 检查 backend/app/routers/notification.py
  notification: {
    list: '/notifications',           // GET /notifications
    markRead: '/notifications/read',  // POST /notifications/read
    settings: '/notifications/settings',
  },
  
  // 文档相关 - 检查 backend/app/routers/document.py
  document: {
    list: '/documents',               // GET /documents
    detail: (id: string) => `/documents/${id}`,
    upload: '/documents/upload',      // POST /documents/upload
    templates: '/document-templates', // GET /document-templates
  },
  
  // 合同审查相关 - 检查 backend/app/routers/contracts.py
  contract: {
    review: '/contracts/review',      // POST /contracts/review
    history: '/contracts/history',    // GET /contracts/history
    detail: (id: string) => `/contracts/${id}`,
  },
  
  // 管理后台相关 - 检查 backend/app/routers/admin.py
  admin: {
    dashboard: '/admin/dashboard',    // GET /admin/dashboard
    users: '/user/admin/list',        // GET /user/admin/list
    stats: '/admin/stats',            // GET /admin/stats
    moderation: '/moderation/pending', // GET /moderation/pending
  },
  
  // 上传相关 - 检查 backend/app/routers/upload.py
  upload: {
    file: '/upload',                  // POST /upload
    image: '/upload/image',           // POST /upload/image
  },
  
  // 搜索相关 - 检查 backend/app/routers/search.py
  search: {
    global: '/search',                // GET /search
    suggestions: '/search/suggestions',
  },
} as const;

// 导出端点类型
export type Endpoints = typeof ENDPOINTS;