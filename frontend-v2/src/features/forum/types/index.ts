// ============================================
// 论坛模块类型定义
// ============================================

/** 帖子状态 */
export type PostStatus = 'pending' | 'approved' | 'rejected';

/** 帖子分类 */
export type PostCategory = 'legal' | 'consultation' | 'experience' | 'discussion' | 'help';

/** 帖子作者 */
export interface PostAuthor {
  id: number;
  nickname: string;
  avatar_url?: string;
  title?: string;
}

/** 表情反应类型 */
export type ReactionEmoji = '👍' | '👎' | '😄' | '😢' | '🔥' | '🎉';

/** 表情反应统计 */
export interface ReactionCount {
  emoji: ReactionEmoji;
  count: number;
}

/** 用户表情反应 */
export interface UserReaction {
  emoji: ReactionEmoji;
  post_id: number;
  created_at: string;
}

/** 帖子基础信息 */
export interface Post {
  id: number;
  title: string;
  content: string;
  category: PostCategory;
  author: PostAuthor;
  view_count: number;
  like_count: number;
  comment_count: number;
  favorite_count: number;
  is_essence: boolean;
  is_liked: boolean;
  is_favorited: boolean;
  review_status: PostStatus;
  reactions: ReactionCount[];
  user_reaction?: ReactionEmoji | null;
  created_at: string;
  updated_at: string;
}

/** 帖子列表响应 */
export interface PostListResponse {
  items: Post[];
  total: number;
  page: number;
  page_size: number;
}

/** 评论信息 */
export interface ForumComment {
  id: number;
  post_id: number;
  content: string;
  author: PostAuthor;
  like_count: number;
  is_liked: boolean;
  parent_id?: number;
  created_at: string;
}

/** 评论列表响应 */
export interface CommentListResponse {
  items: ForumComment[];
  total: number;
}

/** 创建帖子请求 */
export interface CreatePostRequest {
  title: string;
  content: string;
  category: PostCategory;
}

/** 创建评论请求 */
export interface CreateCommentRequest {
  content: string;
  parent_id?: number;
}

/** 点赞响应 */
export interface LikeResponse {
  liked: boolean;
  like_count: number;
  message: string;
}

// ============================================
// 收藏功能类型
// ============================================

/** 收藏切换响应 */
export interface ToggleFavoriteResponse {
  favorited: boolean;
  favorite_count: number;
  message: string;
}

/** 获取收藏列表请求参数 */
export interface GetFavoritesRequest {
  page?: number;
  page_size?: number;
  category?: PostCategory | null;
  keyword?: string;
}

// ============================================
// 表情反应功能类型
// ============================================

/** 表情反应请求 */
export interface ReactionRequest {
  emoji: ReactionEmoji;
}

/** 表情反应响应 */
export interface ReactionResponse {
  reacted: boolean;
  emoji: ReactionEmoji;
  reactions: ReactionCount[];
  message: string;
}

// ============================================
// 律师邀请功能类型
// ============================================

/** 邀请状态 */
export type InvitationStatus = 'pending' | 'accepted' | 'declined' | 'expired';

/** 律师邀请 */
export interface LawyerInvitation {
  id: number;
  post_id: number;
  lawyer_id: number;
  invited_by: number;
  status: InvitationStatus;
  message?: string;
  responded_at?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

/** 律师信息（简化版） */
export interface LawyerInfo {
  id: number;
  name: string;
  avatar?: string;
  title: string;
  law_firm?: string;
  specialties: string[];
  rating: number;
  review_count: number;
}

/** 创建律师邀请请求 */
export interface CreateInvitationRequest {
  post_id: number;
  lawyer_id: number;
  message?: string;
}

/** 律师邀请列表响应 */
export interface LawyerInvitationListResponse {
  items: LawyerInvitation[];
  total: number;
  page: number;
  page_size: number;
}

/** 获取律师列表请求参数 */
export interface GetLawyersRequest {
  page?: number;
  page_size?: number;
  keyword?: string;
  specialty?: string;
}