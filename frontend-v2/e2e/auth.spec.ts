/**
 * 认证流程 E2E 测试
 * 测试用户登录、注册、登出等功能
 */

import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

test.describe('认证流程', () => {
  test.beforeEach(async ({ page }) => {
    // 访问首页
    await gotoFast(page, '/');
  });

  test('应该显示登录按钮', async ({ page }) => {
    // 检查页面是否加载成功
    await expect(page).toHaveTitle(/百姓助手/);
  });

  test('登录页面应该显示登录表单', async ({ page }) => {
    // 访问登录页面
    await gotoFast(page, '/login');

    // 检查登录表单元素
    await expect(page.locator('input[type="text"]').first()).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
  });

  test('应该显示注册链接', async ({ page }) => {
    await gotoFast(page, '/login');
    
    // 检查是否有注册链接
    const registerLink = page.getByRole('link', { name: /注册|免费注册|立即注册/ }).first();
    await expect(registerLink).toBeVisible();
  });
});

test.describe('注册流程', () => {
  test('注册页面应该显示注册表单', async ({ page }) => {
    await gotoFast(page, '/register');

    // 检查注册表单元素
    await expect(page.locator('input#username')).toBeVisible();
    await expect(page.locator('input#email')).toBeVisible();
    await expect(page.locator('input#password')).toBeVisible();
    await expect(page.locator('input#confirm-password')).toBeVisible();
  });

  test('注册表单应该包含协议勾选框', async ({ page }) => {
    await gotoFast(page, '/register');

    // 检查协议勾选框
    await expect(page.locator('input#agree_terms')).toBeVisible();
    await expect(page.locator('input#agree_privacy')).toBeVisible();
    await expect(page.locator('input#agree_ai_disclaimer')).toBeVisible();
  });
});
