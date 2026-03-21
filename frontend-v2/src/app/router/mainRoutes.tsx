import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const NewsPage = lazy(() => import('@/pages/News').then(m => ({ default: m.NewsPage })));
const KnowledgePage = lazy(() => import('@/pages/Knowledge').then(m => ({ default: m.KnowledgePage })));
const LawyerPage = lazy(() => import('@/pages/Lawyer').then(m => ({ default: m.LawyerPage })));
const PaymentPage = lazy(() => import('@/pages/Payment').then(m => ({ default: m.PaymentPage })));
const SettlementPage = lazy(() => import('@/pages/Settlement').then(m => ({ default: m.SettlementPage })));
const ForumListPage = lazy(() => import('@/pages/ForumListPage').then(m => ({ default: m.ForumListPage })));
const CalendarPage = lazy(() => import('@/pages/CalendarPage').then(m => ({ default: m.CalendarPage })));
const NotificationPage = lazy(() => import('@/pages/NotificationPage').then(m => ({ default: m.NotificationPage })));

export const mainRoutes: RouteObject[] = [
  { path: 'news', element: LazyLoad(NewsPage) },
  { path: 'knowledge', element: LazyLoad(KnowledgePage) },
  { path: 'lawyer', element: LazyLoad(LawyerPage) },
  { path: 'payment', element: LazyLoad(PaymentPage) },
  { path: 'settlement', element: LazyLoad(SettlementPage) },
  { path: 'forum', element: LazyLoad(ForumListPage) },
  { path: 'calendar', element: LazyLoad(CalendarPage) },
  { path: 'notifications', element: LazyLoad(NotificationPage) },
];
