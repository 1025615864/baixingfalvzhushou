/**
 * Forum-Admin（论坛管理）API 层
 */

import apiClient from "@/shared/lib/api/client";

import type {
  ForumCategory,
  CreateCategoryRequest,
  UpdateCategoryRequest,
  GetCategoriesRequest,
  GetCategoriesResponse,
  ModerationItem,
  ModerationRecord,
  ModerationAction,
  GetModerationQueueRequest,
  GetModerationQueueResponse,
  GetModerationRecordsRequest,
  GetModerationRecordsResponse,
  ModerateContentRequest,
  ModerateContentResponse,
  BatchModerateRequest,
  BatchModerateResponse,
  ForumUser,
  UserActionRecord,
  GetForumUsersRequest,
  GetForumUsersResponse,
  UpdateUserStatusRequest,
  SetModeratorRequest,
  GetUserActionRecordsResponse,
  ForumStatsOverview,
  GetTrendDataRequest,
  GetTrendDataResponse,
  HotContent,
  ForumConfig,
} from '../types';

// API 基础路径
const API_BASE = '/forum';

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

// ==================== 板块管理 API ====================

/**
 * 获取板块列表
 */
export async function apiGetCategories(params: GetCategoriesRequest = {}): Promise<GetCategoriesResponse> {
  const { data } = await apiClient.get<{
    categories: Array<{
      id: number;
      name: string;
      slug: string;
      description: string;
      icon?: string;
      color?: string;
      sort_order: number;
      status: string;
      post_count: number;
      follower_count: number;
      created_at: string;
      updated_at: string;
      created_by: number;
      parent_id?: number;
      allow_post: boolean;
      need_audit: boolean;
      min_level_to_post: number;
      moderators: number[];
    }>;
    total: number;
  }>(`${API_BASE}/categories`, {
    params: {
      ...(params.status && { status: params.status }),
      ...(params.parentId !== undefined && { parent_id: params.parentId }),
      ...(params.limit && { limit: params.limit }),
      ...(params.offset && { offset: params.offset }),
    },
  });

  return {
    categories: data.categories.map(cat => ({
      id: cat.id,
      name: cat.name,
      slug: cat.slug,
      description: cat.description,
      icon: cat.icon,
      color: cat.color,
      sortOrder: cat.sort_order,
      status: cat.status as ForumCategory['status'],
      postCount: cat.post_count,
      followerCount: cat.follower_count,
      createdAt: cat.created_at,
      updatedAt: cat.updated_at,
      createdBy: cat.created_by,
      parentId: cat.parent_id,
      allowPost: cat.allow_post,
      needAudit: cat.need_audit,
      minLevelToPost: cat.min_level_to_post,
      moderators: cat.moderators,
    })),
    total: data.total,
  };
}

/**
 * 创建板块
 */
export async function apiCreateCategory(request: CreateCategoryRequest): Promise<ForumCategory> {
  const response = await apiClient.post<{
    id: number;
    name: string;
    slug: string;
    description: string;
    icon?: string;
    color?: string;
    sort_order: number;
    status: string;
    post_count: number;
    follower_count: number;
    created_at: string;
    updated_at: string;
    created_by: number;
    parent_id?: number;
    allow_post: boolean;
    need_audit: boolean;
    min_level_to_post: number;
    moderators: number[];
  }>(`${API_BASE}/categories`, {
    name: request.name,
    slug: request.slug,
    description: request.description,
    icon: request.icon,
    color: request.color,
    sort_order: request.sortOrder,
    parent_id: request.parentId,
    allow_post: request.allowPost ?? true,
    need_audit: request.needAudit ?? false,
    min_level_to_post: request.minLevelToPost ?? 0,
    moderator_ids: request.moderatorIds,
  });

  const data = response.data;

  return {
    id: data.id,
    name: data.name,
    slug: data.slug,
    description: data.description,
    icon: data.icon,
    color: data.color,
    sortOrder: data.sort_order,
    status: data.status as ForumCategory['status'],
    postCount: data.post_count,
    followerCount: data.follower_count,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    createdBy: data.created_by,
    parentId: data.parent_id,
    allowPost: data.allow_post,
    needAudit: data.need_audit,
    minLevelToPost: data.min_level_to_post,
    moderators: data.moderators,
  };
}

/**
 * 更新板块
 */
