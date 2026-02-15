/**
 * 示例E2E测试用例
 * 
 * 此文件展示Playwright测试的基本用法
 */

import { test, expect } from '@playwright/test';
import { createTestHelper } from '../helpers/test-helper';

test.describe('首页测试', () => {
  test.beforeEach(async ({ page }) => {
    const helper = createTestHelper(page);
    // 每个测试前的准备工作
    await helper.resetState();
  });

  test('应该成功加载首页', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 访问首页
    await page.goto('/');
    
    // 等待页面加载完成
    await helper.waitForLoad();
    
    // 验证页面标题
    await expect(page).toHaveTitle(/百姓法律助手/);
    
    // 截图
    await helper.screenshot('homepage');
  });

  test('应该显示导航栏', async ({ page }) => {
    await page.goto('/');
    
    // 验证导航栏是否存在
    const navbar = page.locator('[data-testid="navbar"]');
    await expect(navbar).toBeVisible();
  });

  test('应该响应移动端视图', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 设置移动端视口
    await helper.setViewport(375, 667);
    
    await page.goto('/');
    
    // 验证移动端菜单按钮
    const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"]');
    await expect(mobileMenuButton).toBeVisible();
  });
});

test.describe('用户认证测试', () => {
  test('应该支持用户登录', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 模拟登录
    await helper.login('test@example.com', 'password123');
    
    // 验证登录成功
    expect(await helper.isLoggedIn()).toBe(true);
    
    // 验证重定向到dashboard
    expect(page.url()).toContain('/dashboard');
  });

  test('应该显示登录错误信息', async ({ page }) => {
    const helper = createTestHelper(page);
    
    await page.goto('/login');
    await helper.safeFill('[data-testid="email-input"]', 'wrong@example.com');
    await helper.safeFill('[data-testid="password-input"]', 'wrongpassword');
    await helper.safeClick('[data-testid="login-button"]');
    
    // 等待错误提示
    await helper.waitForVisible('[data-testid="error-message"]', 5000);
    
    // 验证错误消息
    const errorText = await helper.getText('[data-testid="error-message"]');
    expect(errorText).toContain('登录失败');
  });

  test('应该支持用户登出', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 先登录
    await helper.login();
    
    // 登出
    await helper.logout();
    
    // 验证登出成功
    expect(await helper.isLoggedIn()).toBe(false);
    expect(page.url()).toContain('/login');
  });
});

test.describe('AI聊天测试', () => {
  test.beforeEach(async ({ page }) => {
    const helper = createTestHelper(page);
    await helper.login();
    await page.goto('/chat');
  });

  test('应该能够发送消息', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 输入消息
    await helper.safeFill('[data-testid="chat-input"]', '你好，我想咨询合同问题');
    
    // 点击发送按钮
    await helper.safeClick('[data-testid="send-button"]');
    
    // 等待AI响应
    await helper.waitForResponse(/\/api\/ai\/chat/, 30000);
    
    // 验证消息出现在聊天记录中
    await expect(page.locator('[data-testid="chat-message"]')).toHaveCount(2);
  });

  test('应该显示加载状态', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 输入消息并发送
    await helper.safeFill('[data-testid="chat-input"]', '测试消息');
    await helper.safeClick('[data-testid="send-button"]');
    
    // 验证加载指示器
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
  });
});

test.describe('API响应测试', () => {
  test('应该正确处理API错误', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 模拟API错误
    await helper.mockAPI('/api/test/error', { error: 'Internal Server Error' });
    
    // 访问测试页面
    await page.goto('/test-api');
    
    // 等待错误提示
    await helper.waitForVisible('[data-testid="api-error"]');
    
    // 验证错误消息
    const errorText = await helper.getText('[data-testid="api-error"]');
    expect(errorText).toContain('Internal Server Error');
  });
});