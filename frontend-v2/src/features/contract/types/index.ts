/**
 * Contract（合同审查）类型定义
 */

// ==================== 核心类型 ====================

/** 风险等级 */
export type RiskLevel = 'low' | 'medium' | 'high';

/** 审查状态 */
export type ReviewStatus = 'pending' | 'processing' | 'completed' | 'failed';

/** 差异类型 */
export type DiffType = 'add' | 'remove' | 'modify';

/** 风险点 */
export interface ContractRisk {
  id: string;
  type: string;
  description: string;
  severity: RiskLevel;
  suggestion: string;
  clause?: string;
  position?: {
    start: number;
    end: number;
  };
}

/** 缺失条款 */
export interface MissingClause {
  type: string;
  description: string;
  importance: RiskLevel;
  suggestion: string;
}

/** 建议修改 */
export interface SuggestedEdit {
  original: string;
  suggested: string;
  reason: string;
  position?: {
    start: number;
    end: number;
  };
}

/** 合同审查报告 */
export interface ContractReviewReport {
  filename: string;
  contentType: string;
  contractType?: string;
  textChars: number;
  textPreview: string;
  riskLevel: RiskLevel;
  riskCount: number;
  risks: ContractRisk[];
  missingClauses: MissingClause[];
  suggestedEdits: SuggestedEdit[];
  summary: string;
  requestId: string;
  createdAt: string;
}

/** 合同审查历史记录 */
export interface ContractReviewHistory {
  id: string;
  filename: string;
  contractType?: string;
  riskLevel: RiskLevel;
  riskCount: number;
  requestId: string;
  createdAt: string;
}

/** 合同审查历史列表响应 */
export interface ContractReviewHistoryListResponse {
  items: ContractReviewHistory[];
  total: number;
  page: number;
  pageSize: number;
}

/** 差异项 */
export interface ContractDiffItem {
  type: DiffType;
  content: string;
  position: {
    page?: number;
    line?: number;
    start?: number;
    end?: number;
  };
}

/** 合同比对结果 */
export interface ContractComparison {
  originalFilename: string;
  newFilename: string;
  differences: ContractDiffItem[];
  summary: {
    added: number;
    removed: number;
    modified: number;
  };
  requestId: string;
}

/** 导出选项 */
export interface ExportOptions {
  includeDetailedRisks: boolean;
  includeRecommendedEdits: boolean;
  includeMissingClauses: boolean;
}

// ==================== API 请求/响应类型 ====================

/** 上传合同审查请求 */
export interface UploadContractRequest {
  file: File;
}

/** 比对合同请求 */
export interface CompareContractsRequest {
  originalFile: File;
  newFile: File;
}

/** 删除审查记录请求 */
export interface DeleteReviewRequest {
  reviewId: string;
}

/** 导出报告请求 */
export interface ExportReportRequest {
  reviewId: string;
  format: 'pdf' | 'word';
  options?: ExportOptions;
}

/** 批量删除请求 */
export interface BatchDeleteReviewsRequest {
  ids: string[];
}

/** 批量操作响应 */
export interface BatchOperationResponse {
  successCount: number;
  failedCount: number;
  message: string;
}

// ==================== 组件 Props 类型 ====================

/** 合同上传组件 Props */
export interface ContractUploaderProps {
  onUpload: (file: File) => void;
  isLoading?: boolean;
  accept?: string;
  maxSize?: number; // 单位：MB
}

/** 审查结果组件 Props */
export interface ReviewResultProps {
  report: ContractReviewReport;
  onExport?: (format: 'pdf' | 'word') => void;
  onCompare?: () => void;
}

/** 历史记录组件 Props */
export interface ReviewHistoryProps {
  items: ContractReviewHistory[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onDelete: (id: string) => void;
  onView: (id: string) => void;
}

/** 合同比对组件 Props */
export interface ContractComparisonProps {
  originalFile?: File;
  newFile?: File;
  result?: ContractComparison;
  onOriginalSelect: (file: File) => void;
  onNewSelect: (file: File) => void;
  onCompare: () => void;
  isLoading?: boolean;
}

/** 风险卡片组件 Props */
export interface RiskCardProps {
  risk: ContractRisk;
  index: number;
}

/** 差异高亮组件 Props */
export interface DiffViewerProps {
  differences: ContractDiffItem[];
  originalText?: string;
  newText?: string;
}