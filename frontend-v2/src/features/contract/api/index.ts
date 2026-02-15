/**
 * Contract（合同审查）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/contracts 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  ContractReviewReport,
  ContractReviewHistory,
  ContractReviewHistoryListResponse,
  ContractComparison,
  ExportOptions,
} from '../types';


// API 基础路径
const API_BASE = '/contracts';

// ==================== 后端响应类型定义 ====================

/** 后端风险点 */
interface BackendContractRisk {
  id: string;
  type: string;
  description: string;
  severity: string;
  suggestion: string;
  clause?: string;
  position?: {
    start: number;
    end: number;
  };
}

/** 后端缺失条款 */
interface BackendMissingClause {
  type: string;
  description: string;
  importance: string;
  suggestion: string;
}

/** 后端建议修改 */
interface BackendSuggestedEdit {
  original: string;
  suggested: string;
  reason: string;
  position?: {
    start: number;
    end: number;
  };
}

/** 后端审查报告 */
interface BackendContractReviewResponse {
  filename: string;
  content_type: string;
  contract_type?: string;
  text_chars: number;
  text_preview: string;
  risk_level: string;
  risk_count: number;
  report_json: {
    risks?: BackendContractRisk[];
    missing_clauses?: BackendMissingClause[];
    suggested_edits?: BackendSuggestedEdit[];
    summary?: string;
  };
  report_markdown: string;
  request_id: string;
}

/** 后端历史记录项 */
interface BackendReviewHistoryItem {
  id: string;
  filename: string;
  contract_type?: string;
  risk_level: string;
  risk_count: number;
  request_id: string;
  created_at: string;
}

