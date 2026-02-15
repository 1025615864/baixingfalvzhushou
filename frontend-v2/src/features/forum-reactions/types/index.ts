/**
 * 论坛点赞和收藏模块类型定义
 */

// ============ 表情反应相关 ============

/** 表情反应类型 */
export type ReactionEmoji = '👍' | '👎' | '😄' | '❤️' | '🎉' | '😮' | '🚀' | '👀';

/** 表情反应统计 */
export interface ReactionCount {
  emoji: string;
  count: number;
}

/** 表情反应请求 */
export interface ReactionRequest {
  emoji: string;
}

/** 表情反应响应 */
export interface ReactionResponse {
  reacted: boolean;
  emoji: string;
  reactions: ReactionCount[];
  message: string;
}

// ============ 点赞相关 ============

/** 点赞响应 */
export interface LikeResponse {
  liked: boolean;
  like_count: number;
  message: string;
}

// ============ 收藏相关 ============

/** 收藏响应 */
export interface FavoriteResponse {
  favorited: boolean;
  favorite_count: number;
  message: string;
}

/** 收藏列表查询参数 */
export interface FavoriteListParams {
  page?: number;
  page_size?: number;
  category?: string;
  keyword?: string;
}

// ============ 作者信息 ============

/** 作者信息 */
export interface AuthorInfo {
  id: number;
  username: string;
  nickname?: string;
  avatar?: string;
}

// ============ 帖子相关（简化版） ============

/** 帖子响应 */
export interface Post {
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
  cover_image?: string;
  images: string[];
  attachments: Array<{ name: string; url: string }>;
  created_at: string;
  updated_at: string;
  review_status?: string;
  author?: AuthorInfo;
  is_liked: boolean;
  is_favorited: boolean;
  reactions: ReactionCount[];
}

/** 帖子列表响应 */
export interface PostListResponse {
  items: Post[];
  total: number;
  page: number;
  page_size: number;
}

// ============ 组件 Props ============

/** 反应栏组件 Props */
export interface ReactionBarProps {
  postId: number;
  likeCount: number;
  isLiked: boolean;
  reactions: ReactionCount[];
  onLikeToggle: () => void;
  onReactionSelect: (emoji: ReactionEmoji) => void;
  disabled?: boolean;
}

/** 收藏按钮组件 Props */
export interface FavoriteButtonProps {
  postId: number;
  isFavorited: boolean;
  favoriteCount: number;
  onToggle: () => void;
  disabled?: boolean;
  showCount?: boolean;
}

/** 帖子反应统计组件 Props */
export interface PostReactionsProps {
  likeCount: number;
  commentCount: number;
  favoriteCount: number;
  viewCount: number;
  reactions?: ReactionCount[];
  showReactions?: boolean;
  compact?: boolean;
}

/** 表情选择器组件 Props */
export interface ReactionPickerProps {
  isOpen: boolean;
  onSelect: (emoji: ReactionEmoji) => void;
  onClose: () => void;
  selectedEmoji?: string | null;
}

// ============ 用户反应状态 ============

/** 用户反应状态 */
export interface UserReactionState {
  postId: number;
  isLiked: boolean;
  isFavorited: boolean;
  userReactionEmoji: string | null;
}