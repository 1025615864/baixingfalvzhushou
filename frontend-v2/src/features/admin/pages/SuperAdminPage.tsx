/**
 * 超级管理员 Dashboard
 * 全量系统管理：用户管理、系统监控、系统设置、角色分配
 */

import React, { Suspense, lazy, useState } from 'react';
import {
  Crown, Users, Activity, Settings, Shield, Scale,
  LayoutDashboard, Newspaper, Brain, Headphones, MessageSquare,
} from 'lucide-react';
import { AdminShell } from '@/features/admin-shared/components/AdminShell';
import type { SidebarMenuItem } from '@/features/admin-shared/components/SidebarShell';

const LazyAdminOverviewPanel = lazy(() =>
  import('@/features/admin/components/AdminOverviewPanel').then(m => ({ default: m.AdminOverviewPanel }))
);
const LazyAdminUsersPanel = lazy(() =>
  import('@/features/admin/components/AdminUsersPanel').then(m => ({ default: m.AdminUsersPanel }))
);
const LazySystemMonitorPanel = lazy(() =>
  import('@/features/admin/components/SystemMonitorPanel').then(m => ({ default: m.SystemMonitorPanel }))
);
const LazySystemSettingsPanel = lazy(() =>
  import('@/features/admin/components/SystemSettingsPanel').then(m => ({ default: m.SystemSettingsPanel }))
);
const LazyAdminExportPanel = lazy(() =>
  import('@/features/admin/components/AdminExportPanel').then(m => ({ default: m.AdminExportPanel }))
);

function SectionSkeleton({ rows = 3 }: { rows?: number }): JSX.Element {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

const menuItems: SidebarMenuItem[] = [
  {
    key: '/admin/super',
    label: '总览',
    icon: React.createElement(LayoutDashboard, { className: 'w-4 h-4' }),
  },
  {
    key: '/admin/super/users',
    label: '用户管理',
    icon: React.createElement(Users, { className: 'w-4 h-4' }),
  },
  {
    key: '/admin/super/monitor',
    label: '系统监控',
    icon: React.createElement(Activity, { className: 'w-4 h-4' }),
  },
  {
    key: '/admin/super/settings',
    label: '系统设置',
    icon: React.createElement(Settings, { className: 'w-4 h-4' }),
  },
  {
    key: '/admin/super/export',
    label: '数据导出',
    icon: React.createElement(Shield, { className: 'w-4 h-4' }),
  },
  {
    key: 'sub-dashboards',
    label: '子管理面板',
    icon: React.createElement(Crown, { className: 'w-4 h-4' }),
    children: [
      { key: '/admin/forum', label: '论坛管理', icon: React.createElement(MessageSquare, { className: 'w-3 h-3' }) },
      { key: '/admin/news', label: '新闻管理', icon: React.createElement(Newspaper, { className: 'w-3 h-3' }) },
      { key: '/admin/ai', label: 'AI 管理', icon: React.createElement(Brain, { className: 'w-3 h-3' }) },
      { key: '/admin/lawyer', label: '律师管理', icon: React.createElement(Scale, { className: 'w-3 h-3' }) },
      { key: '/admin/cs', label: '客服工作台', icon: React.createElement(Headphones, { className: 'w-3 h-3' }) },
    ],
  },
];

export function SuperAdminPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <Suspense fallback={<SectionSkeleton rows={3} />}>
            <LazyAdminOverviewPanel onNavigate={setActiveTab} />
          </Suspense>
        );
      case 'users':
        return (
          <Suspense fallback={<SectionSkeleton rows={4} />}>
            <LazyAdminUsersPanel />
          </Suspense>
        );
      case 'monitor':
        return (
          <Suspense fallback={<SectionSkeleton rows={4} />}>
            <LazySystemMonitorPanel />
          </Suspense>
        );
      case 'settings':
        return (
          <Suspense fallback={<SectionSkeleton rows={4} />}>
            <LazySystemSettingsPanel />
          </Suspense>
        );
      case 'export':
        return (
          <Suspense fallback={<SectionSkeleton rows={3} />}>
            <LazyAdminExportPanel />
          </Suspense>
        );
      default:
        return (
          <Suspense fallback={<SectionSkeleton rows={3} />}>
            <LazyAdminOverviewPanel onNavigate={setActiveTab} />
          </Suspense>
        );
    }
  };

  return (
    <AdminShell title="超级管理" subtitle="系统全量管理" menuItems={menuItems} selectedKey={activeTab}>
      {renderContent()}
    </AdminShell>
  );
}