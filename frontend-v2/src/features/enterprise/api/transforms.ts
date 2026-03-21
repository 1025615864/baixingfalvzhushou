export interface BackendEnterpriseInfo {
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

export interface BackendTeamMember {
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

export interface BackendOrderItem {
  id: string;
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  description?: string;
}

export interface BackendEnterpriseOrder {
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

export interface BackendComplianceReport {
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

export interface BackendComplianceTemplate {
  id: number;
  name: string;
  category: string;
  description: string;
  content: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface BackendPermission {
  id: string;
  name: string;
  code: string;
  description: string;
  category: string;
  default_roles: string[];
}

export interface BackendEnterpriseDocument {
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

export function mapBackendToEnterpriseInfo(data: BackendEnterpriseInfo) {
  return {
    id: data.id,
    companyName: data.company_name,
    adminEmail: data.admin_email,
    industry: data.industry as any,
    scale: data.scale as any,
    subscriptionPlan: data.subscription_plan as any,
    status: data.status as any,
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

export function mapBackendToTeamMember(user: BackendTeamMember) {
  return {
    id: user.id,
    userId: user.user_id,
    enterpriseId: user.enterprise_id,
    name: user.name,
    email: user.email,
    role: user.role as any,
    status: user.status as any,
    avatar: user.avatar,
    department: user.department,
    position: user.position,
    joinedAt: user.joined_at,
    lastActiveAt: user.last_active_at,
    permissions: user.permissions,
  };
}
