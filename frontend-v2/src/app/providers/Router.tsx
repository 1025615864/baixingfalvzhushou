import { Suspense, lazy } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import { RootLayout } from '@/app/layouts/RootLayout';
import { Loading } from '@/shared/components/Loading';
// 立即加载的页面（首屏）
import { HomePage } from '@/pages/Home';
import { NotFoundPage } from '@/pages/NotFound';
// 懒加载的页面 - 按功能模块分组
const LoginPage = lazy(() => import('@/pages/auth/Login').then(m => ({ default: m.Login })));
const RegisterPage = lazy(() => import('@/pages/auth/Register').then(m => ({ default: m.Register })));

const ChatPage = lazy(() => import('@/pages/Chat').then(m => ({ default: m.ChatPage })));
const ConsultationPage = lazy(() => import('@/pages/Consultation').then(m => ({ default: m.ConsultationPage })));
const ConsultationTemplatesPage = lazy(() => import('@/features/consultation/pages/ConsultationTemplatesPage').then(m => ({ default: m.ConsultationTemplatesPage })));

// Settings 模块 - 系统设置
const SystemSettingsPage = lazy(() => import('@/features/settings/pages/SystemSettingsPage').then(m => ({ default: m.SystemSettingsPage })));

const KnowledgePage = lazy(() => import('@/pages/Knowledge').then(m => ({ default: m.KnowledgePage })));
const LawyerPage = lazy(() => import('@/pages/Lawyer').then(m => ({ default: m.LawyerPage })));

const ProfilePage = lazy(() => import('@/pages/Profile').then(m => ({ default: m.ProfilePage })));
const DocumentPage = lazy(() => import('@/pages/Document').then(m => ({ default: m.DocumentPage })));

const NewsPage = lazy(() => import('@/pages/News').then(m => ({ default: m.NewsPage })));
const PaymentPage = lazy(() => import('@/pages/Payment').then(m => ({ default: m.PaymentPage })));
const SettlementPage = lazy(() => import('@/pages/Settlement').then(m => ({ default: m.SettlementPage })));

const ForumListPage = lazy(() => import('@/pages/ForumListPage').then(m => ({ default: m.ForumListPage })));
const NotificationPage = lazy(() => import('@/pages/NotificationPage').then(m => ({ default: m.NotificationPage })));

// Calendar 模块 - 法律日历
const CalendarPage = lazy(() => import('@/features/calendar/pages/CalendarPage').then(m => ({ default: m.CalendarPage })));

// Contracts 模块 - 合同管理
const ContractReviewPage = lazy(() => import('@/features/contracts/pages/ContractReviewPage').then(m => ({ default: m.ContractReviewPage })));
const ContractHistoryPage = lazy(() => import('@/features/contracts/pages/ContractHistoryPage').then(m => ({ default: m.ContractHistoryPage })));

// Document 模块 - 文档管理
const DocumentTemplatesPage = lazy(() => import('@/features/document/pages/DocumentTemplatesPage').then(m => ({ default: m.DocumentTemplatesPage })));

// Points 模块 - 积分系统
const PointsHistoryPage = lazy(() => import('@/features/points/pages/PointsHistoryPage').then(m => ({ default: m.PointsHistoryPage })));
const PointsMallPage = lazy(() => import('@/features/points/pages/PointsMallPage').then(m => ({ default: m.PointsMallPage })));
const CheckInPage = lazy(() => import('@/features/points/pages/CheckInPage').then(m => ({ default: m.CheckInPage })));
const PointsActivitiesPage = lazy(() => import('@/features/points/pages/PointsActivitiesPage').then(m => ({ default: m.PointsActivitiesPage })));
const PointsRulesPage = lazy(() => import('@/features/points/pages/PointsRulesPage').then(m => ({ default: m.PointsRulesPage })));

