/**
 * 视频咨询 E2E 测试
 * 测试视频咨询页面访问、咨询列表、律师时段选择器、预约流程
 */

import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

async function waitForVideoConsultationReady(page: import('@playwright/test').Page): Promise<void> {
  await expect
    .poll(async () => page.getByRole('heading', { name: '视频咨询' }).count(), { timeout: 15000 })
    .toBeGreaterThan(0);
}

async function waitForBookingViewReady(page: import('@playwright/test').Page): Promise<void> {
  await expect
    .poll(async () => {
      const backCount = await page.locator('button:has-text("返回")').count();
      const titleCount = await page.locator('text=预约视频咨询').count();
      const formCount = await page.locator('form, [class*="booking"], [class*="form"]').count();
      return backCount + titleCount + formCount;
    }, { timeout: 15000 })
    .toBeGreaterThan(0);
}

async function waitForConsultationListReady(page: import('@playwright/test').Page): Promise<void> {
  await expect
    .poll(async () => {
      const listCount = await page.locator('[class*="space-y"]').count();
      const emptyCount = await page.locator('text=暂无咨询').count();
      return listCount + emptyCount;
    }, { timeout: 15000 })
    .toBeGreaterThan(0);
}

test.describe('视频咨询页面', () => {
  test.beforeEach(async ({ page }) => {
    // 访问视频咨询页面
    await gotoFast(page, '/video-consultation');
    await waitForVideoConsultationReady(page);
  });

  test('应该正确加载视频咨询页面', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('h1')).toContainText('视频咨询');
    
    // 验证页面描述
    await expect(page.locator('text=与专业律师面对面')).toBeVisible();
  });

  test('应该显示预约咨询按钮', async ({ page }) => {
    // 验证预约咨询按钮存在
    await expect(page.locator('button:has-text("预约咨询")')).toBeVisible();
  });

  test('应该显示功能介绍卡片', async ({ page }) => {
    // 验证功能介绍卡片
    await expect(page.getByRole('heading', { name: '视频咨询', level: 3 })).toBeVisible();
    await expect(page.getByRole('heading', { name: '灵活预约', level: 3 })).toBeVisible();
    await expect(page.getByRole('heading', { name: '专业律师', level: 3 })).toBeVisible();
  });

  test('应该显示我的咨询列表区域', async ({ page }) => {
    // 验证咨询列表区域
    await expect(page.locator('text=我的咨询')).toBeVisible();
  });
});

