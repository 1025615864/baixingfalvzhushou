/**
 * Enterprise（企业服务）API 层
 * 对接后端 /api/enterprise 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  EnterpriseInfo,
  EnterpriseOrder,
  TeamMember,
  ContractReview,
  ComplianceTemplate,
  ComplianceReport,
  EnterpriseDocument,
  UpdateEnterpriseInfoRequest,
  UpdateEnterpriseInfoResponse,
  GetTeamMembersRequest,
  GetTeamMembersResponse,
  AddTeamMemberRequest,
  AddTeamMemberResponse,
  RemoveTeamMemberRequest,
  UpdateMemberRoleRequest,
  GetEnterpriseOrdersRequest,
  GetEnterpriseOrdersResponse,
  GetContractReviewsResponse,
  SubmitContractReviewRequest,
  GetPermissionsResponse,
  GetRolePermissionsResponse,
  UpdateRolePermissionsRequest,
  GenerateReportRequest,
  UploadDocumentRequest,
  UpdateDocumentRequest,
  GetDocumentVersionsResponse,
  ComplianceReportStatus,
} from '../types';


// API 基础路径
const API_BASE = '/enterprise';

// ==================== 类型定义 ====================

/** 后端企业信息响应 */
interface BackendEnterpriseInfo {
  id: number;
  company_name: string;
  admin_email: string;
  industry: string;
  scale: string;
  subscription_plan: string;
  status: string;
  created_at: string;
  updated_at: string;
  member_count: number;
  contract_count: number;
  quota_used: number;
  quota_total: number;
  logo_url?: string;
  contact_phone?: string;
  contact_name?: string;
  address?: string;
  website?: string;
  description?: string;
}

/** 后端团队成员 */
interface BackendTeamMember {
  id: number;
  user_id: number;
  enterprise_id: number;
  name: string;
  email: string;
  role: string;
  status: string;
  avatar?: string;
  department?: string;
  position?: string;
  joined_at: string;
  last_active_at?: string;
  permissions: string[];
}

/** 后端订单 */
interface BackendOrderItem {
  id: string;
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  description?: string;
}

interface BackendEnterpriseOrder {
  id: string;
  enterprise_id: number;
  order_type: string;
  status: string;
  amount: number;
  currency: string;
  description: string;
  items: BackendOrderItem[];
  created_at: string;
  paid_at?: string;
  completed_at?: string;
  invoice_no?: string;
  payment_method?: string;
}

/** 后端合同审查 */
interface BackendContractReview {
  id: number;
  enterprise_id: number;
  user_id: number;
  title: string;
  contract_type: string;
  status: string;
  content: string;
  review_result?: string;
  risk_level?: string;
  created_at: string;
  completed_at?: string;
  reviewer_id?: number;
}

/** 后端合规报告 */
interface BackendComplianceReport {
  id: number;
  account_id: number;
  name: string;
  type: string;
  status: string;
  content?: string;
  generated_at: string;
  completed_at?: string;
  download_url?: string;
  size?: number;
}

