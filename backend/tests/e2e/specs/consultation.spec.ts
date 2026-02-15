/**
 * 法律咨询E2E测试
 * 
 * 测试法律咨询流程
 */
import { test, expect } from '@playwright/test';
import { createTestHelper } from '../helpers/test-helper';

test.describe('法律咨询流程测试', () => {
  test.beforeEach(async ({ page }) => {
    const helper = createTestHelper(page);
    await helper.login();
    await page.goto('/consultation/new');
    await helper.waitForLoad();
  });

  test('应该能够提交法律咨询', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 填写咨询表单
    await helper.safeFill('[data-testid="consultation-title"]', '劳动合同纠纷咨询');
    await helper.safeFill('[data-testid="consultation-content"]', 
      '我在公司工作3年，最近被无故辞退，请问如何维权？');
    
    // 选择咨询类型
    await helper.safeClick('[data-testid="consultation-type-labor"]');
    
    // 提交咨询
    await helper.safeClick('[data-testid="submit-consultation"]');
    
    // 验证创建成功
    await helper.waitForVisible('[data-testid="consultation-success"]');
    await expect(page).toHaveURL(/\/consultation\/\d+/);
  });

  test('应该能够选择律师', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 创建咨询后进入选择律师页面
    await helper.navigate('/consultation/1/select-lawyer');
    
    // 验证律师列表
    const lawyerCount = await page.locator('[data-testid="lawyer-card"]').count();
    expect(lawyerCount).toBeGreaterThan(0);
    
    // 选择第一个律师
    await helper.safeClick('[data-testid="lawyer-card"]:first-child [data-testid="select-lawyer-btn"]');
    
    // 验证选择成功
    await helper.waitForVisible('[data-testid="lawyer-selected"]');
  });

  test('应该能够进行实时咨询', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 进入咨询详情页
    await page.goto('/consultation/1/chat');
    await helper.waitForLoad();
    
    // 发送消息
    await helper.safeFill('[data-testid="chat-input"]', '请问这种情况能拿到多少赔偿？');
    await helper.safeClick('[data-testid="send-button"]');
    
    // 验证消息出现在聊天记录中
    await expect(page.locator('[data-testid="chat-message"]')).toContainText('赔偿');
  });

  test('应该能够查看咨询历史', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 访问咨询列表页
    await page.goto('/consultation/history');
    await helper.waitForLoad();
    
    // 验证咨询列表表格存在
    await expect(page.locator('[data-testid="consultation-list"]')).toBeVisible();
  });
});

test.describe('合同审核流程测试', () => {
  test.beforeEach(async ({ page }) => {
    const helper = createTestHelper(page);
    await helper.login();
    await page.goto('/contract/review');
    await helper.waitForLoad();
  });

  test('应该能够上传合同文件', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 上传合同文件
    const fileInput = page.locator('[data-testid="contract-file-input"]');
    await fileInput.setInputFiles({
      name: 'test-contract.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('test pdf content'),
    });
    
    // 选择审核类型
    await helper.safeClick('[data-testid="review-type-comprehensive"]');
    
    // 提交审核
    await helper.safeClick('[data-testid="submit-review"]');
    
    // 验证上传成功
    await helper.waitForVisible('[data-testid="review-submitted"]');
  });

  test('应该能够查看审核报告', async ({ page }) => {
    const helper = createTestHelper(page);
    
    // 访问审核报告页
    await page.goto('/contract/review/1/report');
    await helper.waitForLoad();
    
    // 验证报告内容
    await expect(page.locator('[data-testid="review-report"]')).toBeVisible();
    await expect(page.locator('[data-testid="risk-items"]')).toBeVisible();
  });
});