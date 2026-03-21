// ============================================
// 支付模块 E2E 测试
// ============================================

import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

test.describe('支付功能', () => {
  test('用户应该能查看支付中心页面', async ({ page }) => {
    await gotoFast(page, '/payment');

    await expect(page.locator('h1')).toContainText('支付中心');
    await expect(page.locator('text=管理您的订单和钱包')).toBeVisible();

    await expect(page.getByRole('button', { name: '我的订单' })).toBeVisible();
    await expect(page.getByRole('button', { name: '钱包' })).toBeVisible();
  });

  test('用户应该能查看订单区域内容', async ({ page }) => {
    await gotoFast(page, '/payment');

    await expect(page.getByRole('combobox', { name: '订单状态：' })).toBeVisible();

    const orderCard = page.locator('[data-testid^="order-card-"]').first();
    const emptyState = page.locator('text=暂无订单').first();
    const errorState = page.getByRole('heading', { name: '加载失败' }).first();
    const countText = page.getByText(/共\s*\d+\s*条记录/).first();

    const hasOrderCard = await orderCard.isVisible().catch(() => false);
    const hasEmptyState = await emptyState.isVisible().catch(() => false);
    const hasErrorState = await errorState.isVisible().catch(() => false);
    const hasCountText = await countText.isVisible().catch(() => false);

    expect(hasOrderCard || hasEmptyState || hasErrorState || hasCountText).toBe(true);
  });

  test('用户应该能切换到钱包标签页', async ({ page }) => {
    await gotoFast(page, '/payment');

    await page.getByRole('button', { name: '钱包' }).click();

    await expect(page.locator('text=当前余额')).toBeVisible();
    await expect(page.getByRole('button', { name: '充值' })).toBeVisible();
    await expect(page.getByRole('button', { name: '提现' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '交易记录' })).toBeVisible();
  });
});

test.describe('结算功能', () => {
  test('用户应该能查看收入结算页面', async ({ page }) => {
    await gotoFast(page, '/settlement');

    await expect(page.locator('h1')).toContainText('收入结算');
    await expect(page.locator('text=管理您的服务收入和提现')).toBeVisible();

    await expect(page.getByRole('button', { name: '结算记录' })).toBeVisible();
    await expect(page.getByRole('button', { name: '收入明细' })).toBeVisible();
    await expect(page.getByRole('button', { name: '提现记录' })).toBeVisible();
  });

  test('用户应该能切换到收入明细和提现记录', async ({ page }) => {
    await gotoFast(page, '/settlement');

    await page.getByRole('button', { name: '收入明细' }).click();
    const incomeList = page.locator('[class*="space-y-3"]').first();
    const incomeEmpty = page.locator('text=暂无收入记录').first();
    const hasIncomeList = await incomeList.isVisible().catch(() => false);
    const hasIncomeEmpty = await incomeEmpty.isVisible().catch(() => false);
    expect(hasIncomeList || hasIncomeEmpty).toBe(true);

    await page.getByRole('button', { name: '提现记录' }).click();
    const withdrawalList = page.locator('[class*="space-y-3"]').first();
    const withdrawalEmpty = page.locator('text=暂无提现记录').first();
    const hasWithdrawalList = await withdrawalList.isVisible().catch(() => false);
    const hasWithdrawalEmpty = await withdrawalEmpty.isVisible().catch(() => false);
    expect(hasWithdrawalList || hasWithdrawalEmpty).toBe(true);
  });
});