export async function apiUpdateCategory(categoryId: number, request: UpdateCategoryRequest): Promise<ForumCategory> {
  const response = await apiClient.put<{
    id: number;
    name: string;
    slug: string;
    description: string;
    icon?: string;
    color?: string;
    sort_order: number;
    status: string;
    post_count: number;
    follower_count: number;
    created_at: string;
    updated_at: string;
    created_by: number;
    parent_id?: number;
    allow_post: boolean;
    need_audit: boolean;
    min_level_to_post: number;
    moderators: number[];
  }>(`${API_BASE}/categories/${categoryId}`, {
    name: request.name,
    description: request.description,
    icon: request.icon,
    color: request.color,
    sort_order: request.sortOrder,
    status: request.status,
    allow_post: request.allowPost,
    need_audit: request.needAudit,
    min_level_to_post: request.minLevelToPost,
    moderator_ids: request.moderatorIds,
  });

  const data = response.data;

  return {
    id: data.id,
    name: data.name,
    slug: data.slug,
    description: data.description,
    icon: data.icon,
    color: data.color,
    sortOrder: data.sort_order,
    status: data.status as ForumCategory['status'],
    postCount: data.post_count,
    followerCount: data.follower_count,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    createdBy: data.created_by,
    parentId: data.parent_id,
    allowPost: data.allow_post,
    needAudit: data.need_audit,
    minLevelToPost: data.min_level_to_post,
    moderators: data.moderators,
  };
}

/**
 * 删除板块
 */
export async function apiDeleteCategory(categoryId: number): Promise<void> {
  await apiClient.delete(`${API_BASE}/categories/${categoryId}`);
}

// ==================== 内容审核 API ====================

/**
 * 获取审核队列
 */
export async function apiGetModerationQueue(params: GetModerationQueueRequest = {}): Promise<GetModerationQueueResponse> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set('status', params.status);
  if (params.contentType) searchParams.set('content_type', params.contentType);
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.offset) searchParams.set('offset', String(params.offset));

  const url = `${API_BASE}/moderation/queue${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取审核队列失败' }));
    throw new Error(getErrorMessage(error, '获取审核队列失败'));
  }

  const data = await safeJson<{
    items: Array<{
      id: number;
      content_type: string;
      content_id: number;
      content: string;
      author_id: number;
      author_name: string;
      author_avatar?: string;
      category_id?: number;
      category_name?: string;
      status: string;
      report_count: number;
      report_reasons: string[];
      reported_by: number[];
      created_at: string;
      updated_at: string;
      ai_score?: number;
      ai_suggestion?: string;
      handled_by?: number;
      handled_at?: string;
      handle_note?: string;
    }>;
    total: number;
    pending_count: number;
  }>(response);

  return {
    items: data.items.map(item => ({
      id: item.id,
      contentType: item.content_type as ModerationItem['contentType'],
      contentId: item.content_id,
      content: item.content,
      authorId: item.author_id,
      authorName: item.author_name,
      authorAvatar: item.author_avatar,
      categoryId: item.category_id,
      categoryName: item.category_name,
      status: item.status as ModerationItem['status'],
      reportCount: item.report_count,
      reportReasons: item.report_reasons as ModerationItem['reportReasons'],
      reportedBy: item.reported_by,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
      aiScore: item.ai_score,
      aiSuggestion: item.ai_suggestion as ModerationAction | undefined,
      handledBy: item.handled_by,
      handledAt: item.handled_at,
      handleNote: item.handle_note,
    })),
    total: data.total,
    pendingCount: data.pending_count,
  };
}

/**
 * 审核内容
 */
export async function apiModerateContent(request: ModerateContentRequest): Promise<ModerateContentResponse> {
  const response = await apiClient.post<{
    success: boolean;
    message: string;
    record: {
      id: number;
      content_type: string;
      content_id: number;
      content_preview: string;
      action: string;
      reason?: string;
      handled_by: number;
      handled_by_name: string;
      handled_at: string;
      old_status: string;
      new_status: string;
    };
  }>(`${API_BASE}/moderation/${request.itemId}`, {
    action: request.action,
    reason: request.reason,
    note: request.note,
  });

  const data = response.data;

  return {
    success: data.success,
    message: data.message,
    record: {
      id: data.record.id,
      contentType: data.record.content_type as ModerationRecord['contentType'],
      contentId: data.record.content_id,
      contentPreview: data.record.content_preview,
      action: data.record.action as ModerationRecord['action'],
      reason: data.record.reason,
      handledBy: data.record.handled_by,
      handledByName: data.record.handled_by_name,
      handledAt: data.record.handled_at,
      oldStatus: data.record.old_status as ModerationRecord['oldStatus'],
      newStatus: data.record.new_status as ModerationRecord['newStatus'],
    },
  };
}

/**
 * 批量审核
 */
export async function apiBatchModerate(request: BatchModerateRequest): Promise<BatchModerateResponse> {
  const response = await apiClient.post<{
    success: boolean;
    processed: number;
    failed: number;
    failed_ids: number[];
  }>(`${API_BASE}/moderation/batch`, {
    item_ids: request.itemIds,
    action: request.action,
    reason: request.reason,
  });

  return {
    success: response.data.success,
    processed: response.data.processed,
    failed: response.data.failed,
    failedIds: response.data.failed_ids,
  };
}

/**
 * 获取审核记录
 */
export async function apiGetModerationRecords(params: GetModerationRecordsRequest = {}): Promise<GetModerationRecordsResponse> {
  const searchParams = new URLSearchParams();
  if (params.contentType) searchParams.set('content_type', params.contentType);
  if (params.startDate) searchParams.set('start_date', params.startDate);
  if (params.endDate) searchParams.set('end_date', params.endDate);
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.offset) searchParams.set('offset', String(params.offset));

  const url = `${API_BASE}/moderation/records${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取审核记录失败' }));
    throw new Error(getErrorMessage(error, '获取审核记录失败'));
  }

  const data = await safeJson<{
    records: Array<{
      id: number;
      content_type: string;
      content_id: number;
      content_preview: string;
      action: string;
      reason?: string;
      handled_by: number;
      handled_by_name: string;
      handled_at: string;
      old_status: string;
      new_status: string;
    }>;
    total: number;
  }>(response);

  return {
    records: data.records.map(record => ({
      id: record.id,
      contentType: record.content_type as ModerationRecord['contentType'],
      contentId: record.content_id,
      contentPreview: record.content_preview,
      action: record.action as ModerationRecord['action'],
      reason: record.reason,
      handledBy: record.handled_by,
      handledByName: record.handled_by_name,
      handledAt: record.handled_at,
      oldStatus: record.old_status as ModerationRecord['oldStatus'],
      newStatus: record.new_status as ModerationRecord['newStatus'],
    })),
    total: data.total,
  };
}

