import { lazy } from 'react';
import type { RouteObject } from 'react-router-dom';

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <React.Suspense fallback={null}>
    <Component />
  </React.Suspense>
);

const HomePage = lazy(() => import('@/pages/Home').then(m => ({ default: m.HomePage })));
const LoginPage = lazy(() => import('@/pages/auth/Login').then(m => ({ default: m.Login })));
const RegisterPage = lazy(() => import('@/pages/auth/Register').then(m => ({ default: m.Register })));

export const publicRoutes: RouteObject[] = [
  { index: true, element: LazyLoad(HomePage) },
  { path: 'login', element: LazyLoad(LoginPage) },
  { path: 'register', element: LazyLoad(RegisterPage) },
];
