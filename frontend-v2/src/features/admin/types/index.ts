/**
 * Admin（管理后台）类型定义
 */

// ==================== 用户角色类型 ====================

/** 用户角色 */
export type UserRole = 'user' | 'lawyer' | 'admin';

/** 用户状态 */
export type UserStatus = 'active' | 'inactive';

// ==================== 用户相关类型 ====================

/** 用户列表项 */
export interface UserListItem {
  id: number;
  username: string;
  email: string;
  nickname: string | null;
  phone: string | null;
  avatar: string | null;
  role: UserRole;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
  updated_at: string | null;
}

/** 系统统计数据 */
export interface AdminStats {
  users: number;
  news: number;
  posts: number;
  lawfirms: number;
  comments: number;
  consultations: number;
  total_users: number;
  revenue_today: number;
  pending_consultations: number;
  pending_withdrawals: number;
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ==================== API 请求/响应类型 ====================

/** 获取用户列表请求 */
export interface GetUsersRequest {
  page?: number;
  pageSize?: number;
  keyword?: string;
}

/** 获取用户列表响应 */
export type GetUsersResponse = PaginatedResponse<UserListItem>;

/** 切换用户状态响应 */
export interface ToggleUserActiveResponse {
  id: number;
  is_active: boolean;
}

/** 更新用户角色请求 */
export interface UpdateUserRoleRequest {
  role: UserRole;
}

/** 更新用户角色响应 */
export type UpdateUserRoleResponse = UserListItem;

/** 获取系统统计响应 */
export type GetAdminStatsResponse = AdminStats;

/** 导出用户请求 */
export interface ExportUsersRequest {
  format?: 'csv';
}

// ==================== 组件Props类型 ====================

/** 用户表格Props */
export interface UserTableProps {
  users: UserListItem[];
  loading: boolean;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
  onPageChange: (page: number, pageSize: number) => void;
  onToggleActive: (userId: number, currentStatus: boolean) => void;
  onEditRole: (user: UserListItem) => void;
}

/** 用户编辑对话框Props */
export interface UserEditDialogProps {
  user: UserListItem | null;
  visible: boolean;
  onCancel: () => void;
  onConfirm: (userId: number, role: UserRole) => void;
  loading: boolean;
}

/** 统计卡片Props */
export interface StatsCardsProps {
  stats: AdminStats | null;
  loading: boolean;
}

/** 侧边栏Props */
export interface SidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
  selectedKey: string;
  onSelect: (key: string) => void;
}

// ==================== 菜单项类型 ====================

/** 管理后台菜单项 */
export interface AdminMenuItem {
  key: string;
  icon: string;
  label: string;
  path?: string;
  children?: AdminMenuItem[];
}

/** 管理员权限检查 */
export interface AdminPermissionCheck {
  isAdmin: boolean;
  isLoading: boolean;
}