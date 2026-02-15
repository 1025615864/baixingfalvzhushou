/**
 * E2E测试数据清理脚本
 * 
 * 在E2E测试运行前后清理测试数据，确保测试环境干净
 */

import { chromium, Browser, Page } from '@playwright/test';

interface CleanupConfig {
  apiUrl: string;
  adminToken?: string;
}

/**
 * 测试数据清理器
 */
export class E2EDataCleaner {
  private browser: Browser | null = null;
  private page: Page | null = null;
  private config: CleanupConfig;

  constructor(config: CleanupConfig) {
    this.config = {
      apiUrl: config.apiUrl || 'http://localhost:8000',
      adminToken: config.adminToken,
    };
  }

  /**
   * 初始化浏览器
   */
  async init() {
    this.browser = await chromium.launch({ headless: true });
    this.page = await this.browser.newPage();
    console.log('[Cleanup] Browser initialized');
  }

  /**
   * 关闭浏览器
   */
  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.page = null;
      console.log('[Cleanup] Browser closed');
    }
  }

  /**
   * 清理所有测试数据
   */
  async cleanupAll() {
    if (!this.page) {
      throw new Error('Cleaner not initialized. Call init() first.');
    }

    console.log('[Cleanup] Starting full cleanup...');

    await Promise.all([
      this.cleanupTestUsers(),
      this.cleanupTestOrders(),
      this.cleanupTestConsultations(),
      this.cleanupTestPosts(),
      this.cleanupTestFiles(),
    ]);

    console.log('[Cleanup] Full cleanup completed');
  }

  /**
   * 清理测试用户
   */
  async cleanupTestUsers() {
    if (!this.page) return;

    try {
      // 调用API删除测试用户（以test_或e2e_开头的用户）
      const response = await this.page.request.post(
        `${this.config.apiUrl}/api/admin/test-cleanup/users`,
        {
          headers: this.getAuthHeaders(),
          data: {
            pattern: '^(test_|e2e_|testuser_)',
            dry_run: false,
          },
        }
      );

      if (response.ok()) {
        const result = await response.json();
        console.log(`[Cleanup] Users cleaned: ${result.deleted_count || 0}`);
      } else {
        console.warn('[Cleanup] Failed to cleanup users:', await response.text());
      }
    } catch (error) {
      console.error('[Cleanup] Error cleaning users:', error);
    }
  }

  /**
   * 清理测试订单
   */
  async cleanupTestOrders() {
    if (!this.page) return;

    try {
      const response = await this.page.request.post(
        `${this.config.apiUrl}/api/admin/test-cleanup/orders`,
        {
          headers: this.getAuthHeaders(),
          data: {
            pattern: '^(ORDER|TEST|E2E)',
            older_than_hours: 24,
          },
        }
      );

      if (response.ok()) {
        const result = await response.json();
        console.log(`[Cleanup] Orders cleaned: ${result.deleted_count || 0}`);
      }
    } catch (error) {
      console.error('[Cleanup] Error cleaning orders:', error);
    }
  }

  /**
   * 清理测试咨询
   */
  async cleanupTestConsultations() {
    if (!this.page) return;

    try {
      const response = await this.page.request.post(
        `${this.config.apiUrl}/api/admin/test-cleanup/consultations`,
        {
          headers: this.getAuthHeaders(),
          data: {
            pattern: '测试咨询|e2e_|test_',
            older_than_hours: 24,
          },
        }
      );

      if (response.ok()) {
        const result = await response.json();
        console.log(`[Cleanup] Consultations cleaned: ${result.deleted_count || 0}`);
      }
    } catch (error) {
      console.error('[Cleanup] Error cleaning consultations:', error);
    }
  }

  /**
   * 清理测试帖子
   */
  async cleanupTestPosts() {
    if (!this.page) return;

    try {
      const response = await this.page.request.post(
        `${this.config.apiUrl}/api/admin/test-cleanup/forum-posts`,
        {
          headers: this.getAuthHeaders(),
          data: {
            pattern: '测试帖子|e2e_|test_',
            older_than_hours: 24,
          },
        }
      );

      if (response.ok()) {
        const result = await response.json();
        console.log(`[Cleanup] Forum posts cleaned: ${result.deleted_count || 0}`);
      }
    } catch (error) {
      console.error('[Cleanup] Error cleaning forum posts:', error);
    }
  }

  /**
   * 清理测试上传文件
   */
  async cleanupTestFiles() {
    if (!this.page) return;

    try {
      const response = await this.page.request.post(
        `${this.config.apiUrl}/api/admin/test-cleanup/files`,
        {
          headers: this.getAuthHeaders(),
          data: {
            pattern: 'test-|e2e-',
            older_than_hours: 1,
          },
        }
      );

      if (response.ok()) {
        const result = await response.json();
        console.log(`[Cleanup] Files cleaned: ${result.deleted_count || 0}`);
      }
    } catch (error) {
      console.error('[Cleanup] Error cleaning files:', error);
    }
  }

  /**
   * 清理Redis测试数据
   */
  async cleanupRedis() {
    if (!this.page) return;

    try {
      const response = await this.page.request.post(
        `${this.config.apiUrl}/api/admin/test-cleanup/redis`,
        {
          headers: this.getAuthHeaders(),
          data: {
            pattern: 'test:*|e2e:*',
          },
        }
      );

      if (response.ok()) {
        const result = await response.json();
        console.log(`[Cleanup] Redis keys cleaned: ${result.deleted_count || 0}`);
      }
    } catch (error) {
      console.error('[Cleanup] Error cleaning Redis:', error);
    }
  }

  /**
   * 获取认证头
   */
  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.config.adminToken) {
      headers['Authorization'] = `Bearer ${this.config.adminToken}`;
    }

    return headers;
  }
}

/**
 * 命令行执行入口
 */
async function main() {
  const apiUrl = process.env.E2E_API_URL || 'http://localhost:8000';
  const adminToken = process.env.E2E_ADMIN_TOKEN;

  const cleaner = new E2EDataCleaner({ apiUrl, adminToken });

  try {
    await cleaner.init();
    await cleaner.cleanupAll();
    await cleaner.cleanupRedis();
  } catch (error) {
    console.error('[Cleanup] Fatal error:', error);
    process.exit(1);
  } finally {
    await cleaner.close();
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  main();
}

export default E2EDataCleaner;