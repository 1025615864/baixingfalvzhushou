/**
 * Forum（论坛）API 层
 *
 * 使用统一的 apiClient 进行 HTTP 请求
 * 后端路由: /api/v1/forum/*
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  Post,
  PostListResponse,
  PostCategory,
  ForumComment,
  CommentListResponse,
  CreatePostRequest,
  CreateCommentRequest,
  LikeResponse,
  ToggleFavoriteResponse,
  GetFavoritesRequest,
  ReactionResponse,
  ReactionRequest,
  ReactionEmoji,
  LawyerInvitation,
  LawyerInvitationListResponse,
  CreateInvitationRequest,
  LawyerInfo,
  GetLawyersRequest,
  PostStatus,
} from '../types';


// API 基础路径
const FORUM_BASE = '/forum';

// ==================== 后端响应类型定义 ====================

/** 后端作者信息 */
interface BackendAuthorInfo {
  id: number;
  username: string;
  nickname: string | null;
  avatar: string | null;
}

/** 后端表情反应统计 */
interface BackendReactionCount {
  emoji: string;
  count: number;
}

/** 后端帖子数据 */
interface BackendPost {
  id: number;
  title: string;
  content: string;
  category: string;
  user_id: number;
  view_count: number;
  like_count: number;
  comment_count: number;
  favorite_count: number;
  share_count: number;
  is_pinned: boolean;
  is_hot: boolean;
  is_essence: boolean;
  is_deleted: boolean;
  heat_score: number;
  cover_image: string | null;
  images: string[];
  attachments: Array<{ name: string; url: string }>;
  created_at: string;
  updated_at: string;
  review_status: PostStatus | null;
  review_reason: string | null;
  reviewed_at: string | null;
  author: BackendAuthorInfo | null;
  is_liked: boolean;
  is_favorited: boolean;
  reactions: BackendReactionCount[];
  user_reaction: string | null;
}

