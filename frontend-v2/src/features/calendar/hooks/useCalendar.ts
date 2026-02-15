/**
 * Calendar（法律日历）React Query Hooks
 * 提供提醒相关的数据获取和变更操作
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  CreateReminderRequest,
  GetReminderListRequest,
  UpdateReminderRequest,
} from '../types';
import {
  createReminder,
  deleteReminder,
  getReminder,
  getReminders,
  toggleReminderStatus,
  updateReminder,
} from '../api';
import { calendarKeys } from '../api/queryKeys';

/**
 * 获取提醒列表 Hook
 */
export function useReminders(params: GetReminderListRequest = {}) {
  return useQuery({
    queryKey: calendarKeys.remindersList(params),
    queryFn: () => getReminders(params),
  });
}

/**
 * 获取单个提醒 Hook
 */
export function useReminder(id: number) {
  return useQuery({
    queryKey: calendarKeys.reminder(id),
    queryFn: () => getReminder(id),
    enabled: id > 0,
  });
}

/**
 * 获取指定日期范围内的提醒
 */
export function useRemindersByDate(fromAt: string, toAt: string) {
  return useQuery({
    queryKey: calendarKeys.remindersByDate({ fromAt, toAt }),
    queryFn: () => getReminders({ fromAt, toAt, pageSize: 1000 }),
  });
}

/**
 * 创建提醒 Mutation
 */
export function useCreateReminder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateReminderRequest) => createReminder(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: calendarKeys.reminders() });
    },
  });
}

/**
 * 更新提醒 Mutation
 */
export function useUpdateReminder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateReminderRequest }) =>
      updateReminder(id, data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({
        queryKey: calendarKeys.reminder(variables.id),
      });
      void queryClient.invalidateQueries({ queryKey: calendarKeys.reminders() });
    },
  });
}

/**
 * 删除提醒 Mutation
 */
export function useDeleteReminder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteReminder(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: calendarKeys.reminders() });
    },
  });
}

/**
 * 切换提醒状态 Mutation
 */
export function useToggleReminderStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, isDone }: { id: number; isDone: boolean }) =>
      toggleReminderStatus(id, isDone),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({
        queryKey: calendarKeys.reminder(variables.id),
      });
      void queryClient.invalidateQueries({ queryKey: calendarKeys.reminders() });
    },
  });
}