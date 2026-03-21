export interface ForumCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon?: string;
  color?: string;
  sortOrder: number;
  status: 'active' | 'inactive' | 'archived';
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

export interface ModerationItem {
  id: number;
  contentType: 'post' | 'comment' | 'reply';
  contentId: number;
  contentPreview: string;
  authorId: number;
  authorName: string;
  authorAvatar?: string;
  reason: string;
  reportedBy?: number;
  reportedAt: string;
  status: 'pending' | 'approved' | 'rejected';
  reviewedBy?: number;
  reviewedAt?: string;
  reviewNote?: string;
}

export interface ModerationRecord {
  id: number;
  action: ModerationAction;
  contentType: 'post' | 'comment' | 'reply';
  contentId: number;
  operatorId: number;
  operatorName: string;
  reason?: string;
  note?: string;
  createdAt: string;
}

export type ModerationAction = 'approve' | 'reject' | 'delete' | 'warn' | 'ban';

export interface ForumUser {
  id: number;
  username: string;
  email: string;
  avatar?: string;
  level: number;
  points: number;
  postCount: number;
  commentCount: number;
  status: 'active' | 'banned' | 'inactive';
  role: 'user' | 'moderator' | 'admin';
  createdAt: string;
  lastActiveAt?: string;
}

export interface UserActionRecord {
  id: number;
  userId: number;
  actionType: string;
  actionTarget: string;
  targetId?: number;
  ip?: string;
  userAgent?: string;
  createdAt: string;
}

export interface ForumStatsOverview {
  totalPosts: number;
  totalComments: number;
  totalUsers: number;
  totalCategories: number;
  todayPosts: number;
  todayComments: number;
  todayNewUsers: number;
  pendingModeration: number;
}

export interface HotContent {
  id: number;
  contentType: 'post' | 'comment';
  title?: string;
  preview: string;
  authorName: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  createdAt: string;
}

export interface ForumConfig {
  key: string;
  value: string;
  description?: string;
  updatedAt: string;
}

export interface CreateCategoryRequest {
  name: string;
  slug: string;
  description?: string;
  icon?: string;
  color?: string;
  sortOrder?: number;
  parentId?: number;
  allowPost?: boolean;
  needAudit?: boolean;
  minLevelToPost?: number;
}

export interface UpdateCategoryRequest {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
  sortOrder?: number;
  status?: 'active' | 'inactive' | 'archived';
  allowPost?: boolean;
  needAudit?: boolean;
  minLevelToPost?: number;
}

export interface GetCategoriesRequest {
  status?: string;
  parentId?: number;
  limit?: number;
  offset?: number;
}

export interface GetCategoriesResponse {
  categories: ForumCategory[];
  total: number;
}

export interface GetModerationQueueRequest {
  contentType?: 'post' | 'comment' | 'reply';
  status?: 'pending' | 'approved' | 'rejected';
  startDate?: string;
  endDate?: string;
  limit?: number;
  offset?: number;
}

export interface GetModerationQueueResponse {
  items: ModerationItem[];
  total: number;
}

export interface GetModerationRecordsRequest {
  contentType?: 'post' | 'comment' | 'reply';
  action?: ModerationAction;
  operatorId?: number;
  startDate?: string;
  endDate?: string;
  limit?: number;
  offset?: number;
}

export interface GetModerationRecordsResponse {
  records: ModerationRecord[];
  total: number;
}

export interface ModerateContentRequest {
  contentType: 'post' | 'comment' | 'reply';
  contentId: number;
  action: ModerationAction;
  reason?: string;
  note?: string;
}

export interface ModerateContentResponse {
  success: boolean;
  message?: string;
}

export interface BatchModerateRequest {
  items: Array<{
    contentType: 'post' | 'comment' | 'reply';
    contentId: number;
    action: ModerationAction;
  }>;
  reason?: string;
}

export interface BatchModerateResponse {
  success: boolean;
  processed: number;
  failed: number;
  errors?: string[];
}

export interface GetForumUsersRequest {
  role?: string;
  status?: string;
  keyword?: string;
  limit?: number;
  offset?: number;
}

export interface GetForumUsersResponse {
  users: ForumUser[];
  total: number;
}

export interface UpdateUserStatusRequest {
  userId: number;
  status: 'active' | 'banned' | 'inactive';
}

export interface SetModeratorRequest {
  userId: number;
  isModerator: boolean;
}

export interface GetUserActionRecordsResponse {
  records: UserActionRecord[];
  total: number;
}

export interface GetTrendDataRequest {
  startDate: string;
  endDate: string;
  interval: 'day' | 'week' | 'month';
}

export interface GetTrendDataResponse {
  dates: string[];
  posts: number[];
  comments: number[];
  newUsers: number[];
}
