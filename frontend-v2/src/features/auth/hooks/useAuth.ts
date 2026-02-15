import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { useAuthStore } from '@/features/auth/store/authStore';
import * as authApi from '@/features/auth/api';
import type { LoginRequest, RegisterRequest } from '@/features/auth/types';

// 查询 keys
export const authKeys = {
  all: ['auth'] as const,
  user: () => [...authKeys.all, 'user'] as const,
};

// 登录 hook
export function useLogin() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: (response) => {
      // 后端直接返回 { user, token?, message }
      const { user, token } = response;
      // 如果后端返回 token，存储到 localStorage
      if (token) {
        localStorage.setItem('access_token', token);
      }
      setAuth(user);
      queryClient.setQueryData(authKeys.user(), user);
      navigate('/');
    },
  });
}

// 注册 hook
export function useRegister() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: (response) => {
      // 后端直接返回 { user, message }
      const { user } = response;
      setAuth(user);
      queryClient.setQueryData(authKeys.user(), user);
      navigate('/');
    },
  });
}

// 登出 hook
export function useLogout() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      localStorage.removeItem('access_token');
      clearAuth();
      // 只清除认证相关的缓存，保留其他数据
      queryClient.removeQueries({ queryKey: authKeys.all });
      navigate('/login');
    },
    onError: () => {
      // 即使失败也清除本地状态
      localStorage.removeItem('access_token');
      clearAuth();
      queryClient.removeQueries({ queryKey: authKeys.all });
      navigate('/login');
    },
  });
}

// 获取当前用户 hook
export function useCurrentUser() {
  const setAuth = useAuthStore((state) => state.setAuth);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return useQuery({
    queryKey: authKeys.user(),
    queryFn: async () => {
      try {
        const user = await authApi.getCurrentUser();
        setAuth(user);
        return user;
      } catch {
        clearAuth();
        return null;
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 分钟
  });
}

// 更新用户信息 hook
export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const updateUser = useAuthStore((state) => state.updateUser);

  return useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: (user) => {
      updateUser(user);
      queryClient.setQueryData(authKeys.user(), user);
    },
  });
}