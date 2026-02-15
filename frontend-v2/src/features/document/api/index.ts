/**
 * 文档管理功能 API 层
 * 基于统一的 apiClient，对接后端 /documents 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  Document as _Document,
  DocumentItem,
  DocumentListResponse,
  DocumentDetail,
  CreateDocumentDTO,
  UpdateDocumentDTO,
  ExportDocumentDTO,
  GenerateDocumentDTO,
  DocumentGenerateResponse,
  DocumentQueryParams,
  DocumentTypeInfo,
  DocumentType,
  // 文档模板管理类型
  DocumentTemplate,
  TemplateVariable,
  GetDocumentTemplatesRequest,
  GetDocumentTemplatesResponse,
  CreateDocumentTemplateRequest,
  UpdateDocumentTemplateRequest,
  PreviewTemplateRequest,
} from '../types';


// API 基础路径
const API_BASE = '/documents';

// ==================== 后端响应类型定义 ====================

/** 后端文档列表项响应 */
interface BackendDocumentItemResponse {
  id: number;
  document_type: string;
  title: string;
  created_at: string;
}

/** 后端文档列表响应 */
interface BackendDocumentListResponse {
  items: BackendDocumentItemResponse[];
  total: number;
}

/** 后端文档详情响应 */
interface BackendDocumentDetailResponse {
  id: number;
  user_id: number;
  document_type: string;
  title: string;
  content: string;
  payload_json: string | null;
  template_key: string | null;
  template_version: number | null;
  version: number;
  parent_id: number | null;
  version_note: string | null;
  created_at: string;
  updated_at: string;
}

/** 后端文档生成响应 */
interface BackendDocumentGenerateResponse {
  document_type: string;
  title: string;
  content: string;
  created_at: string;
  template_key: string | null;
  template_version: number | null;
}

/** 后端文档类型响应 */
interface BackendDocumentTypeResponse {
  key: string;
  name: string;
  description: string;
  category: string;
}

// ==================== 转换函数 ====================

/**
 * 转换后端文档列表项到前端格式
 */
function mapBackendToDocumentItem(data: BackendDocumentItemResponse): DocumentItem {
  return {
    id: data.id,
    documentType: data.document_type as DocumentItem['documentType'],
    title: data.title,
    createdAt: data.created_at,
  };
}

/**
 * 转换后端文档详情到前端格式
 */
function mapBackendToDocumentDetail(data: BackendDocumentDetailResponse): DocumentDetail {
  return {
    id: data.id,
    userId: data.user_id,
    documentType: data.document_type as DocumentType,
    title: data.title,
    content: data.content,
    payloadJson: data.payload_json,
    templateKey: data.template_key,
    templateVersion: data.template_version,
    version: data.version,
    parentId: data.parent_id,
    versionNote: data.version_note,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    canExport: true,
  };
}

/**
 * 转换后端文档生成响应到前端格式
 */
function mapBackendToGenerateResponse(data: BackendDocumentGenerateResponse): DocumentGenerateResponse {
  return {
    documentType: data.document_type,
    title: data.title,
    content: data.content,
    createdAt: data.created_at,
    templateKey: data.template_key,
    templateVersion: data.template_version,
  };
}

// ==================== 文档管理 API ====================

/**
 * 获取我的文档列表
 */
export async function apiGetMyDocuments(params?: DocumentQueryParams): Promise<DocumentListResponse> {
  const response = await apiClient.get<BackendDocumentListResponse>(`${API_BASE}/my`, {
    params: {
      page: params?.page || 1,
      page_size: params?.pageSize || 20,
    },
  });

  return {
    items: response.data.items.map(mapBackendToDocumentItem),
    total: response.data.total,
  };
}

/**
 * 获取文档详情
 */
export async function apiGetDocument(docId: number): Promise<DocumentDetail> {
  const response = await apiClient.get<BackendDocumentDetailResponse>(`${API_BASE}/my/${docId}`);
  return mapBackendToDocumentDetail(response.data);
}

/**
 * 创建文档
 */
export async function apiCreateDocument(data: CreateDocumentDTO): Promise<{ id: number; message: string }> {
  const response = await apiClient.post<{ id: number; message: string }>(`${API_BASE}/save`, {
    document_type: data.documentType,
    title: data.title,
    content: data.content,
    payload: data.payload,
    template_key: data.templateKey,
    template_version: data.templateVersion,
  });
  return response.data;
}

/**
 * 更新文档
 * 注意：后端目前没有直接更新接口，需要保存为新版本或删除后重建
 */
