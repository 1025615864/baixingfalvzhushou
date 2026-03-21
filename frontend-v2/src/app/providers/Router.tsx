import { Suspense, lazy } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import { Loading } from '@/shared/components/Loading';
import { NotFoundPage } from '@/pages/NotFound';

// 懒加载的页面 - 按功能模块分组
const RootLayout = lazy(() => import('@/app/layouts/RootLayout').then(m => ({ default: m.RootLayout })));
const HomePage = lazy(() => import('@/pages/Home').then(m => ({ default: m.HomePage })));
const LoginPage = lazy(() => import('@/pages/auth/Login').then(m => ({ default: m.Login })));
const RegisterPage = lazy(() => import('@/pages/auth/Register').then(m => ({ default: m.Register })));

const ChatPage = lazy(() => import('@/pages/Chat').then(m => ({ default: m.ChatPage })));
const ConsultationPage = lazy(() => import('@/pages/Consultation').then(m => ({ default: m.ConsultationPage })));

const KnowledgePage = lazy(() => import('@/pages/Knowledge').then(m => ({ default: m.KnowledgePage })));
const LawyerPage = lazy(() => import('@/pages/Lawyer').then(m => ({ default: m.LawyerPage })));

const ProfilePage = lazy(() => import('@/pages/Profile').then(m => ({ default: m.ProfilePage })));
const DocumentPage = lazy(() => import('@/pages/Document').then(m => ({ default: m.DocumentPage })));

const NewsPage = lazy(() => import('@/pages/News').then(m => ({ default: m.NewsPage })));
const PaymentPage = lazy(() => import('@/pages/Payment').then(m => ({ default: m.PaymentPage })));
const SettlementPage = lazy(() => import('@/pages/Settlement').then(m => ({ default: m.SettlementPage })));

// Settlement 模块 - 结算管理（新版）
const SettlementWalletPage = lazy(() => import('@/features/settlement/pages/WalletPage').then(m => ({ default: m.WalletPage })));
const SettlementIncomePage = lazy(() => import('@/features/settlement/pages/IncomePage').then(m => ({ default: m.IncomePage })));
const SettlementWithdrawalPage = lazy(() => import('@/features/settlement/pages/WithdrawalPage').then(m => ({ default: m.WithdrawalPage })));
const SettlementBankAccountPage = lazy(() => import('@/features/settlement/pages/BankAccountPage').then(m => ({ default: m.BankAccountPage })));

// User 模块 - 用户中心
const UserProfilePage = lazy(() => import('@/features/user/pages/UserProfilePage').then(m => ({ default: m.UserProfilePage })));
const UserSettingsPage = lazy(() => import('@/features/user/pages/UserSettingsPage').then(m => ({ default: m.UserSettingsPage })));

// Forum 模块 - 论坛（新版）
const ForumHomePage = lazy(() => import('@/features/forum/pages/ForumHomePage').then(m => ({ default: m.ForumHomePage })));
const ForumPostDetailPage = lazy(() => import('@/features/forum/pages/PostDetailPage').then(m => ({ default: m.PostDetailPage })));

// Chat 模块 - AI 聊天（新版）
const AIChatPage = lazy(() => import('@/features/chat/pages/ChatPage').then(m => ({ default: m.ChatPage })));

// Recommendation 模块 - 个性化推荐
const RecommendationPage = lazy(() => import('@/features/recommendation/pages/RecommendationPage').then(m => ({ default: m.RecommendationPage })));
const OnboardingPage = lazy(() => import('@/features/recommendation/pages/OnboardingPage').then(m => ({ default: m.OnboardingPage })));

const ForumListPage = lazy(() => import('@/pages/ForumListPage').then(m => ({ default: m.ForumListPage })));

// Calendar 模块 - 法律日历
const CalendarPage = lazy(() => import('@/pages/CalendarPage').then(m => ({ default: m.CalendarPage })));

// Contracts 模块 - 合同管理
const ContractReviewPage = lazy(() => import('@/features/contracts/pages/ContractReviewPage').then(m => ({ default: m.ContractReviewPage })));
const ContractHistoryPage = lazy(() => import('@/features/contracts/pages/ContractHistoryPage').then(m => ({ default: m.ContractHistoryPage })));

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

// Membership 模块 - 会员系统
const VipPage = lazy(() => import('@/features/membership/pages/VipPage').then(m => ({ default: m.VipPage })));

