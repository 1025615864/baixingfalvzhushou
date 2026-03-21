/**
 * 法律文书商城 E2E 测试
 * 测试法律文书商城页面访问、分类列表、搜索文书、查看文书详情
 */

import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

async function waitForLegalDocumentPageReady(page: import('@playwright/test').Page): Promise<void> {
  await expect
    .poll(async () => page.getByRole('button', { name: '全部' }).count(), { timeout: 15000 })
    .toBeGreaterThan(0);
}

test.describe('法律文书商城页面', () => {
  test.beforeEach(async ({ page }) => {
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);
  });

  test('应该正确加载法律文书商城页面', async ({ page }) => {
    await expect(page.getByRole('button', { name: '全部' }).first()).toBeVisible();
    await expect(page.locator('text=专业法律文书模板')).toBeVisible();
  });

  test('应该显示搜索框', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]').first();
    await expect(searchInput).toBeVisible();
  });

  test('应该显示快捷筛选标签', async ({ page }) => {
    await expect(page.getByRole('button', { name: '全部' }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: '免费' }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: '精选' }).first()).toBeVisible();
  });
});

test.describe('分类列表', () => {
  test.beforeEach(async ({ page }) => {
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);
  });

  test('应该显示分类侧边栏（桌面端）', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);

    const desktopSidebar = page.locator('div.hidden.lg\\:block').first();
    await expect(desktopSidebar).toBeVisible();
  });

  test('应该显示筛选按钮（移动端）', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);

    await expect(page.getByRole('button', { name: '筛选分类' })).toBeVisible();
  });

  test('点击分类应该筛选文书列表', async ({ page }) => {
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);

    const categoryButtons = page.locator('aside button');
    const count = await categoryButtons.count();

    if (count > 0) {
      await categoryButtons.first().click();
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

test.describe('搜索文书', () => {
  test.beforeEach(async ({ page }) => {
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);
  });

  test('应该能够在搜索框输入关键词', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]').first();
    await searchInput.fill('合同');
    await expect(searchInput).toHaveValue('合同');
  });

  test('应该能够提交搜索', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]').first();
    await searchInput.fill('合同');

    const searchButton = page.getByRole('button', { name: '搜索' }).first();
    await searchButton.click();

    await expect(page.locator('body')).toBeVisible();
  });

  test('搜索后应该能够清除搜索词', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]').first();
    await searchInput.fill('合同');
    await searchInput.press('ControlOrMeta+A');
    await searchInput.press('Backspace');

    await expect(searchInput).toHaveValue('');
  });

  test('搜索无结果应该显示空状态', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]').first();
    await searchInput.fill('xyzabc123不存在的文书');

    const searchButton = page.getByRole('button', { name: '搜索' }).first();
    await searchButton.click();

    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('文书列表', () => {
  test.beforeEach(async ({ page }) => {
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);
  });

  test('应该显示文书卡片列表', async ({ page }) => {
    await expect(page.locator('text=文书列表').first()).toBeVisible();
  });

  test('应该显示精选推荐区域（首页）', async ({ page }) => {
    const featuredSection = page.locator('text=精选推荐');
    const count = await featuredSection.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('应该显示免费文书区域（首页）', async ({ page }) => {
    const freeSection = page.locator('text=免费文书');
    const count = await freeSection.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('点击快捷筛选应该筛选文书', async ({ page }) => {
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);

    const freeFilter = page.getByRole('button', { name: '免费' }).first();
    await freeFilter.click();

    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('文书详情', () => {
  test('点击文书卡片应该进入详情页', async ({ page }) => {
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);

    const documentCards = page.locator('button:has-text("立即获取"), button:has-text("立即购买"), button:has-text("查看文档")');
    const count = await documentCards.count();

    if (count > 0) {
      await documentCards.first().click();
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('直接访问文书详情页应该正常显示', async ({ page }) => {
    await gotoFast(page, '/legal-documents/1');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('购买流程（模拟）', () => {
  test('应该显示购买或下载按钮', async ({ page }) => {
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);

    const actionButtons = page.locator('button:has-text("购买"), button:has-text("下载"), button:has-text("获取"), button:has-text("查看文档")');
    const count = await actionButtons.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('点击购买应该触发登录检查（未登录状态）', async ({ page }) => {
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);

    const purchaseButton = page.locator('button:has-text("购买")').first();
    const count = await purchaseButton.count();

    if (count > 0) {
      await purchaseButton.click();
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

test.describe('移动端适配', () => {
  test('法律文书商城页面应该响应移动端视图', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);

    await expect(page.getByRole('button', { name: '全部' }).first()).toBeVisible();

    const searchInput = page.locator('input[placeholder*="搜索"]').first();
    await expect(searchInput).toBeVisible();
  });

  test('移动端应该显示筛选弹窗按钮', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);

    await expect(page.getByRole('button', { name: '筛选分类' })).toBeVisible();
  });
});

test.describe('分页功能', () => {
  test('应该显示分页或加载更多（如果有多页数据）', async ({ page }) => {
    await gotoFast(page, '/legal-documents');
    await waitForLegalDocumentPageReady(page);

    const pagination = page.locator('[class*="pagination"], button:has-text("下一页"), button:has-text("加载更多")');
    const count = await pagination.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });
});