export async function apiUpdateDocument(docId: number, data: UpdateDocumentDTO): Promise<DocumentDetail> {
  // 先获取原文档
  const existingDoc = await apiGetDocument(docId);
  
  // 创建新版本
  const response = await apiClient.post<BackendDocumentDetailResponse>(`${API_BASE}/save`, {
    document_type: existingDoc.documentType,
    title: data.title || existingDoc.title,
    content: data.content || existingDoc.content,
    payload: data.payload || (existingDoc.payloadJson ? JSON.parse(existingDoc.payloadJson) as Record<string, unknown> : undefined),
    template_key: existingDoc.templateKey,
    template_version: existingDoc.templateVersion,
  });
  
  // 删除旧版本
  await apiDeleteDocument(docId);
  
  return mapBackendToDocumentDetail(response.data);
}

/**
 * 删除文档
 */
export async function apiDeleteDocument(docId: number): Promise<{ message: string }> {
  const response = await apiClient.delete<{ message: string }>(`${API_BASE}/my/${docId}`);
  return response.data;
}

/**
 * 导出文档为PDF
 */
export async function apiExportDocumentPdf(data: ExportDocumentDTO): Promise<Blob> {
  const response = await apiClient.post(`${API_BASE}/export/pdf`, {
    title: data.title,
    content: data.content,
  }, {
    responseType: 'blob',
  });
  return response.data as Blob;
}

/**
 * 导出我的文档
 */
export async function apiExportMyDocument(docId: number): Promise<Blob> {
  const response = await apiClient.get(`${API_BASE}/my/${docId}/export`, {
    responseType: 'blob',
  });
  return response.data as Blob;
}

// ==================== 文档生成 API ====================

/**
 * 生成法律文书
 */
export async function apiGenerateDocument(data: GenerateDocumentDTO): Promise<DocumentGenerateResponse> {
  const response = await apiClient.post<BackendDocumentGenerateResponse>(`${API_BASE}/generate`, {
    document_type: data.documentType,
    case_type: data.caseType,
    plaintiff_name: data.plaintiffName,
    defendant_name: data.defendantName,
    facts: data.facts,
    claims: data.claims,
    evidence: data.evidence,
    extra_info: data.extraInfo,
  });
  return mapBackendToGenerateResponse(response.data);
}

/**
 * 获取支持的文档类型
 */
export async function apiGetDocumentTypes(): Promise<DocumentTypeInfo[]> {
  const response = await apiClient.get<BackendDocumentTypeResponse[]>(`${API_BASE}/types`);
  return response.data.map(item => ({
    key: item.key,
    name: item.name,
    description: item.description,
    category: item.category,
  }));
}

// ==================== 文档模板管理API（管理员用） ====================

const ADMIN_API_BASE = '/v1/admin';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
}

/**
 * 安全获取 JSON 响应
 */
async function safeJson<T>(response: Response): Promise<T> {
  const data = await response.json() as T;
  return data;
}

/**
 * 获取 API 错误信息
 */
function getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiErrorResponse).detail || defaultMsg;
  }
  return defaultMsg;
}

/**
 * 转换后端模板数据到前端格式
 */
function mapBackendToTemplate(data: {
  id: number;
  key: string;
  name: string;
  description: string;
  document_type: string;
  category: string;
  content: string;
  variables: Array<{
    name: string;
    type: string;
    label: string;
    description?: string;
    required: boolean;
    default_value?: string;
    options?: string[];
  }>;
  status: string;
  version: number;
  is_default: boolean;
  usage_count: number;
  created_by: string;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}): DocumentTemplate {
  return {
    id: String(data.id),
    key: data.key,
    name: data.name,
    description: data.description,
    documentType: data.document_type as DocumentTemplate['documentType'],
    category: data.category,
    content: data.content,
    variables: (data.variables ?? []).map((v) => ({
      name: v.name,
      type: v.type as TemplateVariable['type'],
      label: v.label,
      description: v.description,
      required: v.required,
      defaultValue: v.default_value,
      options: v.options,
    })),
    status: data.status as DocumentTemplate['status'],
    version: data.version,
    isDefault: data.is_default,
    usageCount: data.usage_count,
    createdBy: data.created_by,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    publishedAt: data.published_at,
  };
}

/**
 * 获取文档模板列表（管理员用）
 */
