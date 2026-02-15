/**
 * 用户反馈功能 React Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  CreateFeedbackDTO,
  UpdateFeedbackDTO,
  FeedbackQueryParams,
  FeedbackStatus,
} from '../types';
import {
  apiCreateFeedback,
  apiGetMyFeedbackList,
  apiGetFeedbackStats,
  apiGetAdminFeedbackList,
  apiUpdateFeedback,
} from '../api';
import { feedbackKeys } from '../api/queryKeys';

// ==================== 用户反馈 Hooks ====================

/**
 * 获取我的反馈列表 Hook
 */
export function useMyFeedbackList(params?: FeedbackQueryParams) {
  return useQuery({
    queryKey: feedbackKeys.myListPaginated(params?.page, params?.pageSize),
    queryFn: () => apiGetMyFeedbackList(params),
  });
}

/**
 * 提交反馈 Hook
 */
export function useCreateFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateFeedbackDTO) => apiCreateFeedback(data),
    onSuccess: () => {
      // 提交成功后刷新我的反馈列表
      void queryClient.invalidateQueries({ queryKey: feedbackKeys.myList() });
    },
  });
}

// ==================== 管理员反馈 Hooks ====================

/**
 * 获取反馈统计 Hook（管理员）
 */
export function useFeedbackStats() {
  return useQuery({
    queryKey: feedbackKeys.stats(),
    queryFn: apiGetFeedbackStats,
  });
}

/**
 * 获取管理员反馈列表 Hook
 */
export function useAdminFeedbackList(params?: FeedbackQueryParams) {
  return useQuery({
    queryKey: feedbackKeys.adminListPaginated(
      params?.page,
      params?.pageSize,
      params?.status,
      params?.keyword
    ),
    queryFn: () => apiGetAdminFeedbackList(params),
  });
}

/**
 * 更新反馈工单 Hook（管理员）
 */
export function useUpdateFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ticketId, data }: { ticketId: number; data: UpdateFeedbackDTO }) =>
      apiUpdateFeedback(ticketId, data),
    onSuccess: () => {
      // 更新成功后刷新相关查询
      void queryClient.invalidateQueries({ queryKey: feedbackKeys.adminList() });
      void queryClient.invalidateQueries({ queryKey: feedbackKeys.stats() });
      void queryClient.invalidateQueries({ queryKey: feedbackKeys.myList() });
    },
  });
}

/**
 * 快捷回复反馈 Hook（管理员）
 */
export function useReplyFeedback() {
  const updateMutation = useUpdateFeedback();

  return {
    ...updateMutation,
    mutate: (params: { ticketId: number; reply: string }) =>
      updateMutation.mutate({
        ticketId: params.ticketId,
        data: { adminReply: params.reply },
      }),
  };
}

/**
 * 更新反馈状态 Hook（管理员）
 */
export function useUpdateFeedbackStatus() {
  const updateMutation = useUpdateFeedback();

  return {
    ...updateMutation,
    mutate: (params: { ticketId: number; status: FeedbackStatus }) =>
      updateMutation.mutate({
        ticketId: params.ticketId,
        data: { status: params.status },
      }),
  };
}

/**
 * 认领/分配反馈工单 Hook（管理员）
 */
export function useAssignFeedback() {
  const updateMutation = useUpdateFeedback();

  return {
    ...updateMutation,
    mutate: (params: { ticketId: number; adminId: number | null }) =>
      updateMutation.mutate({
        ticketId: params.ticketId,
        data: { adminId: params.adminId },
      }),
  };
}