// ==================== 用户管理 API ====================

/**
 * 获取论坛用户列表
 */
export async function apiGetForumUsers(params: GetForumUsersRequest = {}): Promise<GetForumUsersResponse> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set('status', params.status);
  if (params.level) searchParams.set('level', params.level);
  if (params.isModerator !== undefined) searchParams.set('is_moderator', String(params.isModerator));
  if (params.search) searchParams.set('search', params.search);
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.offset) searchParams.set('offset', String(params.offset));

  const url = `${API_BASE}/users${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取用户列表失败' }));
    throw new Error(getErrorMessage(error, '获取用户列表失败'));
  }

  const data = await safeJson<{
    users: Array<{
      id: number;
      username: string;
      nickname: string;
      avatar?: string;
      email: string;
      phone?: string;
      status: string;
      level: string;
      reputation: number;
      post_count: number;
      comment_count: number;
      like_received: number;
      joined_at: string;
      last_active_at: string;
      is_moderator: boolean;
      is_admin: boolean;
      banned_until?: string;
      ban_reason?: string;
      mute_until?: string;
      mute_reason?: string;
    }>;
    total: number;
  }>(response);

  return {
    users: data.users.map(user => ({
      id: user.id,
      username: user.username,
      nickname: user.nickname,
      avatar: user.avatar,
      email: user.email,
      phone: user.phone,
      status: user.status as ForumUser['status'],
      level: user.level as ForumUser['level'],
      reputation: user.reputation,
      postCount: user.post_count,
      commentCount: user.comment_count,
      likeReceived: user.like_received,
      joinedAt: user.joined_at,
      lastActiveAt: user.last_active_at,
      isModerator: user.is_moderator,
      isAdmin: user.is_admin,
      bannedUntil: user.banned_until,
      banReason: user.ban_reason,
      muteUntil: user.mute_until,
      muteReason: user.mute_reason,
    })),
    total: data.total,
  };
}

/**
 * 更新用户状态
 */
export async function apiUpdateUserStatus(request: UpdateUserStatusRequest): Promise<ForumUser> {
  const response = await apiClient.put<{
    id: number;
    username: string;
    nickname: string;
    avatar?: string;
    email: string;
    phone?: string;
    status: string;
    level: string;
    reputation: number;
    post_count: number;
    comment_count: number;
    like_received: number;
    joined_at: string;
    last_active_at: string;
    is_moderator: boolean;
    is_admin: boolean;
    banned_until?: string;
    ban_reason?: string;
    mute_until?: string;
    mute_reason?: string;
  }>(`${API_BASE}/users/${request.userId}/status`, {
    status: request.status,
    reason: request.reason,
    duration: request.duration,
  });

  const data = response.data;

  return {
    id: data.id,
    username: data.username,
    nickname: data.nickname,
    avatar: data.avatar,
    email: data.email,
    phone: data.phone,
    status: data.status as ForumUser['status'],
    level: data.level as ForumUser['level'],
    reputation: data.reputation,
    postCount: data.post_count,
    commentCount: data.comment_count,
    likeReceived: data.like_received,
    joinedAt: data.joined_at,
    lastActiveAt: data.last_active_at,
    isModerator: data.is_moderator,
    isAdmin: data.is_admin,
    bannedUntil: data.banned_until,
    banReason: data.ban_reason,
    muteUntil: data.mute_until,
    muteReason: data.mute_reason,
  };
}

/**
 * 设置版主
 */
export async function apiSetModerator(request: SetModeratorRequest): Promise<void> {
  await apiClient.post(`${API_BASE}/users/${request.userId}/moderator`, {
    category_ids: request.categoryIds,
    is_global: request.isGlobal,
  });
}

/**
 * 获取用户操作记录
 */
export async function apiGetUserActionRecords(userId: number): Promise<GetUserActionRecordsResponse> {
  const response = await fetch(`${API_BASE}/users/${userId}/records`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取用户操作记录失败' }));
    throw new Error(getErrorMessage(error, '获取用户操作记录失败'));
  }

  const data = await safeJson<{
    records: Array<{
      id: number;
      user_id: number;
      action: string;
      reason: string;
      performed_by: number;
      performed_by_name: string;
      performed_at: string;
      expires_at?: string;
      details?: string;
    }>;
    total: number;
  }>(response);

  return {
    records: data.records.map(record => ({
      id: record.id,
      userId: record.user_id,
      action: record.action as UserActionRecord['action'],
      reason: record.reason,
      performedBy: record.performed_by,
      performedByName: record.performed_by_name,
      performedAt: record.performed_at,
      expiresAt: record.expires_at,
      details: record.details,
    })),
    total: data.total,
  };
}

// ==================== 统计 API ====================

/**
 * 获取论坛统计概览
 */
export async function apiGetForumStats(): Promise<ForumStatsOverview> {
  const response = await fetch(`${API_BASE}/stats/overview`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取统计概览失败' }));
    throw new Error(getErrorMessage(error, '获取统计概览失败'));
  }

  const data = await safeJson<{
    total_posts: number;
    total_comments: number;
    total_users: number;
    today_posts: number;
    today_comments: number;
    today_new_users: number;
    pending_moderation: number;
    reported_content: number;
    active_users_7d: number;
    active_users_30d: number;
  }>(response);

  return {
    totalPosts: data.total_posts,
    totalComments: data.total_comments,
    totalUsers: data.total_users,
    todayPosts: data.today_posts,
    todayComments: data.today_comments,
    todayNewUsers: data.today_new_users,
    pendingModeration: data.pending_moderation,
    reportedContent: data.reported_content,
    activeUsers7d: data.active_users_7d,
    activeUsers30d: data.active_users_30d,
  };
}

/**
 * 获取趋势数据
 */
export async function apiGetTrendData(params: GetTrendDataRequest): Promise<GetTrendDataResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set('start_date', params.startDate);
  searchParams.set('end_date', params.endDate);
  searchParams.set('granularity', params.granularity);

  const response = await fetch(`${API_BASE}/stats/trend?${searchParams.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取趋势数据失败' }));
    throw new Error(getErrorMessage(error, '获取趋势数据失败'));
  }

  const data = await safeJson<{
    data: Array<{
      date: string;
      posts: number;
      comments: number;
      new_users: number;
      active_users: number;
    }>;
  }>(response);

  return {
    data: data.data.map(point => ({
      date: point.date,
      posts: point.posts,
      comments: point.comments,
      newUsers: point.new_users,
      activeUsers: point.active_users,
    })),
  };
}

