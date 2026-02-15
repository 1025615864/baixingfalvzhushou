/**
 * 律师认证 Hook
 * 使用 React Query 管理律师认证相关的服务端状态
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  SubmitVerificationRequest,
  VerificationStatusResponse,
  LawyerVerification,
} from '../types';
import {
  submitVerification as submitVerificationApi,
  getVerificationStatus as getVerificationStatusApi,
  getVerificationList as getVerificationListApi,
  reviewVerification as reviewVerificationApi,
} from '../api';

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

// Query Keys
const VERIFICATION_KEYS = {
  all: ['lawyer', 'verification'] as const,
  status: () => [...VERIFICATION_KEYS.all, 'status'] as const,
} as const;

/**
 * 获取认证状态
 */
export function useVerificationStatus() {
  return useQuery<VerificationStatusResponse, Error>({
    queryKey: VERIFICATION_KEYS.status(),
    queryFn: getVerificationStatusApi,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    retry: false,
  });
}

/**
 * 提交认证申请
 */
export function useSubmitVerification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SubmitVerificationRequest) => submitVerificationApi(data),
    onSuccess: () => {
      // 提交成功后刷新认证状态
      void queryClient.invalidateQueries({ queryKey: VERIFICATION_KEYS.status() });
    },
  });
}

/**
 * 检查用户是否可以申请认证
 */
export function useCanApplyVerification(): boolean {
  const { data: status } = useVerificationStatus();

  if (!status) return true;

  // 如果已经通过认证，不能再次申请
  if (status.isVerifiedLawyer) return false;

  // 如果有待审核的申请，不能再次申请
  if (status.verificationStatus === 'pending') return false;

  return true;
}

/**
 * 获取认证状态显示文本
 */
export function useVerificationStatusText(): {
  text: string;
  color: 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'warning';
} {
  const { data: status } = useVerificationStatus();

  if (!status || !status.hasVerification) {
    return { text: '未认证', color: 'default' };
  }

  switch (status.verificationStatus) {
    case 'pending':
      return { text: '审核中', color: 'warning' };
    case 'approved':
      return { text: '已认证', color: 'success' };
    case 'rejected':
      return { text: '已拒绝', color: 'error' };
    default:
      return { text: '未认证', color: 'default' };
  }
}

// ==================== 管理员用 Hooks ====================

interface GetVerificationListParams {
  page?: number;
  pageSize?: number;
  status?: 'pending' | 'approved' | 'rejected';
  keyword?: string;
}

// Query Keys
const VERIFICATION_ADMIN_KEYS = {
  all: ['lawyer', 'verification', 'admin'] as const,
  list: (params: GetVerificationListParams) => [...VERIFICATION_ADMIN_KEYS.all, 'list', params] as const,
} as const;

/**
 * 获取认证列表（管理员用）
 */
export function useVerificationAdmin(params: GetVerificationListParams = {}) {
  return useQuery<PaginatedResponse<LawyerVerification>, Error>({
    queryKey: VERIFICATION_ADMIN_KEYS.list(params),
    queryFn: () => getVerificationListApi(params),
    staleTime: 30 * 1000, // 30秒缓存
  });
}

interface ReviewVerificationRequest {
  approved: boolean;
  rejectReason?: string;
}

/**
 * 审核认证申请（管理员用）
 */
export function useReviewVerification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: ReviewVerificationRequest }) =>
      reviewVerificationApi(id, request),
    onSuccess: () => {
      // 审核成功后刷新认证列表
      void queryClient.invalidateQueries({ queryKey: VERIFICATION_ADMIN_KEYS.all });
    },
  });
}