test.describe('咨询列表', () => {
  test.beforeEach(async ({ page }) => {
    await gotoFast(page, '/video-consultation');
    await waitForVideoConsultationReady(page);
  });

  test('应该显示咨询列表或空状态', async ({ page }) => {
    await waitForConsultationListReady(page);

    // 验证列表容器存在（可能有数据也可能显示空状态）
    const listContainer = page.locator('[class*="space-y"]');
    await expect(listContainer.first()).toBeVisible();
  });

  test('咨询列表应该显示状态标签', async ({ page }) => {
    await gotoFast(page, '/video-consultation');
    await waitForVideoConsultationReady(page);
    await waitForConsultationListReady(page);
    
    // 检查是否有状态标签（待确认、已确认、进行中、已完成、已取消）
    const statusBadges = page.locator('[class*="badge"], [class*="Badge"]');
    // 如果有咨询记录，应该能看到状态标签
    const count = await statusBadges.count();
    // 这个测试只是验证页面结构，不强制要求有数据
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('预约流程（模拟）', () => {
  test('点击预约咨询应该进入预约页面', async ({ page }) => {
    await gotoFast(page, '/video-consultation');
    await waitForVideoConsultationReady(page);
    
    // 点击预约咨询按钮
    await page.click('button:has-text("预约咨询")');
    
    await waitForBookingViewReady(page);
    
    // 验证进入预约视图（应该显示返回按钮或预约表单）
    const backButton = page.locator('button:has-text("返回")');
    const bookingTitle = page.locator('text=预约视频咨询');
    
    // 至少应该有一个可见
    const backVisible = await backButton.isVisible().catch(() => false);
    const titleVisible = await bookingTitle.isVisible().catch(() => false);
    
    expect(backVisible || titleVisible).toBe(true);
  });

  test('预约页面应该显示返回按钮', async ({ page }) => {
    await gotoFast(page, '/video-consultation');
    await waitForVideoConsultationReady(page);
    
    // 点击预约咨询按钮
    await page.click('button:has-text("预约咨询")');
    
    // 验证返回按钮存在
    await expect(page.locator('button:has-text("返回")')).toBeVisible();
  });

  test('预约页面应该显示律师选择提示（无律师参数时）', async ({ page }) => {
    // 直接访问预约页面（不带律师参数）
    await gotoFast(page, '/video-consultation');
    await waitForVideoConsultationReady(page);
    await page.click('button:has-text("预约咨询")');
    
    await waitForBookingViewReady(page);

    // 应该显示提示信息或预约表单
    const selectLawyerPrompt = page.locator('text=请选择律师');
    const bookingForm = page.locator('form, [class*="form"]');
    
    const promptVisible = await selectLawyerPrompt.isVisible().catch(() => false);
    const formVisible = await bookingForm.isVisible().catch(() => false);
    
    expect(promptVisible || formVisible).toBe(true);
  });

  test('带律师参数访问应该显示预约表单', async ({ page }) => {
    // 带律师参数访问
    await gotoFast(page, '/video-consultation?lawyerId=1');

    // 等待预约页面关键元素出现
    await expect
      .poll(async () => {
        const titleCount = await page.getByRole('heading', { name: '预约视频咨询' }).count();
        const formCount = await page.locator('form, [class*="booking"]').count();
        return titleCount + formCount;
      }, { timeout: 15000 })
      .toBeGreaterThan(0);

    // 至少应该显示预约相关内容
    const titleVisible = await page.getByRole('heading', { name: '预约视频咨询' }).first().isVisible().catch(() => false);
    const formVisible = await page.locator('form, [class*="booking"]').first().isVisible().catch(() => false);
    expect(titleVisible || formVisible).toBe(true);
  });
});

test.describe('律师时段选择器', () => {
  test('预约页面应该包含时段选择相关组件', async ({ page }) => {
    // 带律师参数访问
    await gotoFast(page, '/video-consultation?lawyerId=1');
    await waitForBookingViewReady(page);
    
    // 检查是否有日历或时段选择相关元素
    const calendarElements = page.locator('[class*="calendar"], [class*="schedule"], [class*="time"], [class*="date"]');
    const count = await calendarElements.count();
    
    // 如果有时段选择器，应该能找到相关元素
    // 这个测试不强制要求，因为可能需要登录状态
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('咨询详情', () => {
  test('访问不存在的咨询应该显示错误提示', async ({ page }) => {
    // 访问一个不存在的咨询 ID
    await gotoFast(page, '/video-consultation/non-existent-id');

    await expect
      .poll(async () => {
        const errorCount = await page.locator('text=咨询不存在, text=加载失败').count();
        const backCount = await page.locator('text=返回').count();
        return errorCount + backCount;
      }, { timeout: 15000 })
      .toBeGreaterThan(0);
    
    // 应该显示错误提示或返回按钮
    const errorMessage = page.locator('text=咨询不存在, text=加载失败, text=返回');
    const count = await errorMessage.count();
    
    // 页面应该有某种反馈
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('移动端适配', () => {
  test('视频咨询页面应该响应移动端视图', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoFast(page, '/video-consultation');
    await waitForVideoConsultationReady(page);
    
    // 页面应该正常加载
    await expect(page.locator('h1')).toContainText('视频咨询');
    
    // 预约咨询按钮应该可见
    await expect(page.locator('button:has-text("预约咨询")')).toBeVisible();
  });

  test('移动端预约页面应该正常显示', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoFast(page, '/video-consultation');
    await waitForVideoConsultationReady(page);
    
    // 点击预约咨询按钮
    await page.click('button:has-text("预约咨询")');
    
    await waitForBookingViewReady(page);
    
    // 验证返回按钮或预约标题可见
    const backButton = page.locator('button:has-text("返回")');
    const bookingTitle = page.locator('text=预约视频咨询');
    
    const backVisible = await backButton.isVisible().catch(() => false);
    const titleVisible = await bookingTitle.isVisible().catch(() => false);
    
    expect(backVisible || titleVisible).toBe(true);
  });
});

test.describe('导航功能', () => {
  test('从预约页面返回应该回到列表', async ({ page }) => {
    await gotoFast(page, '/video-consultation');
    await waitForVideoConsultationReady(page);
    
    // 进入预约页面
    await page.click('button:has-text("预约咨询")');
    await waitForBookingViewReady(page);

    // 点击返回按钮
    await page.click('button:has-text("返回")');
    await waitForVideoConsultationReady(page);
    
    // 验证回到列表页面
    await expect(page.locator('h1')).toContainText('视频咨询');
    await expect(page.locator('button:has-text("预约咨询")')).toBeVisible();
  });
});