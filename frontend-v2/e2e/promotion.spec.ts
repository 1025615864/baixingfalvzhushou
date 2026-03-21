// ============================================
// 推广系统 E2E 测试
// ============================================

import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

test.describe('推广系统', () => {
  test.describe('推广页面', () => {
    test('推广页面应该正确加载', async ({ page }) => {
      // 导航到推广页面
      await gotoFast(page, '/promotion');

      // 验证页面根元素存在
      await expect(page.locator('#root')).toBeVisible();

      // 验证页面有内容渲染
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('推广页面应该包含按钮元素', async ({ page }) => {
      await gotoFast(page, '/promotion');

      // 验证可见的业务按钮存在
      const tabButton = page.getByRole('button', { name: '概览' });
      await expect(tabButton).toBeVisible();
    });
  });

  test.describe('提现页面', () => {
    test('提现页面应该可以访问', async ({ page }) => {
      // 导航到提现页面
      await gotoFast(page, '/promotion/withdrawal');

      // 验证页面内容存在
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });
  });
});
