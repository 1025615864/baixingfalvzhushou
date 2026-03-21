import { lazy, Suspense } from 'react';

const LazyAppRouter = lazy(() => import('@/app/providers/Router').then((module) => ({ default: module.AppRouter })));

export function App(): JSX.Element {
  return (
    <Suspense fallback={null}>
      <LazyAppRouter />
    </Suspense>
  );
}