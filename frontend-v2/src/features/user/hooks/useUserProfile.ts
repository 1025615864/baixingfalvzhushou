import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type { UserProfile, UpdateProfileDTO } from '../types';
import { apiGetCurrentUser, apiUpdateCurrentUser, apiGetUserStats } from '../api';

/**
 * 获取用户资料 Hook
 * 使用真实 API 获取当前用户资料
 */
export function useUserProfile() {
  return useQuery<UserProfile>({
    queryKey: ['user', 'profile'],
    queryFn: apiGetCurrentUser,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 获取用户统计 Hook
 * 使用真实 API 获取用户统计数据
 */
export function useUserStats() {
  return useQuery({
    queryKey: ['user', 'stats'],
    queryFn: apiGetUserStats,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 更新用户资料 Hook
 * 使用真实 API 更新用户资料
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation<UserProfile, Error, UpdateProfileDTO>({
    mutationFn: (data) => apiUpdateCurrentUser(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['user', 'profile'] });
    },
  });
}