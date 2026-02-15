// ============================================
// 法律咨询模块 E2E 测试
// ============================================

import { test, expect } from '@playwright/test';

test.describe('法律咨询功能', () => {
  test('用户应该能查看咨询列表', async ({ page }) => {
    // 访问咨询页面
    await page.goto('/consultation');
    
    // 验证页面标题
    await expect(page.locator('h1')).toContainText('法律咨询');
    
    // 验证创建咨询按钮存在
    await expect(page.locator('button:has-text("发起咨询")')).toBeVisible();
  });

  test('用户应该能打开创建咨询弹窗', async ({ page }) => {
    await page.goto('/consultation');
    
    // 点击发起咨询按钮
    await page.click('button:has-text("发起咨询")');
    
    // 验证弹窗显示
    await expect(page.locator('.ant-modal')).toBeVisible();
    await expect(page.locator('text=发起法律咨询')).toBeVisible();
    
    // 验证表单字段
    await expect(page.locator('input#title')).toBeVisible();
    await expect(page.locator('textarea#content')).toBeVisible();
    await expect(page.locator('button:has-text("提交咨询")')).toBeVisible();
  });

  test('咨询表单应该进行验证', async ({ page }) => {
    await page.goto('/consultation');
    
    // 打开弹窗
    await page.click('button:has-text("发起咨询")');
    
    // 直接提交空表单
    await page.click('button:has-text("提交咨询")');
    
    // 验证验证错误
    await expect(page.locator('.ant-form-item-explain')).toContainText('请输入咨询标题');
  });

  test('用户应该能筛选咨询状态', async ({ page }) => {
    await page.goto('/consultation');
    
    // 验证筛选按钮存在
    const filterButtons = ['全部', '待回复', '进行中', '已解决'];
    for (const text of filterButtons) {
      await expect(page.locator(`button:has-text("${text}")`)).toBeVisible();
    }
    
    // 点击"进行中"筛选
    await page.click('button:has-text("进行中")');
    
    // 验证筛选按钮被激活
    const activeButton = page.locator('button.bg-blue-600:has-text("进行中")');
    await expect(activeButton).toBeVisible();
  });
});