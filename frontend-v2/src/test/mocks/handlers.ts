/**
 * MSW Handlers
 * API 请求模拟处理器
 */

import { http, HttpResponse, delay } from 'msw';

// API 基础路径
const API_BASE = '/api';

// ============================================
// 用户相关 Handlers
// ============================================
export const userHandlers = [
  // 获取当前用户
  http.get(`${API_BASE}/user/me`, async () => {
    await delay(100);
    return HttpResponse.json({
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      phone: '13800138000',
      nickname: '测试用户',
      avatar: 'https://example.com/avatar.png',
      role: 'user',
      is_active: true,
      email_verified: true,
      phone_verified: true,
      bio: '这是我的个人简介',
      location: '北京市',
      company: '测试公司',
      title: '软件工程师',
      website: 'https://example.com',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });
  }),

  // 登录
  http.post(`${API_BASE}/user/login`, async ({ request }) => {
    await delay(200);
    const body = (await request.json()) as { username?: string; password?: string };

    if (body.username === 'testuser' && body.password === 'Password123!') {
      return HttpResponse.json({
        user: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com',
          role: 'user',
        },
        token: 'mock_access_token_12345',
        message: '登录成功',
      });
    }

    return new HttpResponse(
      JSON.stringify({ detail: '用户名或密码错误' }),
      { status: 401 }
    );
  }),

  // 注册
  http.post(`${API_BASE}/user/register`, async ({ request }) => {
    await delay(200);
    const body = (await request.json()) as { username?: string };

    if (body.username === 'existinguser') {
      return new HttpResponse(
        JSON.stringify({ detail: '用户名已存在' }),
        { status: 400 }
      );
    }

    return HttpResponse.json({
      user: {
        id: '2',
        username: body.username,
        email: 'new@example.com',
        role: 'user',
      },
      message: '注册成功',
    }, { status: 201 });
  }),

  // 登出
  http.post(`${API_BASE}/user/logout`, async () => {
    await delay(100);
    return HttpResponse.json({
      message: '登出成功',
      success: true,
    });
  }),

  // 获取用户统计
  http.get(`${API_BASE}/user/me/stats`, async () => {
    await delay(100);
    return HttpResponse.json({
      post_count: 10,
      favorite_count: 25,
      comment_count: 50,
    });
  }),

  // 更新用户资料
  http.put(`${API_BASE}/user/me`, async ({ request }) => {
    await delay(100);
    const body = (await request.json()) as Record<string, unknown>;

    // 支持 name 和 nickname 两种字段名（name 会被映射到 nickname）
    const nickname = body.nickname
      ? String(body.nickname)
      : body.name
        ? String(body.name)
        : '测试用户';

    // 直接使用传入的值，如果有的话
    return HttpResponse.json({
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      phone: typeof body.phone === 'string' ? body.phone : '13800138000',
      nickname: nickname,
      avatar: 'https://example.com/avatar.png',
      role: 'user',
      is_active: true,
      email_verified: true,
      phone_verified: true,
      bio: typeof body.bio === 'string' ? body.bio : '这是我的个人简介',
      location: typeof body.location === 'string' ? body.location : '北京市',
      company: typeof body.company === 'string' ? body.company : '测试公司',
      title: typeof body.title === 'string' ? body.title : '软件工程师',
      website: typeof body.website === 'string' ? body.website : 'https://example.com',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: new Date().toISOString(),
    });
  }),
];

// ============================================
// 积分相关 Handlers
// ============================================
export const pointsHandlers = [
  // 获取积分余额
  http.get(`${API_BASE}/points/balance`, async () => {
    await delay(50);
    return HttpResponse.json({
      balance: 1000,
      continuous_days: 5,
    });
  }),

  // 签到
  http.post(`${API_BASE}/points/check-in`, async () => {
    await delay(100);
    return HttpResponse.json({
      message: '签到成功',
      points_earned: 10,
      continuous_days: 6,
      total_points: 1010,
    });
  }),

  // 获取积分历史
  http.get(`${API_BASE}/points/history`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const limit = parseInt(url.searchParams.get('limit') || '20');
    const offset = parseInt(url.searchParams.get('offset') || '0');

    const history = Array.from({ length: Math.min(limit, 5) }, (_, i) => ({
      id: `transaction-${offset + i + 1}`,
      action: i % 2 === 0 ? 'sign_in' : 'post_create',
      points: (i + 1) * 10,
      balance_after: 1000 - (offset + i) * 10,
      description: `操作描述 ${offset + i + 1}`,
      created_at: new Date(Date.now() - (offset + i) * 86400000).toISOString(),
    }));

    return HttpResponse.json({
      history,
      total: 100,
      limit,
      offset,
    });
  }),

  // 获取积分商品
  http.get(`${API_BASE}/points/products`, async () => {
    await delay(100);
    return HttpResponse.json({
      products: [
        {
          id: 'product-1',
          name: '测试商品1',
          description: '商品描述1',
          points_required: 100,
          product_type: 'virtual',
          image_url: 'https://example.com/product1.png',
          stock: 100,
          status: 'active',
        },
        {
          id: 'product-2',
          name: '测试商品2',
          description: '商品描述2',
          points_required: 200,
          product_type: 'physical',
          image_url: 'https://example.com/product2.png',
          stock: 50,
          status: 'active',
        },
      ],
    });
  }),
];