/** 后端历史列表响应 */
interface BackendReviewHistoryListResponse {
  items: BackendReviewHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端差异项 */
interface BackendDiffItem {
  type: string;
  content: string;
  position: {
    page?: number;
    line?: number;
    start?: number;
    end?: number;
  };
}

/** 后端比对响应 */
interface BackendCompareResponse {
  original_filename: string;
  new_filename: string;
  differences: BackendDiffItem[];
  summary: {
    added: number;
    removed: number;
    modified: number;
  };
  request_id: string;
}

// ==================== 转换函数 ====================

/**
 * 转换后端风险点到前端格式
 */
function mapBackendToRisk(risk: BackendContractRisk) {
  return {
    id: risk.id,
    type: risk.type,
    description: risk.description,
    severity: risk.severity as ContractReviewReport['riskLevel'],
    suggestion: risk.suggestion,
    clause: risk.clause,
    position: risk.position,
  };
}

/**
 * 转换后端缺失条款到前端格式
 */
function mapBackendToMissingClause(clause: BackendMissingClause) {
  return {
    type: clause.type,
    description: clause.description,
    importance: clause.importance as ContractReviewReport['riskLevel'],
    suggestion: clause.suggestion,
  };
}

/**
 * 转换后端建议修改到前端格式
 */
function mapBackendToSuggestedEdit(edit: BackendSuggestedEdit) {
  return {
    original: edit.original,
    suggested: edit.suggested,
    reason: edit.reason,
    position: edit.position,
  };
}

/**
 * 转换后端审查报告到前端格式
 */
function mapBackendToReviewReport(data: BackendContractReviewResponse): ContractReviewReport {
  const reportJson = data.report_json || {};

  return {
    filename: data.filename,
    contentType: data.content_type,
    contractType: data.contract_type,
    textChars: data.text_chars,
    textPreview: data.text_preview,
    riskLevel: data.risk_level as ContractReviewReport['riskLevel'],
    riskCount: data.risk_count,
    risks: (reportJson.risks || []).map(mapBackendToRisk),
    missingClauses: (reportJson.missing_clauses || []).map(mapBackendToMissingClause),
    suggestedEdits: (reportJson.suggested_edits || []).map(mapBackendToSuggestedEdit),
    summary: reportJson.summary || '',
    requestId: data.request_id,
    createdAt: new Date().toISOString(),
  };
}

/**
 * 转换后端历史记录到前端格式
 */
function mapBackendToHistoryItem(item: BackendReviewHistoryItem): ContractReviewHistory {
  return {
    id: item.id,
    filename: item.filename,
    contractType: item.contract_type,
    riskLevel: item.risk_level as ContractReviewHistory['riskLevel'],
    riskCount: item.risk_count,
    requestId: item.request_id,
    createdAt: item.created_at,
  };
}

/**
 * 转换后端差异项到前端格式
 */
function mapBackendToDiffItem(item: BackendDiffItem) {
  return {
    type: item.type as ContractComparison['differences'][0]['type'],
    content: item.content,
    position: item.position,
  };
}

/**
 * 转换后端比对结果到前端格式
 */
function mapBackendToComparison(data: BackendCompareResponse): ContractComparison {
  return {
    originalFilename: data.original_filename,
    newFilename: data.new_filename,
    differences: data.differences.map(mapBackendToDiffItem),
    summary: {
      added: data.summary.added,
      removed: data.summary.removed,
      modified: data.summary.modified,
    },
    requestId: data.request_id,
  };
}

// ==================== 合同审查 API ====================

/**
 * 上传合同进行审查
 */
export async function apiReviewContract(file: File): Promise<ContractReviewReport> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<BackendContractReviewResponse>(
    `${API_BASE}/review`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return mapBackendToReviewReport(response.data);
}

// ==================== 历史记录 API ====================

/**
 * 获取审查历史列表
 */
export async function apiGetReviewHistory(
  page: number = 1,
  pageSize: number = 10
): Promise<ContractReviewHistoryListResponse> {
  const response = await apiClient.get<BackendReviewHistoryListResponse>(
    `${API_BASE}/review/history`,
    {
      params: {
        page,
        page_size: pageSize,
      },
    }
  );

  return {
    items: response.data.items.map(mapBackendToHistoryItem),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

/**
 * 获取单个审查详情
 */
export async function apiGetReviewDetail(reviewId: string): Promise<ContractReviewReport> {
  const response = await apiClient.get<BackendContractReviewResponse>(
    `${API_BASE}/review/history/${reviewId}`
  );

  return mapBackendToReviewReport(response.data);
}

/**
 * 删除审查记录
 */
export async function apiDeleteReview(reviewId: string): Promise<{ message: string }> {
  await apiClient.delete(`${API_BASE}/review/history/${reviewId}`);
  return { message: '删除成功' };
}

// ==================== 合同比对 API ====================

/**
 * 比对两个合同文件
 */
export async function apiCompareContracts(
  originalFile: File,
  newFile: File
): Promise<ContractComparison> {
  const formData = new FormData();
  formData.append('original_file', originalFile);
  formData.append('new_file', newFile);

  const response = await apiClient.post<BackendCompareResponse>(
    `${API_BASE}/compare`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return mapBackendToComparison(response.data);
}

// ==================== 导出 API ====================

/**
 * 导出审查报告为 PDF
 */
export async function apiExportReviewPdf(
  reviewId: string,
  options?: ExportOptions
): Promise<Blob> {
  const response = await apiClient.get<Blob>(
    `${API_BASE}/review/${reviewId}/export/pdf`,
    {
      params: {
        includeDetailedRisks: options?.includeDetailedRisks ?? true,
        includeRecommendedEdits: options?.includeRecommendedEdits ?? true,
        includeMissingClauses: options?.includeMissingClauses ?? true,
      },
      responseType: 'blob',
    }
  );

  return response.data;
}

/**
 * 导出审查报告为 Word
 */
export async function apiExportReviewWord(
  reviewId: string,
  options?: ExportOptions
): Promise<Blob> {
  const response = await apiClient.get<Blob>(
    `${API_BASE}/review/${reviewId}/export/word`,
    {
      params: {
        includeDetailedRisks: options?.includeDetailedRisks ?? true,
        includeRecommendedEdits: options?.includeRecommendedEdits ?? true,
        includeMissingClauses: options?.includeMissingClauses ?? true,
      },
      responseType: 'blob',
    }
  );

  return response.data;
}

// ==================== 统一导出 ====================

/**
 * Contract API 统一导出对象
 */
export const contractApi = {
  // 合同审查
  reviewContract: apiReviewContract,

  // 历史记录
  getReviewHistory: apiGetReviewHistory,
  getReviewDetail: apiGetReviewDetail,
  deleteReview: apiDeleteReview,

  // 合同比对
  compareContracts: apiCompareContracts,

  // 导出报告
  exportReviewPdf: apiExportReviewPdf,
  exportReviewWord: apiExportReviewWord,
} as const;

export default contractApi;