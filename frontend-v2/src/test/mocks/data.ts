/**
 * 测试数据工厂
 * 用于生成测试中使用的模拟数据
 */

// ============================================
// 用户数据
// ============================================
export const createMockUser = (overrides = {}) => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  phone: '13800138000',
  nickname: '测试用户',
  avatar: 'https://example.com/avatar.png',
  role: 'user',
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

export const createMockLawyer = (overrides = {}) =>
  createMockUser({
    id: 2,
    username: 'testlawyer',
    role: 'lawyer',
    lawyer_profile: {
      firm_name: '测试律所',
      license_number: 'TEST123456',
      specialties: ['民事', '商事'],
      years_of_experience: 5,
      rating: 4.8,
      consultation_count: 100,
    },
    ...overrides,
  });

export const createMockAdmin = (overrides = {}) =>
  createMockUser({
    id: 3,
    username: 'testadmin',
    role: 'admin',
    ...overrides,
  });

// ============================================
// 积分数据
// ============================================
export const createMockPointsBalance = (overrides = {}) => ({
  balance: 1000,
  continuous_days: 5,
  ...overrides,
});

export const createMockPointsTransaction = (overrides = {}) => ({
  id: 'transaction-1',
  action: 'sign_in',
  points: 10,
  balance_after: 1010,
  description: '每日签到',
  created_at: new Date().toISOString(),
  ...overrides,
});

export const createMockPointsTransactions = (count = 5) =>
  Array.from({ length: count }, (_, i) =>
    createMockPointsTransaction({
      id: `transaction-${i + 1}`,
      action: i % 2 === 0 ? 'sign_in' : 'post_create',
      points: (i + 1) * 10,
      balance_after: 1000 - i * 10,
      description: `操作描述 ${i + 1}`,
      created_at: new Date(Date.now() - i * 86400000).toISOString(),
    })
  );

export const createMockPointsProduct = (overrides = {}) => ({
  id: 'product-1',
  name: '测试商品',
  description: '商品描述',
  points_required: 100,
  product_type: 'virtual',
  image_url: 'https://example.com/product.png',
  stock: 100,
  status: 'active',
  ...overrides,
});

export const createMockPointsProducts = (count = 3) =>
  Array.from({ length: count }, (_, i) =>
    createMockPointsProduct({
      id: `product-${i + 1}`,
      name: `测试商品 ${i + 1}`,
      points_required: (i + 1) * 100,
      product_type: i === 0 ? 'virtual' : 'physical',
      stock: 100 - i * 10,
    })
  );

// ============================================
// 新闻数据
// ============================================
export const createMockNews = (overrides = {}) => ({
  id: 'news-1',
  title: '测试新闻标题',
  summary: '这是测试新闻摘要',
  content: '<p>这是测试新闻内容</p>',
  cover_image: 'https://example.com/news.jpg',
  category: '法律知识',
  author: '测试作者',
  view_count: 100,
  like_count: 10,
  comment_count: 5,
  published_at: new Date().toISOString(),
  ...overrides,
});

export const createMockNewsList = (count = 5) =>
  Array.from({ length: count }, (_, i) =>
    createMockNews({
      id: `news-${i + 1}`,
      title: `测试新闻标题 ${i + 1}`,
      view_count: Math.floor(Math.random() * 1000),
      published_at: new Date(Date.now() - i * 86400000).toISOString(),
    })
  );

// ============================================
// 咨询数据
// ============================================
export const createMockConsultation = (overrides = {}) => ({
  id: 1,
  user_id: 1,
  lawyer_id: 2,
  title: '测试咨询标题',
  content: '这是测试咨询内容',
  status: 'pending',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

// ============================================
// 支付数据
// ============================================
export const createMockOrder = (overrides = {}) => ({
  order_id: 'order-12345',
  user_id: 1,
  amount: 100,
  status: 'pending',
  payment_method: 'wechat',
  created_at: new Date().toISOString(),
  ...overrides,
});

// ============================================
// 表单数据
// ============================================
export const createMockLoginForm = (overrides = {}) => ({
  username: 'testuser',
  password: 'password123',
  ...overrides,
});

export const createMockRegisterForm = (overrides = {}) => ({
  username: 'newuser',
  email: 'newuser@example.com',
  phone: '13900139000',
  password: 'Password123!',
  nickname: '新用户',
  agree_terms: true,
  agree_privacy: true,
  agree_ai_disclaimer: true,
  ...overrides,
});

// ============================================
// API 响应包装
// ============================================
export const createMockApiResponse = <T>(data: T, overrides = {}) => ({
  data,
  message: 'success',
  code: 0,
  ...overrides,
});

export const createMockApiError = (message = '请求失败', code = 400) => ({
  detail: message,
  code,
});

// ============================================
// 分页数据
// ============================================
export const createMockPaginatedResponse = <T>(
  items: T[],
  overrides = {}
) => ({
  items,
  total: items.length,
  limit: 20,
  offset: 0,
  has_more: false,
  ...overrides,
});