/**
 * 获取热门内容
 */
export async function apiGetHotContent(): Promise<{ posts: HotContent[]; comments: HotContent[] }> {
  const response = await fetch(`${API_BASE}/stats/hot`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取热门内容失败' }));
    throw new Error(getErrorMessage(error, '获取热门内容失败'));
  }

  const data = await safeJson<{
    posts: Array<{
      id: number;
      title: string;
      author: string;
      view_count: number;
      like_count: number;
      comment_count: number;
      created_at: string;
    }>;
    comments: Array<{
      id: number;
      title: string;
      author: string;
      view_count: number;
      like_count: number;
      comment_count: number;
      created_at: string;
    }>;
  }>(response);

  return {
    posts: data.posts.map(post => ({
      id: post.id,
      title: post.title,
      author: post.author,
      viewCount: post.view_count,
      likeCount: post.like_count,
      commentCount: post.comment_count,
      createdAt: post.created_at,
    })),
    comments: data.comments.map(comment => ({
      id: comment.id,
      title: comment.title,
      author: comment.author,
      viewCount: comment.view_count,
      likeCount: comment.like_count,
      commentCount: comment.comment_count,
      createdAt: comment.created_at,
    })),
  };
}

// ==================== 配置 API ====================

/**
 * 获取论坛配置
 */