/** 后端合规模板 */
interface BackendComplianceTemplate {
  id: number;
  name: string;
  category: string;
  description: string;
  content: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

/** 后端权限 */
interface BackendPermission {
  id: string;
  name: string;
  code: string;
  description: string;
  category: string;
  default_roles: string[];
}

// ==================== 转换函数 ====================

function mapBackendToEnterpriseInfo(data: BackendEnterpriseInfo): EnterpriseInfo {
  return {
    id: data.id,
    companyName: data.company_name,
    adminEmail: data.admin_email,
    industry: data.industry as EnterpriseInfo['industry'],
    scale: data.scale as EnterpriseInfo['scale'],
    subscriptionPlan: data.subscription_plan as EnterpriseInfo['subscriptionPlan'],
    status: data.status as EnterpriseInfo['status'],
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    memberCount: data.member_count,
    contractCount: data.contract_count,
    quotaUsed: data.quota_used,
    quotaTotal: data.quota_total,
    logoUrl: data.logo_url,
    contactPhone: data.contact_phone,
    contactName: data.contact_name,
    address: data.address,
    website: data.website,
    description: data.description,
  };
}

function mapBackendToTeamMember(user: BackendTeamMember): TeamMember {
  return {
    id: user.id,
    userId: user.user_id,
    enterpriseId: user.enterprise_id,
    name: user.name,
    email: user.email,
    role: user.role as TeamMember['role'],
    status: user.status as TeamMember['status'],
    avatar: user.avatar,
    department: user.department,
    position: user.position,
    joinedAt: user.joined_at,
    lastActiveAt: user.last_active_at,
    permissions: user.permissions,
  };
}

// ==================== 企业信息 API ====================

/**
 * 获取企业信息
 */
export async function apiGetEnterpriseInfo(accountId: number): Promise<EnterpriseInfo> {
  const response = await apiClient.get<BackendEnterpriseInfo>(`${API_BASE}/account/${accountId}`);
  return mapBackendToEnterpriseInfo(response.data);
}

/**
 * 更新企业信息
 */
export async function apiUpdateEnterpriseInfo(
  accountId: number,
  request: UpdateEnterpriseInfoRequest
): Promise<UpdateEnterpriseInfoResponse> {
  const response = await apiClient.post<{
    success: boolean;
    enterprise: BackendEnterpriseInfo;
  }>(`${API_BASE}/account/${accountId}/update`, {
    company_name: request.companyName,
    industry: request.industry,
    scale: request.scale,
    subscription_plan: request.subscriptionPlan,
    contact_phone: request.contactPhone,
    contact_name: request.contactName,
    address: request.address,
    website: request.website,
    description: request.description,
  });
  
  return {
    success: response.data.success,
    enterprise: mapBackendToEnterpriseInfo(response.data.enterprise),
  };
}

// ==================== 团队成员 API ====================

/**
 * 获取团队成员列表
 */
export async function apiGetTeamMembers(
  accountId: number,
  _params: GetTeamMembersRequest = {}
): Promise<GetTeamMembersResponse> {
  const response = await apiClient.get<{
    users: BackendTeamMember[];
    total: number;
  }>(`${API_BASE}/account/${accountId}/users`);
  
  return {
    members: response.data.users.map(mapBackendToTeamMember),
    total: response.data.total,
  };
}

/**
 * 添加团队成员
 */
export async function apiAddTeamMember(
  accountId: number,
  request: AddTeamMemberRequest
): Promise<AddTeamMemberResponse> {
  const response = await apiClient.post<{
    success: boolean;
    member: BackendTeamMember;
    invite_link?: string;
  }>(`${API_BASE}/account/${accountId}/users`, {
    email: request.email,
    name: request.name,
    role: request.role,
  });
  
  return {
    success: response.data.success,
    member: mapBackendToTeamMember(response.data.member),
    inviteLink: response.data.invite_link,
  };
}

/**
 * 移除团队成员
 */
export async function apiRemoveTeamMember(
  accountId: number,
  request: RemoveTeamMemberRequest
): Promise<void> {
  await apiClient.delete(`${API_BASE}/account/${accountId}/users/${request.memberId}`);
}

/**
 * 更新成员角色
 */
export async function apiUpdateMemberRole(
  accountId: number,
  request: UpdateMemberRoleRequest
): Promise<void> {
  await apiClient.put(`${API_BASE}/account/${accountId}/users/${request.memberId}/role`, {
    role: request.role,
  });
}

// ==================== 企业订单 API ====================

/**
 * 获取企业订单列表
 */
export async function apiGetEnterpriseOrders(
  accountId: number,
  params: GetEnterpriseOrdersRequest = {}
): Promise<GetEnterpriseOrdersResponse> {
  const response = await apiClient.get<{
    orders: BackendEnterpriseOrder[];
    total: number;
    total_amount: number;
  }>(`${API_BASE}/account/${accountId}/orders`, {
    params: {
      status: params.status,
      order_type: params.orderType,
      start_date: params.startDate,
      end_date: params.endDate,
      limit: params.limit,
      offset: params.offset,
    },
  });
  
  return {
    orders: response.data.orders.map(order => ({
      id: order.id,
      enterpriseId: order.enterprise_id,
      orderType: order.order_type as EnterpriseOrder['orderType'],
      status: order.status as EnterpriseOrder['status'],
      amount: order.amount,
      currency: order.currency,
      description: order.description,
      items: order.items.map(item => ({
        id: item.id,
        name: item.name,
        quantity: item.quantity,
        unitPrice: item.unit_price,
        totalPrice: item.total_price,
        description: item.description,
      })),
      createdAt: order.created_at,
      paidAt: order.paid_at,
      completedAt: order.completed_at,
      invoiceNo: order.invoice_no,
      paymentMethod: order.payment_method,
    })),
    total: response.data.total,
    totalAmount: response.data.total_amount,
  };
}

// ==================== 合同审查 API ====================

/**
 * 获取合同审查列表
 */
export async function apiGetContractReviews(accountId: number): Promise<GetContractReviewsResponse> {
  const response = await apiClient.get<{
    contracts: BackendContractReview[];
    total: number;
  }>(`${API_BASE}/account/${accountId}/contracts`);
  
  return {
    contracts: response.data.contracts.map(contract => ({
      id: contract.id,
      enterpriseId: contract.enterprise_id,
      userId: contract.user_id,
      title: contract.title,
      contractType: contract.contract_type,
      status: contract.status as ContractReview['status'],
      content: contract.content,
      reviewResult: contract.review_result,
      riskLevel: contract.risk_level as ContractReview['riskLevel'],
      createdAt: contract.created_at,
      completedAt: contract.completed_at,
      reviewerId: contract.reviewer_id,
    })),
    total: response.data.total,
  };
}

/**
 * 提交合同审查
 */
export async function apiSubmitContractReview(
  request: SubmitContractReviewRequest
): Promise<void> {
  await apiClient.post(`${API_BASE}/contracts/review`, {
    account_id: request.accountId,
    title: request.title,
    contract_type: request.contractType,
    content: request.content,
    attachments: request.attachments,
  });
}

// ==================== 合规模板 API ====================

/**
 * 获取合规模板列表
 */
export async function apiGetComplianceTemplates(category?: string): Promise<ComplianceTemplate[]> {
  const response = await apiClient.get<BackendComplianceTemplate[]>(`${API_BASE}/templates`, {
    params: category ? { category } : undefined,
  });
  
  return response.data.map(template => ({
    id: template.id,
    name: template.name,
    category: template.category,
    description: template.description,
    content: template.content,
    tags: template.tags,
    createdAt: template.created_at,
    updatedAt: template.updated_at,
  }));
}

// ==================== 合规报告 API ====================

/**
 * 获取合规报告列表
 */
export async function apiGetComplianceReports(
  accountId: number,
  params: { page?: number; pageSize?: number; type?: string }
): Promise<{ reports: ComplianceReport[]; total: number }> {
  const response = await apiClient.get<{
    reports: BackendComplianceReport[];
    total: number;
  }>(`${API_BASE}/account/${accountId}/compliance-reports`, {
    params,
  });

  return {
    reports: response.data.reports.map(report => ({
      id: report.id,
      accountId: report.account_id,
      name: report.name,
      type: report.type as ComplianceReport['type'],
      status: report.status as ComplianceReportStatus,
      content: report.content,
      generatedAt: report.generated_at,
      completedAt: report.completed_at,
      downloadUrl: report.download_url,
      fileSize: report.size,
      createdAt: report.generated_at,
    })),
    total: response.data.total,
  };
}

/**
 * 获取单个合规报告详情
 */
export async function apiGetComplianceReportById(
  accountId: number,
  reportId: number
): Promise<ComplianceReport> {
  const response = await apiClient.get<BackendComplianceReport>(
    `${API_BASE}/account/${accountId}/compliance-reports/${reportId}`
  );

  return {
    id: response.data.id,
    accountId: response.data.account_id,
    name: response.data.name,
    type: response.data.type as ComplianceReport['type'],
    status: response.data.status as ComplianceReportStatus,
    content: response.data.content,
    generatedAt: response.data.generated_at,
    completedAt: response.data.completed_at,
    downloadUrl: response.data.download_url,
    fileSize: response.data.size,
    createdAt: response.data.generated_at,
  };
}

/**
 * 生成合规报告
 */
export async function apiGenerateComplianceReport(
  request: GenerateReportRequest
): Promise<{ reportId: number }> {
  const response = await apiClient.post<{ report_id: number }>(
    `${API_BASE}/account/${request.accountId}/compliance-reports`,
    {
      name: request.name,
      type: request.type,
      parameters: request.parameters,
    }
  );

  return { reportId: response.data.report_id };
}

/**
 * 删除合规报告
 */
export async function apiDeleteComplianceReport(
  accountId: number,
  reportId: number
): Promise<void> {
  await apiClient.delete(
    `${API_BASE}/account/${accountId}/compliance-reports/${reportId}`
  );
}

/**
 * 导出合规报告
 */
export async function apiExportComplianceReport(
  accountId: number,
  reportId: number,
  format: 'pdf' | 'word' | 'excel'
): Promise<Blob> {
  const response = await apiClient.get(
    `${API_BASE}/account/${accountId}/compliance-reports/${reportId}/export`,
    {
      params: { format },
      responseType: 'blob',
    }
  );

  return response.data as Blob;
}

// ==================== 权限管理 API ====================

/**
 * 获取权限列表
 */
export async function apiGetPermissions(): Promise<GetPermissionsResponse> {
  const response = await apiClient.get<BackendPermission[]>(`${API_BASE}/permissions`);
  
  return {
    permissions: response.data.map(perm => ({
      id: perm.id,
      name: perm.name,
      code: perm.code,
      description: perm.description,
      category: perm.category,
      defaultRoles: perm.default_roles as TeamMember['role'][],
    })),
  };
}

/**
 * 获取角色权限配置
 */
export async function apiGetRolePermissions(accountId: number): Promise<GetRolePermissionsResponse> {
  const response = await apiClient.get<{
    configs: Array<{
      role: string;
      permissions: string[];
      allowed_actions: string[];
      restricted_actions: string[];
    }>;
  }>(`${API_BASE}/account/${accountId}/role-permissions`);
  
  return {
    configs: response.data.configs.map(config => ({
      role: config.role as TeamMember['role'],
      permissions: config.permissions,
      allowedActions: config.allowed_actions,
      restrictedActions: config.restricted_actions,
    })),
  };
}

/**
 * 更新角色权限
 */
export async function apiUpdateRolePermissions(
  accountId: number,
  request: UpdateRolePermissionsRequest
): Promise<void> {
  await apiClient.put(`${API_BASE}/account/${accountId}/role-permissions`, {
    configs: request.configs?.map(config => ({
      role: config.role,
      permissions: config.permissions,
      allowed_actions: config.allowedActions,
      restricted_actions: config.restrictedActions,
    })) ?? [],
  });
}

// ==================== 企业文档 API ====================

/** 后端企业文档 */
interface BackendEnterpriseDocument {
  id: number;
  account_id: number;
  name: string;
  type: string;
  size: number;
  url: string;
  uploaded_by: number;
  uploaded_at: string;
  updated_at: string;
  version: number;
  status: string;
}

/**
 * 获取文档列表
 */
export async function apiGetDocuments(
  accountId: number,
  params: { page?: number; pageSize?: number; type?: string }
): Promise<{ documents: EnterpriseDocument[]; total: number }> {
  const response = await apiClient.get<{
    documents: BackendEnterpriseDocument[];
    total: number;
  }>(`${API_BASE}/account/${accountId}/documents`, {
    params,
  });

  return {
    documents: response.data.documents.map(doc => ({
      id: doc.id,
      accountId: doc.account_id,
      name: doc.name,
      type: doc.type,
      size: doc.size,
      url: doc.url,
      uploadedBy: doc.uploaded_by,
      uploadedAt: doc.uploaded_at,
      updatedAt: doc.updated_at,
      version: doc.version,
      status: doc.status as EnterpriseDocument['status'],
    })),
    total: response.data.total,
  };
}

/**
 * 获取单个文档详情
 */
export async function apiGetDocumentById(
  accountId: number,
  documentId: number
): Promise<EnterpriseDocument> {
  const response = await apiClient.get<BackendEnterpriseDocument>(
    `${API_BASE}/account/${accountId}/documents/${documentId}`
  );

  return {
    id: response.data.id,
    accountId: response.data.account_id,
    name: response.data.name,
    type: response.data.type,
    size: response.data.size,
    url: response.data.url,
    uploadedBy: response.data.uploaded_by,
    uploadedAt: response.data.uploaded_at,
    updatedAt: response.data.updated_at,
    version: response.data.version,
    status: response.data.status as EnterpriseDocument['status'],
  };
}

/**
 * 上传文档
 */
export async function apiUploadDocument(
  accountId: number,
  request: UploadDocumentRequest
): Promise<{ documentId: number }> {
  const formData = new FormData();
  formData.append('file', request.file);
  formData.append('name', request.name);
  formData.append('type', request.type);
  if (request.description) {
    formData.append('description', request.description);
  }

  const response = await apiClient.post<{ document_id: number }>(
    `${API_BASE}/account/${accountId}/documents`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return { documentId: response.data.document_id };
}

/**
 * 更新文档
 */
export async function apiUpdateDocument(
  accountId: number,
  documentId: number,
  request: UpdateDocumentRequest
): Promise<void> {
  await apiClient.put(`${API_BASE}/account/${accountId}/documents/${documentId}`, {
    name: request.name,
    description: request.description,
  });
}

/**
 * 删除文档
 */
export async function apiDeleteDocument(
  accountId: number,
  documentId: number
): Promise<void> {
  await apiClient.delete(`${API_BASE}/account/${accountId}/documents/${documentId}`);
}

/**
 * 获取文档版本列表
 */
export async function apiGetDocumentVersions(
  accountId: number,
  documentId: number
): Promise<GetDocumentVersionsResponse> {
  const response = await apiClient.get<{
    versions: Array<{
      version: number;
      uploaded_at: string;
      uploaded_by: number;
      size: number;
      url: string;
    }>;
  }>(`${API_BASE}/account/${accountId}/documents/${documentId}/versions`);

  return {
    versions: response.data.versions.map(v => ({
      version: v.version,
      uploadedAt: v.uploaded_at,
      uploadedBy: v.uploaded_by,
      size: v.size,
      url: v.url,
    })),
  };
}