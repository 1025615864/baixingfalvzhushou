// ============================================
// 测试工具函数 - React Testing Library 封装
// ============================================
/* eslint-disable react-refresh/only-export-components */

import React from 'react';
import { render as rtlRender, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// ============================================
// Query Client 配置
// ============================================

/**
 * 创建测试用的 QueryClient
 * 禁用重试和日志，避免测试中的网络请求
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// ============================================
// 包装器组件
// ============================================

/**
 * 测试 Query Provider 包装器
 */
export function TestQueryProvider({ children }: { children: React.ReactNode }): JSX.Element {
  const [queryClient] = React.useState(() => createTestQueryClient());
  
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

// ============================================
// 渲染函数
// ============================================

/**
 * 带 QueryClient 的渲染函数
 */
export function renderWithQuery(
  ui: React.ReactElement,
  options: Omit<RenderOptions, 'wrapper'> = {}
): ReturnType<typeof rtlRender> {
  return rtlRender(ui, {
    wrapper: TestQueryProvider,
    ...options,
  });
}

/**
 * 基础渲染函数（带所有 provider）
 * 默认包含 QueryClientProvider，避免测试中忘记添加
 */
export function render(
  ui: React.ReactElement,
  options: RenderOptions = {}
): ReturnType<typeof rtlRender> {
  return rtlRender(ui, {
    wrapper: TestQueryProvider,
    ...options,
  });
}

// ============================================
// 重新导出 RTL
// ============================================

export * from '@testing-library/react';
export { userEvent } from '@testing-library/user-event';