export async function apiGetForumConfig(): Promise<ForumConfig> {
  const response = await fetch(`${API_BASE}/config`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取论坛配置失败' }));
    throw new Error(getErrorMessage(error, '获取论坛配置失败'));
  }

  const data = await safeJson<{
    allow_guest_view: boolean;
    allow_guest_post: boolean;
    need_audit_new_post: boolean;
    need_audit_new_user: boolean;
    max_post_length: number;
    max_comment_length: number;
    min_level_to_post: number;
    min_level_to_comment: number;
    post_interval: number;
    comment_interval: number;
    max_daily_posts: number;
    max_daily_comments: number;
    enable_ai_moderation: boolean;
    ai_moderation_threshold: number;
    enable_keyword_filter: boolean;
    filtered_keywords: string[];
  }>(response);

  return {
    allowGuestView: data.allow_guest_view,
    allowGuestPost: data.allow_guest_post,
    needAuditNewPost: data.need_audit_new_post,
    needAuditNewUser: data.need_audit_new_user,
    maxPostLength: data.max_post_length,
    maxCommentLength: data.max_comment_length,
    minLevelToPost: data.min_level_to_post,
    minLevelToComment: data.min_level_to_comment,
    postInterval: data.post_interval,
    commentInterval: data.comment_interval,
    maxDailyPosts: data.max_daily_posts,
    maxDailyComments: data.max_daily_comments,
    enableAiModeration: data.enable_ai_moderation,
    aiModerationThreshold: data.ai_moderation_threshold,
    enableKeywordFilter: data.enable_keyword_filter,
    filteredKeywords: data.filtered_keywords,
  };
}

/**
 * 更新论坛配置
 */
export async function apiUpdateForumConfig(config: Partial<ForumConfig>): Promise<ForumConfig> {
  const response = await apiClient.put<{
    allow_guest_view: boolean;
    allow_guest_post: boolean;
    need_audit_new_post: boolean;
    need_audit_new_user: boolean;
    max_post_length: number;
    max_comment_length: number;
    min_level_to_post: number;
    min_level_to_comment: number;
    post_interval: number;
    comment_interval: number;
    max_daily_posts: number;
    max_daily_comments: number;
    enable_ai_moderation: boolean;
    ai_moderation_threshold: number;
    enable_keyword_filter: boolean;
    filtered_keywords: string[];
  }>(`${API_BASE}/config`, {
    allow_guest_view: config.allowGuestView,
    allow_guest_post: config.allowGuestPost,
    need_audit_new_post: config.needAuditNewPost,
    need_audit_new_user: config.needAuditNewUser,
    max_post_length: config.maxPostLength,
    max_comment_length: config.maxCommentLength,
    min_level_to_post: config.minLevelToPost,
    min_level_to_comment: config.minLevelToComment,
    post_interval: config.postInterval,
    comment_interval: config.commentInterval,
    max_daily_posts: config.maxDailyPosts,
    max_daily_comments: config.maxDailyComments,
    enable_ai_moderation: config.enableAiModeration,
    ai_moderation_threshold: config.aiModerationThreshold,
    enable_keyword_filter: config.enableKeywordFilter,
    filtered_keywords: config.filteredKeywords,
  });

  const data = response.data;

  return {
    allowGuestView: data.allow_guest_view,
    allowGuestPost: data.allow_guest_post,
    needAuditNewPost: data.need_audit_new_post,
    needAuditNewUser: data.need_audit_new_user,
    maxPostLength: data.max_post_length,
    maxCommentLength: data.max_comment_length,
    minLevelToPost: data.min_level_to_post,
    minLevelToComment: data.min_level_to_comment,
    postInterval: data.post_interval,
    commentInterval: data.comment_interval,
    maxDailyPosts: data.max_daily_posts,
    maxDailyComments: data.max_daily_comments,
    enableAiModeration: data.enable_ai_moderation,
    aiModerationThreshold: data.ai_moderation_threshold,
    enableKeywordFilter: data.enable_keyword_filter,
    filteredKeywords: data.filtered_keywords,
  };
}