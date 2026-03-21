import { Suspense, lazy } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { Loading } from '@/shared/components/Loading';

const AdminDashboardPage = lazy(() => import('@/features/admin/pages/AdminDashboardPage').then((m) => ({ default: m.AdminDashboardPage })));
const MonitorPage = lazy(() => import('@/features/admin_monitor/pages/MonitorPage').then((m) => ({ default: m.MonitorPage })));
const AIQualityPage = lazy(() => import('@/features/ai_quality/pages/AIQualityPage').then((m) => ({ default: m.AIQualityPage })));
const ModerationPage = lazy(() => import('@/features/moderation/pages/ModerationPage').then((m) => ({ default: m.ModerationPage })));
const NewsIngestRunsPage = lazy(() => import('@/features/news-admin/pages/NewsIngestRunsPage').then((m) => ({ default: m.NewsIngestRunsPage })));
const NewsSourcesPage = lazy(() => import('@/features/news-admin/pages/NewsSourcesPage').then((m) => ({ default: m.NewsSourcesPage })));
const NewsTopicsPage = lazy(() => import('@/features/news-admin/pages/NewsTopicsPage').then((m) => ({ default: m.NewsTopicsPage })));
const NewsCommentsPage = lazy(() => import('@/features/news-admin/pages/NewsCommentsPage').then((m) => ({ default: m.NewsCommentsPage })));
const LawyerVerificationAdminPage = lazy(() => import('@/features/lawyer/pages/LawyerVerificationAdminPage').then((m) => ({ default: m.LawyerVerificationAdminPage })));
const LawFirmsPage = lazy(() => import('@/features/lawyer/pages/LawFirmsPage').then((m) => ({ default: m.LawFirmsPage })));
const WithdrawalsAdminPage = lazy(() => import('@/features/promotion/pages/WithdrawalsAdminPage').then((m) => ({ default: m.WithdrawalsAdminPage })));
const PostsManagePage = lazy(() => import('@/features/post/pages/PostsManagePage').then((m) => ({ default: m.PostsManagePage })));
const PaymentCallbacksPage = lazy(() => import('@/features/payment/pages/PaymentCallbacksPage').then((m) => ({ default: m.PaymentCallbacksPage })));
const SettlementStatsPage = lazy(() => import('@/features/payment/pages/SettlementStatsPage').then((m) => ({ default: m.SettlementStatsPage })));
const SystemNotificationsPage = lazy(() => import('@/features/notification/pages/SystemNotificationsPage').then((m) => ({ default: m.SystemNotificationsPage })));
const DocumentTemplatesPage = lazy(() => import('@/features/document/pages/DocumentTemplatesPage').then((m) => ({ default: m.DocumentTemplatesPage })));
const ConsultationTemplatesPage = lazy(() => import('@/features/consultation/pages/ConsultationTemplatesPage').then((m) => ({ default: m.ConsultationTemplatesPage })));
const SystemSettingsPage = lazy(() => import('@/features/settings/pages/SystemSettingsPage').then((m) => ({ default: m.SystemSettingsPage })));
const KnowledgeAdminPage = lazy(() => import('@/features/knowledge_admin/pages/KnowledgeAdminPage').then((m) => ({ default: m.KnowledgeAdminPage })));

function renderAdminRoute(pathname: string): JSX.Element {
  if (pathname === '/admin' || pathname === '/admin/') return <AdminDashboardPage />;
  if (pathname.startsWith('/admin/monitor')) return <MonitorPage />;
  if (pathname.startsWith('/admin/ai-quality')) return <AIQualityPage />;
  if (pathname.startsWith('/admin/moderation')) return <ModerationPage />;
  if (pathname.startsWith('/admin/news/ingest-runs')) return <NewsIngestRunsPage />;
  if (pathname.startsWith('/admin/news/sources')) return <NewsSourcesPage />;
  if (pathname.startsWith('/admin/news/topics')) return <NewsTopicsPage />;
  if (pathname.startsWith('/admin/news/comments')) return <NewsCommentsPage />;
  if (pathname.startsWith('/admin/lawyer/verifications')) return <LawyerVerificationAdminPage />;
  if (pathname.startsWith('/admin/lawyer/firms')) return <LawFirmsPage />;
  if (pathname.startsWith('/admin/withdrawals')) return <WithdrawalsAdminPage />;
  if (pathname.startsWith('/admin/posts')) return <PostsManagePage />;
  if (pathname.startsWith('/admin/payment/callbacks')) return <PaymentCallbacksPage />;
  if (pathname.startsWith('/admin/payment/settlement')) return <SettlementStatsPage />;
  if (pathname.startsWith('/admin/notifications')) return <SystemNotificationsPage />;
  if (pathname.startsWith('/admin/document-templates')) return <DocumentTemplatesPage />;
  if (pathname.startsWith('/admin/consultation-templates')) return <ConsultationTemplatesPage />;
  if (pathname.startsWith('/admin/settings')) return <SystemSettingsPage />;
  if (pathname.startsWith('/admin/knowledge')) return <KnowledgeAdminPage />;

  return <Navigate to="/admin" replace />;
}

export function AdminRouteShell(): JSX.Element {
  const { pathname } = useLocation();

  return (
    <Suspense fallback={<Loading fullScreen text="加载中..." />}>
      {renderAdminRoute(pathname)}
    </Suspense>
  );
}
