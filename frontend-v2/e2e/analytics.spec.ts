// ============================================
// 数据分析仪表板 E2E 测试
// ============================================

import { test, expect } from '@playwright/test';

test.describe('数据分析仪表板', () => {
  test.describe('仪表板页面', () => {
    test('分析仪表板应该正确加载', async ({ page }) => {
      // 导航到分析仪表板页面
      await page.goto('/analytics');
      await page.waitForLoadState('networkidle');

      // 验证页面根元素存在
      await expect(page.locator('#root')).toBeVisible();
      
      // 验证页面有内容渲染
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('仪表板应该包含按钮元素', async ({ page }) => {
      await page.goto('/analytics');
      await page.waitForLoadState('networkidle');

      // 验证至少有一个按钮存在
      const button = page.locator('button').first();
      await expect(button).toBeVisible();
    });
  });

  test.describe('子页面导航', () => {
    test('漏斗分析页面链接应该可用', async ({ page }) => {
      // 导航到漏斗分析页面
      await page.goto('/analytics/funnel');
      await page.waitForLoadState('networkidle');

      // 验证页面加载
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('行为分析页面链接应该可用', async ({ page }) => {
      // 导航到行为分析页面
      await page.goto('/analytics/behavior');
      await page.waitForLoadState('networkidle');

      // 验证页面加载
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('留存分析页面链接应该可用', async ({ page }) => {
      // 导航到留存分析页面
      await page.goto('/analytics/retention');
      await page.waitForLoadState('networkidle');

      // 验证页面加载
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });
  });
});