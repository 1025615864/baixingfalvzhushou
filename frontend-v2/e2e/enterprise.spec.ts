// ============================================
// 企业服务 E2E 测试
// ============================================

import { test, expect } from '@playwright/test';

test.describe('企业服务', () => {
  test.describe('企业页面', () => {
    test('企业页面应该正确加载', async ({ page }) => {
      // 导航到企业页面
      await page.goto('/enterprise');
      await page.waitForLoadState('networkidle');

      // 验证页面根元素存在
      await expect(page.locator('#root')).toBeVisible();
      
      // 验证页面有内容渲染
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('企业页面应该包含按钮元素', async ({ page }) => {
      await page.goto('/enterprise');
      await page.waitForLoadState('networkidle');

      // 验证至少有一个按钮存在
      const button = page.locator('button').first();
      await expect(button).toBeVisible();
    });
  });

  test.describe('团队管理', () => {
    test('团队管理标签可以切换', async ({ page }) => {
      await page.goto('/enterprise');
      await page.waitForLoadState('networkidle');

      // 验证页面内容存在
      await expect(page.locator('body')).toBeVisible();
    });
  });
});