/**
 * 文档管理功能类型定义
 */

/**
 * 文档文件类型（用于文件上传管理）
 */
export type DocumentFileType =
  | 'contract'      // 合同
  | 'agreement'     // 协议
  | 'certificate'   // 证件
  | 'evidence'      // 证据材料
  | 'other';        // 其他

/**
 * 文档状态
 */
export type DocumentStatus = 'draft' | 'pending' | 'approved' | 'rejected' | 'archived' | 'deleted';

/**
 * 文档类型枚举（用于文档生成）
 */
export type DocumentType = 
  | 'contract'      // 合同
  | 'agreement'     // 协议
  | 'memo'          // 备忘录
  | 'letter'        // 律师函
  | 'complaint'     // 起诉状
  | 'defense'       // 答辩状
  | 'appeal'        // 上诉状
  | 'application'   // 申请书
  | 'other';        // 其他

/**
 * 文档类型标签配置
 */
export const DOCUMENT_TYPE_LABELS: Record<DocumentType, { label: string; color: string }> = {
  contract: { label: '合同', color: 'bg-blue-100 text-blue-700' },
  agreement: { label: '协议', color: 'bg-green-100 text-green-700' },
  memo: { label: '备忘录', color: 'bg-yellow-100 text-yellow-700' },
  letter: { label: '律师函', color: 'bg-purple-100 text-purple-700' },
  complaint: { label: '起诉状', color: 'bg-red-100 text-red-700' },
  defense: { label: '答辩状', color: 'bg-orange-100 text-orange-700' },
  appeal: { label: '上诉状', color: 'bg-pink-100 text-pink-700' },
  application: { label: '申请书', color: 'bg-cyan-100 text-cyan-700' },
  other: { label: '其他', color: 'bg-gray-100 text-gray-700' },
};

/**
 * 导出格式枚举
 */
export type ExportFormat = 'pdf' | 'word';

/**
 * 导出格式配置
 */
export const EXPORT_FORMAT_CONFIG: Record<ExportFormat, { label: string; icon: string; mimeType: string; extension: string }> = {
  pdf: { 
    label: 'PDF', 
    icon: 'DocumentTextIcon', 
    mimeType: 'application/pdf', 
    extension: '.pdf' 
  },
  word: { 
    label: 'Word', 
    icon: 'DocumentIcon', 
    mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
    extension: '.docx' 
  },
};

/**
 * 文档接口（文件上传管理版本）
 */
export interface Document {
  /** 文档ID */
  id: string;
  /** 文档标题 */
  title: string;
  /** 文档描述 */
  description: string;
  /** 文件名 */
  fileName: string;
  /** 文件URL */
  fileUrl: string;
  /** 文件类型 */
  fileType: string;
  /** 文件大小 */
  fileSize: number;
  /** 文档类型 */
  type: DocumentFileType;
  /** 文档状态 */
  status: DocumentStatus;
  /** 用户ID */
  userId: string;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
  /** 标签 */
  tags: string[];
}

/**
 * 文档筛选条件
 */
export interface DocumentFilters {
  type?: DocumentFileType;
  status?: DocumentStatus;
  searchQuery?: string;
}

/**
 * 上传文档DTO
 */
export interface UploadDocumentDTO {
  title: string;
  description: string;
  type: DocumentFileType;
  file: File;
  tags?: string[];
}

/**
 * 生成文档接口（文档生成版本）
 */
export interface GeneratedDocument {
  /** 文档ID */
  id: number;
  /** 用户ID */
  userId: number;
  /** 文档类型 */
  documentType: DocumentType;
  /** 文档标题 */
  title: string;
  /** 文档内容 */
  content: string;
  /** 模板Key */
  templateKey: string | null;
  /** 模板版本 */
  templateVersion: number | null;
  /** 额外数据JSON */
  payloadJson: string | null;
  /** 版本号 */
  version: number;
  /** 父文档ID */
  parentId: number | null;
  /** 版本说明 */
  versionNote: string | null;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
}

/**
 * 简化文档项（列表展示用）
 */
export interface DocumentItem {
  id: number;
  documentType: DocumentType;
  title: string;
  createdAt: string;
}

/**
 * 文档列表响应
 */
export interface DocumentListResponse {
  /** 文档列表 */
  items: DocumentItem[];
  /** 总数 */
  total: number;
}

/**
 * 文档详情（文档生成版本）
 */
export interface DocumentDetail {
  /** 文档ID */
  id: number;
  /** 用户ID */
  userId: number;
  /** 文档类型 */
  documentType: DocumentType;
  /** 文档标题 */
  title: string;
  /** 文档内容 */
  content: string;
  /** 额外数据JSON */
  payloadJson: string | null;
  /** 模板Key */
  templateKey: string | null;
  /** 模板版本 */
  templateVersion: number | null;
  /** 版本号 */
  version: number;
  /** 父文档ID */
  parentId: number | null;
  /** 版本说明 */
  versionNote: string | null;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
  /** 可导出标记 */
  canExport: boolean;
}

