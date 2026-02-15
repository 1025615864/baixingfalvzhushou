/**
 * Post（帖子管理）类型定义
 */

// ==================== 核心类型 ====================

/** 帖子状态 */
export type PostStatus = 'draft' | 'published' | 'archived' | 'deleted';

/** 帖子分类 */
export type PostCategory = 'general' | 'legal' | 'consultation' | 'discussion' | 'announcement';

/** 作者信息 */
export interface PostAuthor {
  id: string;
  name: string;
  avatar?: string;
  role: 'user' | 'lawyer' | 'admin';
}

/** 帖子类型 */
export interface Post {
  id: string;
  title: string;
  content: string;
  summary?: string;
  coverImage?: string;
  author: PostAuthor;
  category: PostCategory;
  status: PostStatus;
  tags: string[];
  viewCount: number;
  likeCount: number;
  commentCount: number;
  isPinned: boolean;
  isFeatured: boolean;
  createdAt: string;
  updatedAt: string;
  publishedAt?: string;
}

/** 评论类型 */
export interface PostComment {
  id: string;
  postId: string;
  parentId?: string;
  content: string;
  author: PostAuthor;
  likeCount: number;
  replyCount: number;
  isAccepted: boolean;
  createdAt: string;
  updatedAt: string;
}

/** 帖子列表项（精简版） */
export interface PostListItem {
  id: string;
  title: string;
  summary: string;
  coverImage?: string;
  author: PostAuthor;
  category: PostCategory;
  status: PostStatus;
  tags: string[];
  viewCount: number;
  likeCount: number;
  commentCount: number;
  isPinned: boolean;
  isFeatured: boolean;
  createdAt: string;
  publishedAt?: string;
}

/** 帖子筛选条件 */
export interface PostFilter {
  category?: PostCategory;
  status?: PostStatus;
  authorId?: string;
  tag?: string;
  searchQuery?: string;
  isPinned?: boolean;
  isFeatured?: boolean;
  startDate?: string;
  endDate?: string;
}

/** 帖子排序选项 */
export type PostSortOption = 'latest' | 'popular' | 'mostViewed' | 'mostCommented' | 'oldest';

// ==================== API 请求/响应类型 ====================

/** 获取帖子列表请求 */
export interface GetPostsRequest {
  page?: number;
  limit?: number;
  filter?: PostFilter;
  sortBy?: PostSortOption;
}

/** 获取帖子列表响应 */
export interface GetPostsResponse {
  posts: PostListItem[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

/** 获取帖子详情请求 */
export interface GetPostDetailRequest {
  id: string;
}

/** 获取帖子详情响应 */
export interface GetPostDetailResponse {
  post: Post;
  comments: PostComment[];
}

/** 创建帖子请求 */
export interface CreatePostRequest {
  title: string;
  content: string;
  summary?: string;
  coverImage?: string;
  category: PostCategory;
  tags?: string[];
  status: PostStatus;
}

/** 创建帖子响应 */
export interface CreatePostResponse {
  post: Post;
}

/** 编辑帖子请求 */
export interface UpdatePostRequest {
  id: string;
  title?: string;
  content?: string;
  summary?: string;
  coverImage?: string;
  category?: PostCategory;
  tags?: string[];
  status?: PostStatus;
}

/** 编辑帖子响应 */
export interface UpdatePostResponse {
  post: Post;
}

/** 删除帖子请求 */
export interface DeletePostRequest {
  id: string;
  permanent?: boolean;
}

/** 删除帖子响应 */
export interface DeletePostResponse {
  success: boolean;
  message?: string;
}

/** 获取评论列表请求 */
export interface GetCommentsRequest {
  postId: string;
  page?: number;
  limit?: number;
  parentId?: string;
}

/** 获取评论列表响应 */
export interface GetCommentsResponse {
  comments: PostComment[];
  total: number;
  page: number;
  limit: number;
}

/** 创建评论请求 */
export interface CreateCommentRequest {
  postId: string;
  parentId?: string;
  content: string;
}

/** 创建评论响应 */
export interface CreateCommentResponse {
  comment: PostComment;
}

/** 删除评论请求 */
export interface DeleteCommentRequest {
  commentId: string;
}

/** 点赞帖子请求 */
export interface LikePostRequest {
  postId: string;
}

/** 点赞帖子响应 */
export interface LikePostResponse {
  success: boolean;
  likeCount: number;
}

/** 取消点赞帖子请求 */
export interface UnlikePostRequest {
  postId: string;
}

/** 取消点赞帖子响应 */
export interface UnlikePostResponse {
  success: boolean;
  likeCount: number;
}

/** 置顶帖子请求 */
export interface PinPostRequest {
  postId: string;
  isPinned: boolean;
}

/** 精华帖子请求 */
export interface FeaturePostRequest {
  postId: string;
  isFeatured: boolean;
}

/** 帖子操作响应 */
export interface PostActionResponse {
  success: boolean;
  message?: string;
  post?: Post;
}

/** 上传图片响应 */
export interface UploadImageResponse {
  url: string;
  filename: string;
  size: number;
}