// ============================================
// 测试工具函数库
// ============================================

import { vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as React from 'react';

// ============================================
// QueryClient 工厂
// ============================================

/**
 * 创建测试用的 QueryClient
 */
export function createTestQueryClient(options = {}): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        refetchOnWindowFocus: false,
        ...options,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * 创建 QueryClient 包装器
 */
export function createQueryWrapper() {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
}

// ============================================
// Mock 数据生成器
// ============================================

/**
 * 生成模拟用户数据
 */
export function createMockUser(overrides = {}) {
  return {
    id: 'user1',
    name: '测试用户',
    email: 'test@example.com',
    phone: '13800138000',
    role: 'user',
    isVerified: true,
    createdAt: '2025-01-15T08:00:00Z',
    updatedAt: '2026-02-01T10:30:00Z',
    ...overrides,
  };
}

/**
 * 生成模拟订单数据
 */
export function createMockOrder(overrides = {}) {
  return {
    id: 1,
    order_no: 'ORD202602010001',
    order_type: 'consultation',
    amount: 100,
    actual_amount: 100,
    status: 'pending',
    payment_method: null,
    title: '测试订单',
    description: '测试订单描述',
    created_at: new Date().toISOString(),
    paid_at: null,
    ...overrides,
  };
}

/**
 * 生成模拟积分数据
 */
export function createMockPoints(overrides = {}) {
  return {
    balance: 1000,
    continuousDays: 5,
    totalEarned: 5000,
    totalSpent: 4000,
    ...overrides,
  };
}

/**
 * 生成模拟交易记录
 */
export function createMockTransaction(overrides = {}) {
  return {
    id: 'TXN001',
    user_id: 'user1',
    type: 'income',
    amount: 100,
    balance: 1100,
    description: '测试交易',
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

/**
 * 生成模拟新闻数据
 */
export function createMockNews(overrides = {}) {
  return {
    id: 'news1',
    title: '测试新闻',
    summary: '这是测试新闻摘要',
    content: '<p>这是测试新闻内容</p>',
    cover_image: 'https://example.com/cover.jpg',
    category: '法律知识',
    author: '测试作者',
    view_count: 100,
    published_at: new Date().toISOString(),
    ...overrides,
  };
}

// ============================================
// 异步工具
// ============================================

/**
 * 等待指定毫秒
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * 等待下一个微任务
 */
export function nextTick(): Promise<void> {
  return Promise.resolve();
}

// ============================================
// Mock 函数工具
// ============================================

/**
 * 创建成功的 API 响应 Mock
 */
export function createSuccessMock<T>(data: T, delay = 0) {
  return vi.fn().mockImplementation(async () => {
    if (delay > 0) {
      await sleep(delay);
    }
    return data;
  });
}

/**
 * 创建失败的 API 响应 Mock
 */
export function createErrorMock(message: string, _status = 400, delay = 0) {
  return vi.fn().mockImplementation(async () => {
    if (delay > 0) {
      await sleep(delay);
    }
    throw new Error(message);
  });
}

// ============================================
// 断言辅助函数
// ============================================

/**
 * 检查是否是有效的 ISO 日期字符串
 */
export function isValidDateString(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  const date = new Date(value);
  return !isNaN(date.getTime());
}

/**
 * 检查是否是非负数
 */
export function isNonNegativeNumber(value: unknown): boolean {
  return typeof value === 'number' && value >= 0;
}

/**
 * 检查是否是正数
 */
export function isPositiveNumber(value: unknown): boolean {
  return typeof value === 'number' && value > 0;
}

// ============================================
// DOM 测试工具
// ============================================

/**
 * 等待元素出现
 */
export async function waitForElement(
  selector: string,
  timeout = 5000
): Promise<Element | null> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const element = document.querySelector(selector);
    if (element) return element;
    await sleep(50);
  }
  
  return null;
}

/**
 * 模拟用户输入
 */
export function simulateInput(element: HTMLInputElement | HTMLTextAreaElement, value: string) {
  element.value = value;
  element.dispatchEvent(new Event('input', { bubbles: true }));
  element.dispatchEvent(new Event('change', { bubbles: true }));
}

// ============================================
// 类型导出
// ============================================

export interface MockUser {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: string;
  isVerified: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface MockOrder {
  id: number;
  order_no: string;
  order_type: string;
  amount: number;
  actual_amount: number;
  status: string;
  payment_method: string | null;
  title: string;
  description?: string;
  created_at: string;
  paid_at: string | null;
}

export interface MockPoints {
  balance: number;
  continuousDays: number;
  totalEarned: number;
  totalSpent: number;
}

export interface MockTransaction {
  id: string;
  user_id: string;
  type: 'income' | 'expense';
  amount: number;
  balance: number;
  description: string;
  created_at: string;
}

export interface MockNews {
  id: string;
  title: string;
  summary: string;
  content: string;
  cover_image: string;
  category: string;
  author: string;
  view_count: number;
  published_at: string;
}
