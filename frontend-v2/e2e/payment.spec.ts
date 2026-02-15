// ============================================
// 支付模块 E2E 测试
// ============================================

import { test, expect } from '@playwright/test';

test.describe('支付功能', () => {
  test('用户应该能查看支付订单列表', async ({ page }) => {
    // 访问支付页面
    await page.goto('/payment');
    
    // 验证页面标题
    await expect(page.locator('h1')).toContainText('支付订单');
    
    // 验证统计卡片存在
    await expect(page.locator('text=总订单数')).toBeVisible();
    await expect(page.locator('text=待支付')).toBeVisible();
    await expect(page.locator('text=已完成')).toBeVisible();
    await expect(page.locator('text=总金额')).toBeVisible();
  });

  test('用户应该能筛选订单状态', async ({ page }) => {
    await page.goto('/payment');
    
    // 验证筛选选项
    const filterOptions = ['全部订单', '待支付', '支付中', '已完成', '已取消', '已退款'];
    for (const option of filterOptions) {
      await expect(page.locator(`button:has-text("${option}")`)).toBeVisible();
    }
    
    // 点击"已完成"筛选
    await page.click('button:has-text("已完成")');
    
    // 验证筛选生效
    const activeButton = page.locator('button.bg-blue-600:has-text("已完成")');
    await expect(activeButton).toBeVisible();
  });

  test('订单列表应该正确显示', async ({ page }) => {
    await page.goto('/payment');
    
    // 验证订单列表容器存在
    await expect(page.locator('.space-y-4')).toBeVisible();
    
    // 验证订单卡片内容
    const orderCards = page.locator('.bg-white.rounded-lg');
    await expect(orderCards.first()).toBeVisible();
    
    // 验证订单包含必要信息
    const firstCard = orderCards.first();
    await expect(firstCard.locator('text=订单编号')).toBeVisible();
    await expect(firstCard.locator('text=¥')).toBeVisible();
  });
});

test.describe('结算功能', () => {
  test('用户应该能查看结算信息', async ({ page }) => {
    await page.goto('/settlement');
    
    // 验证页面标题
    await expect(page.locator('h1')).toContainText('我的结算');
    
    // 验证钱包概览
    await expect(page.locator('text=可用余额')).toBeVisible();
    await expect(page.locator('text=冻结金额')).toBeVisible();
    await expect(page.locator('text=总收入')).toBeVisible();
    await expect(page.locator('text=累计提现')).toBeVisible();
  });

  test('用户应该能查看收入明细', async ({ page }) => {
    await page.goto('/settlement');
    
    // 验证收入明细表格存在
    await expect(page.locator('text=收入明细')).toBeVisible();
    
    // 验证表格列
    const headers = ['来源', '金额', '状态', '时间'];
    for (const header of headers) {
      await expect(page.locator(`th:has-text("${header}")`)).toBeVisible();
    }
  });
});