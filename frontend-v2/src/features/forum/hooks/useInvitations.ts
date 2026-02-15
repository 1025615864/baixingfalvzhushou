// ============================================
// 律师邀请功能 Hooks
// ============================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  apiGetInvitations,
  apiCreateInvitation,
  apiAcceptInvitation,
  apiDeclineInvitation,
  apiGetLawyers,
} from '../api';
import type {
  LawyerInvitationListResponse,
  LawyerInvitation,
  CreateInvitationRequest,
  LawyerInfo,
  InvitationStatus,
} from '../types';

// Query Keys
const INVITATION_KEYS = {
  all: ['forum', 'invitations'] as const,
  list: (status?: InvitationStatus) => [...INVITATION_KEYS.all, 'list', status ?? 'all'] as const,
  lawyers: (keyword?: string) => [...INVITATION_KEYS.all, 'lawyers', keyword ?? ''] as const,
} as const;

/**
 * 获取律师邀请列表
 */
export function useInvitations(status?: InvitationStatus) {
  return useQuery({
    queryKey: INVITATION_KEYS.list(status),
    queryFn: async (): Promise<LawyerInvitationListResponse> => {
      return apiGetInvitations(1, 20, status);
    },
  });
}

/**
 * 创建律师邀请
 */
export function useCreateInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: CreateInvitationRequest): Promise<LawyerInvitation> => {
      return apiCreateInvitation(request);
    },
    onSuccess: () => {
      // 使邀请列表失效
      void queryClient.invalidateQueries({
        queryKey: INVITATION_KEYS.all,
      });
    },
  });
}

/**
 * 接受律师邀请
 */
export function useAcceptInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (invitationId: number): Promise<{ message: string }> => {
      return apiAcceptInvitation(invitationId);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: INVITATION_KEYS.all,
      });
    },
  });
}

/**
 * 拒绝律师邀请
 */
export function useDeclineInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (invitationId: number): Promise<{ message: string }> => {
      return apiDeclineInvitation(invitationId);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: INVITATION_KEYS.all,
      });
    },
  });
}

/**
 * 获取律师列表
 */
export function useLawyers(keyword?: string) {
  return useQuery({
    queryKey: INVITATION_KEYS.lawyers(keyword),
    queryFn: async (): Promise<{ items: LawyerInfo[]; total: number }> => {
      return apiGetLawyers({ keyword, page: 1, page_size: 20 });
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}