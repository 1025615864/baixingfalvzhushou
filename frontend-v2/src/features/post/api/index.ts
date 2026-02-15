/**
 * Post（帖子管理）API 层
 */

import apiClient from "@/shared/lib/api/client";

import type {
  Post,
  PostComment,
  GetPostsRequest,
  GetPostsResponse,
  CreatePostRequest,
  UpdatePostRequest,
  DeletePostRequest,
  DeletePostResponse,
  GetCommentsRequest,
  GetCommentsResponse,
  CreateCommentRequest,
  LikePostResponse,
  UnlikePostResponse,
  UploadImageResponse,
} from '../types';

// API 基础路径
const API_BASE = '/posts';

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
 * 获取帖子列表
 */
export async function apiGetPosts(params: GetPostsRequest = {}): Promise<GetPostsResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.sortBy) searchParams.set('sort_by', params.sortBy);
  if (params.filter?.category) searchParams.set('category', params.filter.category);
  if (params.filter?.status) searchParams.set('status', params.filter.status);
  if (params.filter?.authorId) searchParams.set('author_id', params.filter.authorId);
  if (params.filter?.tag) searchParams.set('tag', params.filter.tag);
  if (params.filter?.searchQuery) searchParams.set('q', params.filter.searchQuery);
  if (params.filter?.isPinned !== undefined) searchParams.set('is_pinned', String(params.filter.isPinned));
  if (params.filter?.isFeatured !== undefined) searchParams.set('is_featured', String(params.filter.isFeatured));
  if (params.filter?.startDate) searchParams.set('start_date', params.filter.startDate);
  if (params.filter?.endDate) searchParams.set('end_date', params.filter.endDate);

  const url = `${API_BASE}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取帖子列表失败' }));
    throw new Error(getErrorMessage(error, '获取帖子列表失败'));
  }

  const data = await safeJson<{
    posts: Array<{
      id: string;
      title: string;
      summary: string;
      cover_image?: string;
      author: {
        id: string;
        name: string;
        avatar?: string;
        role: string;
      };
      category: string;
      status: string;
      tags: string[];
      view_count: number;
      like_count: number;
      comment_count: number;
      is_pinned: boolean;
      is_featured: boolean;
      created_at: string;
      published_at?: string;
    }>;
    total: number;
    page: number;
    limit: number;
    total_pages: number;
  }>(response);

  return {
    posts: data.posts.map((item) => ({
      id: item.id,
      title: item.title,
      summary: item.summary,
      coverImage: item.cover_image,
      author: {
        id: item.author.id,
        name: item.author.name,
        avatar: item.author.avatar,
        role: item.author.role as 'user' | 'lawyer' | 'admin',
      },
      category: item.category as 'general' | 'legal' | 'consultation' | 'discussion' | 'announcement',
      status: item.status as 'draft' | 'published' | 'archived' | 'deleted',
      tags: item.tags,
      viewCount: item.view_count,
      likeCount: item.like_count,
      commentCount: item.comment_count,
      isPinned: item.is_pinned,
      isFeatured: item.is_featured,
      createdAt: item.created_at,
      publishedAt: item.published_at,
    })),
    total: data.total,
    page: data.page,
    limit: data.limit,
    totalPages: data.total_pages,
  };
}

/**
 * 获取帖子详情
 */
export async function apiGetPostDetail(postId: string): Promise<Post> {
  const response = await fetch(`${API_BASE}/${postId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取帖子详情失败' }));
    throw new Error(getErrorMessage(error, '获取帖子详情失败'));
  }

  const data = await safeJson<{
    id: string;
    title: string;
    content: string;
    summary?: string;
    cover_image?: string;
    author: {
      id: string;
      name: string;
      avatar?: string;
      role: string;
    };
    category: string;
    status: string;
    tags: string[];
    view_count: number;
    like_count: number;
    comment_count: number;
    is_pinned: boolean;
    is_featured: boolean;
    created_at: string;
    updated_at: string;
    published_at?: string;
  }>(response);

  return {
    id: data.id,
    title: data.title,
    content: data.content,
    summary: data.summary,
    coverImage: data.cover_image,
    author: {
      id: data.author.id,
      name: data.author.name,
      avatar: data.author.avatar,
      role: data.author.role as 'user' | 'lawyer' | 'admin',
    },
    category: data.category as 'general' | 'legal' | 'consultation' | 'discussion' | 'announcement',
    status: data.status as 'draft' | 'published' | 'archived' | 'deleted',
    tags: data.tags,
    viewCount: data.view_count,
    likeCount: data.like_count,
    commentCount: data.comment_count,
    isPinned: data.is_pinned,
    isFeatured: data.is_featured,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    publishedAt: data.published_at,
  };
}

/**
 * 创建帖子
 */
