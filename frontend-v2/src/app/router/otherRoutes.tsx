import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const RecommendationPage = lazy(() => import('@/features/recommendation/pages/RecommendationPage').then(m => ({ default: m.RecommendationPage })));
const OnboardingPage = lazy(() => import('@/features/recommendation/pages/OnboardingPage').then(m => ({ default: m.OnboardingPage })));
const ContractReviewPage = lazy(() => import('@/features/contracts/pages/ContractReviewPage').then(m => ({ default: m.ContractReviewPage })));
const ContractHistoryPage = lazy(() => import('@/features/contracts/pages/ContractHistoryPage').then(m => ({ default: m.ContractHistoryPage })));
const FeedbackPage = lazy(() => import('@/features/feedback/pages/FeedbackPage').then(m => ({ default: m.FeedbackPage })));
const WechatPage = lazy(() => import('@/features/wechat/pages/WechatPage').then(m => ({ default: m.WechatPage })));
const WechatCallbackPage = lazy(() => import('@/features/wechat/pages/WechatCallbackPage').then(m => ({ default: m.WechatCallbackPage })));
const WechatOfficialAccountPage = lazy(() => import('@/features/wechat/pages/WechatOfficialAccountPage').then(m => ({ default: m.WechatOfficialAccountPage })));
const NotificationCenterPage = lazy(() => import('@/features/notification/pages/NotificationCenter').then(m => ({ default: m.NotificationCenter })));

export const otherRoutes: RouteObject[] = [
  { path: 'recommendation', element: LazyLoad(RecommendationPage) },
  { path: 'onboarding', element: LazyLoad(OnboardingPage) },
  { path: 'contracts', element: LazyLoad(ContractReviewPage) },
  { path: 'contracts/history', element: LazyLoad(ContractHistoryPage) },
  { path: 'feedback', element: LazyLoad(FeedbackPage) },
  { path: 'wechat', element: LazyLoad(WechatPage) },
  { path: 'wechat/callback', element: LazyLoad(WechatCallbackPage) },
  { path: 'wechat/official-account', element: LazyLoad(WechatOfficialAccountPage) },
  { path: 'notifications', element: LazyLoad(NotificationCenterPage) },
];
