// ============================================
// 导航流程 E2E 测试
// ============================================

import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

test.describe('页面导航', () => {
  test('用户应该能从首页导航到各功能页面', async ({ page }) => {
    await gotoFast(page, '/');

    await expect
      .poll(async () => page.getByRole('link', { name: 'AI咨询' }).count(), { timeout: 15000 })
      .toBeGreaterThan(0);

    const aiConsultationLink = page.getByRole('link', { name: 'AI咨询' }).first();
    await aiConsultationLink.click();
    await expect(page).toHaveURL(/.*chat/);

    await gotoFast(page, '/');

    await page.getByRole('link', { name: '法律知识' }).first().click();
    await expect(page).toHaveURL(/.*knowledge/);
  });

  test('移动端应该有响应式菜单', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoFast(page, '/');

    const menuButton = page.locator('button[aria-label="菜单"]').first();
    await expect(menuButton).toBeVisible();

    await menuButton.click();

    await expect(page.locator('[data-testid="mobile-menu-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="mobile-nav-items"]')).toBeVisible();
  });
});
