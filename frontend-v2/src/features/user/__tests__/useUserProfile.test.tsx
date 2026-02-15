// ============================================
// useUserProfile Hook 测试
// ============================================

import { vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as React from 'react';

import {
  useUserProfile,
  useUserStats,
  useUpdateProfile,
} from '../hooks/useUserProfile';

// 创建测试用的 QueryClient
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// 创建包装器
function createWrapper() {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
}

describe('useUserProfile Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============================================
  // useUserProfile 测试
  // ============================================
  describe('useUserProfile', () => {
    it('应该成功获取用户资料', async () => {
      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data).toHaveProperty('id');
      expect(result.current.data).toHaveProperty('name');
      expect(result.current.data).toHaveProperty('email');
    });

    it('用户资料应该包含必要字段', async () => {
      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const profile = result.current.data;
      expect(profile?.id).toBeDefined();
      expect(profile?.name).toBeDefined();
      expect(profile?.email).toBeDefined();
      expect(profile?.phone).toBeDefined();
      expect(profile?.role).toBeDefined();
    });

    it('用户资料应该包含可选字段', async () => {
      const { result } = renderHook(() => useUserProfile(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const profile = result.current.data;
      expect(profile?.bio).toBeDefined();
      expect(profile?.location).toBeDefined();
      expect(profile?.company).toBeDefined();
      expect(profile?.title).toBeDefined();
    });
  });

  // ============================================
  // useUserStats 测试
  // ============================================
  describe('useUserStats', () => {
    it('应该成功获取用户统计', async () => {
      const { result } = renderHook(() => useUserStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
    });

    it('用户统计应该包含正确的字段', async () => {
      const { result } = renderHook(() => useUserStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const stats = result.current.data;
      expect(stats).toHaveProperty('consultationCount');
      expect(stats).toHaveProperty('documentCount');
      expect(stats).toHaveProperty('knowledgeCount');
      expect(stats).toHaveProperty('totalSpent');
    });

    it('统计数值应该是非负数', async () => {
      const { result } = renderHook(() => useUserStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const stats = result.current.data;
      expect(stats?.consultationCount).toBeGreaterThanOrEqual(0);
      expect(stats?.documentCount).toBeGreaterThanOrEqual(0);
      expect(stats?.knowledgeCount).toBeGreaterThanOrEqual(0);
      expect(stats?.totalSpent).toBeGreaterThanOrEqual(0);
    });
  });

  // ============================================
  // useUpdateProfile 测试
  // ============================================
  describe('useUpdateProfile', () => {
    it('应该成功更新用户资料', async () => {
      const { result } = renderHook(() => useUpdateProfile(), {
        wrapper: createWrapper(),
      });

      const updateData = {
        nickname: '李四',
        bio: '新的个人简介',
      };

      await act(async () => {
        result.current.mutate(updateData);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.name).toBe(updateData.nickname);
      expect(result.current.data?.bio).toBe(updateData.bio);
    });

    it('更新后应该更新 updatedAt 时间戳', async () => {
      const { result } = renderHook(() => useUpdateProfile(), {
        wrapper: createWrapper(),
      });

      const beforeUpdate = new Date().toISOString();

      await act(async () => {
        result.current.mutate({ name: '测试用户' });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const afterUpdate = new Date().toISOString();
      const updatedAt = result.current.data?.updatedAt;

      expect(updatedAt).toBeDefined();
      expect(updatedAt! >= beforeUpdate).toBe(true);
      expect(updatedAt! <= afterUpdate).toBe(true);
    });

    it('应该支持更新多个字段', async () => {
      const { result } = renderHook(() => useUpdateProfile(), {
        wrapper: createWrapper(),
      });

      const updateData = {
        nickname: '王五',
        bio: '更新后的简介',
        location: '上海市',
        company: '新公司',
        title: '新职位',
      };

      await act(async () => {
        result.current.mutate(updateData);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const updated = result.current.data;
      expect(updated?.name).toBe(updateData.nickname);
      expect(updated?.bio).toBe(updateData.bio);
      expect(updated?.location).toBe(updateData.location);
      expect(updated?.company).toBe(updateData.company);
      expect(updated?.title).toBe(updateData.title);
    });
  });
});
