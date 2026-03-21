import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const AboutPage = lazy(() => import('@/features/static-pages/pages/AboutPage').then(m => ({ default: m.AboutPage })));
const ContactPage = lazy(() => import('@/features/static-pages/pages/ContactPage').then(m => ({ default: m.ContactPage })));
const TermsPage = lazy(() => import('@/features/static-pages/pages/TermsPage').then(m => ({ default: m.TermsPage })));
const PrivacyPage = lazy(() => import('@/features/static-pages/pages/PrivacyPage').then(m => ({ default: m.PrivacyPage })));
const HelpPage = lazy(() => import('@/features/static-pages/pages/HelpPage').then(m => ({ default: m.HelpPage })));
const FeeCalculatorPage = lazy(() => import('@/features/static-pages/pages/FeeCalculatorPage').then(m => ({ default: m.FeeCalculatorPage })));

export const staticRoutes: RouteObject[] = [
  { path: 'about', element: LazyLoad(AboutPage) },
  { path: 'contact', element: LazyLoad(ContactPage) },
  { path: 'terms', element: LazyLoad(TermsPage) },
  { path: 'privacy', element: LazyLoad(PrivacyPage) },
  { path: 'help', element: LazyLoad(HelpPage) },
  { path: 'calculator', element: LazyLoad(FeeCalculatorPage) },
  { path: 'ai-disclaimer', element: LazyLoad(TermsPage) },
];
