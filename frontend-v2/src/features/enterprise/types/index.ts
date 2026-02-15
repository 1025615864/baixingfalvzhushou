/**
 * Enterprise（企业服务）类型定义
 */

// ==================== 核心类型 ====================

/** 企业规模类型 */
export type EnterpriseScale = 'smb' | 'mid' | 'enterprise';

/** 企业订阅计划类型 */
export type SubscriptionPlan = 'basic' | 'standard' | 'premium';

/** 企业账号状态 */
export type EnterpriseStatus = 'active' | 'suspended' | 'expired';

/** 团队成员角色 */
export type TeamMemberRole = 'owner' | 'admin' | 'member' | 'viewer';

/** 成员状态 */
export type MemberStatus = 'active' | 'pending' | 'disabled';

/** 订单状态 */
export type OrderStatus = 'pending' | 'paid' | 'processing' | 'completed' | 'cancelled' | 'refunded';

/** 订单类型 */
export type OrderType = 'subscription' | 'service' | 'consultation' | 'document' | 'other';

/** 合同审查状态 */
export type ContractReviewStatus = 'pending' | 'reviewing' | 'completed' | 'failed';

/** 风险等级 */
export type RiskLevel = 'low' | 'medium' | 'high';

/** 行业类型 */
export type IndustryType =
  | 'general'
  | 'technology'
  | 'finance'
  | 'manufacturing'
  | 'retail'
  | 'healthcare'
  | 'education'
  | 'realestate'
  | 'legal'
  | 'other';

/** 企业信息 */
export interface EnterpriseInfo {
  id: number;
  companyName: string;
  adminEmail: string;
  industry: IndustryType;
  scale: EnterpriseScale;
  subscriptionPlan: SubscriptionPlan;
  status: EnterpriseStatus;
  createdAt: string;
  updatedAt: string;
  memberCount: number;
  contractCount: number;
  quotaUsed: number;
  quotaTotal: number;
  logoUrl?: string;
  contactPhone?: string;
  contactName?: string;
  address?: string;
  website?: string;
  description?: string;
}

/** 团队成员 */
export interface TeamMember {
  id: number;
  userId: number;
  enterpriseId: number;
  name: string;
  email: string;
  role: TeamMemberRole;
  status: MemberStatus;
  avatar?: string;
  department?: string;
  position?: string;
  joinedAt: string;
  lastActiveAt?: string;
  permissions: string[];
}

/** 订单项 */
export interface OrderItem {
  id: string;
  name: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  description?: string;
}

/** 企业订单 */
export interface EnterpriseOrder {
  id: string;
  enterpriseId: number;
  orderType: OrderType;
  status: OrderStatus;
  amount: number;
  currency: string;
  description: string;
  items: OrderItem[];
  createdAt: string;
  paidAt?: string;
  completedAt?: string;
  invoiceNo?: string;
  paymentMethod?: string;
}

/** 合同审查 */
export interface ContractReview {
  id: number;
  enterpriseId: number;
  userId: number;
  title: string;
  contractType: string;
  status: ContractReviewStatus;
  content: string;
  reviewResult?: string;
  riskLevel?: RiskLevel;
  createdAt: string;
  completedAt?: string;
  reviewerId?: number;
}