export async function apiCreatePost(request: CreatePostRequest): Promise<Post> {
  const response = await apiClient.post<{
    id: string;
    title: string;
    content: string;
    summary?: string;
    cover_image?: string;
    author: {
      id: string;
      name: string;
      avatar?: string;
      role: string;
    };
    category: string;
    status: string;
    tags: string[];
    view_count: number;
    like_count: number;
    comment_count: number;
    is_pinned: boolean;
    is_featured: boolean;
    created_at: string;
    updated_at: string;
    published_at?: string;
  }>(API_BASE, {
    title: request.title,
    content: request.content,
    summary: request.summary,
    cover_image: request.coverImage,
    category: request.category,
    tags: request.tags,
    status: request.status,
  });

  const data = response.data;

  return {
    id: data.id,
    title: data.title,
    content: data.content,
    summary: data.summary,
    coverImage: data.cover_image,
    author: {
      id: data.author.id,
      name: data.author.name,
      avatar: data.author.avatar,
      role: data.author.role as 'user' | 'lawyer' | 'admin',
    },
    category: data.category as 'general' | 'legal' | 'consultation' | 'discussion' | 'announcement',
    status: data.status as 'draft' | 'published' | 'archived' | 'deleted',
    tags: data.tags,
    viewCount: data.view_count,
    likeCount: data.like_count,
    commentCount: data.comment_count,
    isPinned: data.is_pinned,
    isFeatured: data.is_featured,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    publishedAt: data.published_at,
  };
}

/**
 * 编辑帖子
 */
export async function apiUpdatePost(request: UpdatePostRequest): Promise<Post> {
  const response = await apiClient.put<{
    id: string;
    title: string;
    content: string;
    summary?: string;
    cover_image?: string;
    author: {
      id: string;
      name: string;
      avatar?: string;
      role: string;
    };
    category: string;
    status: string;
    tags: string[];
    view_count: number;
    like_count: number;
    comment_count: number;
    is_pinned: boolean;
    is_featured: boolean;
    created_at: string;
    updated_at: string;
    published_at?: string;
  }>(`${API_BASE}/${request.id}`, {
    title: request.title,
    content: request.content,
    summary: request.summary,
    cover_image: request.coverImage,
    category: request.category,
    tags: request.tags,
    status: request.status,
  });

  const data = response.data;

  return {
    id: data.id,
    title: data.title,
    content: data.content,
    summary: data.summary,
    coverImage: data.cover_image,
    author: {
      id: data.author.id,
      name: data.author.name,
      avatar: data.author.avatar,
      role: data.author.role as 'user' | 'lawyer' | 'admin',
    },
    category: data.category as 'general' | 'legal' | 'consultation' | 'discussion' | 'announcement',
    status: data.status as 'draft' | 'published' | 'archived' | 'deleted',
    tags: data.tags,
    viewCount: data.view_count,
    likeCount: data.like_count,
    commentCount: data.comment_count,
    isPinned: data.is_pinned,
    isFeatured: data.is_featured,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    publishedAt: data.published_at,
  };
}

/**
 * 删除帖子
 */
export async function apiDeletePost(request: DeletePostRequest): Promise<DeletePostResponse> {
  try {
    await apiClient.delete(`${API_BASE}/${request.id}${request.permanent ? '?permanent=true' : ''}`);
    return { success: true, message: '帖子删除成功' };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : '删除帖子失败',
    };
  }
}

/**
 * 获取评论列表
 */
