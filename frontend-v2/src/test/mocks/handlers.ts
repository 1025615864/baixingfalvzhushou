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

  // 创建订单 - 支持多种请求格式
  http.post(`${API_BASE}/payment/orders`, async ({ request }) => {
    await delay(200);
    const body = (await request.json()) as {
      amount?: number;
      title?: string;
      description?: string;
      type?: string;
      order_type?: string;
    };

    // 生成订单号
    const orderNo = `ORD-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    return HttpResponse.json({
      order_id: 'mock_order_12345',
      order_no: orderNo,
      amount: body.amount || 100,
      title: body.title || '测试订单',
      description: body.description || '',
      order_type: body.order_type || body.type || 'service',
      status: 'pending',
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
    }, { status: 201 });
  }),

  // 获取订单列表 - 支持分页参数
  http.get(`${API_BASE}/payment/orders`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('page_size') || '20');

    // 模拟订单数据
    const orders = Array.from({ length: Math.min(pageSize, 5) }, (_, i) => ({
      id: i + 1,
      order_no: `ORDER-2026-${String(i + 1).padStart(3, '0')}`,
      order_type: i % 2 === 0 ? 'recharge' : 'consultation',
      amount: (i + 1) * 100,
      actual_amount: (i + 1) * 100,
      status: i % 3 === 0 ? 'paid' : i % 3 === 1 ? 'pending' : 'cancelled',
      payment_method: 'wechat',
      title: `测试订单 ${i + 1}`,
      description: `这是测试订单 ${i + 1} 的描述`,
      created_at: new Date(Date.now() - i * 86400000).toISOString(),
      paid_at: i % 3 === 0 ? new Date().toISOString() : null,
    }));

    return HttpResponse.json({
      items: orders,
      total: 10,
      page,
      page_size: pageSize,
    });
  }),

  // 获取订单详情
  http.get(`${API_BASE}/payment/orders/:orderNo`, async ({ params }) => {
    await delay(50);
    const { orderNo } = params;
    return HttpResponse.json({
      id: 1,
      order_no: orderNo as string,
      order_type: 'consultation',
      amount: 100,
      actual_amount: 100,
      status: 'pending',
      payment_method: null,
      title: '测试订单详情',
      description: '这是订单详情描述',
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
    });
  }),

  // 支付订单 - 支持 :orderNo 和 :orderId 两种路径参数
  http.post(`${API_BASE}/payment/orders/:orderNo/pay`, async ({ params }) => {
    await delay(200);
    const { orderNo } = params;
    const orderNoStr = String(orderNo);

    return HttpResponse.json({
      success: true,
      order_no: orderNoStr,
      payment_url: `https://mock-payment.example.com/pay/${orderNoStr}`,
      qr_code: 'data:image/png;base64,mock-qr-code',
      message: '支付请求已处理',
    });
  }),

  // 取消订单
  http.post(`${API_BASE}/payment/orders/:orderId/cancel`, async ({ params }) => {
    await delay(100);
    const { orderId } = params;
    return HttpResponse.json({
      success: true,
      order_id: orderId as string,
      message: '订单已取消',
    });
  }),

  // 申请退款
  http.post(`${API_BASE}/payment/refunds`, async ({ request }) => {
    await delay(100);
    const body = (await request.json()) as { order_no?: string; amount?: number; reason?: string } | undefined;

    return HttpResponse.json({
      refund_no: `REFUND-${Date.now()}`,
      order_no: body?.order_no || 'ORDER-2026-001',
      amount: body?.amount || 100,
      status: 'pending' as const,
      reason: body?.reason || null,
      created_at: new Date().toISOString(),
      success: true,
    });
  }),

  // 获取退款列表
  http.get(`${API_BASE}/payment/refunds`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('page_size') || '20');
    const status = url.searchParams.get('status');

    const refunds = Array.from({ length: Math.min(pageSize, 3) }, (_, i) => ({
      refund_no: `REFUND-2026-${String(i + 1).padStart(3, '0')}`,
      order_no: `ORDER-2026-${String(i + 1).padStart(3, '0')}`,
      amount: (i + 1) * 50,
      status: status || 'pending',
      reason: i === 0 ? '用户申请退款' : null,
      created_at: new Date(Date.now() - i * 86400000).toISOString(),
    }));

    return HttpResponse.json({
      items: refunds,
      total: 3,
      page,
      page_size: pageSize,
    });
  }),

  // 获取退款详情
  http.get(`${API_BASE}/payment/refunds/:refundNo`, async ({ params }) => {
    await delay(50);
    const { refundNo } = params;
    return HttpResponse.json({
      refund_no: refundNo as string,
      order_no: 'ORDER-2026-001',
      amount: 100,
      status: 'pending',
      reason: '用户申请退款',
      created_at: new Date().toISOString(),
    });
  }),

  // 获取钱包余额
  http.get(`${API_BASE}/payment/balance`, async () => {
    await delay(50);
    return HttpResponse.json({
      balance: 1000,
      frozen: 0,
      currency: 'CNY',
    });
  }),

  // 获取余额交易记录
  http.get(`${API_BASE}/payment/balance/transactions`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('page_size') || '20');

    const transactions = Array.from({ length: Math.min(pageSize, 10) }, (_, i) => ({
      id: i + 1,
      type: i % 2 === 0 ? 'recharge' : 'payment',
      amount: (i + 1) * 100,
      balance_after: 1000 + i * 100,
      description: i % 2 === 0 ? '余额充值' : '支付消费',
      created_at: new Date(Date.now() - i * 86400000).toISOString(),
    }));

    return HttpResponse.json({
      items: transactions,
      total: 10,
      page,
      page_size: pageSize,
    });
  }),

  // 获取价格表
  http.get(`${API_BASE}/payment/pricing`, async () => {
    await delay(50);
    return HttpResponse.json({
      items: [
        {
          id: 'consultation-1',
          name: '单次咨询',
          description: '30 分钟在线咨询',
          amount: 100,
          currency: 'CNY',
        },
        {
          id: 'consultation-10',
          name: '10 次咨询套餐',
          description: '10 次在线咨询（有效期 90 天）',
          amount: 800,
          currency: 'CNY',
        },
      ],
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