/** 合规模板 */
export interface ComplianceTemplate {
  id: number;
  name: string;
  category: string;
  description: string;
  content: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

/** 权限项 */
export interface PermissionItem {
  id: string;
  name: string;
  code: string;
  description: string;
  category: string;
  defaultRoles: TeamMemberRole[];
}

/** 角色权限配置 */
export interface RolePermissionConfig {
  role: TeamMemberRole;
  permissions: string[];
  allowedActions: string[];
  restrictedActions: string[];
}

// ==================== API 请求/响应类型 ====================

/** 获取企业信息响应 */
export interface GetEnterpriseInfoResponse {
  enterprise: EnterpriseInfo;
}

/** 更新企业信息请求 */
export interface UpdateEnterpriseInfoRequest {
  companyName?: string;
  industry?: IndustryType;
  scale?: EnterpriseScale;
  subscriptionPlan?: SubscriptionPlan;
  contactPhone?: string;
  contactName?: string;
  address?: string;
  website?: string;
  description?: string;
}

/** 更新企业信息响应 */
export interface UpdateEnterpriseInfoResponse {
  success: boolean;
  enterprise: EnterpriseInfo;
}

/** 获取团队成员请求 */
export interface GetTeamMembersRequest {
  role?: TeamMemberRole;
  status?: MemberStatus;
  limit?: number;
  offset?: number;
}

/** 获取团队成员响应 */
export interface GetTeamMembersResponse {
  members: TeamMember[];
  total: number;
}

/** 添加团队成员请求 */
export interface AddTeamMemberRequest {
  email: string;
  name: string;
  role: TeamMemberRole;
}

/** 添加团队成员响应 */
export interface AddTeamMemberResponse {
  success: boolean;
  member: TeamMember;
  inviteLink?: string;
}

/** 移除团队成员请求 */
export interface RemoveTeamMemberRequest {
  memberId: number;
}

/** 更新成员角色请求 */
export interface UpdateMemberRoleRequest {
  memberId: number;
  role: TeamMemberRole;
}

/** 获取企业订单请求 */
export interface GetEnterpriseOrdersRequest {
  status?: OrderStatus;
  orderType?: OrderType;
  startDate?: string;
  endDate?: string;
  limit?: number;
  offset?: number;
}

/** 获取企业订单响应 */
export interface GetEnterpriseOrdersResponse {
  orders: EnterpriseOrder[];
  total: number;
  totalAmount: number;
}

/** 获取合同审查列表响应 */
export interface GetContractReviewsResponse {
  contracts: ContractReview[];
  total: number;
}

/** 提交合同审查请求 */
export interface SubmitContractReviewRequest {
  accountId: number;
  userId: number;
  title: string;
  content: string;
  contractType: string;
  attachments?: string[];
}

/** 获取权限列表响应 */
export interface GetPermissionsResponse {
  permissions: PermissionItem[];
}

/** 获取角色权限响应 */
export interface GetRolePermissionsResponse {
  configs: RolePermissionConfig[];
}

/** 更新角色权限请求 */
export interface UpdateRolePermissionsRequest {
  role: TeamMemberRole;
  permissions: string[];
  configs?: RolePermissionConfig[];
}

/** 企业统计数据 */
export interface EnterpriseStats {
  totalContracts: number;
  pendingContracts: number;
  completedContracts: number;
  totalTemplatesUsed: number;
  teamSize: number;
  quotaUsage: {
    used: number;
    total: number;
  };
}

/** 获取企业统计响应 */
export interface GetEnterpriseStatsResponse {
  stats: EnterpriseStats;
}

/** 团队活动记录 */
export interface TeamActivity {
  id: string;
  userId: number;
  userName: string;
  action: string;
  target?: string;
  createdAt: string;
}

/** 获取团队活动响应 */
export interface GetTeamActivitiesResponse {
  activities: TeamActivity[];
  total: number;
}

/** 企业订阅信息 */
export interface SubscriptionInfo {
  plan: SubscriptionPlan;
  status: 'active' | 'cancelled' | 'expired';
  startDate: string;
  endDate: string;
  autoRenew: boolean;
  price: number;
  features: string[];
}

/** 获取订阅信息响应 */
export interface GetSubscriptionInfoResponse {
  subscription: SubscriptionInfo;
}

/** 邀请成员响应 */
export interface InviteMemberResponse {
  success: boolean;
  inviteToken: string;
  inviteLink: string;
  expiresAt: string;
}

// ==================== 合规报告相关类型 ====================

/** 合规报告类型 */
export type ComplianceReportType = 'gdpr' | 'iso27001' | 'hipaa' | 'soc2' | 'pci' | 'custom';

/** 合规报告状态 */
export type ComplianceReportStatus = 'pending' | 'generating' | 'completed' | 'failed';

/** 合规报告 */
export interface ComplianceReport {
  id: number;
  accountId: number;
  name: string;
  type: ComplianceReportType;
  status: ComplianceReportStatus;
  content?: string;
  periodStart?: string;
  periodEnd?: string;
  generatedAt?: string;
  completedAt?: string;
  downloadUrl?: string;
  fileSize?: number;
  createdBy?: number;
  createdAt: string;
  updatedAt?: string;
}

/** 获取合规报告列表请求 */
export interface GetComplianceReportsRequest {
  type?: ComplianceReportType;
  status?: ComplianceReportStatus;
  startDate?: string;
  endDate?: string;
  limit?: number;
  offset?: number;
}

/** 获取合规报告列表响应 */
export interface GetComplianceReportsResponse {
  reports: ComplianceReport[];
  total: number;
}

/** 生成报告请求 */
export interface GenerateReportRequest {
  accountId: number;
  name: string;
  type: ComplianceReportType;
  description?: string;
  periodStart?: string;
  periodEnd?: string;
  parameters?: Record<string, unknown>;
}

/** 导出报告请求 */
export interface ExportReportRequest {
  reportId: number;
  format: 'pdf' | 'excel' | 'csv';
}

// ==================== 文档管理相关类型 ====================

/** 文档类型 */
export type DocumentType = 'contract' | 'policy' | 'template' | 'compliance' | 'other';

/** 文档状态 */
export type DocumentStatus = 'draft' | 'pending_review' | 'approved' | 'rejected' | 'archived';

/** 文档 */
export interface EnterpriseDocument {
  id: number;
  accountId: number;
  name: string;
  type: string;
  status: DocumentStatus;
  size?: number;
  url?: string;
  uploadedBy?: number;
  uploadedAt?: string;
  updatedAt?: string;
  version?: number;
}

/** 获取文档列表请求 */
export interface GetDocumentsRequest {
  type?: DocumentType;
  status?: DocumentStatus;
  search?: string;
  tags?: string[];
  limit?: number;
  offset?: number;
}

/** 获取文档列表响应 */
export interface GetDocumentsResponse {
  documents: EnterpriseDocument[];
  total: number;
}

/** 上传文档请求 */
export interface UploadDocumentRequest {
  name: string;
  type: DocumentType;
  description?: string;
  tags?: string[];
  file: File;
}

/** 更新文档请求 */
export interface UpdateDocumentRequest {
  name?: string;
  description?: string;
  tags?: string[];
  status?: DocumentStatus;
}

/** 文档版本 */
export interface DocumentVersion {
  version: number;
  uploadedAt?: string;
  uploadedBy?: number;
  size?: number;
  url?: string;
}

/** 获取文档版本历史响应 */
export interface GetDocumentVersionsResponse {
  versions: DocumentVersion[];
  total?: number;
}