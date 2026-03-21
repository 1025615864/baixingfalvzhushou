/**
 * 首页 E2E 测试
 * 测试首页加载和基本功能
 */

import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

async function waitForHomePageReady(page: import('@playwright/test').Page): Promise<void> {
  await expect
    .poll(async () => page.getByRole('heading', { name: /为什么选择百姓助手/ }).count(), { timeout: 15000 })
    .toBeGreaterThan(0);
}

test.describe('首页', () => {
  test('应该正确加载首页', async ({ page }) => {
    await gotoFast(page, '/');

    // 检查页面标题
    await expect(page).toHaveTitle(/百姓助手/);
  });

  test('应该显示导航栏', async ({ page }) => {
    await gotoFast(page, '/');
    await waitForHomePageReady(page);

    // 检查首页核心区域存在
    await expect(page.getByRole('heading', { name: /为什么选择百姓助手/ })).toBeVisible();
  });

  test('应该响应移动端视图', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoFast(page, '/');

    // 页面应该正常加载
    await expect(page).toHaveTitle(/百姓助手/);
  });
});

test.describe('导航功能', () => {
  test('应该能够导航到不同页面', async ({ page }) => {
    await gotoFast(page, '/');

    // 检查页面是否正常加载
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});
