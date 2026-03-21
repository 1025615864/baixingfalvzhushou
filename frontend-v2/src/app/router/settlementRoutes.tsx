import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const WalletPage = lazy(() => import('@/features/settlement/pages/WalletPage').then(m => ({ default: m.WalletPage })));
const IncomePage = lazy(() => import('@/features/settlement/pages/IncomePage').then(m => ({ default: m.IncomePage })));
const WithdrawalPage = lazy(() => import('@/features/settlement/pages/WithdrawalPage').then(m => ({ default: m.WithdrawalPage })));
const BankAccountPage = lazy(() => import('@/features/settlement/pages/BankAccountPage').then(m => ({ default: m.BankAccountPage })));

export const settlementRoutes: RouteObject[] = [
  { path: 'settlement/wallet', element: LazyLoad(WalletPage) },
  { path: 'settlement/income', element: LazyLoad(IncomePage) },
  { path: 'settlement/withdrawal', element: LazyLoad(WithdrawalPage) },
  { path: 'settlement/bank-account', element: LazyLoad(BankAccountPage) },
];
