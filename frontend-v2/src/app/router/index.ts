import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { publicRoutes } from './publicRoutes';
import { mainRoutes } from './mainRoutes';
import { userRoutes } from './userRoutes';
import { consultationRoutes } from './consultationRoutes';
import { forumRoutes } from './forumRoutes';
import { settlementRoutes } from './settlementRoutes';
import { pointsRoutes } from './pointsRoutes';
import { adminRoutes } from './adminRoutes';
import { staticRoutes } from './staticRoutes';
import { analyticsRoutes } from './analyticsRoutes';
import { channelRoutes } from './channelRoutes';
import { otherRoutes } from './otherRoutes';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));
const RootLayout = lazy(() => import('@/app/layouts/RootLayout').then(m => ({ default: m.RootLayout })));
const NotFoundPage = lazy(() => import('@/pages/NotFound').then(m => ({ default: m.NotFoundPage })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const allRoutes = [
  ...publicRoutes,
  ...mainRoutes,
  ...userRoutes,
  ...consultationRoutes,
  ...forumRoutes,
  ...settlementRoutes,
  ...pointsRoutes,
  ...adminRoutes,
  ...staticRoutes,
  ...analyticsRoutes,
  ...channelRoutes,
  ...otherRoutes,
  { path: '*', element: LazyLoad(NotFoundPage) },
];

const router = createBrowserRouter([
  {
    path: '/',
    element: <LazyLoad(RootLayout) />,
    children: allRoutes,
  },
]);

export function AppRouter(): JSX.Element {
  return <RouterProvider router={router} />;
}

export { publicRoutes } from './publicRoutes';
export { mainRoutes } from './mainRoutes';
export { userRoutes } from './userRoutes';
export { consultationRoutes } from './consultationRoutes';
export { forumRoutes } from './forumRoutes';
export { settlementRoutes } from './settlementRoutes';
export { pointsRoutes } from './pointsRoutes';
export { adminRoutes } from './adminRoutes';
export { staticRoutes } from './staticRoutes';
export { analyticsRoutes } from './analyticsRoutes';
export { channelRoutes } from './channelRoutes';
export { otherRoutes } from './otherRoutes';