export async function apiGetComments(params: GetCommentsRequest): Promise<GetCommentsResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.parentId) searchParams.set('parent_id', params.parentId);

  const url = `${API_BASE}/${params.postId}/comments${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取评论列表失败' }));
    throw new Error(getErrorMessage(error, '获取评论列表失败'));
  }

  const data = await safeJson<{
    comments: Array<{
      id: string;
      post_id: string;
      parent_id?: string;
      content: string;
      author: {
        id: string;
        name: string;
        avatar?: string;
        role: string;
      };
      like_count: number;
      reply_count: number;
      is_accepted: boolean;
      created_at: string;
      updated_at: string;
    }>;
    total: number;
    page: number;
    limit: number;
  }>(response);

  return {
    comments: data.comments.map((item) => ({
      id: item.id,
      postId: item.post_id,
      parentId: item.parent_id,
      content: item.content,
      author: {
        id: item.author.id,
        name: item.author.name,
        avatar: item.author.avatar,
        role: item.author.role as 'user' | 'lawyer' | 'admin',
      },
      likeCount: item.like_count,
      replyCount: item.reply_count,
      isAccepted: item.is_accepted,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
    })),
    total: data.total,
    page: data.page,
    limit: data.limit,
  };
}

/**
 * 创建评论
 */
export async function apiCreateComment(request: CreateCommentRequest): Promise<PostComment> {
  const response = await apiClient.post<{
    id: string;
    post_id: string;
    parent_id?: string;
    content: string;
    author: {
      id: string;
      name: string;
      avatar?: string;
      role: string;
    };
    like_count: number;
    reply_count: number;
    is_accepted: boolean;
    created_at: string;
    updated_at: string;
  }>(`${API_BASE}/${request.postId}/comments`, {
    content: request.content,
    parent_id: request.parentId,
  });

  const data = response.data;

  return {
    id: data.id,
    postId: data.post_id,
    parentId: data.parent_id,
    content: data.content,
    author: {
      id: data.author.id,
      name: data.author.name,
      avatar: data.author.avatar,
      role: data.author.role as 'user' | 'lawyer' | 'admin',
    },
    likeCount: data.like_count,
    replyCount: data.reply_count,
    isAccepted: data.is_accepted,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 删除评论
 */
export async function apiDeleteComment(commentId: string): Promise<void> {
  await apiClient.delete(`/forum/comments/${commentId}`);
}

/**
 * 点赞帖子
 */
export async function apiLikePost(postId: string): Promise<LikePostResponse> {
  const response = await apiClient.post<{ success: boolean; like_count: number }>(`${API_BASE}/${postId}/like`);
  return {
    success: response.data.success,
    likeCount: response.data.like_count,
  };
}

/**
 * 取消点赞帖子
 */
export async function apiUnlikePost(postId: string): Promise<UnlikePostResponse> {
  const response = await apiClient.delete<{ success: boolean; like_count: number }>(`${API_BASE}/${postId}/like`);
  return {
    success: response.data.success,
    likeCount: response.data.like_count,
  };
}

/**
 * 置顶帖子
 */
export async function apiPinPost(postId: string, isPinned: boolean): Promise<Post> {
  const response = await apiClient.put<{
    id: string;
    title: string;
    content: string;
    summary?: string;
    cover_image?: string;
    author: {
      id: string;
      name: string;
      avatar?: string;
      role: string;
    };
    category: string;
    status: string;
    tags: string[];
    view_count: number;
    like_count: number;
    comment_count: number;
    is_pinned: boolean;
    is_featured: boolean;
    created_at: string;
    updated_at: string;
    published_at?: string;
  }>(`${API_BASE}/${postId}/pin`, { is_pinned: isPinned });

  const data = response.data;

  return {
    id: data.id,
    title: data.title,
    content: data.content,
    summary: data.summary,
    coverImage: data.cover_image,
    author: {
      id: data.author.id,
      name: data.author.name,
      avatar: data.author.avatar,
      role: data.author.role as 'user' | 'lawyer' | 'admin',
    },
    category: data.category as 'general' | 'legal' | 'consultation' | 'discussion' | 'announcement',
    status: data.status as 'draft' | 'published' | 'archived' | 'deleted',
    tags: data.tags,
    viewCount: data.view_count,
    likeCount: data.like_count,
    commentCount: data.comment_count,
    isPinned: data.is_pinned,
    isFeatured: data.is_featured,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    publishedAt: data.published_at,
  };
}

/**
 * 标记帖子为精华
 */
export async function apiFeaturePost(postId: string, isFeatured: boolean): Promise<Post> {
  const response = await apiClient.put<{
    id: string;
    title: string;
    content: string;
    summary?: string;
    cover_image?: string;
    author: {
      id: string;
      name: string;
      avatar?: string;
      role: string;
    };
    category: string;
    status: string;
    tags: string[];
    view_count: number;
    like_count: number;
    comment_count: number;
    is_pinned: boolean;
    is_featured: boolean;
    created_at: string;
    updated_at: string;
    published_at?: string;
  }>(`${API_BASE}/${postId}/feature`, { is_featured: isFeatured });

  const data = response.data;

  return {
    id: data.id,
    title: data.title,
    content: data.content,
    summary: data.summary,
    coverImage: data.cover_image,
    author: {
      id: data.author.id,
      name: data.author.name,
      avatar: data.author.avatar,
      role: data.author.role as 'user' | 'lawyer' | 'admin',
    },
    category: data.category as 'general' | 'legal' | 'consultation' | 'discussion' | 'announcement',
    status: data.status as 'draft' | 'published' | 'archived' | 'deleted',
    tags: data.tags,
    viewCount: data.view_count,
    likeCount: data.like_count,
    commentCount: data.comment_count,
    isPinned: data.is_pinned,
    isFeatured: data.is_featured,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    publishedAt: data.published_at,
  };
}

/**
 * 上传图片
 */
export async function apiUploadImage(file: File): Promise<UploadImageResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<{
    url: string;
    filename: string;
    size: number;
  }>('/api/upload/image', formData);

  const data = response.data;

  return {
    url: data.url,
    filename: data.filename,
    size: data.size,
  };
}