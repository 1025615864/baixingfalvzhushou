import path from 'path';

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/app': path.resolve(__dirname, './src/app'),
      '@/features': path.resolve(__dirname, './src/features'),
      '@/shared': path.resolve(__dirname, './src/shared'),
      '@/widgets': path.resolve(__dirname, './src/widgets'),
      '@/pages': path.resolve(__dirname, './src/pages'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        onlyExplicitManualChunks: true,
        manualChunks: (id) => {
          const normalizedId = id.replace(/\\/g, '/');

          if (normalizedId.includes('/src/features/moderation/components/ModerationQueue')) {
            return 'admin-moderation-queue';
          }

          if (normalizedId.includes('/src/features/moderation/components/ModerationDetail')) {
            return 'admin-moderation-detail';
          }

          if (normalizedId.includes('/src/features/moderation/components/ModerationStats')) {
            return 'admin-moderation-stats';
          }

          if (normalizedId.includes('/src/features/moderation/components/QuickReviewModal')) {
            return 'admin-moderation-modal';
          }

          if (normalizedId.includes('/src/features/security/components/SecurityLevel')) {
            return 'admin-security-overview';
          }

          if (normalizedId.includes('/src/features/security/components/TwoFactorSetup')) {
            return 'admin-security-2fa';
          }

          if (normalizedId.includes('/src/features/security/components/LoginAuditTable')) {
            return 'admin-security-audit';
          }

          if (normalizedId.includes('/src/features/security/components/DeviceList')) {
            return 'admin-security-devices';
          }

          if (normalizedId.includes('/src/features/security/components/PasswordChange')) {
            return 'admin-security-password';
          }

          if (
            normalizedId.includes('/src/features/news-admin/components/ArticleList') ||
            normalizedId.includes('/src/features/news-admin/components/NewsArticlesPanel')
          ) {
            return 'admin-news-articles';
          }

          if (normalizedId.includes('/src/features/news-admin/components/ArticleEditor')) {
            return 'admin-news-editor';
          }

          if (normalizedId.includes('/src/features/news-admin/components/ArticleReview')) {
            return 'admin-news-review';
          }

          if (normalizedId.includes('/src/features/news-admin/components/CategoryManager')) {
            return 'admin-news-categories';
          }

          if (
            normalizedId.includes('/src/features/admin/components/AIConfig') ||
            normalizedId.includes('/src/features/admin/hooks/useAIConfig') ||
            normalizedId.includes('/src/features/admin/types/ai-config')
          ) {
            return 'admin-ai-config-app';
          }

          if (normalizedId.includes('/src/features/moderation/')) {
            return 'admin-moderation-app';
          }

          if (normalizedId.includes('/src/features/security/')) {
            return 'admin-security-app';
          }

          if (normalizedId.includes('/src/features/news-admin/')) {
            return 'admin-news-admin-app';
          }

          if (
            normalizedId.includes('/src/features/admin/') ||
            normalizedId.includes('/src/features/admin_monitor/') ||
            normalizedId.includes('/src/pages/AdminDashboardPage/')
          ) {
            return 'admin-app';
          }

          if (normalizedId.includes('/src/features/ai_quality/')) {
            return 'ai-quality-app';
          }

          if (!normalizedId.includes('node_modules/')) {
            return undefined;
          }

          if (
            normalizedId.includes('node_modules/react/') ||
            normalizedId.includes('node_modules/react-dom/') ||
            normalizedId.includes('node_modules/scheduler/')
          ) {
            return 'react-vendor';
          }

          if (
            normalizedId.includes('node_modules/react-router/') ||
            normalizedId.includes('node_modules/react-router-dom/') ||
            normalizedId.includes('node_modules/@remix-run/router/')
          ) {
            return 'router-vendor';
          }

          if (
            normalizedId.includes('node_modules/@tanstack/react-query/') ||
            normalizedId.includes('node_modules/@tanstack/query-core/')
          ) {
            return 'query-vendor';
          }

          if (normalizedId.includes('node_modules/axios/')) {
            return 'http-vendor';
          }

          if (normalizedId.includes('node_modules/framer-motion/')) {
            return 'motion-vendor';
          }

          if (
            normalizedId.includes('node_modules/antd/es/config-provider/') ||
            normalizedId.includes('node_modules/antd/es/theme/') ||
            normalizedId.includes('node_modules/antd/es/_util/') ||
            normalizedId.includes('node_modules/antd/es/style/') ||
            normalizedId.includes('node_modules/antd/es/locale/')
          ) {
            return 'antd-core-vendor';
          }

          if (
            normalizedId.includes('node_modules/rc-table/') ||
            normalizedId.includes('node_modules/rc-pagination/') ||
            normalizedId.includes('node_modules/rc-resize-observer/') ||
            normalizedId.includes('node_modules/rc-virtual-list/') ||
            normalizedId.includes('node_modules/antd/es/table/') ||
            normalizedId.includes('node_modules/antd/es/pagination/')
          ) {
            return 'antd-table-vendor';
          }

          if (normalizedId.includes('node_modules/@ant-design/icons/')) {
            return 'antd-icons-vendor';
          }

          return undefined;
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name || '')) {
            return 'assets/images/[name]-[hash][extname]';
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
            return 'assets/fonts/[name]-[hash][extname]';
          }
          return 'assets/[ext]/[name]-[hash][extname]';
        },
      },
    },
    chunkSizeWarningLimit: 500,
    cssCodeSplit: true,
    sourcemap: false, // 关闭 sourcemap 减少体积
    // 启用代码压缩 (使用esbuild，更快)
    minify: 'esbuild',
    // 压缩时移除注释
    reportCompressedSize: true,
    // 启用 modulePreload polyfill
    modulePreload: {
      polyfill: true,
    },
    // 目标现代浏览器以获得更好的优化
    target: 'es2020',
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      // ==================== 所有 API 统一代理到 BFF 后端 (8000) ====================
      // Docker 容器内通过服务名 backend 访问后端
      // 本地开发时通过环境变量 VITE_BACKEND_URL 或默认 localhost:8000 访问
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://backend:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: (process.env.VITE_WS_URL || 'ws://backend:8000').replace('http', 'ws'),
        changeOrigin: true,
        ws: true,
      },
    },
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'antd',
      '@ant-design/icons',
      '@tanstack/react-query',
      'zustand',
      'axios',
      'framer-motion',
    ],
  },
  // 性能优化
  esbuild: {
    drop: ['console', 'debugger'],
  },
});