/**
 * 创建文档请求DTO
 */
export interface CreateDocumentDTO {
  /** 文档类型 */
  documentType: DocumentType;
  /** 文档标题 */
  title: string;
  /** 文档内容 */
  content: string;
  /** 额外数据 */
  payload?: Record<string, unknown>;
  /** 模板Key */
  templateKey?: string;
  /** 模板版本 */
  templateVersion?: number;
}

/**
 * 更新文档请求DTO
 */
export interface UpdateDocumentDTO {
  /** 文档标题 */
  title?: string;
  /** 文档内容 */
  content?: string;
  /** 额外数据 */
  payload?: Record<string, unknown>;
}

/**
 * 导出文档请求DTO
 */
export interface ExportDocumentDTO {
  /** 文档标题 */
  title: string;
  /** 文档内容 */
  content: string;
  /** 导出格式 */
  format?: ExportFormat;
}

/**
 * 文档查询参数
 */
export interface DocumentQueryParams {
  /** 页码 */
  page?: number;
  /** 每页数量 */
  pageSize?: number;
  /** 文档类型筛选 */
  documentType?: DocumentType;
  /** 关键词搜索 */
  keyword?: string;
}

/**
 * 生成文档请求DTO
 */
export interface GenerateDocumentDTO {
  /** 文档类型 */
  documentType: string;
  /** 案件类型 */
  caseType: string;
  /** 原告名称 */
  plaintiffName: string;
  /** 被告名称 */
  defendantName: string;
  /** 案件事实 */
  facts: string;
  /** 诉讼请求/要求 */
  claims: string;
  /** 证据材料 */
  evidence?: string;
  /** 额外信息 */
  extraInfo?: Record<string, string>;
}

/**
 * 文档生成响应
 */
export interface DocumentGenerateResponse {
  documentType: string;
  title: string;
  content: string;
  createdAt: string;
  templateKey: string | null;
  templateVersion: number | null;
}

/**
 * 文档模板类型
 */
export interface DocumentTypeInfo {
  key: string;
  name: string;
  description: string;
  category: string;
}

/**
 * 获取文档类型标签
 */
export function getDocumentTypeLabel(type: DocumentType): string {
  return DOCUMENT_TYPE_LABELS[type]?.label || '其他';
}

/**
 * 获取文档类型样式
 */
export function getDocumentTypeClass(type: DocumentType): string {
  return DOCUMENT_TYPE_LABELS[type]?.color || 'bg-gray-100 text-gray-700';
}

// ==================== 文档模板管理类型（管理员用） ====================

/**
 * 文档模板状态
 */
export type DocumentTemplateStatus = 'draft' | 'published' | 'deprecated';

/**
 * 文档模板
 */
export interface DocumentTemplate {
  id: string;
  key: string;
  name: string;
  description: string;
  documentType: DocumentType;
  category: string;
  content: string;
  variables: TemplateVariable[];
  status: DocumentTemplateStatus;
  version: number;
  isDefault: boolean;
  usageCount: number;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  publishedAt: string | null;
}

/**
 * 模板变量
 */
export interface TemplateVariable {
  name: string;
  type: 'text' | 'number' | 'date' | 'select' | 'textarea';
  label: string;
  description?: string;
  required: boolean;
  defaultValue?: string;
  options?: string[];
}

/**
 * 获取文档模板列表请求
 */
export interface GetDocumentTemplatesRequest {
  page?: number;
  pageSize?: number;
  documentType?: DocumentType;
  status?: DocumentTemplateStatus;
  category?: string;
  keyword?: string;
}

/**
 * 获取文档模板列表响应
 */
export interface GetDocumentTemplatesResponse {
  items: DocumentTemplate[];
  total: number;
  page: number;
  pageSize: number;
  categories: string[];
}

/**
 * 创建文档模板请求
 */
export interface CreateDocumentTemplateRequest {
  key: string;
  name: string;
  description: string;
  documentType: DocumentType;
  category: string;
  content: string;
  variables: TemplateVariable[];
  isDefault?: boolean;
}

/**
 * 更新文档模板请求
 */
export interface UpdateDocumentTemplateRequest {
  name?: string;
  description?: string;
  category?: string;
  content?: string;
  variables?: TemplateVariable[];
  isDefault?: boolean;
}

/**
 * 预览模板请求
 */
export interface PreviewTemplateRequest {
  templateId: string;
  variables: Record<string, string>;
}