// Lawyer-Matching 模块 - 律师匹配
const LawyerMatchingPage = lazy(() => import('@/features/lawyer-matching/pages/LawyerMatchingPage').then(m => ({ default: m.LawyerMatchingPage })));

// AI-Consultation 模块 - AI 咨询
const AIConsultationPage = lazy(() => import('@/features/ai-consultation/pages/AIConsultationPage').then(m => ({ default: m.AIConsultationPage })));
const ConsultationFormPage = lazy(() => import('@/features/ai-consultation/pages/ConsultationFormPage').then(m => ({ default: m.ConsultationFormPage })));
const ConsultationHistoryPage = lazy(() => import('@/features/ai-consultation/pages/ConsultationHistoryPage').then(m => ({ default: m.ConsultationHistoryPage })));
const LawyerSelectionPage = lazy(() => import('@/features/ai-consultation/pages/LawyerSelectionPage').then(m => ({ default: m.LawyerSelectionPage })));
const ConsultationChatPage = lazy(() => import('@/features/ai-consultation/pages/ConsultationChatPage').then(m => ({ default: m.ConsultationChatPage })));

// Video Consultation 模块 - 视频咨询
const VideoConsultationPage = lazy(() => import('@/features/video-consultation/pages').then(m => ({ default: m.VideoConsultationPage })));

// Post 模块 - 帖子管理
const PostListPage = lazy(() => import('@/features/post/pages/PostListPage').then(m => ({ default: m.PostListPage })));
const PostDetailPage = lazy(() => import('@/features/post/pages/PostDetailPage').then(m => ({ default: m.PostDetailPage })));
const NewPostPage = lazy(() => import('@/features/post/pages/NewPostPage').then(m => ({ default: m.NewPostPage })));
const EditPostPage = lazy(() => import('@/features/post/pages/EditPostPage').then(m => ({ default: m.EditPostPage })));
// Forum-Assistant 模块 - 论坛助手
const ForumAssistantPage = lazy(() => import('@/features/forum-assistant/pages/ForumAssistantPage').then(m => ({ default: m.ForumAssistantPage })));

// Feedback 模块 - 用户反馈系统
const FeedbackPage = lazy(() => import('@/features/feedback/pages/FeedbackPage').then(m => ({ default: m.FeedbackPage })));

// Static Pages 模块 - 静态页面
const AboutPage = lazy(() => import('@/features/static-pages/pages/AboutPage').then(m => ({ default: m.AboutPage })));
const ContactPage = lazy(() => import('@/features/static-pages/pages/ContactPage').then(m => ({ default: m.ContactPage })));
const TermsPage = lazy(() => import('@/features/static-pages/pages/TermsPage').then(m => ({ default: m.TermsPage })));
const PrivacyPage = lazy(() => import('@/features/static-pages/pages/PrivacyPage').then(m => ({ default: m.PrivacyPage })));
const HelpPage = lazy(() => import('@/features/static-pages/pages/HelpPage').then(m => ({ default: m.HelpPage })));
const FeeCalculatorPage = lazy(() => import('@/features/static-pages/pages/FeeCalculatorPage').then(m => ({ default: m.FeeCalculatorPage })));

// Order 模块 - 订单管理
const OrderListPage = lazy(() => import('@/features/order/pages/OrderListPage').then(m => ({ default: m.OrderListPage })));
const OrderDetailPage = lazy(() => import('@/features/order/pages/OrderDetailPage').then(m => ({ default: m.OrderDetailPage })));

// Notification 模块 - 通知中心
const NotificationCenterPage = lazy(() => import('@/features/notification/pages/NotificationCenter').then(m => ({ default: m.NotificationCenter })));

// Wechat 模块 - 微信生态
const WechatPage = lazy(() => import('@/features/wechat/pages/WechatPage').then(m => ({ default: m.WechatPage })));
const WechatCallbackPage = lazy(() => import('@/features/wechat/pages/WechatCallbackPage').then(m => ({ default: m.WechatCallbackPage })));
const WechatOfficialAccountPage = lazy(() => import('@/features/wechat/pages/WechatOfficialAccountPage').then(m => ({ default: m.WechatOfficialAccountPage })));

// Security 模块 - 安全中心
const SecurityPage = lazy(() => import('@/features/security/pages/SecurityPage').then(m => ({ default: m.SecurityPage })));
const TwoFactorSetupPage = lazy(() => import('@/features/security/pages/TwoFactorSetupPage').then(m => ({ default: m.TwoFactorSetupPage })));
const LoginAuditPage = lazy(() => import('@/features/security/pages/LoginAuditPage').then(m => ({ default: m.LoginAuditPage })));
const DeviceListPage = lazy(() => import('@/features/security/pages/DeviceListPage').then(m => ({ default: m.DeviceListPage })));