// Promotion 模块 - 推广系统
const PromotionPage = lazy(() => import('@/features/promotion/pages/PromotionPage').then(m => ({ default: m.PromotionPage })));
const WithdrawalPage = lazy(() => import('@/features/promotion/pages/WithdrawalPage').then(m => ({ default: m.WithdrawalPage })));

// Analytics 模块 - 数据分析统计
const AnalyticsDashboardPage = lazy(() => import('@/features/analytics/pages/AnalyticsDashboardPage').then(m => ({ default: m.AnalyticsDashboardPage })));
const FunnelAnalysisPage = lazy(() => import('@/features/analytics/pages/FunnelAnalysisPage').then(m => ({ default: m.FunnelAnalysisPage })));
const BehaviorAnalysisPage = lazy(() => import('@/features/analytics/pages/BehaviorAnalysisPage').then(m => ({ default: m.BehaviorAnalysisPage })));
const RetentionAnalysisPage = lazy(() => import('@/features/analytics/pages/RetentionAnalysisPage').then(m => ({ default: m.RetentionAnalysisPage })));

// Channel 模块 - 渠道管理
const ChannelPage = lazy(() => import('@/features/channel/pages/ChannelPage').then(m => ({ default: m.ChannelPage })));

// VerticalChannel 模块 - 垂直频道
const VerticalChannelPage = lazy(() => import('@/features/vertical-channel/pages/VerticalChannelPage').then(m => ({ default: m.VerticalChannelPage })));

// Enterprise 模块 - 企业服务
const EnterprisePage = lazy(() => import('@/features/enterprise/pages/EnterprisePage').then(m => ({ default: m.EnterprisePage })));

// Cross-Domain 模块 - 跨域管理
const CrossDomainPage = lazy(() => import('@/features/cross-domain/pages/CrossDomainPage').then(m => ({ default: m.CrossDomainPage })));

// System-Config 模块 - 系统配置
const SystemConfigPage = lazy(() => import('@/features/system-config/pages/SystemConfigPage').then(m => ({ default: m.SystemConfigPage })));

// Forum-Admin 模块 - 论坛管理
const ForumAdminPage = lazy(() => import('@/features/forum-admin/pages/ForumAdminPage').then(m => ({ default: m.ForumAdminPage })));

// News-Admin 模块 - 新闻管理
const NewsAdminPage = lazy(() => import('@/features/news-admin/pages/NewsAdminPage').then(m => ({ default: m.NewsAdminPage })));
const NewsIngestRunsPage = lazy(() => import('@/features/news-admin/pages/NewsIngestRunsPage').then(m => ({ default: m.NewsIngestRunsPage })));
const NewsSourcesPage = lazy(() => import('@/features/news-admin/pages/NewsSourcesPage').then(m => ({ default: m.NewsSourcesPage })));
const NewsTopicsPage = lazy(() => import('@/features/news-admin/pages/NewsTopicsPage').then(m => ({ default: m.NewsTopicsPage })));
const NewsCommentsPage = lazy(() => import('@/features/news-admin/pages/NewsCommentsPage').then(m => ({ default: m.NewsCommentsPage })));

// Membership 模块 - 会员系统
const VipPage = lazy(() => import('@/features/membership/pages/VipPage').then(m => ({ default: m.VipPage })));

// Lawyer-Matching 模块 - 律师匹配
const LawyerMatchingPage = lazy(() => import('@/features/lawyer-matching/pages/LawyerMatchingPage').then(m => ({ default: m.LawyerMatchingPage })));

// Lawyer 模块 - 律师管理
const LawyerVerificationAdminPage = lazy(() => import('@/features/lawyer/pages/LawyerVerificationAdminPage').then(m => ({ default: m.LawyerVerificationAdminPage })));
const LawFirmsPage = lazy(() => import('@/features/lawyer/pages/LawFirmsPage').then(m => ({ default: m.LawFirmsPage })));

