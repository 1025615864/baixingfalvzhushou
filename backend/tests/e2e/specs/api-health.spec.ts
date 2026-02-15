/**
 * API健康检查E2E测试
 * 
 * 测试后端API基本可用性
 */
import { test, expect } from '@playwright/test';

test.describe('API健康检查', () => {
  const baseURL = process.env.API_URL || 'http://localhost:8000';

  test('健康检查端点应该返回正常', async ({ request }) => {
    const response = await request.get(`${baseURL}/health`);
    expect(response.status()).toBe(200);
    
    const body = await response.json();
    expect(body).toHaveProperty('status', 'healthy');
  });

  test('API根路径应该返回服务信息', async ({ request }) => {
    const response = await request.get(`${baseURL}/`);
    expect(response.status()).toBe(200);
    
    const body = await response.json();
    expect(body).toHaveProperty('message');
    expect(body.message).toContain('百姓');
  });

  test('未授权访问应该返回401', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/user/profile`);
    expect(response.status()).toBe(401);
  });

  test('404错误应该正确处理', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/nonexistent`);
    expect(response.status()).toBe(404);
  });
});