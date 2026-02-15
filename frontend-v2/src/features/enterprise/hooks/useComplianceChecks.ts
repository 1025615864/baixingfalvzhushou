/**
 * useComplianceChecks - 合规检查数据 Hook
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type { ContractReview, ContractReviewStatus } from '../types';
import { apiGetContractReviews, apiSubmitContractReview } from '../api';

/**
 * 合规检查查询键
 */
const COMPLIANCE_QUERY_KEYS = {
  reviews: (accountId: number) => ['compliance', 'reviews', accountId] as const,
  reviewDetail: (reviewId: number) => ['compliance', 'review', reviewId] as const,
};

interface UseComplianceChecksOptions {
  /** 是否启用查询 */
  enabled?: boolean;
  /** 状态过滤 */
  status?: ContractReviewStatus;
}

/**
 * 获取合规检查列表 Hook
 * @param accountId 企业账户ID
 * @param options 配置选项
 * @returns 合规检查列表
 */
export function useComplianceChecks(
  accountId: number,
  options: UseComplianceChecksOptions = {}
) {
  const { enabled = true, status } = options;

  return useQuery<ContractReview[]>({
    queryKey: COMPLIANCE_QUERY_KEYS.reviews(accountId),
    queryFn: async () => {
      const response = await apiGetContractReviews(accountId);
      // 如果指定了状态，进行过滤
      if (status) {
        return response.contracts.filter((r: ContractReview) => r.status === status);
      }
      return response.contracts;
    },
    staleTime: 30 * 1000, // 30秒缓存
    enabled: enabled && accountId > 0,
  });
}

/**
 * 获取待处理的合规检查
 */
export function usePendingComplianceChecks(accountId: number) {
  return useComplianceChecks(accountId, { status: 'pending' });
}

/**
 * 获取已完成的合规检查
 */
export function useCompletedComplianceChecks(accountId: number) {
  return useComplianceChecks(accountId, { status: 'completed' });
}

/**
 * 提交合规检查 Hook
 */
export function useSubmitComplianceCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiSubmitContractReview,
    onSuccess: (_data, variables) => {
      // 提交成功后刷新检查列表
      void queryClient.invalidateQueries({
        queryKey: COMPLIANCE_QUERY_KEYS.reviews(variables.accountId),
      });
    },
  });
}

/**
 * 合规检查统计
 */
export function useComplianceStats(accountId: number) {
  const { data: reviews } = useComplianceChecks(accountId);

  return {
    total: reviews?.length || 0,
    pending: reviews?.filter((r) => r.status === 'pending').length || 0,
    reviewing: reviews?.filter((r) => r.status === 'reviewing').length || 0,
    completed: reviews?.filter((r) => r.status === 'completed').length || 0,
    failed: reviews?.filter((r) => r.status === 'failed').length || 0,
    highRisk: reviews?.filter((r) => r.riskLevel === 'high').length || 0,
  };
}