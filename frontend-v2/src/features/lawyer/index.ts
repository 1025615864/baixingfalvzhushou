/**
 * 律师模块导出
 */

// ==================== 类型 ====================
export type {
  // 基础类型
  Lawyer,
  LawyerProfile,
  LawyerReview,
  LawyerSchedule,
  AvailableSlot,
  Consultation,
  ReviewSummary,
  ReviewDimensionStats,
  RatingDistribution,
  TagStat,
  
  // 认证相关
  LawyerVerification,
  VerificationStatus,
  SubmitVerificationRequest,
  SubmitVerificationResponse,
  VerificationStatusResponse,
  
  // 主页相关
  LawyerHomepage,
  LawyerHomepagePublic,
  HomepageCase,
  HomepageReview,
  CreateHomepageRequest,
  UpdateHomepageRequest,
  
  // 推广链接相关
  LawyerPromotionLink,
  CreatePromotionLinkRequest,
  UpdatePromotionLinkRequest,
  PromotionLinkListResponse,
  PromotionLinkStats,
  
  // 快捷回复模板相关
  LawyerReplyTemplate,
  CreateReplyTemplateRequest,
  UpdateReplyTemplateRequest,
  ReplyTemplateListResponse,
  ReplyTemplateCategoriesResponse,
  UseReplyTemplateResponse,
} from './types';

export type { LawyerFilters } from './hooks/useLawyers';

// ==================== API ====================
export {
  // 基础API
  getLawyers,
  getLawyer,
  getLawyerReviews,
  createReview,
  getLawyerSchedule,
  getLawyerAvailableSlots,
  createBooking,
  getMyConsultations,
  cancelConsultation,
  getLawyerRanking,
  getLawyerReviewSummary,
  
  // 认证API
  submitVerification,
  getVerificationStatus,
  
  // 主页API
  getMyHomepage,
  createHomepage,
  updateHomepage,
  publishHomepage,
  unpublishHomepage,
  getPublicHomepage,
  
  // 推广链接API
  getPromotionLinks,
  createPromotionLink,
  getPromotionLink,
  updatePromotionLink,
  deletePromotionLink,
  getPromotionLinkStats,
  
  // 快捷回复模板API
  getReplyTemplates,
  getReplyTemplateCategories,
  createReplyTemplate,
  getReplyTemplate,
  updateReplyTemplate,
  deleteReplyTemplate,
  useReplyTemplate,
} from './api';

// ==================== Hooks ====================
export {
  // 律师列表hooks
  useLawyers,
} from './hooks/useLawyers';

export {
  // 律所hooks
  useLawFirms,
} from './hooks/useLawFirms';

export {
  // 认证hooks
  useVerificationStatus,
  useSubmitVerification,
  useCanApplyVerification,
} from './hooks/useVerification';

export {
  // 主页hooks
  useMyHomepage,
  useCreateHomepage,
  useUpdateHomepage,
  usePublishHomepage,
  useUnpublishHomepage,
  usePublicHomepage,
} from './hooks/useHomepage';

export {
  // 推广链接hooks
  usePromotionLinks,
  useCreatePromotionLink,
  useUpdatePromotionLink,
  useDeletePromotionLink,
  usePromotionLinkStats,
} from './hooks/usePromotions';

export {
  // 快捷回复模板hooks
  useReplyTemplates,
  useReplyTemplateCategories,
  useCreateReplyTemplate,
  useUpdateReplyTemplate,
  useDeleteReplyTemplate,
  useUseReplyTemplate,
} from './hooks/useReplyTemplates';

// ==================== 组件 ====================
export { LawyerCard } from './components/LawyerCard';
export { LawyerList } from './components/LawyerList';
export { VerificationForm } from './components/VerificationForm';
export { VerificationStatus as VerificationStatusComponent } from './components/VerificationStatus';
export { HomepageEditor } from './components/HomepageEditor';
export { PromotionLinkGenerator } from './components/PromotionLinkGenerator';
export { PromotionStats } from './components/PromotionStats';
export { ReplyTemplates } from './components/ReplyTemplates';

// ==================== 页面 ====================
export { VerificationPage } from './pages/VerificationPage';
export { LawyerHomepage as LawyerHomepagePage } from './pages/LawyerHomepage';
export { PromotionPage } from './pages/PromotionPage';