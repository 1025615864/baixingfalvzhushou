/**
 * 新闻评论模块类型定义
 */

// ==================== 核心类型 ====================

/** 评论作者信息 */
export interface CommentAuthor {
  id: number;
  username: string;
  nickname: string | null;
  avatar: string | null;
}

/** 评论状态 */
export type CommentReviewStatus = 'pending' | 'approved' | 'rejected';

/** 新闻评论 */
export interface NewsComment {
  id: number;
  newsId: number;
  userId: number;
  content: string;
  reviewStatus: CommentReviewStatus | null;
  reviewReason: string | null;
  createdAt: string;
  author: CommentAuthor | null;
}

/** 评论列表项（用于展示） */
export interface CommentListItem extends NewsComment {
  isOwner?: boolean;
}

// ==================== API 请求/响应类型 ====================

/** 获取评论列表请求参数 */
export interface GetNewsCommentsRequest {
  newsId: number;
  page?: number;
  pageSize?: number;
}

/** 获取评论列表响应 */
export interface GetNewsCommentsResponse {
  items: NewsComment[];
  total: number;
  page: number;
  pageSize: number;
}

/** 创建评论请求 */
export interface CreateNewsCommentRequest {
  newsId: number;
  content: string;
}

/** 创建评论响应 */
export interface CreateNewsCommentResponse {
  id: number;
  newsId: number;
  userId: number;
  content: string;
  reviewStatus: CommentReviewStatus | null;
  reviewReason: string | null;
  createdAt: string;
  author: CommentAuthor | null;
}

/** 删除评论参数 */
export interface DeleteNewsCommentRequest {
  newsId: number;
  commentId: number;
}

/** 删除评论响应 */
export interface DeleteNewsCommentResponse {
  message: string;
}

// ==================== 组件 Props 类型 ====================

/** 评论列表组件 Props */
export interface CommentListProps {
  newsId: number;
  comments: NewsComment[];
  currentUserId?: number | null;
  onDelete?: (commentId: number) => void;
  isLoading?: boolean;
}

/** 评论项组件 Props */
export interface CommentItemProps {
  comment: NewsComment;
  isOwner: boolean;
  onDelete?: (commentId: number) => void;
  isDeleting?: boolean;
}

/** 评论表单组件 Props */
export interface CommentFormProps {
  newsId: number;
  onSubmit?: (content: string) => void;
  isSubmitting?: boolean;
  placeholder?: string;
}

/** 评论分页组件 Props */
export interface CommentPaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

/** 评论空状态组件 Props */
export interface CommentEmptyProps {
  title?: string;
  description?: string;
}

/** 评论错误状态组件 Props */
export interface CommentErrorProps {
  error: string;
  onRetry?: () => void;
}

/** 评论加载状态组件 Props */
export interface CommentLoadingProps {
  count?: number;
}

/** 评论面板组件 Props（整合组件） */
export interface CommentPanelProps {
  newsId: number;
  currentUserId?: number | null;
  className?: string;
}