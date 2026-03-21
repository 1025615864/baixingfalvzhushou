import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const ProfilePage = lazy(() => import('@/pages/Profile').then(m => ({ default: m.ProfilePage })));
const UserProfilePage = lazy(() => import('@/features/user/pages/UserProfilePage').then(m => ({ default: m.UserProfilePage })));
const UserSettingsPage = lazy(() => import('@/features/user/pages/UserSettingsPage').then(m => ({ default: m.UserSettingsPage })));
const OrderListPage = lazy(() => import('@/features/order/pages/OrderListPage').then(m => ({ default: m.OrderListPage })));
const OrderDetailPage = lazy(() => import('@/features/order/pages/OrderDetailPage').then(m => ({ default: m.OrderDetailPage })));
const VipPage = lazy(() => import('@/features/membership/pages/VipPage').then(m => ({ default: m.VipPage })));
const SecurityPage = lazy(() => import('@/features/security/pages/SecurityPage').then(m => ({ default: m.SecurityPage })));
const TwoFactorSetupPage = lazy(() => import('@/features/security/pages/TwoFactorSetupPage').then(m => ({ default: m.TwoFactorSetupPage })));
const LoginAuditPage = lazy(() => import('@/features/security/pages/LoginAuditPage').then(m => ({ default: m.LoginAuditPage })));
const DeviceListPage = lazy(() => import('@/features/security/pages/DeviceListPage').then(m => ({ default: m.DeviceListPage })));

export const userRoutes: RouteObject[] = [
  { path: 'profile', element: LazyLoad(ProfilePage) },
  { path: 'user/profile', element: LazyLoad(UserProfilePage) },
  { path: 'user/settings', element: LazyLoad(UserSettingsPage) },
  { path: 'orders', element: LazyLoad(OrderListPage) },
  { path: 'orders/:orderNo', element: LazyLoad(OrderDetailPage) },
  { path: 'vip', element: LazyLoad(VipPage) },
  { path: 'membership', element: LazyLoad(VipPage) },
  { path: 'security', element: LazyLoad(SecurityPage) },
  { path: 'security/2fa-setup', element: LazyLoad(TwoFactorSetupPage) },
  { path: 'security/audit-logs', element: LazyLoad(LoginAuditPage) },
  { path: 'security/devices', element: LazyLoad(DeviceListPage) },
];
