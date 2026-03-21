// ============================================
// useAuth Hook 测试
// ============================================

import { vi, Mock } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as React from 'react';
import { BrowserRouter } from 'react-router-dom';

import {
  useLogin,
  useRegister,
  useLogout,
  useCurrentUser,
  useUpdateProfile,
  authKeys,
} from '../hooks/useAuth';

// Mock API
vi.mock('../api', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn(),
  updateProfile: vi.fn(),
}));

import * as authApi from '../api';

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
      BrowserRouter,
      {},
      React.createElement(
        QueryClientProvider,
        { client: queryClient },
        children
      )
    );
  };
}

describe('useAuth Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============================================
  // useLogin 测试
  // ============================================
  describe('useLogin', () => {
    it('应该成功登录并返回用户信息', async () => {
      const mockUser = { id: 1, username: 'test', email: 'test@example.com' };
      const mockToken = {
        access_token: 'mock-access-token',
        token_type: 'bearer',
        expires_in: 3600,
      };
      (authApi.login as Mock).mockResolvedValue({ user: mockUser, token: mockToken });

      const { result } = renderHook(() => useLogin(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ username: 'test', password: 'password' });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(authApi.login).toHaveBeenCalledWith({ username: 'test', password: 'password' });
    });

    it('登录失败应该设置isError状态', async () => {
      (authApi.login as Mock).mockRejectedValue(new Error('登录失败'));

      const { result } = renderHook(() => useLogin(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ username: 'test', password: 'wrong' });
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });
  });

  // ============================================
  // useRegister 测试
  // ============================================
  describe('useRegister', () => {
    it('应该成功注册并返回用户信息', async () => {
      const mockUser = { id: 1, username: 'newuser', email: 'new@example.com' };
      (authApi.register as Mock).mockResolvedValue({ user: mockUser });

      const { result } = renderHook(() => useRegister(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ username: 'newuser', password: 'password', email: 'new@example.com' });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(authApi.register).toHaveBeenCalled();
    });
  });

  // ============================================
  // useLogout 测试
  // ============================================
  describe('useLogout', () => {
    it('应该成功登出', async () => {
      (authApi.logout as Mock).mockResolvedValue({ success: true });

      const { result } = renderHook(() => useLogout(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate();
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(authApi.logout).toHaveBeenCalled();
    });
  });

  // ============================================
  // useCurrentUser 测试
  // ============================================
  describe('useCurrentUser', () => {
    it('应该成功获取当前用户信息', async () => {
      const mockUser = { id: 1, username: 'test', email: 'test@example.com' };
      (authApi.getCurrentUser as Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useCurrentUser(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockUser);
    });

    it('获取失败应该返回null', async () => {
      (authApi.getCurrentUser as Mock).mockRejectedValue(new Error('Unauthorized'));

      const { result } = renderHook(() => useCurrentUser(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeNull();
    });
  });

  // ============================================
  // useUpdateProfile 测试
  // ============================================
  describe('useUpdateProfile', () => {
    it('应该成功更新用户信息', async () => {
      const updatedUser = { id: 1, username: 'updated', email: 'updated@example.com' };
      (authApi.updateProfile as Mock).mockResolvedValue(updatedUser);

      const { result } = renderHook(() => useUpdateProfile(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ username: 'updated' });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(updatedUser);
    });
  });

  // ============================================
  // authKeys 测试
  // ============================================
  describe('authKeys', () => {
    it('authKeys.all 应该返回正确的值', () => {
      expect(authKeys.all).toEqual(['auth']);
    });

    it('authKeys.user 应该返回正确的值', () => {
      expect(authKeys.user()).toEqual(['auth', 'user']);
    });
  });
});
