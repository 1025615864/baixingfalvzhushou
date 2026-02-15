/**
 * Compliance Reports（合规报告）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  ComplianceReport,
  GenerateReportRequest,
  GetComplianceReportsRequest,
  GetComplianceReportsResponse,
} from '../types';
import {
  apiGetComplianceReports,
  apiGetComplianceReportById,
  apiGenerateComplianceReport,
  apiDeleteComplianceReport,
  apiExportComplianceReport,
} from '../api';

// ==================== Query Keys ====================

const COMPLIANCE_QUERY_KEYS = {
  reports: (accountId: number, params?: GetComplianceReportsRequest) =>
    ['compliance', 'reports', accountId, params] as const,
  report: (reportId: number) => ['compliance', 'report', reportId] as const,
  reportTypes: ['compliance', 'report-types'] as const,
} as const;

// ==================== Compliance Report Hooks ====================

/**
 * 获取合规报告列表 Hook
 */
export function useComplianceReports(accountId: number, params: GetComplianceReportsRequest = {}) {
  return useQuery<GetComplianceReportsResponse>({
    queryKey: COMPLIANCE_QUERY_KEYS.reports(accountId, params),
    queryFn: async () => {
      const response = await apiGetComplianceReports(accountId, params);
      return response;
    },
    staleTime: 60 * 1000, // 1分钟缓存
    enabled: accountId > 0,
  });
}

/**
 * 获取单个合规报告详情 Hook
 */
export function useComplianceReport(accountId: number, reportId: number) {
  return useQuery<ComplianceReport>({
    queryKey: COMPLIANCE_QUERY_KEYS.report(reportId),
    queryFn: () => apiGetComplianceReportById(accountId, reportId),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: reportId > 0,
  });
}

/**
 * 生成合规报告 Hook
 */
export function useGenerateComplianceReport(accountId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: GenerateReportRequest) => apiGenerateComplianceReport(request),
    onSuccess: () => {
      // 生成成功后刷新报告列表
      void queryClient.invalidateQueries({ queryKey: ['compliance', 'reports', accountId] });
    },
  });
}

/**
 * 删除合规报告 Hook
 */
export function useDeleteComplianceReport(accountId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reportId: number) => apiDeleteComplianceReport(accountId, reportId),
    onSuccess: () => {
      // 删除成功后刷新报告列表
      void queryClient.invalidateQueries({ queryKey: ['compliance', 'reports', accountId] });
    },
  });
}

/**
 * 导出合规报告 Hook
 */
export function useExportComplianceReport(accountId: number) {
  return useMutation({
    mutationFn: ({ reportId, format }: { reportId: number; format: 'pdf' | 'word' | 'excel' }) =>
      apiExportComplianceReport(accountId, reportId, format),
  });
}