/** 后端帖子列表响应 */
interface BackendPostListResponse {
  items: BackendPost[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端评论数据 */
interface BackendComment {
  id: number;
  content: string;
  post_id: number;
  user_id: number;
  parent_id: number | null;
  like_count: number;
  images: string[];
  created_at: string;
  review_status: PostStatus | null;
  review_reason: string | null;
  reviewed_at: string | null;
  author: BackendAuthorInfo | null;
  is_liked: boolean;
  replies: BackendComment[];
}

/** 后端评论列表响应 */
interface BackendCommentListResponse {
  items: BackendComment[];
  total: number;
}

/** 后端点赞响应 */
interface BackendLikeResponse {
  liked: boolean;
  like_count: number;
  message: string;
}

/** 后端收藏响应 */
interface BackendFavoriteResponse {
  favorited: boolean;
  favorite_count: number;
  message: string;
}

/** 后端表情反应响应 */
interface BackendReactionResponse {
  reacted: boolean;
  emoji: string;
  reactions: BackendReactionCount[];
  message: string;
}

/** 后端律师邀请数据 */
interface BackendLawyerInvitation {
  id: number;
  post_id: number;
  lawyer_id: number;
  invited_by: number;
  status: 'pending' | 'accepted' | 'declined' | 'expired';
  message: string | null;
  responded_at: string | null;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

/** 后端律师邀请列表响应 */
interface BackendLawyerInvitationListResponse {
  items: BackendLawyerInvitation[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端律师信息 */
interface BackendLawyerInfo {
  id: number;
  name: string;
  avatar: string | null;
  title: string;
  law_firm: string | null;
  specialties: string[];
  rating: number;
  review_count: number;
}

// ==================== 数据转换函数 ====================

/**
 * 转换后端作者信息为前端格式
 */
function transformAuthorInfo(backend: BackendAuthorInfo | null): Post['author'] {
  if (!backend) {
    return { id: 0, nickname: '未知用户' };
  }
  return {
    id: backend.id,
    nickname: backend.nickname || backend.username || '未知用户',
    avatar_url: backend.avatar || undefined,
  };
}

/**
 * 转换后端帖子数据为前端格式
 */
function transformPost(backend: BackendPost): Post {
  return {
    id: backend.id,
    title: backend.title,
    content: backend.content,
    category: backend.category as PostCategory,
    author: transformAuthorInfo(backend.author),
    view_count: backend.view_count,
    like_count: backend.like_count,
    comment_count: backend.comment_count,
    favorite_count: backend.favorite_count,
    is_essence: backend.is_essence,
    is_liked: backend.is_liked,
    is_favorited: backend.is_favorited,
    review_status: backend.review_status || 'approved',
    reactions: backend.reactions.map(r => ({
      emoji: r.emoji as ReactionEmoji,
      count: r.count,
    })),
    user_reaction: (backend.user_reaction as ReactionEmoji) || null,
    created_at: backend.created_at,
    updated_at: backend.updated_at,
  };
}

/**
 * 转换后端评论数据为前端格式
 */
function transformComment(backend: BackendComment): ForumComment {
  return {
    id: backend.id,
    post_id: backend.post_id,
    content: backend.content,
    author: transformAuthorInfo(backend.author),
    like_count: backend.like_count,
    is_liked: backend.is_liked,
    parent_id: backend.parent_id || undefined,
    created_at: backend.created_at,
  };
}

/**
 * 转换后端律师邀请数据为前端格式
 */
function transformLawyerInvitation(backend: BackendLawyerInvitation): LawyerInvitation {
  return {
    id: backend.id,
    post_id: backend.post_id,
    lawyer_id: backend.lawyer_id,
    invited_by: backend.invited_by,
    status: backend.status,
    message: backend.message || undefined,
    responded_at: backend.responded_at || undefined,
    expires_at: backend.expires_at || undefined,
    created_at: backend.created_at,
    updated_at: backend.updated_at,
  };
}

/**
 * 转换后端律师信息为前端格式
 */
function transformLawyerInfo(backend: BackendLawyerInfo): LawyerInfo {
  return {
    id: backend.id,
    name: backend.name,
    avatar: backend.avatar || undefined,
    title: backend.title,
    law_firm: backend.law_firm || undefined,
    specialties: backend.specialties,
    rating: backend.rating,
    review_count: backend.review_count,
  };
}

// ==================== API 函数 ====================

/**
 * 获取帖子列表
 * GET /forum/posts
 */
export async function apiGetPosts(
  page: number = 1,
  page_size: number = 20,
  category?: PostCategory | null,
  keyword?: string,
  is_essence?: boolean | null
): Promise<PostListResponse> {
  const { data } = await apiClient.get<BackendPostListResponse>(`${FORUM_BASE}/posts`, {
    params: {
      page,
      page_size,
      ...(category && { category }),
      ...(keyword && { keyword }),
      ...(is_essence !== undefined && { is_essence }),
    },
  });

  return {
    items: data.items.map(transformPost),
    total: data.total,
    page: data.page,
    page_size: data.page_size,
  };
}

/**
 * 获取热门帖子
 * GET /forum/hot
 */
export async function apiGetHotPosts(
  limit: number = 10,
  category?: string
): Promise<PostListResponse> {
  const { data } = await apiClient.get<BackendPostListResponse>(`${FORUM_BASE}/hot`, {
    params: {
      limit,
      ...(category && { category }),
    },
  });

  return {
    items: data.items.map(transformPost),
    total: data.total,
    page: 1,
    page_size: limit,
  };
}

/**
 * 获取我发布的帖子
 * GET /forum/me/posts
 */
export async function apiGetMyPosts(
  page: number = 1,
  page_size: number = 20,
  category?: string,
  keyword?: string
): Promise<PostListResponse> {
  const { data } = await apiClient.get<BackendPostListResponse>(`${FORUM_BASE}/me/posts`, {
    params: {
      page,
      page_size,
      ...(category && { category }),
      ...(keyword && { keyword }),
    },
  });

  return {
    items: data.items.map(transformPost),
    total: data.total,
    page: data.page,
    page_size: data.page_size,
  };
}

/**
 * 获取我删除的帖子（回收站）
 * GET /forum/me/posts/deleted
 */
export async function apiGetMyDeletedPosts(
  page: number = 1,
  page_size: number = 20,
  category?: string,
  keyword?: string
): Promise<PostListResponse> {
  const { data } = await apiClient.get<BackendPostListResponse>(`${FORUM_BASE}/me/posts/deleted`, {
    params: {
      page,
      page_size,
      ...(category && { category }),
      ...(keyword && { keyword }),
    },
  });

  return {
    items: data.items.map(transformPost),
    total: data.total,
    page: data.page,
    page_size: data.page_size,
  };
}

/**
 * 获取帖子详情
 * GET /forum/posts/:id
 */
export async function apiGetPostDetail(postId: number): Promise<Post> {
  const { data } = await apiClient.get<BackendPost>(`${FORUM_BASE}/posts/${postId}`);
  return transformPost(data);
}

/**
 * 查看回收站帖子详情
 * GET /forum/posts/:id/recycle
 */
export async function apiGetDeletedPostDetail(postId: number): Promise<Post> {
  const { data } = await apiClient.get<BackendPost>(`${FORUM_BASE}/posts/${postId}/recycle`);
  return transformPost(data);
}

/**
 * 创建帖子
 * POST /forum/posts
 */
export async function apiCreatePost(request: CreatePostRequest): Promise<Post> {
  const { data } = await apiClient.post<BackendPost>(`${FORUM_BASE}/posts`, request);
  return transformPost(data);
}

/**
 * 更新帖子
 * PUT /forum/posts/:id
 */
export async function apiUpdatePost(
  postId: number,
  request: Partial<CreatePostRequest>
): Promise<Post> {
  const { data } = await apiClient.put<BackendPost>(`${FORUM_BASE}/posts/${postId}`, request);
  return transformPost(data);
}

/**
 * 删除帖子
 * DELETE /forum/posts/:id
 */
export async function apiDeletePost(postId: number): Promise<{ message: string }> {
  const { data } = await apiClient.delete<{ message: string }>(`${FORUM_BASE}/posts/${postId}`);
  return data;
}

/**
 * 点赞/取消点赞帖子
 * POST /forum/posts/:id/like
 */
export async function apiTogglePostLike(postId: number): Promise<LikeResponse> {
  const { data } = await apiClient.post<BackendLikeResponse>(`${FORUM_BASE}/posts/${postId}/like`);
  return {
    liked: data.liked,
    like_count: data.like_count,
    message: data.message,
  };
}

// ==================== 评论相关 API ====================

/**
 * 获取评论列表
 * GET /forum/posts/:id/comments
 */
export async function apiGetComments(
  postId: number,
  page: number = 1,
  page_size: number = 50,
  include_unapproved: boolean = false
): Promise<CommentListResponse> {
  const { data } = await apiClient.get<BackendCommentListResponse>(
    `${FORUM_BASE}/posts/${postId}/comments`,
    {
      params: {
        page,
        page_size,
        include_unapproved,
      },
    }
  );

  return {
    items: data.items.map(transformComment),
    total: data.total,
  };
}

/**
 * 创建评论
 * POST /forum/posts/:id/comments
 */
export async function apiCreateComment(
  postId: number,
  request: CreateCommentRequest
): Promise<ForumComment> {
  const { data } = await apiClient.post<BackendComment>(
    `${FORUM_BASE}/posts/${postId}/comments`,
    request
  );
  return transformComment(data);
}

/**
 * 删除评论
 * DELETE /forum/comments/:id
 */
export async function apiDeleteComment(commentId: number): Promise<{ message: string }> {
  const { data } = await apiClient.delete<{ message: string }>(`${FORUM_BASE}/comments/${commentId}`);
  return data;
}

/**
 * 恢复评论
 * POST /forum/comments/:id/restore
 */
export async function apiRestoreComment(commentId: number): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>(
    `${FORUM_BASE}/comments/${commentId}/restore`
  );
  return data;
}

/**
 * 点赞/取消点赞评论
 * POST /forum/comments/:id/like
 */
export async function apiToggleCommentLike(commentId: number): Promise<LikeResponse> {
  const { data } = await apiClient.post<BackendLikeResponse>(
    `${FORUM_BASE}/comments/${commentId}/like`
  );
  return {
    liked: data.liked,
    like_count: data.like_count,
    message: data.message,
  };
}

/**
 * 获取我发布的评论
 * GET /forum/me/comments
 */
export async function apiGetMyComments(
  page: number = 1,
  page_size: number = 20,
  status?: 'all' | 'pending' | 'approved' | 'rejected'
): Promise<{ items: ForumComment[]; total: number; page: number; page_size: number }> {
  const { data } = await apiClient.get<{
    items: Array<{
      id: number;
      post_id: number;
      post_title: string | null;
      content: string;
      created_at: string;
      review_status: PostStatus | null;
      review_reason: string | null;
    }>;
    total: number;
    page: number;
    page_size: number;
  }>(`${FORUM_BASE}/me/comments`, {
    params: {
      page,
      page_size,
      ...(status && { status }),
    },
  });

  return {
    items: data.items.map(item => ({
      id: item.id,
      post_id: item.post_id,
      content: item.content,
      author: { id: 0, nickname: '我' },
      like_count: 0,
      is_liked: false,
      created_at: item.created_at,
    })),
    total: data.total,
    page: data.page,
    page_size: data.page_size,
  };
}

// ==================== 收藏相关 API ====================

/**
 * 获取我的收藏列表
 * GET /forum/favorites
 */
export async function apiGetFavorites(params: GetFavoritesRequest = {}): Promise<PostListResponse> {
  const { page = 1, page_size = 20, category, keyword } = params;

  const { data } = await apiClient.get<BackendPostListResponse>(`${FORUM_BASE}/favorites`, {
    params: {
      page,
      page_size,
      ...(category && { category }),
      ...(keyword && { keyword }),
    },
  });

  return {
    items: data.items.map(transformPost),
    total: data.total,
    page: data.page,
    page_size: data.page_size,
  };
}

/**
 * 收藏/取消收藏帖子
 * POST /forum/posts/:id/favorite
 */
export async function apiToggleFavorite(postId: number): Promise<ToggleFavoriteResponse> {
  const { data } = await apiClient.post<BackendFavoriteResponse>(
    `${FORUM_BASE}/posts/${postId}/favorite`
  );
  return {
    favorited: data.favorited,
    favorite_count: data.favorite_count,
    message: data.message,
  };
}

// ==================== 表情反应相关 API ====================

/**
 * 添加/取消表情反应
 * POST /forum/posts/:id/reaction
 */
export async function apiToggleReaction(
  postId: number,
  emoji: ReactionEmoji
): Promise<ReactionResponse> {
  const request: ReactionRequest = { emoji };
  const { data } = await apiClient.post<BackendReactionResponse>(
    `${FORUM_BASE}/posts/${postId}/reaction`,
    request
  );
  return {
    reacted: data.reacted,
    emoji: data.emoji as ReactionEmoji,
    reactions: data.reactions.map(r => ({
      emoji: r.emoji as ReactionEmoji,
      count: r.count,
    })),
    message: data.message,
  };
}

// ==================== 律师邀请相关 API ====================

/**
 * 获取律师邀请列表
 * GET /forum/lawyer/invitations
 */
export async function apiGetInvitations(
  page: number = 1,
  page_size: number = 20,
  status?: 'all' | 'pending' | 'accepted' | 'declined' | 'expired'
): Promise<LawyerInvitationListResponse> {
  const { data } = await apiClient.get<BackendLawyerInvitationListResponse>(
    `${FORUM_BASE}/lawyer/invitations`,
    {
      params: {
        page,
        page_size,
        ...(status && status !== 'all' && { status }),
      },
    }
  );

  return {
    items: data.items.map(transformLawyerInvitation),
    total: data.total,
    page: data.page,
    page_size: data.page_size,
  };
}

/**
 * 发送律师邀请
 * POST /forum/posts/:id/invite-lawyer
 */
export async function apiCreateInvitation(
  request: CreateInvitationRequest
): Promise<LawyerInvitation> {
  const { data } = await apiClient.post<BackendLawyerInvitation>(
    `${FORUM_BASE}/posts/${request.post_id}/invite-lawyer`,
    {
      lawyer_id: request.lawyer_id,
      message: request.message,
    }
  );
  return transformLawyerInvitation(data);
}

/**
 * 接受律师邀请
 * POST /forum/lawyer/invitations/:id/accept
 */
export async function apiAcceptInvitation(invitationId: number): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>(
    `${FORUM_BASE}/lawyer/invitations/${invitationId}/accept`
  );
  return data;
}

/**
 * 拒绝律师邀请
 * POST /forum/lawyer/invitations/:id/decline
 */
export async function apiDeclineInvitation(invitationId: number): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>(
    `${FORUM_BASE}/lawyer/invitations/${invitationId}/decline`
  );
  return data;
}

/**
 * 获取律师列表
 * GET /lawyers
 */
export async function apiGetLawyers(
  params: GetLawyersRequest = {}
): Promise<{ items: LawyerInfo[]; total: number }> {
  const { page = 1, page_size = 20, keyword, specialty } = params;

  const { data } = await apiClient.get<{ items: BackendLawyerInfo[]; total: number }>(
    '/lawyers',
    {
      params: {
        page,
        page_size,
        ...(keyword && { keyword }),
        ...(specialty && { specialty }),
      },
    }
  );

  return {
    items: data.items.map(transformLawyerInfo),
    total: data.total,
  };
}

// ==================== 导出 API 对象 ====================

export const forumApi = {
  // 帖子相关
  getPosts: apiGetPosts,
  getHotPosts: apiGetHotPosts,
  getMyPosts: apiGetMyPosts,
  getMyDeletedPosts: apiGetMyDeletedPosts,
  getPostDetail: apiGetPostDetail,
  getDeletedPostDetail: apiGetDeletedPostDetail,
  createPost: apiCreatePost,
  updatePost: apiUpdatePost,
  deletePost: apiDeletePost,
  togglePostLike: apiTogglePostLike,

  // 评论相关
  getComments: apiGetComments,
  createComment: apiCreateComment,
  deleteComment: apiDeleteComment,
  restoreComment: apiRestoreComment,
  toggleCommentLike: apiToggleCommentLike,
  getMyComments: apiGetMyComments,

  // 收藏相关
  getFavorites: apiGetFavorites,
  toggleFavorite: apiToggleFavorite,

  // 表情反应相关
  toggleReaction: apiToggleReaction,

  // 律师邀请相关
  getInvitations: apiGetInvitations,
  createInvitation: apiCreateInvitation,
  acceptInvitation: apiAcceptInvitation,
  declineInvitation: apiDeclineInvitation,

  // 律师相关
  getLawyers: apiGetLawyers,
};

export default forumApi;