// AI-Consultation 模块 - AI 咨询
const AIConsultationPage = lazy(() => import('@/features/ai-consultation/pages/AIConsultationPage').then(m => ({ default: m.AIConsultationPage })));

// Post 模块 - 帖子管理
const PostListPage = lazy(() => import('@/features/post/pages/PostListPage').then(m => ({ default: m.PostListPage })));
const PostDetailPage = lazy(() => import('@/features/post/pages/PostDetailPage').then(m => ({ default: m.PostDetailPage })));
const NewPostPage = lazy(() => import('@/features/post/pages/NewPostPage').then(m => ({ default: m.NewPostPage })));
const EditPostPage = lazy(() => import('@/features/post/pages/EditPostPage').then(m => ({ default: m.EditPostPage })));
const PostsManagePage = lazy(() => import('@/features/post/pages/PostsManagePage').then(m => ({ default: m.PostsManagePage })));

// Forum-Assistant 模块 - 论坛助手
const ForumAssistantPage = lazy(() => import('@/features/forum-assistant/pages/ForumAssistantPage').then(m => ({ default: m.ForumAssistantPage })));

// Search 模块 - 搜索系统
const SearchPage = lazy(() => import('@/features/search/pages/SearchPage').then(m => ({ default: m.SearchPage })));

// Feedback 模块 - 用户反馈系统
const FeedbackPage = lazy(() => import('@/features/feedback/pages/FeedbackPage').then(m => ({ default: m.FeedbackPage })));

// FAQ 模块 - 常见问题
const FAQPage = lazy(() => import('@/features/faq/pages/FAQPage').then(m => ({ default: m.FAQPage })));
const FAQAdminPage = lazy(() => import('@/features/faq/pages/FAQAdminPage').then(m => ({ default: m.FAQAdminPage })));

// Order 模块 - 订单管理
const OrderListPage = lazy(() => import('@/features/order/pages/OrderListPage').then(m => ({ default: m.OrderListPage })));
const OrderDetailPage = lazy(() => import('@/features/order/pages/OrderDetailPage').then(m => ({ default: m.OrderDetailPage })));

// Payment 模块 - 支付回调管理（管理员用）
const PaymentCallbacksPage = lazy(() => import('@/features/payment/pages/PaymentCallbacksPage').then(m => ({ default: m.PaymentCallbacksPage })));
const SettlementStatsPage = lazy(() => import('@/features/payment/pages/SettlementStatsPage').then(m => ({ default: m.SettlementStatsPage })));

// Notification 模块 - 通知中心
const NotificationCenterPage = lazy(() => import('@/features/notification/pages/NotificationCenter').then(m => ({ default: m.NotificationCenter })));
const SystemNotificationsPage = lazy(() => import('@/features/notification/pages/SystemNotificationsPage').then(m => ({ default: m.SystemNotificationsPage })));

// Wechat 模块 - 微信生态
const WechatPage = lazy(() => import('@/features/wechat/pages/WechatPage').then(m => ({ default: m.WechatPage })));
const WechatCallbackPage = lazy(() => import('@/features/wechat/pages/WechatCallbackPage').then(m => ({ default: m.WechatCallbackPage })));
const WechatOfficialAccountPage = lazy(() => import('@/features/wechat/pages/WechatOfficialAccountPage').then(m => ({ default: m.WechatOfficialAccountPage })));

// Security 模块 - 安全中心
const SecurityPage = lazy(() => import('@/features/security/pages/SecurityPage').then(m => ({ default: m.SecurityPage })));
const TwoFactorSetupPage = lazy(() => import('@/features/security/pages/TwoFactorSetupPage').then(m => ({ default: m.TwoFactorSetupPage })));
const LoginAuditPage = lazy(() => import('@/features/security/pages/LoginAuditPage').then(m => ({ default: m.LoginAuditPage })));
const DeviceListPage = lazy(() => import('@/features/security/pages/DeviceListPage').then(m => ({ default: m.DeviceListPage })));

