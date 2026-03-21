/**
 * E2E测试辅助函数
 * 
 * 提供通用测试辅助方法，包括：
 * - 登录/登出
 * - 数据清理
 * - 截图和录制
 * - 等待和断言
 * - Mock数据
 */

import { Page, expect } from '@playwright/test';

export class TestHelper {
  constructor(private page: Page) {}

  /**
   * 等待元素可见
   */
  async waitForVisible(selector: string, timeout = 5000) {
    await this.page.waitForSelector(selector, { state: 'visible', timeout });
  }

  /**
   * 等待元素消失
   */
  async waitForHidden(selector: string, timeout = 5000) {
    await this.page.waitForSelector(selector, { state: 'hidden', timeout });
  }

  /**
   * 等待API响应
   */
  async waitForResponse(urlPattern: string | RegExp, timeout = 30000) {
    return this.page.waitForResponse(response => {
      return typeof urlPattern === 'string'
        ? response.url().includes(urlPattern)
        : urlPattern.test(response.url());
    }, { timeout });
  }

  /**
   * 截图
   */
  async screenshot(name: string, fullPage = false) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${name}_${timestamp}.png`;
    await this.page.screenshot({ 
      path: `test-results/screenshots/${filename}`,
      fullPage 
    });
    return filename;
  }

  /**
   * 模拟登录
   */
  async login(username = 'test@example.com', password = 'password123') {
    await this.page.goto('/login');
    await this.waitForVisible('[data-testid="email-input"]');
    await this.page.fill('[data-testid="email-input"]', username);
    await this.page.fill('[data-testid="password-input"]', password);
    await this.page.click('[data-testid="login-button"]');
    // 等待登录成功（等待 URL 变化或用户菜单出现）
    try {
      await this.page.waitForURL(/\/dashboard|\/home|^\//, { timeout: 10000 });
    } catch {
      // 如果 URL 没有变化，检查是否已登录
      await this.waitForVisible('[data-testid="user-menu"]', 5000);
    }
    await this.screenshot('login-success');
  }

  /**
   * 登出
   */
  async logout() {
    await this.page.click('[data-testid="user-menu"]');
    await this.page.click('[data-testid="logout-button"]');
    await this.page.waitForURL('/login');
  }

  /**
   * 安全点击（等待可点击后再点击）
   */
  async safeClick(selector: string) {
    await this.waitForVisible(selector);
    await this.page.click(selector);
  }

  /**
   * 安全填充（等待可见后再填充）
   */
  async safeFill(selector: string, value: string) {
    await this.waitForVisible(selector);
    await this.page.fill(selector, value);
  }

  /**
   * 等待并检查元素文本
   */
  async waitForText(selector: string, text: string, timeout = 5000) {
    await this.waitForVisible(selector);
    await expect(this.page.locator(selector)).toContainText(text, { timeout });
  }

  /**
   * 检查元素是否存在
   */
  async exists(selector: string) {
    return await this.page.locator(selector).count() > 0;
  }

  /**
   * 获取元素文本
   */
  async getText(selector: string) {
    await this.waitForVisible(selector);
    return await this.page.textContent(selector);
  }

  /**
   * 清空表单
   */
  async clearForm(formSelector: string) {
    const inputs = await this.page.locator(`${formSelector} input`).all();
    for (const input of inputs) {
      await input.fill('');
    }
  }

  /**
   * 模拟API响应
   */
  async mockAPI(endpoint: string, response: any) {
    await this.page.route(endpoint, route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    });
  }

  /**
   * 等待加载完成
   */
  async waitForLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 滚动到元素
   */
  async scrollToElement(selector: string) {
    const element = this.page.locator(selector);
    await element.scrollIntoViewIfNeeded();
  }

  /**
   * 获取控制台日志
   */
  getConsoleErrors() {
    const errors: string[] = [];
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    return errors;
  }

  /**
   * 设置视口大小
   */
  async setViewport(width: number, height: number) {
    await this.page.setViewportSize({ width, height });
  }

  /**
   * 等待并点击按钮
   */
  async waitForAndClickButton(buttonText: string) {
    const button = this.page.getByRole('button', { name: buttonText });
    await button.click();
  }

  /**
   * 检查是否已登录
   */
  async isLoggedIn() {
    return await this.exists('[data-testid="user-menu"]');
  }

  /**
   * 获取当前URL
   */
  getCurrentURL() {
    return this.page.url();
  }

  /**
   * 导航到页面
   */
  async navigate(path: string) {
    await this.page.goto(path);
    await this.waitForLoad();
  }

  /**
   * 重置浏览器状态
   */
  async resetState() {
    await this.page.context().clearCookies();
    await this.page.context().clearPermissions();
    await this.page.evaluate(() => {
      // eslint-disable-next-line no-restricted-globals
      (window as any).localStorage.clear();
      // eslint-disable-next-line no-restricted-globals
      (window as any).sessionStorage.clear();
    });
  }
}

/**
 * 创建测试辅助实例
 */
export function createTestHelper(page: Page) {
  return new TestHelper(page);
}