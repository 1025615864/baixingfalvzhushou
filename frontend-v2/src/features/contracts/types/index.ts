/**
 * Contracts（合同管理）类型定义
 */

// ==================== 核心类型 ====================

/** 风险等级 */
export type RiskLevel = 'low' | 'medium' | 'high';

/** 合同类型 */
export type ContractType =
  | 'sales'           // 买卖合同
  | 'lease'           // 租赁合同
  | 'labor'           // 劳动合同
  | 'loan'            // 借款合同
  | 'service'         // 服务合同
  | 'cooperation'     // 合作协议
  | 'confidentiality' // 保密协议
  | 'other';          // 其他

/** 差异类型 */
export type DiffType = 'add' | 'remove' | 'modify';

/** 风险项 */
export interface RiskItem {
  id: string;
  type: string;
  severity: RiskLevel;
  description: string;
  clause: string;
  suggestion: string;
}

/** 缺失条款 */
export interface MissingClause {
  clause: string;
  importance: RiskLevel;
  suggestion: string;
}

/** 建议修改 */
export interface SuggestedEdit {
  original: string;
  suggested: string;
  reason: string;
}

/** 合同审查报告 JSON 结构 */
export interface ContractReviewReport {
  summary: string;
  overallRiskLevel: RiskLevel;
  riskCount: number;
  risks: RiskItem[];
  missingClauses: MissingClause[];
  suggestedEdits: SuggestedEdit[];
  legalBasis: string[];
  recommendations: string[];
}

// ==================== 审查记录类型 ====================

/** 审查历史记录项 */
export interface ContractReviewHistoryItem {
  id: string;
  filename: string;
  contractType: ContractType | null;
  riskLevel: RiskLevel;
  riskCount: number;
  requestId: string;
  createdAt: string;
}

/** 审查详情 */
export interface ContractReviewDetail {
  id: string;
  filename: string;
  contentType: string | null;
  contractType: ContractType | null;
  textChars: number;
  textPreview: string;
  riskLevel: RiskLevel;
  riskCount: number;
  reportJson: ContractReviewReport;
  reportMarkdown: string;
  requestId: string;
  createdAt: string;
}

// ==================== 版本对比类型 ====================

/** 差异项 */
export interface ContractDiffItem {
  type: DiffType;
  content: string;
  position: {
    page: number;
    line: number;
  };
}

/** 合同对比结果 */
export interface ContractCompareResult {
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

// ==================== 合同生成功型 ====================

/** 合同生成模板 */
export interface ContractTemplate {
  id: string;
  name: string;
  description: string;
  contractType: ContractType;
  fields: ContractTemplateField[];
}

/** 模板字段 */
export interface ContractTemplateField {
  key: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'select' | 'textarea';
  required: boolean;
  options?: string[];
  placeholder?: string;
  defaultValue?: string;
}

/** 生成的合同 */
export interface GeneratedContract {
  id: string;
  title: string;
  content: string;
  contractType: ContractType;
  createdAt: string;
}

// ==================== API 请求/响应类型 ====================

/** 获取审查历史请求 */
export interface GetReviewHistoryRequest {
  page?: number;
  pageSize?: number;
}

/** 获取审查历史响应 */
export interface GetReviewHistoryResponse {
  items: ContractReviewHistoryItem[];
  total: number;
  page: number;
  pageSize: number;
}

/** 审查合同响应 */
export interface ReviewContractResponse {
  filename: string;
  contentType: string | null;
  contractType: ContractType | null;
  textChars: number;
  textPreview: string;
  riskLevel: RiskLevel;
  riskCount: number;
  reportJson: ContractReviewReport;
  reportMarkdown: string;
  requestId: string;
}

/** 审查合同错误响应 */
export interface ReviewContractErrorResponse {
  errorCode: string;
  message: string;
  requestId: string;
}

/** 对比合同请求 */
export interface CompareContractsRequest {
  originalFile: File;
  newFile: File;
}

/** 对比合同响应 */
export interface CompareContractsResponse {
  success: boolean;
  data?: ContractCompareResult;
  error?: string;
}

/** 生成合同请求 */
export interface GenerateContractRequest {
  templateId: string;
  fields: Record<string, string>;
}

/** 生成合同响应 */
export interface GenerateContractResponse {
  success: boolean;
  contract?: GeneratedContract;
  error?: string;
}

/** 导出报告选项 */
export interface ExportReportOptions {
  includeDetailedRisks?: boolean;
  includeRecommendedEdits?: boolean;
  includeMissingClauses?: boolean;
}

/** 删除审查记录响应 */
export interface DeleteReviewResponse {
  success: boolean;
  message?: string;
  error?: string;
}