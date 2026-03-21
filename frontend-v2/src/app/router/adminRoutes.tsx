import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const AdminRouteShell = lazy(() => import('@/pages/AdminDashboardPage').then(m => ({ default: m.AdminRouteShell })));
const ForumAdminPage = lazy(() => import('@/features/forum-admin/pages/ForumAdminPage').then(m => ({ default: m.ForumAdminPage })));
const NewsAdminPage = lazy(() => import('@/features/news-admin/pages/NewsAdminPage').then(m => ({ default: m.NewsAdminPage })));

export const adminRoutes: RouteObject[] = [
  { path: 'admin/*', element: LazyLoad(AdminRouteShell) },
  { path: 'forum-admin', element: LazyLoad(ForumAdminPage) },
  { path: 'news-admin', element: LazyLoad(NewsAdminPage) },
];
