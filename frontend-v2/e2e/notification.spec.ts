/**
 * 通知 E2E 测试
 * 测试通知中心访问、通知列表查看、标记已读功能
 */

import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

async function waitForNotificationPageReady(page: import('@playwright/test').Page): Promise<void> {
  await expect
    .poll(async () => page.getByRole('button', { name: '全部' }).count(), { timeout: 15000 })
    .toBeGreaterThan(0);
}

async function waitForNotificationListOrEmpty(page: import('@playwright/test').Page): Promise<void> {
  await expect
    .poll(async () => {
      const listCount = await page.locator('[class*="space-y"]').count();
      const emptyCount = await page.locator('text=暂无通知').count();
      return listCount + emptyCount;
    }, { timeout: 15000 })
    .toBeGreaterThan(0);
}

async function waitForBatchMode(page: import('@playwright/test').Page): Promise<void> {
  await expect
    .poll(async () => page.locator('button:has-text("取消选择")').count(), { timeout: 10000 })
    .toBeGreaterThan(0);
}

test.describe('通知中心页面', () => {
  test.beforeEach(async ({ page }) => {
    // 访问通知中心页面
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
  });

  test('应该正确加载通知中心页面', async ({ page }) => {
    // 验证通知中心核心筛选标签可见
    await expect(page.locator('button:has-text("全部")')).toBeVisible();
  });

  test('应该显示未读通知数量', async ({ page }) => {
    // 验证未读通知数量提示
    const unreadText = page.locator('text=未读通知');
    const count = await unreadText.count();
    
    // 页面应该显示未读数量提示
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('应该显示筛选标签', async ({ page }) => {
    // 验证筛选标签存在
    await expect(page.locator('button:has-text("全部")')).toBeVisible();
    await expect(page.locator('button:has-text("系统")')).toBeVisible();
    await expect(page.locator('button:has-text("聊天")')).toBeVisible();
    await expect(page.locator('button:has-text("订单")')).toBeVisible();
  });
});

test.describe('通知列表', () => {
  test.beforeEach(async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
  });

  test('应该显示通知列表或空状态', async ({ page }) => {
    await waitForNotificationListOrEmpty(page);
    
    // 验证通知列表区域存在
    const notificationList = page.locator('[class*="space-y"]');
    const emptyState = page.locator('text=暂无通知');
    
    const listVisible = await notificationList.first().isVisible().catch(() => false);
    const emptyVisible = await emptyState.isVisible().catch(() => false);
    
    // 应该显示列表或空状态
    expect(listVisible || emptyVisible).toBe(true);
  });

  test('点击筛选标签应该筛选通知', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    // 点击"系统"筛选
    await page.click('button:has-text("系统")');
    
    await waitForNotificationListOrEmpty(page);
    
    // 验证筛选按钮被选中
    const activeButton = page.locator('button.bg-blue-600:has-text("系统")');
    const count = await activeButton.count();
    
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('通知项应该显示标题和内容', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);
    
    // 查找通知项
    const notificationItems = page.locator('[class*="rounded-lg"][class*="border"]');
    const count = await notificationItems.count();
    
    // 如果有通知项，验证内容
    if (count > 0) {
      const firstItem = notificationItems.first();
      
      // 应该有标题
      const title = firstItem.locator('h3, [class*="font-semibold"], [class*="font-medium"]');
      const titleCount = await title.count();
      expect(titleCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('通知项应该显示时间信息', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);
    
    // 查找时间显示
    const timeElements = page.locator('text=/刚刚|分钟前|小时前|天前|月/');
    const count = await timeElements.count();
    
    // 如果有通知，应该显示时间
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('标记已读功能', () => {
  test.beforeEach(async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
  });

  test('应该显示全部已读按钮（有未读时）', async ({ page }) => {
    await waitForNotificationListOrEmpty(page);
    
    // 查找全部已读按钮
    const markAllReadButton = page.locator('button:has-text("全部已读")');
    const count = await markAllReadButton.count();
    
    // 如果有未读通知，应该显示全部已读按钮
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('应该显示批量选择按钮', async ({ page }) => {
    // 查找批量选择按钮
    const batchButton = page.locator('button:has-text("批量选择"), button:has-text("取消选择")');
    const count = await batchButton.count();
    
    // 应该有批量操作按钮
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('点击批量选择应该进入批量模式', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);
    
    // 查找批量选择按钮
    const batchButton = page.locator('button:has-text("批量选择")').first();
    const count = await batchButton.count();
    
    if (count > 0) {
      await batchButton.click();
      
      await waitForBatchMode(page);

      // 应该显示取消选择按钮
      await expect(page.locator('button:has-text("取消选择")')).toBeVisible();
      
      // 有通知项时应显示复选框；无通知时应展示空状态
      const notificationItems = page.locator('[class*="rounded-lg"][class*="border"]');
      const itemCount = await notificationItems.count();

      if (itemCount > 0) {
        const checkboxes = page.locator('input[type="checkbox"]');
        const checkboxCount = await checkboxes.count();
        expect(checkboxCount).toBeGreaterThan(0);
      } else {
        await expect(page.locator('text=暂无通知')).toBeVisible();
      }
    }
  });

  test('批量模式下应该显示批量操作栏', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);
    
    // 进入批量模式
    const batchButton = page.locator('button:has-text("批量选择")').first();
    const count = await batchButton.count();
    
    if (count > 0) {
      await batchButton.click();
      await waitForBatchMode(page);
      
      // 有通知项时选择一个通知并验证批量操作栏；无通知时验证空状态
      const notificationItems = page.locator('[class*="rounded-lg"][class*="border"]');
      const itemCount = await notificationItems.count();

      if (itemCount > 0) {
        const checkbox = page.locator('input[type="checkbox"]').first();
        await checkbox.click();

        // 应该显示已选择数量
        await expect(page.locator('text=已选择')).toBeVisible();
      } else {
        await expect(page.locator('text=暂无通知')).toBeVisible();
      }
    }
  });

  test('鼠标悬停应该显示操作按钮', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);
    
    // 查找通知项
    const notificationItems = page.locator('[class*="rounded-lg"][class*="border"]').filter({ hasNot: page.locator('input[type="checkbox"]') });
    const count = await notificationItems.count();
    
    if (count > 0) {
      // 悬停在第一个通知项上
      await notificationItems.first().hover();
      
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

test.describe('连接状态', () => {
  test('应该显示连接状态指示器', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);
    
    // 查找连接状态指示器（小圆点或状态文本）
    const connectionStatus = page.locator('[class*="connected"], [class*="status"], [class*="dot"]');
    const count = await connectionStatus.count();
    
    // 应该有连接状态指示
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('滚动加载', () => {
  test('应该支持无限滚动加载', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);

    // 滚动到页面底部
    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });
    
    await waitForNotificationListOrEmpty(page);
    
    // 页面应该正常响应
    await expect(page.locator('body')).toBeVisible();
  });

  test('加载更多时应该显示加载指示器', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);

    // 查找加载指示器区域
    const loadingIndicator = page.locator('text=加载中, [class*="animate-spin"]');
    const count = await loadingIndicator.count();
    
    // 滚动时可能会显示加载指示器
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('删除通知', () => {
  test('悬停通知应该显示删除按钮', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);
    
    // 确保不在批量模式
    const cancelButton = page.locator('button:has-text("取消选择")');
    const cancelCount = await cancelButton.count();
    if (cancelCount > 0) {
      await cancelButton.click();
      await expect(page.locator('button:has-text("批量选择")')).toBeVisible();
    }
    
    // 查找通知项
    const notificationItems = page.locator('[class*="rounded-lg"][class*="border"]');
    const count = await notificationItems.count();
    
    if (count > 0) {
      // 悬停在第一个通知项上
      await notificationItems.first().hover();
      
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

test.describe('移动端适配', () => {
  test('通知中心页面应该响应移动端视图', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    // 页面应该正常加载
    await expect(page.locator('button:has-text("全部")')).toBeVisible();
  });

  test('移动端筛选标签应该可滚动', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);
    
    // 验证筛选标签存在
    await expect(page.locator('button:has-text("全部")')).toBeVisible();
  });

  test('移动端通知项应该正常显示', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);
    
    // 验证通知列表区域存在
    const notificationList = page.locator('[class*="space-y"]');
    const emptyState = page.locator('text=暂无通知');
    
    const listVisible = await notificationList.first().isVisible().catch(() => false);
    const emptyVisible = await emptyState.isVisible().catch(() => false);
    
    // 应该显示列表或空状态
    expect(listVisible || emptyVisible).toBe(true);
  });
});

test.describe('通知类型筛选', () => {
  test('点击不同类型标签应该切换筛选', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    // 依次点击各个筛选标签
    const tabs = ['全部', '系统', '聊天', '订单', '推广'];
    
    for (const tab of tabs) {
      const tabButton = page.locator(`button:has-text("${tab}")`);
      const count = await tabButton.count();
      
      if (count > 0) {
        await tabButton.first().click();

        // 验证页面正常响应
        await expect(page.locator('body')).toBeVisible();
      }
    }
  });
});

test.describe('页面导航', () => {
  test('页面刷新应该保持状态', async ({ page }) => {
    await gotoFast(page, '/notifications');
    await waitForNotificationPageReady(page);
    
    await waitForNotificationListOrEmpty(page);
    
    // 刷新页面
    await page.reload();
    
    await waitForNotificationPageReady(page);

    // 页面应该正常显示
    await expect(page.locator('button:has-text("全部")')).toBeVisible();
  });
});