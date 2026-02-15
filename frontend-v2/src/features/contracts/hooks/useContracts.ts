/**
 * Contracts（合同管理）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  ContractReviewHistoryItem,
  ContractReviewDetail,
  ContractCompareResult,
  GeneratedContract,
  GetReviewHistoryRequest,
  ReviewContractResponse,
  ExportReportOptions,
  DeleteReviewResponse,
} from '../types';
import {
  apiGetReviewHistory,
  apiGetReviewDetail,
  apiReviewContract,
  apiCompareContracts,
  apiGenerateContract,
  apiDeleteReview,
  apiExportReportPdf,
  apiExportReportWord,
  downloadBlob,
} from '../api';

// ==================== Query Keys ====================

const CONTRACTS_QUERY_KEYS = {
  history: (params?: GetReviewHistoryRequest) => ['contracts', 'history', params] as const,
  detail: (reviewId: string) => ['contracts', 'detail', reviewId] as const,
  compare: () => ['contracts', 'compare'] as const,
  generate: () => ['contracts', 'generate'] as const,
} as const;

// ==================== History Hooks ====================

/**
 * 获取审查历史列表 Hook
 */
export function useReviewHistory(params: GetReviewHistoryRequest = {}) {
  return useQuery<{
    items: ContractReviewHistoryItem[];
    total: number;
    page: number;
    pageSize: number;
  }>({
    queryKey: CONTRACTS_QUERY_KEYS.history(params),
    queryFn: async () => {
      const response = await apiGetReviewHistory(params);
      return {
        items: response.items,
        total: response.total,
        page: response.page,
        pageSize: response.pageSize,
      };
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

// ==================== Detail Hooks ====================

/**
 * 获取审查详情 Hook
 */
export function useReviewDetail(reviewId: string | null) {
  return useQuery<ContractReviewDetail>({
    queryKey: CONTRACTS_QUERY_KEYS.detail(reviewId || ''),
    queryFn: async () => {
      if (!reviewId) {
        throw new Error('Review ID is required');
      }
      return apiGetReviewDetail(reviewId);
    },
    enabled: !!reviewId,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== Review Hooks ====================

/**
 * 审查合同 Hook
 */
export function useReviewContract() {
  const queryClient = useQueryClient();

  return useMutation<ReviewContractResponse, Error, File>({
    mutationFn: apiReviewContract,
    onSuccess: () => {
      // 审查成功后，刷新历史列表
      void queryClient.invalidateQueries({ queryKey: ['contracts', 'history'] });
    },
  });
}

// ==================== Compare Hooks ====================

/**
 * 对比合同 Hook
 */
export function useCompareContracts() {
  return useMutation<ContractCompareResult | null, Error, { originalFile: File; newFile: File }>({
    mutationFn: async ({ originalFile, newFile }) => {
      const response = await apiCompareContracts({ originalFile, newFile });
      if (!response.success || !response.data) {
        throw new Error(response.error || '合同对比失败');
      }
      return response.data;
    },
  });
}

// ==================== Generate Hooks ====================

/**
 * 生成合同 Hook
 */
export function useGenerateContract() {
  return useMutation<GeneratedContract | null, Error, { templateId: string; fields: Record<string, string> }>({
    mutationFn: async ({ templateId, fields }) => {
      const response = await apiGenerateContract({ templateId, fields });
      if (!response.success || !response.contract) {
        throw new Error(response.error || '生成合同失败');
      }
      return response.contract;
    },
  });
}

// ==================== Delete Hooks ====================

/**
 * 删除审查记录 Hook
 */
export function useDeleteReview() {
  const queryClient = useQueryClient();

  return useMutation<DeleteReviewResponse, Error, string>({
    mutationFn: apiDeleteReview,
    onSuccess: () => {
      // 删除成功后，刷新历史列表
      void queryClient.invalidateQueries({ queryKey: ['contracts', 'history'] });
    },
  });
}

// ==================== Export Hooks ====================

/**
 * 导出 PDF 报告 Hook
 */
export function useExportReportPdf() {
  return useMutation<void, Error, { reviewId: string; filename?: string; options?: ExportReportOptions }>({
    mutationFn: async ({ reviewId, filename, options }) => {
      const blob = await apiExportReportPdf(reviewId, options);
      const defaultFilename = `contract_review_${reviewId}_${new Date().toISOString().split('T')[0]}.pdf`;
      downloadBlob(blob, filename || defaultFilename);
    },
  });
}

/**
 * 导出 Word 报告 Hook
 */
export function useExportReportWord() {
  return useMutation<void, Error, { reviewId: string; filename?: string; options?: ExportReportOptions }>({
    mutationFn: async ({ reviewId, filename, options }) => {
      const blob = await apiExportReportWord(reviewId, options);
      const defaultFilename = `contract_review_${reviewId}_${new Date().toISOString().split('T')[0]}.docx`;
      downloadBlob(blob, filename || defaultFilename);
    },
  });
}