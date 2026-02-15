/**
 * Forum-Admin（论坛管理）类型定义
 */

// ==================== 板块管理类型 ====================

/** 板块状态 */
export type CategoryStatus = 'active' | 'inactive' | 'archived';

/** 排序类型 */
export type SortType = 'newest' | 'hot' | 'replies';

/** 板块信息 */
export interface ForumCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon?: string;
  color?: string;
  sortOrder: number;
  status: CategoryStatus;
  postCount: number;
  followerCount: number;
  createdAt: string;
  updatedAt: string;
  createdBy: number;
  parentId?: number;
  allowPost: boolean;
  needAudit: boolean;
  minLevelToPost: number;
  moderators: number[];
}

/** 创建板块请求 */
export interface CreateCategoryRequest {
  name: string;
  slug: string;
  description: string;
  icon?: string;
  color?: string;
  sortOrder?: number;
  parentId?: number;
  allowPost?: boolean;
  needAudit?: boolean;
  minLevelToPost?: number;
  moderatorIds?: number[];
}

/** 更新板块请求 */
export interface UpdateCategoryRequest {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
  sortOrder?: number;
  status?: CategoryStatus;
  allowPost?: boolean;
  needAudit?: boolean;
  minLevelToPost?: number;
  moderatorIds?: number[];
}

/** 获取板块列表请求 */
export interface GetCategoriesRequest {
  status?: CategoryStatus;
  parentId?: number;
  limit?: number;
  offset?: number;
}

/** 获取板块列表响应 */
export interface GetCategoriesResponse {
  categories: ForumCategory[];
  total: number;
}

// ==================== 内容审核类型 ====================

/** 审核状态 */
export type ModerationStatus = 'pending' | 'approved' | 'rejected' | 'auto_approved';

/** 审核内容类型 */
export type ContentType = 'post' | 'comment' | 'reply';

/** 审核动作 */
export type ModerationAction = 'approve' | 'reject' | 'escalate' | 'ignore';

/** 举报原因 */
export type ReportReason =
  | 'spam'
  | 'harassment'
  | 'inappropriate'
  | 'misinformation'
  | 'copyright'
  | 'violence'
  | 'other';

/** 审核队列项 */
export interface ModerationItem {
  id: number;
  contentType: ContentType;
  contentId: number;
  content: string;
  authorId: number;
  authorName: string;
  authorAvatar?: string;
  categoryId?: number;
  categoryName?: string;
  status: ModerationStatus;
  reportCount: number;
  reportReasons: ReportReason[];
  reportedBy: number[];
  createdAt: string;
  updatedAt: string;
  aiScore?: number;
  aiSuggestion?: ModerationAction;
  handledBy?: number;
  handledAt?: string;
  handleNote?: string;
}

/** 审核记录 */
export interface ModerationRecord {
  id: number;
  contentType: ContentType;
  contentId: number;
  contentPreview: string;
  action: ModerationAction;
  reason?: string;
  handledBy: number;
  handledByName: string;
  handledAt: string;
  oldStatus: ModerationStatus;
  newStatus: ModerationStatus;
}

/** 获取审核队列请求 */
export interface GetModerationQueueRequest {
  status?: ModerationStatus;
  contentType?: ContentType;
  limit?: number;
  offset?: number;
}

/** 获取审核队列响应 */
export interface GetModerationQueueResponse {
  items: ModerationItem[];
  total: number;
  pendingCount: number;
}

/** 获取审核记录请求 */
export interface GetModerationRecordsRequest {
  contentType?: ContentType;
  startDate?: string;
  endDate?: string;
  limit?: number;
  offset?: number;
}

/** 获取审核记录响应 */
export interface GetModerationRecordsResponse {
  records: ModerationRecord[];
  total: number;
}

/** 审核内容请求 */
export interface ModerateContentRequest {
  itemId: number;
  action: ModerationAction;
  reason?: string;
  note?: string;
}

/** 审核内容响应 */
export interface ModerateContentResponse {
  success: boolean;
  message: string;
  record: ModerationRecord;
}

