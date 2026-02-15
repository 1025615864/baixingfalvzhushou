import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 测试配置
 *
 * 功能特性：
 * - 自动清理测试数据
 * - 支持多浏览器测试
 * - 失败自动重试和截图
 * - 与本地开发服务器集成
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // 测试文件位置
  testDir: './specs',
  
  // 测试运行时的超时时间（毫秒）
  timeout: 30 * 1000,
  
  // 期望匹配超时时间
  expect: {
    timeout: 5000
  },
  
  // 完全并行运行所有测试文件
  fullyParallel: true,
  
  // CI环境下重试失败测试
  retries: 2,
  
  // 并行工作进程数
  workers: 1,
  
  // 测试报告配置
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],
  
  // 共享设置（所有测试可访问）
  use: {
    // 基础URL
    baseURL: 'http://localhost:5173',
    
    // 追踪失败测试
    trace: 'on-first-retry',
    
    // 截图配置
    screenshot: 'only-on-failure',
    
    // 视频录制配置
    video: 'retain-on-failure',
    
    // 操作超时
    actionTimeout: 10 * 1000,
    
    // 导航超时
    navigationTimeout: 30 * 1000,
  },

  // 配置不同的浏览器环境
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // 移动端测试配置
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
    // 无头模式配置（用于CI）
    {
      name: 'chromium-headless',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // 本地开发服务器配置
  webServer: {
    command: 'cd ../../.. && npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    timeout: 120000,
  },
  
  // 输出目录
  outputDir: 'test-results',
});