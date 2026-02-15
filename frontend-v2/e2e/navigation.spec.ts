// ============================================
// 导航流程 E2E 测试
// ============================================

import { test, expect } from '@playwright/test';

test.describe('页面导航', () => {
  test('用户应该能从首页导航到各功能页面', async ({ page }) => {
    // 访问首页
    await page.goto('/');
    
    // 验证首页加载
    await expect(page.locator('nav')).toBeVisible();
    
    // 导航到 AI 对话
    await page.click('text=AI咨询');
    await expect(page).toHaveURL(/.*chat/);
    
    // 返回首页
    await page.goto('/');
    
    // 导航到知识库
    await page.click('text=知识库');
    await expect(page).toHaveURL(/.*knowledge/);
  });

  test('移动端应该有响应式菜单', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/');
    
    // 验证移动端菜单按钮存在
    const menuButton = page.locator('button[aria-label="菜单"]').first();
    await expect(menuButton).toBeVisible();
    
    // 点击菜单按钮
    await menuButton.click();
    
    // 验证菜单展开
    await expect(page.locator('nav')).toBeVisible();
  });
});