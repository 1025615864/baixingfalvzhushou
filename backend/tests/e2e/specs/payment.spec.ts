/**
 * 支付流程E2E测试
 * 
 * 测试支付相关的核心流程
 */
import { test, expect } from '@playwright/test';
import { createTestHelper } from '../helpers/test-helper';

test.describe('支付流程测试', () => {
  test.beforeEach(async ({ page }) => {
    const helper = createTestHelper(page);
    // 登录并进入支付页面
    await helper.login();
    await page.goto('/payment');
    await helper.waitForLoad();
  });

  test('应该显示支付方式选择', async ({ page }) => {
    // 验证支付方式选项存在
    await expect(page.locator('[data-testid="payment-method-alipay"]')).toBeVisible();
    await expect(page.locator('[data-testid="payment-method-wechat"]')).toBeVisible();
  });

  test('应该能够创建支付订单', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 选择商品
    await helper.safeClick('[data-testid="product-consultation-1"]');
    
    // 选择支付方式
    await helper.safeClick('[data-testid="payment-method-alipay"]');
    
    // 点击支付
    await helper.safeClick('[data-testid="pay-button"]');
    
    // 等待订单创建API响应
    const response = await helper.waitForResponse(/\/api\/payment\/orders/, 10000);
    expect(response.status()).toBe(200);
    
    // 验证跳转到支付确认页
    await expect(page).toHaveURL(/\/payment\/confirm/);
  });

  test('应该显示支付历史记录', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 访问支付历史页面
    await page.goto('/payment/history');
    await helper.waitForLoad();
    
    // 验证历史记录表格存在
    await expect(page.locator('[data-testid="payment-history-table"]')).toBeVisible();
  });

  test('应该处理支付失败情况', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 模拟支付失败
    await helper.mockAPI('/api/payment/orders/*/pay', {
      success: false,
      error: '余额不足'
    });
    
    // 尝试支付
    await helper.safeClick('[data-testid="product-consultation-1"]');
    await helper.safeClick('[data-testid="payment-method-alipay"]');
    await helper.safeClick('[data-testid="pay-button"]');
    
    // 验证错误提示
    await helper.waitForVisible('[data-testid="payment-error"]');
    const errorText = await helper.getText('[data-testid="payment-error"]');
    expect(errorText).toContain('余额不足');
  });
});

test.describe('钱包功能测试', () => {
  test.beforeEach(async ({ page }) => {
    const helper = createTestHelper(page);
    await helper.login();
  });

  test('应该显示钱包余额', async ({ page }) => {
    const helper = createTestHelper(page);
    
    await page.goto('/wallet');
    await helper.waitForLoad();
    
    // 验证余额显示
    await expect(page.locator('[data-testid="wallet-balance"]')).toBeVisible();
  });

  test('应该支持提现申请', async ({ page }) => {
    const helper = createTestHelper(page);
    
    await page.goto('/wallet/withdrawal');
    await helper.waitForLoad();
    
    // 填写提现金额
    await helper.safeFill('[data-testid="withdrawal-amount"]', '100');
    
    // 选择银行卡
    await helper.safeClick('[data-testid="bank-card-select"]');
    await helper.safeClick('[data-testid="bank-card-option-0"]');
    
    // 提交提现申请
    await helper.safeClick('[data-testid="withdrawal-submit"]');
    
    // 验证成功提示
    await helper.waitForVisible('[data-testid="withdrawal-success"]');
  });
});