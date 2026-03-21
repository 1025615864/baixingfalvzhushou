import path from 'path';

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

function getChunks(id: string | undefined) {
  if (!id) return;

  const normalizedId = id.replace(/\\/g, '/');
  const nodeModules = normalizedId.includes('node_modules/');

  if (!nodeModules) {
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
    if (normalizedId.includes('/src/features/lawyer/api/')) {
      return 'lawyer-api';
    }
    if (normalizedId.includes('/src/features/')) {
      const featureName = normalizedId.split('/src/features/')[1]?.split('/')[0];
      if (featureName) {
        return `feature-${featureName}`;
      }
    }
    return;
  }

  if (
    normalizedId.includes('node_modules/react/') ||
    normalizedId.includes('node_modules/react-dom/') ||
    normalizedId.includes('node_modules/scheduler/')
  ) {
    return 'vendor-react';
  }

  if (
    normalizedId.includes('node_modules/react-router/') ||
    normalizedId.includes('node_modules/react-router-dom/') ||
    normalizedId.includes('node_modules/@remix-run/router/')
  ) {
    return 'vendor-router';
  }

  if (
    normalizedId.includes('node_modules/@tanstack/react-query/') ||
    normalizedId.includes('node_modules/@tanstack/query-core/')
  ) {
    return 'vendor-query';
  }

  if (normalizedId.includes('node_modules/axios/')) {
    return 'vendor-http';
  }

  if (normalizedId.includes('node_modules/framer-motion/')) {
    return 'vendor-motion';
  }

  if (
    normalizedId.includes('node_modules/antd/es/config-provider/') ||
    normalizedId.includes('node_modules/antd/es/theme/') ||
    normalizedId.includes('node_modules/antd/es/_util/') ||
    normalizedId.includes('node_modules/antd/es/style/') ||
    normalizedId.includes('node_modules/antd/es/locale/')
  ) {
    return 'vendor-antd-core';
  }

  if (
    normalizedId.includes('node_modules/rc-table/') ||
    normalizedId.includes('node_modules/rc-pagination/') ||
    normalizedId.includes('node_modules/rc-resize-observer/') ||
    normalizedId.includes('node_modules/rc-virtual-list/') ||
    normalizedId.includes('node_modules/antd/es/table/') ||
    normalizedId.includes('node_modules/antd/es/pagination/')
  ) {
    return 'vendor-antd-table';
  }

  if (
    normalizedId.includes('node_modules/@ant-design/icons/')
  ) {
    return 'vendor-antd-icons';
  }

  if (
    normalizedId.includes('node_modules/dayjs/') ||
    normalizedId.includes('node_modules/moment/') ||
    normalizedId.includes('node_modules/luxon/')
  ) {
    return 'vendor-date';
  }

  if (
    normalizedId.includes('node_modules/lodash/') ||
    normalizedId.includes('node_modules/lodash-es/')
  ) {
    return 'vendor-lodash';
  }

  if (
    normalizedId.includes('node_modules/zustand/') ||
    normalizedId.includes('node_modules/immer/') ||
    normalizedId.includes('node_modules/redux/') ||
    normalizedId.includes('node_modules/react-redux/')
  ) {
    return 'vendor-state';
  }

  if (
    normalizedId.includes('node_modules/recharts/') ||
    normalizedId.includes('node_modules/d3-')
  ) {
    return 'vendor-charts';
  }

  if (
    normalizedId.includes('node_modules/dompurify/') ||
    normalizedId.includes('node_modules/isomorphic-dompurify/')
  ) {
    return 'vendor-sanitize';
  }

  if (
    normalizedId.includes('node_modules/qrcode/')
  ) {
    return 'vendor-qrcode';
  }

  return 'vendor-misc';
}

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
        manualChunks: getChunks,
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name || '')) {
            return 'assets/images/[name]-[hash][extname]';
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
            return 'assets/fonts/[name]-[hash][extname]';
          }
          if (/\.css$/i.test(assetInfo.name || '')) {
            return 'assets/css/[name]-[hash][extname]';
          }
          return 'assets/[ext]/[name]-[hash][extname]';
        },
      },
    },
    chunkSizeWarningLimit: 500,
    cssCodeSplit: true,
    sourcemap: false,
    minify: 'esbuild',
    reportCompressedSize: true,
    modulePreload: {
      polyfill: true,
    },
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: getChunks,
      },
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/api/v1/auth': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/api/v1/users': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/api/v1/profiles': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/api/v1/membership': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/api/v1/payment': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
      },
      '/api/v1/balance': {
        target: 'http://127.0.0.1:8003',
        changeOrigin: true,
      },
      '/api/v1/settlement': {
        target: 'http://127.0.0.1:8003',
        changeOrigin: true,
      },
      '/api/v1/legal': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
      },
      '/api/v1/lawyers': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
      },
      '/api/v1/firms': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
      },
      '/api/v1/ai': {
        target: 'http://127.0.0.1:8005',
        changeOrigin: true,
      },
      '/api/v1/news': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
      },
      '/api/v1/community': {
        target: 'http://127.0.0.1:8007',
        changeOrigin: true,
      },
      '/api/v1/points': {
        target: 'http://127.0.0.1:8008',
        changeOrigin: true,
      },
      '/api/v1/notifications': {
        target: 'http://127.0.0.1:8009',
        changeOrigin: true,
      },
      '/api/v1/recommendations': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
      },
      '/api/v1/search': {
        target: 'http://127.0.0.1:8011',
        changeOrigin: true,
      },
      '/api/v1/knowledge': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
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
      'dayjs',
      'immer',
      'zod',
      'react-hook-form',
    ],
    exclude: [
      '@tanstack/react-query-devtools',
    ],
  },
  esbuild: {
    drop: ['console', 'debugger'],
  },
  preview: {
    port: 4173,
  },
});