// ============================================
// 支付相关 Handlers
// ============================================
export const paymentHandlers = [
  // 获取支付配置
  http.get(`${API_BASE}/payment/config`, async () => {
    await delay(50);
    return HttpResponse.json({
      wechat_enabled: true,
      alipay_enabled: true,
      min_amount: 1,
      max_amount: 10000,
    });
  }),

  // 创建订单
  http.post(`${API_BASE}/payment/orders`, async ({ request }) => {
    await delay(200);
    const body = (await request.json()) as { amount?: number };

    return HttpResponse.json({
      order_id: 'mock_order_12345',
      order_no: 'ORDER-2026-001',
      amount: body.amount || 100,
      status: 'pending',
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
    }, { status: 201 });
  }),

  // 获取订单列表
  http.get(`${API_BASE}/payment/orders`, async () => {
    await delay(100);
    return HttpResponse.json({
      items: [
        {
          id: 1,
          order_no: 'ORDER-2026-001',
          order_type: 'recharge',
          amount: 100,
          actual_amount: 100,
          status: 'paid',
          payment_method: 'wechat',
          title: '测试订单',
          created_at: new Date().toISOString(),
          paid_at: new Date().toISOString(),
        },
      ],
      total: 1,
    });
  }),

  // 取消订单
  http.post(`${API_BASE}/payment/orders/:orderId/cancel`, async () => {
    await delay(100);
    return HttpResponse.json({
      message: '订单已取消',
      success: true,
    });
  }),

  // 申请退款
  http.post(`${API_BASE}/payment/refunds`, async ({ request }) => {
    await delay(100);
    const body = (await request.json()) as { order_no?: string; amount?: number; reason?: string };

    return HttpResponse.json({
      refund_no: 'REFUND-2026-001',
      order_no: body.order_no || 'ORDER-2026-001',
      amount: body.amount || 100,
      status: 'pending',
      reason: body.reason || null,
      created_at: new Date().toISOString(),
    });
  }),

  // 充值钱包 - 注意这个 endpoint 是 /payment/balance/recharge 而不是 /payment/wallet/recharge
  http.post(`${API_BASE}/payment/balance/recharge`, async ({ request }) => {
    await delay(200);
    const body = (await request.json()) as { amount?: number; payment_method?: string };

    return HttpResponse.json({
      success: true,
      transaction_id: 'trans-123',
      amount: body.amount || 100,
      balance_after: 1000 + (body.amount || 100),
      status: 'success',
      created_at: new Date().toISOString(),
      message: '充值成功',
    });
  }),

  // 获取钱包余额
  http.get(`${API_BASE}/payment/balance`, async () => {
    await delay(50);
    return HttpResponse.json({
      balance: 1000,
      frozen: 0,
      total_recharged: 5000,
      total_consumed: 4000,
    });
  }),

  // 获取交易记录
  http.get(`${API_BASE}/payment/balance/transactions`, async () => {
    await delay(100);
    return HttpResponse.json({
      items: [
        {
          id: 1,
          type: 'recharge',
          amount: 100,
          balance_after: 1000,
          description: '余额充值',
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
    });
  }),
];

// ============================================
// 新闻相关 Handlers
// ============================================
export const newsHandlers = [
  // 获取新闻列表
  http.get(`${API_BASE}/news`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const limit = parseInt(url.searchParams.get('limit') || '10');

    const news = Array.from({ length: limit }, (_, i) => ({
      id: `news-${i + 1}`,
      title: `测试新闻 ${i + 1}`,
      summary: `这是测试新闻摘要 ${i + 1}`,
      content: `<p>这是测试新闻内容 ${i + 1}</p>`,
      cover_image: `https://example.com/news${i + 1}.jpg`,
      category: '法律知识',
      author: '测试作者',
      view_count: Math.floor(Math.random() * 1000),
      published_at: new Date(Date.now() - i * 86400000).toISOString(),
    }));

    return HttpResponse.json({
      news,
      total: 100,
      limit,
      offset: 0,
    });
  }),
];

// ============================================
// 所有 Handlers
// ============================================
export const handlers = [
  ...userHandlers,
  ...pointsHandlers,
  ...paymentHandlers,
  ...newsHandlers,
];
