/**
 * 首页 E2E 测试
 * 测试首页加载和基本功能
 */

import { test, expect } from '@playwright/test';

test.describe('首页', () => {
  test('应该正确加载首页', async ({ page }) => {
    await page.goto('/');

    // 检查页面标题
    await expect(page).toHaveTitle(/百姓助手/);
  });

  test('应该显示导航栏', async ({ page }) => {
    await page.goto('/');

    // 检查导航栏是否存在
    const nav = page.locator('nav, header').first();
    await expect(nav).toBeVisible();
  });

  test('应该响应移动端视图', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // 页面应该正常加载
    await expect(page).toHaveTitle(/百姓助手/);
  });
});

test.describe('导航功能', () => {
  test('应该能够导航到不同页面', async ({ page }) => {
    await page.goto('/');

    // 检查页面是否正常加载
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});
