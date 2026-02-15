import path from 'path';
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    exclude: ['node_modules', 'dist', 'e2e'],
    setupFiles: ['./src/test/setup.ts'],
    // 测试覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        'src/**/*.d.ts',
        'src/**/*.stories.tsx',
        'src/main.tsx',
        '**/*.config.*',
        '**/index.ts',
      ],
      // 覆盖率阈值（可根据实际情况调整）
      thresholds: {
        lines: 40,
        functions: 40,
        branches: 35,
        statements: 40,
      },
      // 覆盖率报告输出目录
      reportsDirectory: './coverage',
    },
    // 测试超时配置
    testTimeout: 10000,
    hookTimeout: 10000,
    // 并行执行
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@app': path.resolve(__dirname, './src/app'),
      '@features': path.resolve(__dirname, './src/features'),
      '@shared': path.resolve(__dirname, './src/shared'),
      '@widgets': path.resolve(__dirname, './src/widgets'),
      '@pages': path.resolve(__dirname, './src/pages'),
    },
  },
});