// Admin 模块 - 聚合子路由入口（仅访问 /admin 时加载）
const AdminRouteShell = lazy(() => import('@/pages/AdminDashboardPage').then(m => ({ default: m.AdminRouteShell })));

// Legal Document Mall 模块 - 法律文书商城
const LegalDocumentMallPage = lazy(() => import('@/features/legal-document-mall/pages/LegalDocumentMallPage').then(m => ({ default: m.default })));

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
      { index: true, element: lazyLoad(HomePage) },
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
      { path: 'settlement/wallet', element: lazyLoad(SettlementWalletPage) },
      { path: 'settlement/income', element: lazyLoad(SettlementIncomePage) },
      { path: 'settlement/withdrawal', element: lazyLoad(SettlementWithdrawalPage) },
      { path: 'settlement/bank-account', element: lazyLoad(SettlementBankAccountPage) },
      // User 模块路由 - 用户中心
      { path: 'user/profile', element: lazyLoad(UserProfilePage) },
      { path: 'user/settings', element: lazyLoad(UserSettingsPage) },
      // Forum 模块路由 - 论坛（新版）
      { path: 'forum/home', element: lazyLoad(ForumHomePage) },
      { path: 'forum/post/:id', element: lazyLoad(ForumPostDetailPage) },
      // Chat 模块路由 - AI 聊天（新版）
      { path: 'ai-chat', element: lazyLoad(AIChatPage) },
      { path: 'ai-chat/:sessionId', element: lazyLoad(AIChatPage) },
      // Recommendation 模块路由 - 个性化推荐
      { path: 'recommendation', element: lazyLoad(RecommendationPage) },
      { path: 'onboarding', element: lazyLoad(OnboardingPage) },
      { path: 'forum', element: lazyLoad(ForumListPage) },
      { path: 'calendar', element: lazyLoad(CalendarPage) },
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
      { path: 'ai-consultation/:sessionId', element: lazyLoad(AIConsultationPage) },
      { path: 'video-consultation', element: lazyLoad(VideoConsultationPage) },
      { path: 'video-consultation/:id', element: lazyLoad(VideoConsultationPage) },
      { path: 'video-consultation/:id/:action', element: lazyLoad(VideoConsultationPage) },
      { path: 'consultation/new', element: lazyLoad(ConsultationFormPage) },
      { path: 'consultation/history', element: lazyLoad(ConsultationHistoryPage) },
      { path: 'consultation/:id/select-lawyer', element: lazyLoad(LawyerSelectionPage) },
      { path: 'consultation/:id/chat', element: lazyLoad(ConsultationChatPage) },
      { path: 'posts', element: lazyLoad(PostListPage) },
      { path: 'posts/new', element: lazyLoad(NewPostPage) },
      { path: 'posts/:id', element: lazyLoad(PostDetailPage) },
      { path: 'posts/:id/edit', element: lazyLoad(EditPostPage) },
      { path: 'forum-assistant', element: lazyLoad(ForumAssistantPage) },
      { path: 'feedback', element: lazyLoad(FeedbackPage) },
      { path: 'admin/*', element: lazyLoad(AdminRouteShell) },
      { path: 'forum-admin', element: lazyLoad(ForumAdminPage) },
      { path: 'news-admin', element: lazyLoad(NewsAdminPage) },
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
      // Static Pages 模块路由 - 静态页面
      { path: 'about', element: lazyLoad(AboutPage) },
      { path: 'contact', element: lazyLoad(ContactPage) },
      { path: 'terms', element: lazyLoad(TermsPage) },
      { path: 'privacy', element: lazyLoad(PrivacyPage) },
      { path: 'help', element: lazyLoad(HelpPage) },
      { path: 'calculator', element: lazyLoad(FeeCalculatorPage) },
      { path: 'ai-disclaimer', element: lazyLoad(TermsPage) }, // AI免责声明暂时重定向到用户协议
      // Legal Document Mall 模块路由 - 法律文书商城
      { path: 'legal-documents', element: lazyLoad(LegalDocumentMallPage) },
      { path: 'legal-documents/:id', element: lazyLoad(LegalDocumentMallPage) },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);

export function AppRouter(): JSX.Element {
  return <RouterProvider router={router} />;
}