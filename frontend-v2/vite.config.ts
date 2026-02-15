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
        manualChunks: {
          // React 生态 - 核心库
          'react-core': ['react', 'react-dom', 'react-router-dom'],
          // UI 组件库
          'ui-framework': ['antd', '@ant-design/icons'],
          // 数据管理
          'data-management': ['@tanstack/react-query', 'zustand'],
          // 工具库
          'utils': ['axios', 'dayjs'],
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
    chunkSizeWarningLimit: 1000,
    cssCodeSplit: true,
    sourcemap: true,
    // 启用代码压缩 (使用esbuild，更快)
    minify: 'esbuild',
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
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
    ],
  },
  // 性能优化
  esbuild: {
    drop: ['console', 'debugger'],
  },
});