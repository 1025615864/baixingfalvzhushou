import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const AnalyticsDashboardPage = lazy(() => import('@/features/analytics/pages/AnalyticsDashboardPage').then(m => ({ default: m.AnalyticsDashboardPage })));
const FunnelAnalysisPage = lazy(() => import('@/features/analytics/pages/FunnelAnalysisPage').then(m => ({ default: m.FunnelAnalysisPage })));
const BehaviorAnalysisPage = lazy(() => import('@/features/analytics/pages/BehaviorAnalysisPage').then(m => ({ default: m.BehaviorAnalysisPage })));
const RetentionAnalysisPage = lazy(() => import('@/features/analytics/pages/RetentionAnalysisPage').then(m => ({ default: m.RetentionAnalysisPage })));

export const analyticsRoutes: RouteObject[] = [
  { path: 'analytics', element: LazyLoad(AnalyticsDashboardPage) },
  { path: 'analytics/funnel', element: LazyLoad(FunnelAnalysisPage) },
  { path: 'analytics/behavior', element: LazyLoad(BehaviorAnalysisPage) },
  { path: 'analytics/retention', element: LazyLoad(RetentionAnalysisPage) },
];
