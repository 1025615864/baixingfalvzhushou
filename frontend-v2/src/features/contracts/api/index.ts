/**
 * Contracts（合同管理）API 层
 */

import apiClient from "@/shared/lib/api/client";

import type {
  GetReviewHistoryRequest,
  GetReviewHistoryResponse,
  ReviewContractResponse,
  CompareContractsRequest,
  CompareContractsResponse,
  GenerateContractRequest,
  GenerateContractResponse,
  ContractReviewDetail,
  ExportReportOptions,
  DeleteReviewResponse,
} from '../types';


// API 基础路径
const API_BASE = '/contracts';

/**
 * 获取审查历史记录列表
 */
export async function apiGetReviewHistory(
  params: GetReviewHistoryRequest = {}
): Promise<GetReviewHistoryResponse> {
  const { data } = await apiClient.get<{
    items: Array<{
      id: string;
      filename: string;
      contract_type: string | null;
      risk_level: 'low' | 'medium' | 'high';
      risk_count: number;
      request_id: string;
      created_at: string;
    }>;
    total: number;
    page: number;
    page_size: number;
  }>(`${API_BASE}/review/history`, {
    params: {
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
    },
  });

  return {
    items: data.items.map(item => ({
      id: item.id,
      filename: item.filename,
      contractType: item.contract_type as import('../types').ContractType | null,
      riskLevel: item.risk_level,
      riskCount: item.risk_count,
      requestId: item.request_id,
      createdAt: item.created_at,
    })),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

/**
 * 获取审查详情
 */
export async function apiGetReviewDetail(reviewId: string): Promise<ContractReviewDetail> {
  const { data } = await apiClient.get<{
    filename: string;
    content_type: string | null;
    contract_type: string | null;
    text_chars: number;
    text_preview: string;
    risk_level: 'low' | 'medium' | 'high';
    risk_count: number;
    report_json: import('../types').ContractReviewReport;
    report_markdown: string;
    request_id: string;
    created_at?: string;
  }>(`${API_BASE}/review/history/${reviewId}`);

  return {
    id: reviewId,
    filename: data.filename,
    contentType: data.content_type,
    contractType: data.contract_type as import('../types').ContractType | null,
    textChars: data.text_chars,
    textPreview: data.text_preview,
    riskLevel: data.risk_level,
    riskCount: data.risk_count,
    reportJson: data.report_json,
    reportMarkdown: data.report_markdown,
    requestId: data.request_id,
    createdAt: data.created_at || new Date().toISOString(),
  };
}

/**
 * 审查合同（上传文件）
 */
export async function apiReviewContract(file: File): Promise<ReviewContractResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<{
    filename: string;
    content_type: string | null;
    contract_type: string | null;
    text_chars: number;
    text_preview: string;
    risk_level: 'low' | 'medium' | 'high';
    risk_count: number;
    report_json: import('../types').ContractReviewReport;
    report_markdown: string;
    request_id: string;
  }>(`${API_BASE}/review`, formData);

  const data = response.data;

  return {
    filename: data.filename,
    contentType: data.content_type,
    contractType: data.contract_type as import('../types').ContractType | null,
    textChars: data.text_chars,
    textPreview: data.text_preview,
    riskLevel: data.risk_level,
    riskCount: data.risk_count,
    reportJson: data.report_json,
    reportMarkdown: data.report_markdown,
    requestId: data.request_id,
  };
}

/**
 * 对比两个合同文件
 */
export async function apiCompareContracts(
  request: CompareContractsRequest
): Promise<CompareContractsResponse> {
  const formData = new FormData();
  formData.append('original_file', request.originalFile);
  formData.append('new_file', request.newFile);

  try {
    const response = await apiClient.post<{
      original_filename: string;
      new_filename: string;
      differences: Array<{
        type: 'add' | 'remove' | 'modify';
        content: string;
        position: { page: number; line: number };
      }>;
      summary: { added: number; removed: number; modified: number };
      request_id: string;
    }>(`${API_BASE}/compare`, formData);

    const data = response.data;

    return {
      success: true,
      data: {
        originalFilename: data.original_filename,
        newFilename: data.new_filename,
        differences: data.differences.map(diff => ({
          type: diff.type,
          content: diff.content,
          position: {
            page: diff.position.page,
            line: diff.position.line,
          },
        })),
        summary: data.summary,
        requestId: data.request_id,
      },
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : '合同对比失败',
    };
  }
}

/**
 * 生成合同
 */
export async function apiGenerateContract(
  request: GenerateContractRequest
): Promise<GenerateContractResponse> {
  try {
    const response = await apiClient.post<{
      id: string;
      title: string;
      content: string;
      contract_type: string;
      created_at: string;
    }>(`${API_BASE}/generate`, {
      template_id: request.templateId,
      fields: request.fields,
    });

    const data = response.data;

    return {
      success: true,
      contract: {
        id: data.id,
        title: data.title,
        content: data.content,
        contractType: data.contract_type as import('../types').ContractType,
        createdAt: data.created_at,
      },
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : '生成合同失败',
    };
  }
}

/**
 * 删除审查记录
 */
export async function apiDeleteReview(reviewId: string): Promise<DeleteReviewResponse> {
  try {
    const response = await apiClient.delete<{ message?: string }>(`${API_BASE}/review/history/${reviewId}`);
    return {
      success: true,
      message: response.data.message || '删除成功',
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : '删除记录失败',
    };
  }
}

/**
 * 导出审查报告为 PDF
 */
export async function apiExportReportPdf(
  reviewId: string,
  options: ExportReportOptions = {}
): Promise<Blob> {
  const searchParams = new URLSearchParams();
  searchParams.set('includeDetailedRisks', String(options.includeDetailedRisks ?? true));
  searchParams.set('includeRecommendedEdits', String(options.includeRecommendedEdits ?? true));
  searchParams.set('includeMissingClauses', String(options.includeMissingClauses ?? true));

  const response = await fetch(
    `${API_BASE}/review/${reviewId}/export/pdf?${searchParams.toString()}`,
    {
      method: 'GET',
      credentials: 'include',
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '导出 PDF 失败' })) as { detail?: string };
    throw new Error(error.detail || '导出 PDF 失败');
  }

  return response.blob();
}

/**
 * 导出审查报告为 Word
 */
export async function apiExportReportWord(
  reviewId: string,
  options: ExportReportOptions = {}
): Promise<Blob> {
  const searchParams = new URLSearchParams();
  searchParams.set('includeDetailedRisks', String(options.includeDetailedRisks ?? true));
  searchParams.set('includeRecommendedEdits', String(options.includeRecommendedEdits ?? true));
  searchParams.set('includeMissingClauses', String(options.includeMissingClauses ?? true));

  const response = await fetch(
    `${API_BASE}/review/${reviewId}/export/word?${searchParams.toString()}`,
    {
      method: 'GET',
      credentials: 'include',
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '导出 Word 失败' })) as { detail?: string };
    throw new Error(error.detail || '导出 Word 失败');
  }

  return response.blob();
}

/**
 * 下载 Blob 文件
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}