import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const PointsMallPage = lazy(() => import('@/features/points/pages/PointsMallPage').then(m => ({ default: m.PointsMallPage })));
const PointsHistoryPage = lazy(() => import('@/features/points/pages/PointsHistoryPage').then(m => ({ default: m.PointsHistoryPage })));
const CheckInPage = lazy(() => import('@/features/points/pages/CheckInPage').then(m => ({ default: m.CheckInPage })));
const PointsActivitiesPage = lazy(() => import('@/features/points/pages/PointsActivitiesPage').then(m => ({ default: m.PointsActivitiesPage })));
const PointsRulesPage = lazy(() => import('@/features/points/pages/PointsRulesPage').then(m => ({ default: m.PointsRulesPage })));
const PromotionPage = lazy(() => import('@/features/promotion/pages/PromotionPage').then(m => ({ default: m.PromotionPage })));

export const pointsRoutes: RouteObject[] = [
  { path: 'points', element: LazyLoad(PointsMallPage) },
  { path: 'points/history', element: LazyLoad(PointsHistoryPage) },
  { path: 'points/mall', element: LazyLoad(PointsMallPage) },
  { path: 'points/checkin', element: LazyLoad(CheckInPage) },
  { path: 'points/activities', element: LazyLoad(PointsActivitiesPage) },
  { path: 'points/rules', element: LazyLoad(PointsRulesPage) },
  { path: 'promotion', element: LazyLoad(PromotionPage) },
  { path: 'promotion/withdrawal', element: LazyLoad(PointsMallPage) },
];
