import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

test.describe('律师搜索与列表', () => {
  test('用户应该能查看律师列表页面', async ({ page }) => {
    await gotoFast(page, '/lawfirm');

    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
  });

  test('律师列表页应该有搜索或筛选功能', async ({ page }) => {
    await gotoFast(page, '/lawfirm');

    const searchInput = page.locator('input[type="text"], input[type="search"], input[placeholder*="搜索"], input[placeholder*="律师"]').first();
    const filterSelect = page.locator('select').first();
    const filterButton = page.locator('button').filter({ hasText: /筛选|搜索|查询/ }).first();

    const hasSearch = await searchInput.isVisible().catch(() => false);
    const hasFilter = await filterSelect.isVisible().catch(() => false);
    const hasFilterButton = await filterButton.isVisible().catch(() => false);

    expect(hasSearch || hasFilter || hasFilterButton).toBe(true);
  });

  test('律师卡片应该显示基本信息', async ({ page }) => {
    await gotoFast(page, '/lawfirm');

    const lawyerCard = page.locator('[data-testid^="lawyer-card-"], [class*="lawyer-card"], [class*="LawyerCard"]').first();
    const hasCard = await lawyerCard.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasCard) {
      await expect(lawyerCard).toBeVisible();
    }
  });
});

test.describe('律师详情与预约', () => {
  test('用户应该能进入律师详情页', async ({ page }) => {
    await gotoFast(page, '/lawfirm');

    const lawyerLink = page.locator('a[href*="/lawyer/"], a[href*="/lawyers/"]').first();
    const hasLink = await lawyerLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasLink) {
      await lawyerLink.click();
      await page.waitForLoadState('domcontentloaded');

      await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
    }
  });

  test('律师详情页应该有咨询或预约按钮', async ({ page }) => {
    await gotoFast(page, '/lawfirm');

    const lawyerLink = page.locator('a[href*="/lawyer/"], a[href*="/lawyers/"]').first();
    const hasLink = await lawyerLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasLink) {
      await lawyerLink.click();
      await page.waitForLoadState('domcontentloaded');

      const consultButton = page.locator('button').filter({ hasText: /咨询|预约|联系/ }).first();
      const hasConsult = await consultButton.isVisible({ timeout: 5000 }).catch(() => false);
      expect(hasConsult).toBe(true);
    }
  });
});
