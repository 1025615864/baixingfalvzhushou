// ============================================
// 响应式设计 E2E 测试
// ============================================

import { test, expect } from '@playwright/test';

test.describe('响应式设计', () => {
  const viewports = [
    { name: 'Mobile', width: 375, height: 667 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Desktop', width: 1920, height: 1080 },
  ];

  for (const viewport of viewports) {
    test(`页面在 ${viewport.name} 视口下应该正确显示`, async ({ page }) => {
      // 设置视口大小
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      
      // 访问首页
      await page.goto('/');
      
      // 验证页面主要内容可见
      await expect(page.locator('main')).toBeVisible();
      await expect(page.locator('nav')).toBeVisible();
      
      // 验证没有水平滚动条（布局溢出）
      const body = await page.locator('body');
      const scrollWidth = await body.evaluate((el) => el.scrollWidth);
      const clientWidth = await body.evaluate((el) => el.clientWidth);
      
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1); // 允许 1px 的误差
    });
  }

  test('移动端应该显示汉堡菜单', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // 验证汉堡菜单按钮存在
    const menuButton = page.locator('button[aria-label="菜单"]').first();
    await expect(menuButton).toBeVisible();
    
    // 点击菜单按钮
    await menuButton.click();
    
    // 验证导航菜单展开
    await expect(page.locator('nav a')).toBeVisible();
  });

  test('桌面端应该显示完整导航栏', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    // 验证导航链接可见
    const navLinks = ['首页', 'AI咨询', '知识库', '律师', '资讯'];
    for (const link of navLinks) {
      await expect(page.locator(`nav a:has-text("${link}")`)).toBeVisible();
    }
  });

  test('页面内容应该适应不同屏幕尺寸', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // 验证主要内容区域存在
    const main = page.locator('main');
    await expect(main).toBeVisible();
    
    // 验证页脚存在
    const footer = page.locator('footer');
    await expect(footer).toBeVisible();
    
    // 切换到桌面端
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    // 验证页面重新加载后布局仍然正确
    await page.reload();
    await expect(main).toBeVisible();
    await expect(footer).toBeVisible();
  });
});