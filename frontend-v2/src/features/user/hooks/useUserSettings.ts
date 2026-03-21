/**
 * useUserSettings - 用户设置 Hook
 * 用于获取和更新用户设置
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type { UserSettings, UpdateSettingsDTO } from '../types';
import { apiGetUserSettings, apiUpdateUserSettings } from '../api';
import { userKeys } from '../api/queryKeys';

/**
 * 获取用户设置 Hook
 */
export function useUserSettings() {
  return useQuery<UserSettings>({
    queryKey: userKeys.settings(),
    queryFn: apiGetUserSettings,
    staleTime: 5 * 60 * 1000, // 5 分钟缓存
  });
}

/**
 * 更新用户设置 Hook
 */
export function useUpdateUserSettings() {
  const queryClient = useQueryClient();

  return useMutation<UserSettings, Error, UpdateSettingsDTO>({
    mutationFn: (data) => apiUpdateUserSettings(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: userKeys.settings() });
    },
  });
}

/**
 * 修改密码 Hook
 */
export function useChangePassword() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string; success: boolean }, Error, { currentPassword: string; newPassword: string }>({
    mutationFn: async (data) => {
      const { apiChangePassword } = await import('../api');
      return apiChangePassword(data);
    },
    onSuccess: () => {
      // 密码修改成功后，可以考虑清除本地 token
      void queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}
