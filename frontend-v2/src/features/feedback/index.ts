/**
 * 用户反馈功能模块
 *
 * 本模块提供用户反馈相关的功能，包括：
 * - 提交反馈（建议/Bug/投诉/其他）
 * - 查看反馈历史
 * - 管理员管理反馈工单
 */

// ==================== 类型定义 ====================
export type {
  Feedback,
  FeedbackType,
  FeedbackStatus,
  CreateFeedbackDTO,
  UpdateFeedbackDTO,
  FeedbackListResponse,
  FeedbackStatsResponse,
  FeedbackQueryParams,
} from './types';

export {
  FEEDBACK_TYPE_LABELS,
  FEEDBACK_STATUS_LABELS,
  getFeedbackTypeLabel,
  getFeedbackTypeClass,
  getFeedbackStatusLabel,
  getFeedbackStatusClass,
} from './types';

// ==================== API ====================
export {
  apiCreateFeedback,
  apiGetMyFeedbackList,
  apiGetFeedbackStats,
  apiGetAdminFeedbackList,
  apiUpdateFeedback,
} from './api';

export { feedbackKeys } from './api/queryKeys';

// ==================== Hooks ====================
export {
  useMyFeedbackList,
  useCreateFeedback,
  useFeedbackStats,
  useAdminFeedbackList,
  useUpdateFeedback,
  useReplyFeedback,
  useUpdateFeedbackStatus,
  useAssignFeedback,
} from './hooks/useFeedback';

// ==================== 组件 ====================
export { FeedbackForm } from './components/FeedbackForm';
export { FeedbackTypeSelector } from './components/FeedbackTypeSelector';
export { FeedbackList } from './components/FeedbackList';
export { FeedbackItem } from './components/FeedbackItem';
export { FeedbackModal } from './components/FeedbackModal';
export { FeedbackSuccess } from './components/FeedbackSuccess';

// ==================== 页面 ====================
export { FeedbackPage } from './pages/FeedbackPage';
export { FeedbackAdminPage } from './pages/FeedbackAdminPage';