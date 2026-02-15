/**
 * Forum-Admin（论坛管理）模块
 */

// 类型导出
export type {
  // 板块管理类型
  ForumCategory,
  CategoryStatus,
  CreateCategoryRequest,
  UpdateCategoryRequest,
  GetCategoriesRequest,
  GetCategoriesResponse,
  // 内容审核类型
  ModerationItem,
  ModerationRecord,
  ModerationAction,
  ContentType,
  ModerationStatus,
  ReportReason,
  GetModerationQueueRequest,
  GetModerationQueueResponse,
  GetModerationRecordsRequest,
  GetModerationRecordsResponse,
  ModerateContentRequest,
  ModerateContentResponse,
  BatchModerateRequest,
  BatchModerateResponse,
  // 用户管理类型
  ForumUser,
  ForumUserStatus,
  UserLevel,
  UserActionRecord,
  GetForumUsersRequest,
  GetForumUsersResponse,
  UpdateUserStatusRequest,
  SetModeratorRequest,
  GetUserActionRecordsResponse,
  // 统计类型
  ForumStatsOverview,
  TrendDataPoint,
  GetTrendDataRequest,
  GetTrendDataResponse,
  HotContent,
  // 配置类型
  ForumConfig,
} from './types';

// API 导出
export {
  // 板块管理 API
  apiGetCategories,
  apiCreateCategory,
  apiUpdateCategory,
  apiDeleteCategory,
  // 内容审核 API
  apiGetModerationQueue,
  apiModerateContent,
  apiBatchModerate,
  apiGetModerationRecords,
  // 用户管理 API
  apiGetForumUsers,
  apiUpdateUserStatus,
  apiSetModerator,
  apiGetUserActionRecords,
  // 统计 API
  apiGetForumStats,
  apiGetTrendData,
  apiGetHotContent,
  // 配置 API
  apiGetForumConfig,
  apiUpdateForumConfig,
} from './api';

// Hooks 导出
export {
  // 板块管理 Hooks
  useForumCategories,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
  // 内容审核 Hooks
  useModerationQueue,
  useModerateContent,
  useBatchModerate,
  useModerationRecords,
  // 用户管理 Hooks
  useForumUsers,
  useUpdateUserStatus,
  useSetModerator,
  useUserActionRecords,
  // 统计 Hooks
  useForumStats,
  useTrendData,
  useHotContent,
  // 配置 Hooks
  useForumConfig,
  useUpdateForumConfig,
} from './hooks/useForumAdmin';

// 组件导出
export { CategoryManager } from './components/CategoryManager';
export { ContentModeration } from './components/ContentModeration';
export { UserManagement } from './components/UserManagement';

// 页面导出
export { ForumAdminPage } from './pages/ForumAdminPage';