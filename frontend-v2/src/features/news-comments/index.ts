/**
 * 新闻评论功能模块
 * 
 * @module news-comments
 * @description 提供新闻评论的完整功能，包括评论列表、发表评论、删除评论等
 */

// ==================== 类型导出 ====================

export type {
  // 核心类型
  CommentAuthor,
  CommentReviewStatus,
  NewsComment,
  CommentListItem,
  
  // API 请求/响应类型
  GetNewsCommentsRequest,
  GetNewsCommentsResponse,
  CreateNewsCommentRequest,
  CreateNewsCommentResponse,
  DeleteNewsCommentRequest,
  DeleteNewsCommentResponse,
  
  // 组件 Props 类型
  CommentListProps,
  CommentItemProps,
  CommentFormProps,
  CommentPaginationProps,
  CommentEmptyProps,
  CommentErrorProps,
  CommentLoadingProps,
  CommentPanelProps,
} from './types';

// ==================== API 导出 ====================

export {
  apiGetNewsComments,
  apiCreateNewsComment,
  apiDeleteNewsComment,
  apiDeleteNewsCommentById,
} from './api';

// ==================== Hooks 导出 ====================

export {
  useNewsComments,
  useCreateNewsComment,
  useDeleteNewsComment,
  useDeleteNewsCommentById,
  useNewsCommentPanel,
} from './hooks';

export type {
  PaginatedCommentsResult,
} from './hooks';

// ==================== 组件导出 ====================

export {
  CommentItem,
  CommentList,
  CommentForm,
  CommentEmpty,
  CommentLoading,
  CommentError,
  CommentPagination,
  CommentPanel,
} from './components';

// ==================== 页面导出 ====================

export {
  NewsCommentsPage,
} from './pages';