/** 批量审核请求 */
export interface BatchModerateRequest {
  itemIds: number[];
  action: ModerationAction;
  reason?: string;
}

/** 批量审核响应 */
export interface BatchModerateResponse {
  success: boolean;
  processed: number;
  failed: number;
  failedIds: number[];
}

// ==================== 用户管理类型 ====================

/** 论坛用户状态 */
export type ForumUserStatus = 'active' | 'banned' | 'muted' | 'unverified';

/** 用户等级 */
export type UserLevel = 'newbie' | 'member' | 'active' | 'senior' | 'expert' | 'legend';

/** 论坛用户 */
export interface ForumUser {
  id: number;
  username: string;
  nickname: string;
  avatar?: string;
  email: string;
  phone?: string;
  status: ForumUserStatus;
  level: UserLevel;
  reputation: number;
  postCount: number;
  commentCount: number;
  likeReceived: number;
  joinedAt: string;
  lastActiveAt: string;
  isModerator: boolean;
  isAdmin: boolean;
  bannedUntil?: string;
  banReason?: string;
  muteUntil?: string;
  muteReason?: string;
}

/** 用户操作记录 */
export interface UserActionRecord {
  id: number;
  userId: number;
  action: 'ban' | 'unban' | 'mute' | 'unmute' | 'warn' | 'delete_post';
  reason: string;
  performedBy: number;
  performedByName: string;
  performedAt: string;
  expiresAt?: string;
  details?: string;
}

/** 获取用户列表请求 */
export interface GetForumUsersRequest {
  status?: ForumUserStatus;
  level?: UserLevel;
  isModerator?: boolean;
  search?: string;
  limit?: number;
  offset?: number;
}

/** 获取用户列表响应 */
export interface GetForumUsersResponse {
  users: ForumUser[];
  total: number;
}

/** 更新用户状态请求 */
export interface UpdateUserStatusRequest {
  userId: number;
  status: ForumUserStatus;
  reason: string;
  duration?: number; // 禁言/封禁时长（小时），0表示永久
}

/** 设置版主请求 */
export interface SetModeratorRequest {
  userId: number;
  categoryIds: number[];
  isGlobal: boolean;
}

/** 获取用户操作记录响应 */
export interface GetUserActionRecordsResponse {
  records: UserActionRecord[];
  total: number;
}

// ==================== 论坛统计类型 ====================

/** 论坛统计概览 */
export interface ForumStatsOverview {
  totalPosts: number;
  totalComments: number;
  totalUsers: number;
  todayPosts: number;
  todayComments: number;
  todayNewUsers: number;
  pendingModeration: number;
  reportedContent: number;
  activeUsers7d: number;
  activeUsers30d: number;
}

/** 趋势数据点 */
export interface TrendDataPoint {
  date: string;
  posts: number;
  comments: number;
  newUsers: number;
  activeUsers: number;
}

/** 获取趋势数据请求 */
export interface GetTrendDataRequest {
  startDate: string;
  endDate: string;
  granularity: 'day' | 'week' | 'month';
}

/** 获取趋势数据响应 */
export interface GetTrendDataResponse {
  data: TrendDataPoint[];
}

/** 热门内容 */
export interface HotContent {
  id: number;
  title: string;
  author: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  createdAt: string;
}

/** 获取热门内容响应 */
export interface GetHotContentResponse {
  posts: HotContent[];
  comments: HotContent[];
}

// ==================== 配置类型 ====================

/** 论坛配置 */
export interface ForumConfig {
  allowGuestView: boolean;
  allowGuestPost: boolean;
  needAuditNewPost: boolean;
  needAuditNewUser: boolean;
  maxPostLength: number;
  maxCommentLength: number;
  minLevelToPost: number;
  minLevelToComment: number;
  postInterval: number; // 发帖间隔（秒）
  commentInterval: number; // 评论间隔（秒）
  maxDailyPosts: number;
  maxDailyComments: number;
  enableAiModeration: boolean;
  aiModerationThreshold: number;
  enableKeywordFilter: boolean;
  filteredKeywords: string[];
}