// ============================================
// 法律咨询模块 E2E 测试
// ============================================

import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

async function waitForConsultationPageReady(page: import('@playwright/test').Page): Promise<void> {
  await expect
    .poll(async () => page.getByRole('button', { name: '发起咨询' }).count(), { timeout: 15000 })
    .toBeGreaterThan(0);
}

test.describe('法律咨询功能', () => {
  test('用户应该能查看咨询页面', async ({ page }) => {
    await gotoFast(page, '/consultation');
    await waitForConsultationPageReady(page);

    await expect(page.getByRole('button', { name: '发起咨询' })).toBeVisible();
    await expect(page.locator('text=查看和管理您的法律咨询记录')).toBeVisible();
  });

  test('用户应该能打开创建咨询弹窗', async ({ page }) => {
    await gotoFast(page, '/consultation');
    await waitForConsultationPageReady(page);

    await page.getByRole('button', { name: '发起咨询' }).click();

    await expect(page.locator('h2')).toContainText('发起咨询');
    await expect(page.locator('input#subject')).toBeVisible();
    await expect(page.locator('select#category')).toBeVisible();
    await expect(page.locator('textarea#description')).toBeVisible();
    await expect(page.getByRole('button', { name: '提交咨询' })).toBeVisible();
  });

  test('咨询表单在空内容时应禁用提交按钮', async ({ page }) => {
    await gotoFast(page, '/consultation');
    await waitForConsultationPageReady(page);
    await page.getByRole('button', { name: '发起咨询' }).click();

    const submitButton = page.getByRole('button', { name: '提交咨询' });
    await expect(submitButton).toBeDisabled();

    await page.fill('input#subject', '测试咨询标题');
    await expect(submitButton).toBeDisabled();

    await page.fill('textarea#description', '测试咨询描述内容');
    await expect(submitButton).toBeEnabled();
  });

  test('咨询弹窗应该可以取消关闭', async ({ page }) => {
    await gotoFast(page, '/consultation');
    await waitForConsultationPageReady(page);

    await page.getByRole('button', { name: '发起咨询' }).click();
    await expect(page.locator('h2')).toContainText('发起咨询');

    await page.getByRole('button', { name: '取消' }).click();
    await expect(page.locator('h2')).toHaveCount(0);
  });
});
