import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const ChannelPage = lazy(() => import('@/features/channel/pages/ChannelPage').then(m => ({ default: m.ChannelPage })));
const VerticalChannelPage = lazy(() => import('@/features/vertical-channel/pages/VerticalChannelPage').then(m => ({ default: m.VerticalChannelPage })));
const EnterprisePage = lazy(() => import('@/features/enterprise/pages/EnterprisePage').then(m => ({ default: m.EnterprisePage })));
const CrossDomainPage = lazy(() => import('@/features/cross-domain/pages/CrossDomainPage').then(m => ({ default: m.CrossDomainPage })));
const SystemConfigPage = lazy(() => import('@/features/system-config/pages/SystemConfigPage').then(m => ({ default: m.SystemConfigPage })));
const LegalDocumentMallPage = lazy(() => import('@/features/legal-document-mall/pages/LegalDocumentMallPage').then(m => ({ default: m.default })));

export const channelRoutes: RouteObject[] = [
  { path: 'channels', element: LazyLoad(ChannelPage) },
  { path: 'vertical-channel', element: LazyLoad(VerticalChannelPage) },
  { path: 'vertical-channel/:channelKey', element: LazyLoad(VerticalChannelPage) },
  { path: 'enterprise', element: LazyLoad(EnterprisePage) },
  { path: 'cross-domain', element: LazyLoad(CrossDomainPage) },
  { path: 'system-config', element: LazyLoad(SystemConfigPage) },
  { path: 'legal-documents', element: LazyLoad(LegalDocumentMallPage) },
  { path: 'legal-documents/:id', element: LazyLoad(LegalDocumentMallPage) },
];