// 管理后台 - 单独打包
const AdminDashboardPage = lazy(() => import('@/features/admin/pages/AdminDashboardPage').then(m => ({ default: m.AdminDashboardPage })));

// Admin Monitor 模块 - 系统监控
const MonitorPage = lazy(() => import('@/features/admin_monitor/pages/MonitorPage').then(m => ({ default: m.MonitorPage })));

// Promotion 模块 - 提现管理（管理员用）
const WithdrawalsAdminPage = lazy(() => import('@/features/promotion/pages/WithdrawalsAdminPage').then(m => ({ default: m.WithdrawalsAdminPage })));

// Knowledge-Admin 模块 - 知识库管理
const KnowledgeAdminPage = lazy(() => import('@/features/knowledge_admin/pages/KnowledgeAdminPage').then(m => ({ default: m.KnowledgeAdminPage })));

// AI Quality 模块 - AI质量监控
const AIQualityPage = lazy(() => import('@/features/ai_quality/pages/AIQualityPage').then(m => ({ default: m.AIQualityPage })));

// Moderation 模块 - 内容审核
const ModerationPage = lazy(() => import('@/features/moderation/pages/ModerationPage').then(m => ({ default: m.ModerationPage })));

// 懒加载包装器
const lazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'login', element: lazyLoad(LoginPage) },
      { path: 'register', element: lazyLoad(RegisterPage) },
      { path: 'chat', element: lazyLoad(ChatPage) },
      { path: 'consultation', element: lazyLoad(ConsultationPage) },
      { path: 'knowledge', element: lazyLoad(KnowledgePage) },
      { path: 'lawyer', element: lazyLoad(LawyerPage) },
      { path: 'profile', element: lazyLoad(ProfilePage) },
      { path: 'document', element: lazyLoad(DocumentPage) },
      { path: 'news', element: lazyLoad(NewsPage) },
      { path: 'payment', element: lazyLoad(PaymentPage) },
      { path: 'settlement', element: lazyLoad(SettlementPage) },
      { path: 'forum', element: lazyLoad(ForumListPage) },
      { path: 'calendar', element: lazyLoad(CalendarPage) },
      { path: 'notifications', element: lazyLoad(NotificationPage) },
      { path: 'contracts', element: lazyLoad(ContractReviewPage) },
      { path: 'contracts/history', element: lazyLoad(ContractHistoryPage) },
      { path: 'points', element: lazyLoad(PointsMallPage) },
      { path: 'points/history', element: lazyLoad(PointsHistoryPage) },
      { path: 'points/mall', element: lazyLoad(PointsMallPage) },
      { path: 'points/checkin', element: lazyLoad(CheckInPage) },
      { path: 'points/activities', element: lazyLoad(PointsActivitiesPage) },
      { path: 'points/rules', element: lazyLoad(PointsRulesPage) },
      { path: 'promotion', element: lazyLoad(PromotionPage) },
      { path: 'promotion/withdrawal', element: lazyLoad(WithdrawalPage) },
      { path: 'analytics', element: lazyLoad(AnalyticsDashboardPage) },
      { path: 'analytics/funnel', element: lazyLoad(FunnelAnalysisPage) },
      { path: 'analytics/behavior', element: lazyLoad(BehaviorAnalysisPage) },
      { path: 'analytics/retention', element: lazyLoad(RetentionAnalysisPage) },
      { path: 'channels', element: lazyLoad(ChannelPage) },
      { path: 'vertical-channel', element: lazyLoad(VerticalChannelPage) },
      { path: 'vertical-channel/:channelKey', element: lazyLoad(VerticalChannelPage) },
      { path: 'enterprise', element: lazyLoad(EnterprisePage) },
      { path: 'cross-domain', element: lazyLoad(CrossDomainPage) },
      { path: 'system-config', element: lazyLoad(SystemConfigPage) },
      { path: 'vip', element: lazyLoad(VipPage) },
      { path: 'membership', element: lazyLoad(VipPage) },
      { path: 'lawyer-matching', element: lazyLoad(LawyerMatchingPage) },
      { path: 'orders', element: lazyLoad(OrderListPage) },
      { path: 'orders/:orderNo', element: lazyLoad(OrderDetailPage) },
      { path: 'ai-consultation', element: lazyLoad(AIConsultationPage) },
      { path: 'posts', element: lazyLoad(PostListPage) },
      { path: 'posts/new', element: lazyLoad(NewPostPage) },
      { path: 'posts/:id', element: lazyLoad(PostDetailPage) },
      { path: 'posts/:id/edit', element: lazyLoad(EditPostPage) },
      { path: 'forum-assistant', element: lazyLoad(ForumAssistantPage) },
      { path: 'search', element: lazyLoad(SearchPage) },
      { path: 'feedback', element: lazyLoad(FeedbackPage) },
      { path: 'faq', element: lazyLoad(FAQPage) },
      { path: 'admin', element: lazyLoad(AdminDashboardPage) },
      { path: 'admin/faq', element: lazyLoad(FAQAdminPage) },
      { path: 'admin/*', element: lazyLoad(AdminDashboardPage) },
      { path: 'admin/monitor', element: lazyLoad(MonitorPage) },
      { path: 'admin/ai-quality', element: lazyLoad(AIQualityPage) },
      { path: 'admin/moderation', element: lazyLoad(ModerationPage) },
      { path: 'forum-admin', element: lazyLoad(ForumAdminPage) },
      { path: 'news-admin', element: lazyLoad(NewsAdminPage) },
      { path: 'admin/news/ingest-runs', element: lazyLoad(NewsIngestRunsPage) },
      { path: 'admin/news/sources', element: lazyLoad(NewsSourcesPage) },
      { path: 'admin/news/topics', element: lazyLoad(NewsTopicsPage) },
      { path: 'admin/news/comments', element: lazyLoad(NewsCommentsPage) },
      { path: 'admin/lawyer/verifications', element: lazyLoad(LawyerVerificationAdminPage) },
      { path: 'admin/lawyer/firms', element: lazyLoad(LawFirmsPage) },
      { path: 'admin/withdrawals', element: lazyLoad(WithdrawalsAdminPage) },
      { path: 'admin/posts', element: lazyLoad(PostsManagePage) },
      { path: 'admin/payment/callbacks', element: lazyLoad(PaymentCallbacksPage) },
      { path: 'admin/payment/settlement', element: lazyLoad(SettlementStatsPage) },
      { path: 'admin/notifications', element: lazyLoad(SystemNotificationsPage) },
      { path: 'admin/document-templates', element: lazyLoad(DocumentTemplatesPage) },
      { path: 'admin/consultation-templates', element: lazyLoad(ConsultationTemplatesPage) },
      { path: 'admin/settings', element: lazyLoad(SystemSettingsPage) },
      { path: 'admin/knowledge', element: lazyLoad(KnowledgeAdminPage) },
      // Notification 模块路由
      { path: 'notifications', element: lazyLoad(NotificationCenterPage) },
      // Wechat 模块路由
      { path: 'wechat', element: lazyLoad(WechatPage) },
      { path: 'wechat/callback', element: lazyLoad(WechatCallbackPage) },
      { path: 'wechat/official-account', element: lazyLoad(WechatOfficialAccountPage) },
      // Security 模块路由 - 安全中心
      { path: 'security', element: lazyLoad(SecurityPage) },
      { path: 'security/2fa-setup', element: lazyLoad(TwoFactorSetupPage) },
      { path: 'security/audit-logs', element: lazyLoad(LoginAuditPage) },
      { path: 'security/devices', element: lazyLoad(DeviceListPage) },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);

export function AppRouter(): JSX.Element {
  return <RouterProvider router={router} />;
}