export async function apiGetDocumentTemplates(
  params: GetDocumentTemplatesRequest = {}
): Promise<GetDocumentTemplatesResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));
  if (params.documentType) searchParams.set('document_type', params.documentType);
  if (params.status) searchParams.set('status', params.status);
  if (params.category) searchParams.set('category', params.category);
  if (params.keyword) searchParams.set('keyword', params.keyword);

  const response = await fetch(`${ADMIN_API_BASE}/document-templates?${searchParams.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取文档模板列表失败' }));
    throw new Error(getErrorMessage(error, '获取文档模板列表失败'));
  }

  const data = await safeJson<{
    items: Array<{
      id: number;
      key: string;
      name: string;
      description: string;
      document_type: string;
      category: string;
      content: string;
      variables: Array<{
        name: string;
        type: string;
        label: string;
        description?: string;
        required: boolean;
        default_value?: string;
        options?: string[];
      }>;
      status: string;
      version: number;
      is_default: boolean;
      usage_count: number;
      created_by: string;
      created_at: string;
      updated_at: string;
      published_at: string | null;
    }>;
    total: number;
    page: number;
    page_size: number;
    categories: string[];
  }>(response);

  return {
    items: (data.items ?? []).map(mapBackendToTemplate),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    categories: data.categories ?? [],
  };
}

/**
 * 获取文档模板详情（管理员用）
 */
export async function apiGetDocumentTemplate(id: string): Promise<DocumentTemplate> {
  const response = await fetch(`${ADMIN_API_BASE}/document-templates/${id}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取文档模板详情失败' }));
    throw new Error(getErrorMessage(error, '获取文档模板详情失败'));
  }

  const data = await safeJson<{
    id: number;
    key: string;
    name: string;
    description: string;
    document_type: string;
    category: string;
    content: string;
    variables: Array<{
      name: string;
      type: string;
      label: string;
      description?: string;
      required: boolean;
      default_value?: string;
      options?: string[];
    }>;
    status: string;
    version: number;
    is_default: boolean;
    usage_count: number;
    created_by: string;
    created_at: string;
    updated_at: string;
    published_at: string | null;
  }>(response);

  return mapBackendToTemplate(data);
}

/**
 * 创建文档模板（管理员用）
 */
export async function apiCreateDocumentTemplate(
  request: CreateDocumentTemplateRequest
): Promise<DocumentTemplate> {
  const response = await apiClient.post<{
    id: number;
    key: string;
    name: string;
    description: string;
    document_type: string;
    category: string;
    content: string;
    variables: Array<{
      name: string;
      type: string;
      label: string;
      description?: string;
      required: boolean;
      default_value?: string;
      options?: string[];
    }>;
    status: string;
    version: number;
    is_default: boolean;
    usage_count: number;
    created_by: string;
    created_at: string;
    updated_at: string;
    published_at: string | null;
  }>(`${ADMIN_API_BASE}/document-templates`, {
    key: request.key,
    name: request.name,
    description: request.description,
    document_type: request.documentType,
    category: request.category,
    content: request.content,
    variables: request.variables,
    is_default: request.isDefault,
  });

  return mapBackendToTemplate(response.data);
}

/**
 * 更新文档模板（管理员用）
 */
export async function apiUpdateDocumentTemplate(
  id: string,
  request: UpdateDocumentTemplateRequest
): Promise<DocumentTemplate> {
  const response = await apiClient.put<{
    id: number;
    key: string;
    name: string;
    description: string;
    document_type: string;
    category: string;
    content: string;
    variables: Array<{
      name: string;
      type: string;
      label: string;
      description?: string;
      required: boolean;
      default_value?: string;
      options?: string[];
    }>;
    status: string;
    version: number;
    is_default: boolean;
    usage_count: number;
    created_by: string;
    created_at: string;
    updated_at: string;
    published_at: string | null;
  }>(`${ADMIN_API_BASE}/document-templates/${id}`, {
    name: request.name,
    description: request.description,
    category: request.category,
    content: request.content,
    variables: request.variables,
    is_default: request.isDefault,
  });

  return mapBackendToTemplate(response.data);
}

/**
 * 删除文档模板（管理员用）
 */
export async function apiDeleteDocumentTemplate(id: string): Promise<void> {
  await apiClient.delete(`${ADMIN_API_BASE}/document-templates/${id}`);
}

/**
 * 发布文档模板（管理员用）
 */
export async function apiPublishDocumentTemplate(id: string): Promise<DocumentTemplate> {
  const response = await apiClient.post<{
    id: number;
    key: string;
    name: string;
    description: string;
    document_type: string;
    category: string;
    content: string;
    variables: Array<{
      name: string;
      type: string;
      label: string;
      description?: string;
      required: boolean;
      default_value?: string;
      options?: string[];
    }>;
    status: string;
    version: number;
    is_default: boolean;
    usage_count: number;
    created_by: string;
    created_at: string;
    updated_at: string;
    published_at: string | null;
  }>(`${ADMIN_API_BASE}/document-templates/${id}/publish`, {});

  return mapBackendToTemplate(response.data);
}

/**
 * 预览模板（管理员用）
 */
export async function apiPreviewTemplate(
  request: PreviewTemplateRequest
): Promise<{ content: string }> {
  const response = await apiClient.post<{ content: string }>(
    `${ADMIN_API_BASE}/document-templates/${request.templateId}/preview`,
    { variables: request.variables }
  );
  return response.data;
}