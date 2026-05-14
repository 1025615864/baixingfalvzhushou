/**
 * 通用管理员 Dashboard
 * 内容总览、数据导出、用户查询
 */

import React, { Suspense, lazy, useState } from 'react';
import { LayoutDashboard, FileDown, Users, Shield } from 'lucide-react';
import { AdminShell } from '@/features/admin-shared/components/AdminShell';
import type { SidebarMenuItem } from '@/features/admin-shared/components/SidebarShell';

const LazyAdminOverviewPanel = lazy(() =>
  import('@/features/admin/components/AdminOverviewPanel').then(m => ({ default: m.AdminOverviewPanel }))
);
const LazyAdminExportPanel = lazy(() =>
  import('@/features/admin/components/AdminExportPanel').then(m => ({ default: m.AdminExportPanel }))
);
const LazyAdminUsersPanel = lazy(() =>
  import('@/features/admin/components/AdminUsersPanel').then(m => ({ default: m.AdminUsersPanel }))
);

function SectionSkeleton(): JSX.Element {
  return <div className="space-y-4">{[1, 2, 3].map(i => <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100" />)}</div>;
}

const menuItems: SidebarMenuItem[] = [
  { key: 'overview', label: '总览', icon: React.createElement(LayoutDashboard, { className: 'w-4 h-4' }) },
  { key: 'export', label: '数据导出', icon: React.createElement(FileDown, { className: 'w-4 h-4' }) },
  { key: 'users', label: '用户查询', icon: React.createElement(Users, { className: 'w-4 h-4' }) },
];

export function GeneralAdminPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <Suspense fallback={<SectionSkeleton />}><LazyAdminOverviewPanel onNavigate={setActiveTab} /></Suspense>;
      case 'export':
        return <Suspense fallback={<SectionSkeleton />}><LazyAdminExportPanel /></Suspense>;
      case 'users':
        return <Suspense fallback={<SectionSkeleton />}><LazyAdminUsersPanel /></Suspense>;
      default:
        return <Suspense fallback={<SectionSkeleton />}><LazyAdminOverviewPanel onNavigate={setActiveTab} /></Suspense>;
    }
  };

  return (
    <AdminShell title="通用管理" subtitle="内容与数据管理" menuItems={menuItems} selectedKey={activeTab}>
      {renderContent()}
    </AdminShell>
  );
}